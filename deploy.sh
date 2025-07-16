#!/bin/bash

# IASO Scribe RunPod Deployment Script

echo "🚀 IASO Scribe - RunPod Deployment"
echo "=================================="

# Configuration
RUNPOD_API_KEY=${RUNPOD_API_KEY:-""}
DEPLOYMENT_NAME="iaso-scribe"
REGION=${REGION:-"US"}

# Check if RunPod CLI is installed
if ! command -v runpod &> /dev/null; then
    echo "❌ RunPod CLI not found. Installing..."
    pip install runpod
fi

# Check API key
if [ -z "$RUNPOD_API_KEY" ]; then
    echo "❌ RUNPOD_API_KEY not set. Please export your API key:"
    echo "   export RUNPOD_API_KEY='your-api-key'"
    exit 1
fi

echo ""
echo "📋 Deployment Options:"
echo "1. Use existing Faster Whisper template (recommended)"
echo "2. Deploy custom image from Docker Hub"
echo "3. Build and deploy locally"
echo ""
read -p "Select option (1-3): " option

case $option in
    1)
        echo "✅ Using Faster Whisper template"
        echo ""
        echo "Steps to deploy with template:"
        echo "1. Go to: https://runpod.io/console/serverless"
        echo "2. Click 'Deploy New Endpoint'"
        echo "3. Search for 'Faster Whisper' template"
        echo "4. Configure with these settings:"
        echo "   - Container Image: runpod/faster-whisper:latest"
        echo "   - GPU Type: RTX A4000 or better"
        echo "   - Active Workers: 0 (scales to zero)"
        echo "   - Max Workers: 5"
        echo ""
        echo "5. After deployment, update the handler to include Phi-3"
        echo ""
        echo "📝 Note: You can modify the deployed container to add Phi-3 support"
        ;;
        
    2)
        echo "🐳 Deploying from Docker Hub"
        echo "First, let's push our image to Docker Hub..."
        
        # Build minimal image
        docker build -t iaso-scribe:runpod .
        
        # Tag for Docker Hub
        read -p "Docker Hub username: " docker_user
        docker tag iaso-scribe:runpod $docker_user/iaso-scribe:latest
        
        # Push to Docker Hub
        echo "Pushing to Docker Hub..."
        docker push $docker_user/iaso-scribe:latest
        
        echo ""
        echo "✅ Image pushed. Now deploy to RunPod:"
        echo "1. Go to: https://runpod.io/console/serverless"
        echo "2. Click 'Deploy New Endpoint'"
        echo "3. Select 'Custom Container'"
        echo "4. Enter image: $docker_user/iaso-scribe:latest"
        echo "5. Configure GPU and scaling settings"
        ;;
        
    3)
        echo "🔨 Building and deploying locally"
        echo "Note: This requires RunPod CLI v2"
        
        # Create runpod.toml
        cat > runpod.toml << EOF
[project]
name = "iaso-scribe"
base_image = "runpod/base:0.4.0-cuda12.1.0"

[project.env]
WHISPER_MODEL = "large-v3"
PHI3_MODEL = "microsoft/Phi-3-mini-4k-instruct-gguf"

[deployment]
gpu_type = "NVIDIA RTX A4000"
min_workers = 0
max_workers = 5
EOF
        
        # Deploy
        runpod deploy
        ;;
esac

echo ""
echo "📊 After deployment, test with:"
echo ""
cat > test_request.json << 'EOF'
{
  "input": {
    "audio": "https://example.com/sample-medical-audio.wav",
    "language": "en",
    "generate_insights": true
  }
}
EOF

echo "curl -X POST https://api.runpod.ai/v2/$DEPLOYMENT_NAME/runsync \\"
echo "  -H 'Authorization: Bearer $RUNPOD_API_KEY' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d @test_request.json"
echo ""
echo "✅ Deployment configuration complete!"