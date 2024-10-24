import boto3

s3 = boto3.client('s3')

bucket_name = 'your-bucket-name'

def find_and_load_reward_function(bucket_name):
    paginator = s3.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(Bucket=bucket_name):
        if 'Contents' in page:
            # Iterate over each object in the page
            for obj in page['Contents']:
                key = obj['Key']
                
                if key.endswith('reward_function.py'):
                    print(f"Found: {key}")
                    
                    response = s3.get_object(Bucket=bucket_name, Key=key)
                    file_content = response['Body'].read().decode('utf-8')
                    
                    return file_content
    return None


reward_function_content = find_and_load_reward_function(bucket_name)

if reward_function_content:
    print("Content of reward_function.py:")
    print(reward_function_content)
else:
    print("Not found")