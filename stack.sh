#!/bin/bash

# Check if stack prefix is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <stack-prefix>"
    exit 1
fi

stack_prefix=$1

log_file="script_output.txt"

# Example function that logs with timestamp
log_with_timestamp() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $log_file
}

# Function to delete bucket policy
delete_bucket_policy() {
    bucket_name=$1
    log_with_timestamp "Deleting bucket policy for $bucket_name..."

    if aws s3api get-bucket-policy --bucket "$bucket_name" 2>/dev/null; then
        aws s3api delete-bucket-policy --bucket "$bucket_name"
        log_with_timestamp "Bucket policy deleted for $bucket_name."
    else
        log_with_timestamp "No bucket policy found for $bucket_name."
    fi
}

# Function to delete objects from the S3 bucket
delete_bucket_objects() {
    bucket_name=$1
    log_with_timestamp "Deleting all objects in $bucket_name..."

    if aws s3 ls "s3://$bucket_name" --recursive 2>/dev/null | grep -q .; then
        aws s3 rm "s3://$bucket_name" --recursive
        log_with_timestamp "All objects in $bucket_name deleted."
    else
        log_with_timestamp "No objects found in the bucket $bucket_name."
    fi
}

# Function to delete the S3 bucket
delete_bucket() {
    bucket_name=$1
    log_with_timestamp "Deleting S3 bucket: $bucket_name..."

    if aws s3api delete-bucket --bucket "$bucket_name" 2>/dev/null; then
        log_with_timestamp "Bucket $bucket_name deleted successfully."
    else
        log_with_timestamp "Error: Bucket $bucket_name could not be deleted. Make sure it's empty and not in use."
    fi
}

# Function to delete a security group
delete_security_group() {
    group_name=$1
    log_with_timestamp "Deleting security group: $group_name..."
    
    if aws ec2 delete-security-group --group-name "$group_name"; then
        log_with_timestamp "Security group $group_name deleted successfully."
    else
        log_with_timestamp "Error: Security group $group_name could not be deleted. Ensure no instances are using it."
    fi
}

# Function to delete a Lambda function
delete_lambda_function() {
    function_name=$1
    log_with_timestamp "Deleting Lambda function: $function_name..."
    
    if aws lambda delete-function --function-name "$function_name"; then
        log_with_timestamp "Lambda function $function_name deleted successfully."
    else
        log_with_timestamp "Error: Lambda function $function_name could not be deleted."
    fi
}

# Function to delete an SNS topic
delete_sns_topic() {
    topic_name=$1
    log_with_timestamp "Deleting SNS topic: $topic_name..."
    
    if aws sns delete-topic --topic-arn "$topic_name"; then
        log_with_timestamp "SNS topic $topic_name deleted successfully."
    else
        log_with_timestamp "Error: SNS topic $topic_name could not be deleted."
    fi
}

# Function to delete a Network ACL Entry
delete_network_acl() {
    acl_id=$1
    log_with_timestamp "Deleting Network ACL Entry: $acl_id..."
    
    if aws ec2 delete-network-acl --network-acl-id "$acl_id"; then
        log_with_timestamp "Network ACL Entry $acl_id deleted successfully."
    else
        log_with_timestamp "Error: Network ACL Entry $acl_id could not be deleted."
    fi
}

# Function to remove role from instance profile, delete role policies, and the role
delete_iam_role() {
    role_name=$1
    log_with_timestamp "Processing IAM role: $role_name..."

    # Fetch instance profile associated with the role
    instance_profile=$(aws iam list-instance-profiles-for-role --role-name "$role_name" --query "InstanceProfiles[].InstanceProfileName" --output text)

    if [ -n "$instance_profile" ]; then
        log_with_timestamp "Removing role $role_name from instance profile $instance_profile..."
        aws iam remove-role-from-instance-profile --instance-profile-name "$instance_profile" --role-name "$role_name"
        log_with_timestamp "Role $role_name removed from instance profile $instance_profile."
    fi

    # Detach managed policies from the role
    log_with_timestamp "Detaching managed policies from $role_name..."
    policies=$(aws iam list-attached-role-policies --role-name "$role_name" --query "AttachedPolicies[].PolicyArn" --output text)
    if [ -n "$policies" ]; then
        for policy_arn in $policies; do
            aws iam detach-role-policy --role-name "$role_name" --policy-arn "$policy_arn"
            log_with_timestamp "Detached policy: $policy_arn from role $role_name."
        done
    else
        log_with_timestamp "No managed policies attached to $role_name."
    fi

    # Delete inline policies attached to the role
    log_with_timestamp "Deleting inline policies from $role_name..."
    inline_policies=$(aws iam list-role-policies --role-name "$role_name" --query "PolicyNames" --output text)
    if [ -n "$inline_policies" ]; then
        for policy_name in $inline_policies; do
            aws iam delete-role-policy --role-name "$role_name" --policy-name "$policy_name"
            log_with_timestamp "Deleted inline policy: $policy_name from role $role_name."
        done
    else
        log_with_timestamp "No inline policies found for $role_name."
    fi

    # Finally, delete the IAM role
    log_with_timestamp "Deleting IAM role $role_name..."
    if aws iam delete-role --role-name "$role_name"; then
        log_with_timestamp "Role $role_name deleted successfully."
    else
        log_with_timestamp "Error: Role $role_name could not be deleted. Make sure it's not in use."
    fi
}

