#!/bin/bash

# Build and train RASA model for IasoVoice
# Usage: ./build-rasa-model.sh [environment]

set -e

ENVIRONMENT=${1:-development}
PROJECT_ROOT="/Users/vivekkrishnan/dev/iaso/services/iaso-scribe/runpod"
RASA_DIR="$PROJECT_ROOT/rasa"

echo "Building RASA model for IasoVoice..."
echo "Environment: $ENVIRONMENT"

# Change to RASA directory
cd "$RASA_DIR"

# Check if RASA is installed
if ! command -v rasa &> /dev/null; then
    echo "RASA not found. Installing..."
    pip install rasa==3.6.0
fi

# Create models directory if it doesn't exist
mkdir -p models

# Train the model
echo "Training RASA model..."
rasa train --config config.yml --domain domain.yml --data data/

# Check if model was created
if [ -f "models/"*.tar.gz ]; then
    echo "✅ Model training completed successfully!"
    echo "Model file: $(ls -la models/*.tar.gz)"
else
    echo "❌ Model training failed!"
    exit 1
fi

# Validate the model
echo "Validating model..."
rasa data validate --config config.yml --domain domain.yml --data data/

# Test the model with sample stories
echo "Testing model with sample stories..."
rasa test --config config.yml --domain domain.yml --data data/ --out results/

# Build Docker images
echo "Building Docker images..."

# Build RASA server image
docker build -t iaso/rasa-server:latest -f Dockerfile .

# Build RASA actions image
docker build -t iaso/rasa-actions-medical:latest -f Dockerfile.actions .

# Build RASA MCP server image (if MCP Dockerfile exists)
if [ -f "../mcp/Dockerfile.rasa" ]; then
    cd ../mcp
    docker build -t iaso/rasa-mcp:latest -f Dockerfile.rasa .
    cd "$RASA_DIR"
fi

echo "✅ Docker images built successfully!"

# Tag images for different environments
if [ "$ENVIRONMENT" != "development" ]; then
    docker tag iaso/rasa-server:latest iaso/rasa-server:$ENVIRONMENT
    docker tag iaso/rasa-actions-medical:latest iaso/rasa-actions-medical:$ENVIRONMENT
    docker tag iaso/rasa-mcp:latest iaso/rasa-mcp:$ENVIRONMENT
fi

# Show built images
echo "Built images:"
docker images | grep "iaso/rasa"

echo ""
echo "Next steps:"
echo "1. Test the model locally: rasa shell"
echo "2. Start action server: rasa run actions"
echo "3. Start RASA server: rasa run --enable-api --cors '*'"
echo "4. Deploy to Kubernetes: cd ../kubernetes/rasa && ./deploy-rasa.sh"
echo ""
echo "To test the REST API:"
echo "curl -X POST http://localhost:5005/webhooks/rest/webhook \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"sender\": \"test\", \"message\": \"hello\"}'"