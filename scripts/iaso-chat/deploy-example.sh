#!/bin/bash

# IasoChat Deployment Example Script
# This script shows how to deploy IasoChat using the environment variables

# Source the .env file
source /Users/vivekkrishnan/dev/iaso/.env

# Generate secure passwords if not set
if [ "$IASOCHAT_REDIS_PASSWORD" == "your_secure_redis_password_here" ]; then
    export IASOCHAT_REDIS_PASSWORD=$(openssl rand -base64 32)
    echo "Generated Redis password: $IASOCHAT_REDIS_PASSWORD"
    echo "Please update this in your .env file"
fi

# Set deployment variables
export AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-727646479986}
export AWS_REGION=${AWS_REGION:-us-west-2}
export CLUSTER_NAME=${CLUSTER_NAME:-nexuscare-eks-dev}
export NAMESPACE=${NAMESPACE:-iaso-chat}
export ENVIRONMENT=${IASOCHAT_ENVIRONMENT:-dev}

# RunPod API Key (must be set)
if [ -z "$RUNPOD_API_KEY" ]; then
    echo "Error: RUNPOD_API_KEY is not set in .env file"
    echo "Please add: RUNPOD_API_KEY=your_actual_runpod_api_key"
    exit 1
fi

echo "=== IasoChat Deployment Configuration ==="
echo "AWS Account: $AWS_ACCOUNT_ID"
echo "AWS Region: $AWS_REGION"
echo "EKS Cluster: $CLUSTER_NAME"
echo "Namespace: $NAMESPACE"
echo "Environment: $ENVIRONMENT"
echo "RunPod API Key: ${RUNPOD_API_KEY:0:10}..."
echo "========================================"

# Step 1: Build and push Docker images
echo ""
echo "Step 1: Building and pushing Docker images..."
echo "Run: ./scripts/iaso-chat/build-and-deploy.sh"

# Step 2: Deploy to EKS
echo ""
echo "Step 2: Deploy to EKS Fargate..."
echo "Run: ./scripts/iaso-chat/deploy-eks-fargate.sh"

# Step 3: Verify deployment
echo ""
echo "Step 3: Verify deployment..."
echo "kubectl get pods -n $NAMESPACE"
echo "kubectl get services -n $NAMESPACE"

# Example commands to test the deployment
echo ""
echo "=== Testing Commands ==="
echo "# Port forward to test locally:"
echo "kubectl port-forward -n $NAMESPACE service/iaso-chat-rasa 5005:5005"
echo ""
echo "# Test RASA endpoint:"
echo "curl -X POST http://localhost:5005/webhooks/rest/webhook \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"sender\": \"test_user\", \"message\": \"Hello\"}'"
echo ""
echo "# Check logs:"
echo "kubectl logs -n $NAMESPACE -l app=iaso-chat-rasa"
echo "kubectl logs -n $NAMESPACE -l app=iaso-chat-actions"
echo ""
echo "# Scale deployment:"
echo "kubectl scale deployment -n $NAMESPACE iaso-chat-rasa --replicas=3"