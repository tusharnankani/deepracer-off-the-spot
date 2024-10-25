import boto3
import json
import pandas as pd
import re

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


responses = []


def remove_comments_from_code(code):
    # Remove single-line comments (lines starting with #)
    code_without_single_comments = re.sub(r'#.*', '', code)
    
    # Remove multi-line comments (""" or ''')
    code_without_comments = re.sub(r'(\'\'\'[\s\S]*?\'\'\'|\"\"\"[\s\S]*?\"\"\")', '', code_without_single_comments)
    
    return code_without_comments

def detect_hardcoded_waypoints(reward_function_code, waypoint_threshold=5):
    # Regex to match tuple with numeric literals, like (1.23, 4.56)
    literal_tuple_pattern = r'\(\s*\d+(\.\d+)?\s*,\s*\d+(\.\d+)?\s*\)'
    
    # Regex to match lists or arrays of waypoints, e.g., [(1.23, 4.56), (7.89, 10.11)]
    literal_list_pattern = r'\[\s*\(\s*\d+(\.\d+)?\s*,\s*\d+(\.\d+)?\s*\)(?:\s*,\s*\(\s*\d+(\.\d+)?\s*,\s*\d+(\.\d+)?\s*\))*\s*\]'
    
    # This regex excludes variable names like 'x', 'y', 'waypoints' from being falsely detected
    exclusion_pattern = r'\b(x|y|waypoints|closest_waypoints)\b\s*'
    
    # Combine regex patterns for tuples and lists that are literals, and exclude variable patterns
    combined_pattern = f'(?!{exclusion_pattern})({literal_tuple_pattern}|{literal_list_pattern})'
    
    matches = re.findall(combined_pattern, reward_function_code)
    
    if len(matches) > waypoint_threshold:
        return True, matches
    else:
        return False, None


deepracer_buckets = list_deepracer_buckets()
print(deepracer_buckets)

# Dictionary to store all reward_function.py files for each bucket
bucket_files = {}


# Fetch reward_function.py files for each bucket
for bucket in deepracer_buckets:
    bucket_files[bucket] = find_reward_function_files(bucket)
    print(bucket_files)

    for bucket in deepracer_buckets:
        print(bucket)
        for file_key in bucket_files[bucket]:
            file_content = read_file_from_s3(bucket, file_key)

            # If either is not found, skip comparison
            if not file_content:
                continue

            is_hardcoded, matches = detect_hardcoded_waypoints(remove_comments_from_code(file_content), 10)
                    
            if is_hardcoded:
                response_dict = {
                    'bucket': bucket,
                    'file_key': file_key,
                    'file_content': file_content,
                    'flagged': 'Y',
                    'match_count': len(matches),
                    'potential_waypoint_content': matches
                }
            else:
                response_dict = {
                    'bucket': bucket,
                    'file_key': file_key,
                    'file_content': file_content,
                    'flagged': 'N',
                    'match_count': None,
                    'potential_waypoint_content': None
                }

            responses.append(response_dict)



df = pd.DataFrame(responses)

csv_file_path = 'output/waypoint_responses.csv'
df.to_csv(csv_file_path, index=False)

print(f"Waypoint Detection results saved to {csv_file_path}")

