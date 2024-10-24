import boto3
import ast
import difflib

# Initialize the S3 client
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

# AST-based plagiarism detection
def detect_plagiarism_ast(code1, code2):
    try:
        ast1 = ast.parse(code1)
        ast2 = ast.parse(code2)
    except SyntaxError as e:
        return False

    return ast.dump(ast1) == ast.dump(ast2)

# Difflib-based plagiarism detection
def detect_plagiarism_difflib(code1, code2):
    seq_matcher = difflib.SequenceMatcher(None, code1, code2)
    similarity_ratio = seq_matcher.ratio()
    return similarity_ratio >= 0.8  # Threshold for plagiarism

# Compare all reward_function.py files from different buckets
def compare_reward_functions():
    # List all Deepracer buckets
    deepracer_buckets = list_deepracer_buckets()

    # Dictionary to store all reward_function.py files for each bucket
    bucket_files = {}

    # Fetch reward_function.py files for each bucket
    for bucket in deepracer_buckets:
        bucket_files[bucket] = find_reward_function_files(bucket)

    # Compare files between different buckets
    for i, bucket1 in enumerate(deepracer_buckets):
        for bucket2 in deepracer_buckets[i + 1:]:  # Compare only with buckets after the current one
            for file1_key in bucket_files[bucket1]:
                for file2_key in bucket_files[bucket2]:
                    # Read the files
                    file1_content = read_file_from_s3(bucket1, file1_key)
                    file2_content = read_file_from_s3(bucket2, file2_key)

                    # If either file is not found, skip comparison
                    if not file1_content or not file2_content:
                        continue

                    # Detect plagiarism using AST
                    if detect_plagiarism_ast(file1_content, file2_content):
                        print(f"Plagiarism detected between {bucket1}/{file1_key} and {bucket2}/{file2_key} using AST.")

                    # Detect plagiarism using Difflib
                    elif detect_plagiarism_difflib(file1_content, file2_content):
                        print(f"Plagiarism detected between {bucket1}/{file1_key} and {bucket2}/{file2_key} using difflib.")

# Example usage
if __name__ == "__main__":
    compare_reward_functions()
