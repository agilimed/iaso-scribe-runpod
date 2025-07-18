#!/bin/bash
cd /Users/vivekkrishnan/dev/iaso

# ECR Configuration
ECR_REGISTRY="727646479986.dkr.ecr.us-west-2.amazonaws.com"

# Login to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $ECR_REGISTRY

echo "Building remaining services..."

# Build and push template service
echo "Building template service..."
docker build -t ${ECR_REGISTRY}/iaso-template:latest -f clinical-ai/template_service/Dockerfile clinical-ai/
docker push ${ECR_REGISTRY}/iaso-template:latest

# Build and push SLM service
echo "Building SLM service..."
docker build -t ${ECR_REGISTRY}/iaso-slm:latest -f clinical-ai/slm_service/Dockerfile clinical-ai/
docker push ${ECR_REGISTRY}/iaso-slm:latest

# Build and push embeddings service
echo "Building embeddings service..."
docker build -t ${ECR_REGISTRY}/iaso-embeddings:latest -f services/embeddings-service/Dockerfile services/embeddings-service/
docker push ${ECR_REGISTRY}/iaso-embeddings:latest

echo "Build complete!"