import boto3
import json

with open('config.json') as config_file:
    config = json.load(config_file)

s3_client = boto3.client('s3')

# Function to list all S3 buckets starting with 'aws-deepracer-assets'
def list_deepracer_buckets():
    response = s3_client.list_buckets()
    deepracer_buckets = [bucket['Name'] for bucket in response['Buckets'] if bucket['Name'].startswith('aws-deepracer-assets')]
    return deepracer_buckets

# Function to find all reward_function.py files inside folders containing 'MUDR'
def find_reward_function_files(bucket_name):

    reward_function_files = []
    response = s3_client.list_objects_v2(Bucket=bucket_name)

    for obj in response.get('Contents', []):
        key = obj['Key']
        if 'MUDR' in key and key.endswith('reward_function.py'):
            reward_function_files.append(key)
    
    return reward_function_files

# Function to read the content of a file from S3
def read_file_from_s3(bucket_name, file_key):

    try:
        obj = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        content = obj['Body'].read().decode('utf-8')
        return content
    except s3_client.exceptions.NoSuchKey:
        # If the file is not found, return None and continue
        return None


deepracer_buckets = list_deepracer_buckets()

# Dictionary to store all reward_function.py files for each bucket
bucket_files = {}

global_details = []

# Fetch reward_function.py files for each bucket
for bucket in deepracer_buckets:
    bucket_files[bucket] = find_reward_function_files(bucket)

    record = {
        'bucket_name': bucket,
        'file_name': bucket_files[bucket]
    }

    global_details.append(record)

print(global_details)

