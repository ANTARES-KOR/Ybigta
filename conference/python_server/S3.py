import os
import boto3


class S3service :
  def __init__(self, access_key, secret_key):

    self.s3_client = boto3.client('s3', 
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name='ap-northeast-2'
    )
  
  def download_file(file_name, bucket, object_name=None) :

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