import boto3
import ast
import pandas as pd

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
        return None

# AST-based plagiarism detection with similarity percentage
def detect_plagiarism_ast_with_similarity(code1, code2):
    try:
        ast1 = ast.parse(code1)
        ast2 = ast.parse(code2)
    except SyntaxError as e:
        print(f"Syntax error in the code: {e}")
        return 0

    # Recursive function to count nodes
    def count_nodes(node):
        return 1 + sum(count_nodes(child) for child in ast.iter_child_nodes(node))

    # Function to compare ASTs and count matches
    def count_matches(node1, node2):
        if type(node1) != type(node2):
            return 0
        matches = 1  # Nodes match
        for child1, child2 in zip(ast.iter_child_nodes(node1), ast.iter_child_nodes(node2)):
            matches += count_matches(child1, child2)
        return matches

    total_nodes1 = count_nodes(ast1)
    total_nodes2 = count_nodes(ast2)
    matches = count_matches(ast1, ast2)

    # Calculate similarity percentage
    similarity_percentage = (2 * matches) / (total_nodes1 + total_nodes2) * 100
    return similarity_percentage

# Compare all reward_function.py files from different buckets with AST similarity percentage and export results to CSV
def compare_reward_functions():
    # Ask the user for the plagiarism threshold
    threshold = float(input("Please enter the plagiarism similarity threshold (in percentage, e.g., 60): "))

    # List all Deepracer buckets
    deepracer_buckets = list_deepracer_buckets()

    # Dictionary to store all reward_function.py files for each bucket
    bucket_files = {}

    # List to store plagiarism detection results for CSV export
    plagiarism_results = []

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

                    # Detect plagiarism using AST similarity percentage
                    similarity_percentage = detect_plagiarism_ast_with_similarity(file1_content, file2_content)

                    # Check if similarity exceeds the threshold
                    if similarity_percentage >= threshold:
                        print(f"Plagiarism detected between {bucket1}/{file1_key} and {bucket2}/{file2_key} "
                              f"with {similarity_percentage:.2f}% similarity using AST.")
                        
                        # Save the data in the plagiarism_results list for CSV export
                        plagiarism_results.append({
                            'bucket1': bucket1,
                            'file1': file1_key,
                            'bucket2': bucket2,
                            'file2': file2_key,
                            'similarity_percentage': similarity_percentage,
                            'file1_content': file1_content,
                            'file2_content': file2_content
                        })

    # Convert results to a DataFrame and save to CSV
    df = pd.DataFrame(plagiarism_results)
    csv_file_path = 'output/plagiarism_detection_results.csv'
    df.to_csv(csv_file_path, index=False)
    print(f"Plagiarism detection results saved to {csv_file_path}")


if __name__ == "__main__":
    compare_reward_functions()
