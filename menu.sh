#!/bin/bash


# Get the directory of the current script
script_dir="$(dirname "$0")"


delete_shell_script() {
    echo "Running shell script..."

    read -p "Enter your stack name prefix: " prefix

    bash "$script_dir/stack.sh $prefix"
}

detect_waypoint_python_script() {
    echo "Running Python script..."
    python3 "$script_dir/access_bucket.py"
}


plag_python_script() {
    echo "Running Python script..."
    python3 "$script_dir/plagiarismCheckS3Buckets.py"
}


mail_python_script() {
    echo "Running Python script..."
    python3 "$script_dir/mail.py"
}


# Function to display the menu
display_menu() {
    echo "" 
    echo "Select an option [1 - 5]:"
    echo "1. Delete Stack Resources"
    echo "2. Detect Waypoints in Submissions"
    echo "3. Plagiarism Check in Submissions"
    echo "4. Email Output Logs"
    echo "5. Exit"
}

# Loop to keep the script running until the user chooses to exit
while true; do
    display_menu
    read -p "Enter your choice: " choice

    case $choice in
        1)
            delete_shell_script
            ;;
        2)
            detect_waypoint_python_script
            ;;
        3)
            plag_python_script
            ;;
        4)
            mail_python_script
            ;;
        5)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid choice, please try again."
            ;;
    esac
done
