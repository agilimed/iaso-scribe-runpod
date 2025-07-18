#!/bin/bash

# Build Docker images for IasoChat locally
# Usage: ./build-docker-images.sh

set -e

echo "🏗️  Building IasoChat Docker images locally..."

# Build timestamp for tagging
BUILD_TAG=$(date +%Y%m%d-%H%M%S)
COMMIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "local")

echo "Build tag: $BUILD_TAG"
echo "Commit SHA: $COMMIT_SHA"

# Build RASA Actions image
echo "📦 Building RASA Actions image..."
cd /Users/vivekkrishnan/dev/iaso/services/iaso-chat

# Ensure we have all the files
if [ ! -f "actions/actions.py" ]; then
    echo "❌ actions/actions.py not found. Please ensure the file exists."
    exit 1
fi

if [ ! -f "requirements-actions.txt" ]; then
    echo "❌ requirements-actions.txt not found. Please ensure the file exists."
    exit 1
fi

# Build actions image
docker build -t iaso/rasa-actions-medical:$BUILD_TAG -f Dockerfile.actions .
docker tag iaso/rasa-actions-medical:$BUILD_TAG iaso/rasa-actions-medical:latest

echo "✅ RASA Actions image built successfully!"

# Build RASA MCP image
echo "📦 Building RASA MCP image..."
cd /Users/vivekkrishnan/dev/iaso/services/iaso-scribe/runpod/mcp

# Check if MCP server exists
if [ ! -f "rasa_mcp_server.py" ]; then
    echo "❌ rasa_mcp_server.py not found. Please ensure the file exists."
    exit 1
fi

# Create Dockerfile for MCP server if it doesn't exist
if [ ! -f "Dockerfile.rasa" ]; then
    cat > Dockerfile.rasa << 'EOF'
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy MCP server code
COPY rasa_mcp_server.py .

# Change ownership to app user
RUN chown -R app:app /app

# Switch to app user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8091/health || exit 1

# Expose port
EXPOSE 8091

# Run MCP server
CMD ["python", "rasa_mcp_server.py"]
EOF
fi

# Build MCP image
docker build -t iaso/rasa-mcp:$BUILD_TAG -f Dockerfile.rasa .
docker tag iaso/rasa-mcp:$BUILD_TAG iaso/rasa-mcp:latest

echo "✅ RASA MCP image built successfully!"

# Show built images
echo "📋 Built images:"
docker images | grep "iaso/rasa"

echo ""
echo "🎉 Docker images built successfully!"
echo ""
echo "🏷️  Images:"
echo "  • Actions: iaso/rasa-actions-medical:$BUILD_TAG"
echo "  • MCP: iaso/rasa-mcp:$BUILD_TAG"
echo ""
echo "🧪 Test locally:"
echo "  docker run -p 5055:5055 iaso/rasa-actions-medical:latest"
echo "  docker run -p 8091:8091 iaso/rasa-mcp:latest"
echo ""
echo "⬆️  Next steps:"
echo "  1. Configure AWS CLI: aws configure"
echo "  2. Set RunPod API key: export RUNPOD_API_KEY=your-api-key"
echo "  3. Run full deployment: ./build-and-deploy.sh"