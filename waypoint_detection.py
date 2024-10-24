import re
import os
import pandas as pd

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
    

def check_files_in_folder(folder_path):

    for file_name in os.listdir(folder_path):
        if file_name.endswith('.py'):  # Only process Python files
            file_path = os.path.join(folder_path, file_name)
            
            try:
                with open(file_path, 'r') as file:
                    file_content = file.read()

                    is_hardcoded, matches = detect_hardcoded_waypoints(remove_comments_from_code(file_content), 10)
                    
                    if is_hardcoded:
                        print("Hardcoded waypoints detected in " + file_name)
                        # print(matches)
                        response_dict = {
                            'file_name': file_name,
                            'file_content': file_content,
                            'potential_waypoint_content': matches 
                        }
                        responses.append(response_dict)
                    else:
                        print("No hardcoded waypoints detected.")

            except Exception as e:
                print(f"Error processing file {file_name}: {e}")


check_files_in_folder('./test')

df = pd.DataFrame(responses)

csv_file_path = 'output/waypoint_responses.csv'
df.to_csv(csv_file_path, index=False)
