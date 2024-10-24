#!/bin/bash

# Check if stack name is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <stack-name>"
    exit 1
fi

stack_name=$1

# Function to delete bucket policy
delete_bucket_policy() {
    bucket_name=$1
    echo "Deleting bucket policy for $bucket_name..."

    if aws s3api get-bucket-policy --bucket "$bucket_name" 2>/dev/null; then
        aws s3api delete-bucket-policy --bucket "$bucket_name"
        echo "Bucket policy deleted for $bucket_name."
    else
        echo "No bucket policy found for $bucket_name."
    fi
}

# Function to delete objects from the S3 bucket
delete_bucket_objects() {
    bucket_name=$1
    echo "Deleting all objects in $bucket_name..."

    if aws s3 ls "s3://$bucket_name" --recursive 2>/dev/null | grep -q .; then
        aws s3 rm "s3://$bucket_name" --recursive
        echo "All objects in $bucket_name deleted."
    else
        echo "No objects found in the bucket $bucket_name."
    fi
}

# Function to delete the S3 bucket
delete_bucket() {
    bucket_name=$1
    echo "Deleting S3 bucket: $bucket_name..."

    if aws s3api delete-bucket --bucket "$bucket_name" 2>/dev/null; then
        echo "Bucket $bucket_name deleted successfully."
    else
        echo "Error: Bucket $bucket_name could not be deleted. Make sure it's empty and not in use."
    fi
}

# Function to remove role from instance profile, delete role policies, and the role
delete_iam_role() {
    role_name=$1
    echo "Processing IAM role: $role_name..."

    # Fetch instance profile associated with the role
    instance_profile=$(aws iam list-instance-profiles-for-role --role-name "$role_name" --query "InstanceProfiles[].InstanceProfileName" --output text)

    if [ -n "$instance_profile" ]; then
        echo "Removing role $role_name from instance profile $instance_profile..."
        aws iam remove-role-from-instance-profile --instance-profile-name "$instance_profile" --role-name "$role_name"
        echo "Role $role_name removed from instance profile $instance_profile."
    fi

    # Detach managed policies from the role
    echo "Detaching managed policies from $role_name..."
    policies=$(aws iam list-attached-role-policies --role-name "$role_name" --query "AttachedPolicies[].PolicyArn" --output text)
    if [ -n "$policies" ]; then
        for policy_arn in $policies; do
            aws iam detach-role-policy --role-name "$role_name" --policy-arn "$policy_arn"
            echo "Detached policy: $policy_arn from role $role_name."
        done
    else
        echo "No managed policies attached to $role_name."
    fi

    # Delete inline policies attached to the role
    echo "Deleting inline policies from $role_name..."
    inline_policies=$(aws iam list-role-policies --role-name "$role_name" --query "PolicyNames" --output text)
    if [ -n "$inline_policies" ]; then
        for policy_name in $inline_policies; do
            aws iam delete-role-policy --role-name "$role_name" --policy-name "$policy_name"
            echo "Deleted inline policy: $policy_name from role $role_name."
        done
    else
        echo "No inline policies found for $role_name."
    fi

    # Finally, delete the IAM role
    echo "Deleting IAM role $role_name..."
    if aws iam delete-role --role-name "$role_name"; then
        echo "Role $role_name deleted successfully."
    else
        echo "Error: Role $role_name could not be deleted. Make sure it's not in use."
    fi
}

# Main script to delete resources for a specific stack

echo "Fetching resources for stack: $stack_name..."
resources=$(aws cloudformation list-stack-resources --stack-name "$stack_name" --query "StackResourceSummaries[].{Type: ResourceType, Name: PhysicalResourceId}" --output json)

# Iterate through each resource
for resource in $(echo "${resources}" | jq -c '.[]'); do
    resource_type=$(echo "$resource" | jq -r '.Type')
    resource_name=$(echo "$resource" | jq -r '.Name')

    case $resource_type in
        "AWS::S3::Bucket")
            echo "Processing S3 bucket: $resource_name"
            delete_bucket_policy "$resource_name"
            delete_bucket_objects "$resource_name"
            delete_bucket "$resource_name"
            ;;
        "AWS::IAM::Role")
            echo "Processing IAM role: $resource_name"
            delete_iam_role "$resource_name"
            ;;
        *)
            echo "Skipping resource type: $resource_type with name: $resource_name"
            ;;
    esac
done

echo "Cleanup for stack $stack_name completed."
