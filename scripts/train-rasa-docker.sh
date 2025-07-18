#!/bin/bash

# Train RASA model using Docker
# Usage: ./train-rasa-docker.sh

set -e

PROJECT_ROOT="/Users/vivekkrishnan/dev/iaso/services/iaso-scribe/runpod"
RASA_DIR="$PROJECT_ROOT/rasa"

echo "Training RASA model using Docker..."

# Change to RASA directory
cd "$RASA_DIR"

# Create models directory if it doesn't exist
mkdir -p models

# Pull RASA Docker image
echo "Pulling RASA Docker image..."
docker pull rasa/rasa:3.6.0

# Train the model using Docker
echo "Training RASA model..."
docker run -it --rm \
  -v "$RASA_DIR:/app" \
  -u "$(id -u):$(id -g)" \
  rasa/rasa:3.6.0 \
  train --domain domain.yml --config config.yml --data data/ --out models/

# Check if model was created
if [ -f "models/"*.tar.gz ]; then
    echo "✅ Model training completed successfully!"
    echo "Model files:"
    ls -la models/
else
    echo "❌ Model training failed!"
    exit 1
fi

# Validate the model
echo "Validating model..."
docker run -it --rm \
  -v "$RASA_DIR:/app" \
  -u "$(id -u):$(id -g)" \
  rasa/rasa:3.6.0 \
  data validate --config config.yml --domain domain.yml --data data/

echo "✅ Model validation completed!"

# Build Docker images
echo "Building Docker images..."

# Build RASA server image
docker build -t iaso/rasa-server:latest -f Dockerfile .

# Build RASA actions image
docker build -t iaso/rasa-actions-medical:latest -f Dockerfile.actions .

echo "✅ Docker images built successfully!"

# Show built images
echo "Built images:"
docker images | grep "iaso/rasa"

echo ""
echo "✅ RASA model training and Docker build completed!"
echo ""
echo "To test the model:"
echo "1. Start action server: docker run -p 5055:5055 iaso/rasa-actions-medical:latest"
echo "2. Start RASA server: docker run -p 5005:5005 iaso/rasa-server:latest"
echo "3. Test REST API: curl -X POST http://localhost:5005/webhooks/rest/webhook -H 'Content-Type: application/json' -d '{\"sender\": \"test\", \"message\": \"hello\"}'"