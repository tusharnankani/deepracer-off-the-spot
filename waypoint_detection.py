import re
import os

def detect_hardcoded_waypoints(reward_function_code, waypoint_threshold=5):
    # common patterns for coordinate tuples like (x, y)
    waypoint_pattern = r'\(\s*\d+(\.\d+)?\s*,\s*\d+(\.\d+)?\s*\)'
    
    # list or arrays of waypoints, e.g., [(1.23, 4.56), (7.89, 10.11)] or [1.23, 2.34]
    list_pattern = r'\[\s*\d+(\.\d+)?(?:\s*,\s*\d+(\.\d+)?)*\s*\]'
    
    # separate x and y coordinate arrays
    separate_coords_pattern = r'([xy]_coords)\s*=\s*\[\s*\d+(\.\d+)?(?:\s*,\s*\d+(\.\d+)?)*\s*\]'
    


    combined_pattern = f'{waypoint_pattern}|{list_pattern}|{separate_coords_pattern}'
    
    matches = re.findall(combined_pattern, reward_function_code)
    
    if len(matches) > waypoint_threshold:
        return True, matches
    else:
        return False, None


def remove_comments_from_code(code):
    # single-line comments (with #)
    code_without_single_comments = re.sub(r'#.*', '', code)
    
    # multi-line comments (""" or ''')
    code_without_comments = re.sub(r'(\'\'\'[\s\S]*?\'\'\'|\"\"\"[\s\S]*?\"\"\")', '', code_without_single_comments)
    
    return code_without_comments


def check_files_in_folder(folder_path):

    for file_name in os.listdir(folder_path):
        if file_name.endswith('.py'):  # Only process Python files
            file_path = os.path.join(folder_path, file_name)
            
            try:
                # Read the content of the Python file
                with open(file_path, 'r') as file:
                    file_content = file.read()

                    is_hardcoded, matches = detect_hardcoded_waypoints(remove_comments_from_code(file_content), 10)
                    
                    # Output the result
                    if is_hardcoded:
                        print("Hardcoded waypoints detected in " + file_name)
                        print(matches)
                    else:
                        print("No hardcoded waypoints detected.")

            except Exception as e:
                print(f"Error processing file {file_name}: {e}")


check_files_in_folder('./test')