# Function to delete the CloudFormation stack
delete_stack() {
    stack_name=$1
    log_with_timestamp "Deleting CloudFormation stack: $stack_name..."

    aws cloudformation delete-stack --stack-name "$stack_name"
    log_with_timestamp "Waiting for stack $stack_name to be deleted..."
    aws cloudformation wait stack-delete-complete --stack-name "$stack_name"
    
    if [ $? -eq 0 ]; then
        log_with_timestamp "Stack $stack_name deleted successfully."
    else
        log_with_timestamp "Error: Stack $stack_name deletion failed."
    fi
}

# Main script to delete resources for all stacks with the given prefix
log_with_timestamp "Fetching list of CloudFormation stacks with prefix: $stack_prefix..."
stack_names=$(aws cloudformation list-stacks  --query "StackSummaries[?starts_with(StackName, '$stack_prefix')].StackName" --output text)

if [ -z "$stack_names" ]; then
    log_with_timestamp "No stacks found with prefix: $stack_prefix"
    exit 0
fi

# Loop through each stack
for stack in $stack_names; do
    log_with_timestamp "Processing resources for stack: $stack..."

    resources=$(aws cloudformation list-stack-resources --stack-name "$stack" --query "StackResourceSummaries[].{Type: ResourceType, Name: PhysicalResourceId}" --output json)

    # Arrays to hold resources to delete in specified order
    s3_buckets=()
    security_groups=()
    lambda_functions=()
    sns_topics=()
    network_acls=()
    iam_roles=()

    # Iterate through each resource and categorize them
    for resource in $(echo "${resources}" | jq -c '.[]'); do
        resource_type=$(echo "$resource" | jq -r '.Type')
        resource_name=$(echo "$resource" | jq -r '.Name')

        case $resource_type in
            "AWS::S3::Bucket")
                log_with_timestamp "Found S3 bucket: $resource_name"
                s3_buckets+=("$resource_name")
                ;;
            "AWS::EC2::SecurityGroup")
                log_with_timestamp "Found Security group: $resource_name"
                security_groups+=("$resource_name")
                ;;
            "AWS::Lambda::Function")
                log_with_timestamp "Found Lambda function: $resource_name"
                lambda_functions+=("$resource_name")
                ;;
            "AWS::SNS::Topic")
                log_with_timestamp "Found SNS topic: $resource_name"
                sns_topics+=("$resource_name")
                ;;
            "AWS::EC2::NetworkAcl")
                log_with_timestamp "Found Network ACL: $resource_name"
                network_acls+=("$resource_name")
                ;;
            "AWS::IAM::Role")
                log_with_timestamp "Found IAM role: $resource_name"
                iam_roles+=("$resource_name")
                ;;
            *)
                log_with_timestamp "Skipping resource type: $resource_type with name: $resource_name"
                ;;
        esac
    done

    # Delete resources in specified order
    # 1. S3 Buckets
    for bucket in "${s3_buckets[@]}"; do
        log_with_timestamp "Processing S3 bucket: $bucket"
        delete_bucket_policy "$bucket"
        delete_bucket_objects "$bucket"
        delete_bucket "$bucket"
    done

    # 2. Security Groups
    for group in "${security_groups[@]}"; do
        log_with_timestamp "Processing Security group: $group"
        delete_security_group "$group"
    done

    # 3. Lambda Functions
    for function in "${lambda_functions[@]}"; do
        log_with_timestamp "Processing Lambda function: $function"
        delete_lambda_function "$function"
    done

    # 4. SNS Topics
    for topic in "${sns_topics[@]}"; do
        log_with_timestamp "Processing SNS topic: $topic"
        delete_sns_topic "$topic"
    done

    # 5. Network ACLs
    for acl in "${network_acls[@]}"; do
        log_with_timestamp "Processing Network ACL: $acl"
        delete_network_acl "$acl"
    done

    # 6. IAM Roles
    for role in "${iam_roles[@]}"; do
        log_with_timestamp "Processing IAM role: $role"
        delete_iam_role "$role"
    done

    # Delete the CloudFormation stack
    delete_stack "$stack"
done

log_with_timestamp "Cleanup for all stacks with prefix $stack_prefix completed."
