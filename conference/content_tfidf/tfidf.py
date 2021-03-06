from sklearn.feature_extraction.text import TfidfVectorizer
import os
import re
import pandas as pd
import nltk
nltk.download('stopwords')
import boto3
import boto3.s3
from nltk.corpus import stopwords
from dotenv import load_dotenv
import logging
from botocore.exceptions import ClientError

load_dotenv(verbose=True)

aws_access_key=os.getenv("AWS_ACCESS_KEY")
aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")



s3_client = boto3.client('s3', 
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_access_key,
    region_name='ap-northeast-2'
)


def upload_file_to_s3(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def download_file_from_s3(file_name, bucket, object_name=None):

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    try:
        s3_client.download_file(bucket, object_name, file_name)

    except ClientError as e:
        print(e)
        logging.error(e)
        return False
    return True



class ContentTFIDF:
    
    def __init__(self, data):
        self.data = data
     
 
    def cleanText(self, text_data_in_list):
        text = re.sub('[-=+#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…》]','', str(text_data_in_list))
        return text

    def preprocess(self):
        genre = []
        for i in self.data['artist_genre']:
            if i == '[]':
                i = 'NA'
                genre.append(i.strip()) #"'[]'"
            else:
                i = self.cleanText(i)
                genre.append(i.strip())
        self.data['genre'] = genre
        self.data = self.data[self.data['genre'] != "NA"]
        self.data = self.data.reset_index()
        self.data['track_popularity'] = self.data['track_popularity'] / 100 


    def calculateTFIDF(self):
        tfidf = TfidfVectorizer(analyzer='word', ngram_range=(1,2) ,stop_words=stopwords.words('english'))
        tfidf_content = tfidf.fit_transform(self.data['genre'])
        tfidf_dict = tfidf.get_feature_names()

        return tfidf_dict, tfidf_content

    def saveTFIDF(self, path = "./data"):
        tfidf_dict, tfidf_content = self.calculateTFIDF()
        tfidf_array = tfidf_content.toarray()
        tfidf_matrix = pd.DataFrame(tfidf_array, columns = tfidf_dict)
        tfidf_file = 'tfidf_matrix.csv'
        if path == None:
            tfidf_path = tfidf_file
        else:
            tfidf_path = os.path.join(path, tfidf_file)
        tfidf_matrix.to_csv(tfidf_path, encoding = 'utf-8', index = False)

if __name__ == "__main__":
    download_file_from_s3("./data/dataset.json", "spotify-recomendation-dataset", "dataset.json")
    data = pd.read_json('./data/dataset.json', encoding = 'utf-8', orient='records')
    ctfidf = ContentTFIDF(data)
    ctfidf.preprocess()
    ctfidf.saveTFIDF()
    upload_file_to_s3("./data/tfidf_matrix.csv", "spotify-tfidf", "tfidf_matrix.csv")