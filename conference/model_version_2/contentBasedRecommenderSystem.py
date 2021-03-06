import os
import re
import logging
import argparse
import numpy as np
import pandas as pd
import boto3
import boto3.s3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity

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


class ContentBasedRecommenderSystem:
    
    def __init__(self, data, tfidf, music, mood, speed, emotion):
        self.data = data
        self.tfidf = tfidf
        self.music = music
        self.mood = mood
        self.speed = speed
        self.emotion = emotion
        self.result = pd.DataFrame()

    def cleanText(self, text_data):
        text = re.sub('[-=+#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…》]','', str(text_data))
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

    def euclidean_distance(self, x, y):   
        return np.sqrt(np.sum((x - y) ** 2))
    
    def recommend_features(self, top=200):
        scaler = MinMaxScaler()
        index = self.data[self.data['track_name'] == self.music].index.values
        track_new = self.data[['danceability', 'energy', 'valence', 'tempo', 'acousticness']]
        track_scaled = scaler.fit_transform(track_new)
        target_index = track_scaled[index]

        euclidean = []
        for value in track_scaled:
            eu = self.euclidean_distance(target_index, value)
            euclidean.append(eu)

        self.data['euclidean_distance'] = euclidean
        result_features = self.data.sort_values(by='euclidean_distance', ascending=True)[:top]

        return result_features[['id','artist_name', 'track_name', 'euclidean_distance']]

    
    def recommend_genre(self, top=200):
        # 코사인 유사도
        ts_genre = cosine_similarity(self.tfidf, self.tfidf)

        #특정 장르 정보 뽑아오기
        target_genre_index = self.data[self.data['track_name'] == self.music].index.values

        # 입력한 영화의 유사도 데이터 프레임 추가
        self.data["cos_similarity"] = ts_genre[target_genre_index, :].reshape(-1,1)
        sim_genre = self.data.sort_values(by="cos_similarity", ascending=False)
        final_index = sim_genre.index.values[ : top]
        result_genre = self.data.iloc[final_index]

        return result_genre[['id','artist_name', 'track_name', 'cos_similarity']]

    
    def get_feature_genre_intersection(self):
        recommended_feature = self.recommend_features()
        recommended_genre = self.recommend_genre()
        intersection = pd.merge(recommended_feature, recommended_genre, how='inner')
        similarity = intersection[['euclidean_distance', 'cos_similarity']]
        scaler = MinMaxScaler()
        scale = scaler.fit_transform(similarity)
        scale = pd.DataFrame(scale, columns=['eu_scaled', 'cos_scaled'])
        
        intersection['euclidean_scaled'] = scale['eu_scaled']
        intersection['cosine_scaled'] = scale['cos_scaled']
        intersection['ratio'] = intersection['euclidean_scaled'] + (1 - intersection['cosine_scaled'])
        result_intersection = intersection.sort_values('ratio', ascending=True)
        self.result = pd.merge(self.data, result_intersection, how='inner').sort_values(by='ratio')
        
        return self.result

    
    def get_genre_score(self):
        cosine_sim_score = cosine_similarity(self.tfidf, self.tfidf)
        target_genre_index = self.result[self.result['track_name'] == self.music].index.values
        genre_score = cosine_sim_score[target_genre_index, :].reshape(-1, 1)
        return genre_score

    
    def get_mood_score(self):
        temp = pd.DataFrame(self.result['valence'])
        if self.mood == 1:
            temp['mood_score'] = temp['valence']
        else:
            temp['mood_score'] = temp['valence'].apply(lambda x: 1-x)
        return temp['mood_score']
    
    
    def get_speed_score(self):
        temp = pd.DataFrame(self.result['tempo'])
        temp['tempo_scaled'] = MinMaxScaler().fit_transform(pd.DataFrame(temp['tempo']))
        if self.speed == 1:
            temp['speed_score'] = temp['tempo_scaled']
        else:
            temp['speed_score'] = temp['tempo_scaled'].apply(lambda x: 1-x)
        return temp['speed_score']

    
    def get_emotion_score(self):
        temp = self.result[['danceability', 'energy', 'acousticness']]
        temp['danceability_scaled'] = MinMaxScaler().fit_transform((pd.DataFrame(temp['danceability'])))
        temp['acousticness_reverse'] = temp['acousticness'].apply(lambda x: 1-x)
        if self.emotion == 1:
            temp['emotion_score'] = temp.apply(lambda x: 1/3 * (x['danceability_scaled'] + x['energy'] + x['acousticness_reverse']), axis = 1)
        elif self.emotion == 2:
            temp['emotion_score'] = temp.apply(lambda x: 2/3 * (abs(x['danceability_scaled']-0.5) + abs(x['energy']-0.5) + abs(x['acousticness_reverse']-0.5)), axis = 1)
        else:
            temp['emotion_score'] = temp.apply(lambda x: 1/3 * ((1-x['danceability_scaled']) + (1-x['energy']) + (1-x['acousticness_reverse'])), axis = 1)
        return temp['emotion_score']

    def get_total_score(self, top_n = 20):
        result_df = self.result[['artist_name', 'track_name', 'album_name']]
        result_df['mood_score'] = pd.DataFrame(self.get_mood_score())
        result_df['speed_score'] = pd.DataFrame(self.get_speed_score())
        result_df['emotion_score'] = pd.DataFrame(self.get_emotion_score())
        result_df['genre_score'] = pd.DataFrame(self.get_genre_score())
        result_df['total_score'] = result_df.apply(lambda x: 1/6*(x['mood_score'] + x['speed_score'] + x['emotion_score']) + 0.5*x['genre_score'], axis = 1)
        
        return result_df.iloc[1:].sort_values(by = 'total_score', ascending=False)[:top_n]

def download_file(file_name, bucket, object_name=None):
    
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    load_dotenv(verbose = True)

    s3_client = boto3.client('s3', 
      aws_access_key_id=os.getenv('S3_ACCESS_KEY'),
      aws_secret_access_key=os.getenv('S3_SECRET_KEY'),
      region_name='ap-northeast-2'
    )
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

if __name__ == "__main__":


    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument(
        '--data_path', type=str, default="./data/track/track_dataset.json"
    )
    argument_parser.add_argument(
        '--tfidf_path', type=str, default="./data/tfidf/tfidf_matrix.csv"
    )
    argument_parser.add_argument(
        '--music', type=str, default="Electric Shock"
    )
    argument_parser.add_argument(
        '--mood', type=int, default=1
    )
    argument_parser.add_argument(
        '--speed', type=int, default=1
    )
    argument_parser.add_argument(
        '--emotion', type=int, default=1
    )
    args = argument_parser.parse_args()

    download_file_from_s3(args.data_path, "spotify-recomendation-dataset", "dataset.json")
    track = pd.read_json(args.data_path, encoding = 'utf-8', orient='records')
    download_file_from_s3(args.tfidf_path, "spotify-tfidf", "tfidf_matrix.csv")
    ct_tfidf = pd.read_csv(args.tfidf_path, encoding = 'utf-8')
    
    cbr = ContentBasedRecommenderSystem(track, ct_tfidf, args.music, args.mood, args.speed, args.emotion)
    cbr.preprocess()
    cbr.get_feature_genre_intersection()
    cbr.get_total_score()