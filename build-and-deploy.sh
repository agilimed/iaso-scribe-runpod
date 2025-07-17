#!/bin/bash

# Build and deploy Docker image to RunPod

echo "Building Docker image..."
docker build -t iaso-scribe-runpod .

echo "Tagging for RunPod registry..."
docker tag iaso-scribe-runpod registry.runpod.ai/rntxttrdl8uv3i/iaso-scribe:latest

echo "Logging in to RunPod registry..."
echo $RUNPOD_API_KEY | docker login registry.runpod.ai -u rntxttrdl8uv3i --password-stdin

echo "Pushing to RunPod..."
docker push registry.runpod.ai/rntxttrdl8uv3i/iaso-scribe:latest

echo "Deploy complete! The endpoint will automatically use the new image."