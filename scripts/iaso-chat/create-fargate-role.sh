#!/bin/bash

# Create IAM role for EKS Fargate pod execution
set -e

ROLE_NAME="AmazonEKSFargatePodExecutionRole"
REGION="us-west-2"

echo "Creating Fargate Pod Execution Role..."

# Create trust policy
cat > /tmp/fargate-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "eks-fargate-pods.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create the role
aws iam create-role \
    --role-name $ROLE_NAME \
    --assume-role-policy-document file:///tmp/fargate-trust-policy.json \
    --region $REGION || echo "Role might already exist"

# Attach the required policy
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonEKSFargatePodExecutionRolePolicy \
    --region $REGION

echo "✅ Fargate Pod Execution Role created successfully!"
echo "Role ARN: $(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)"

# Clean up
rm -f /tmp/fargate-trust-policy.json