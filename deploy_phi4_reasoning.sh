#!/bin/bash

# IASO Scribe - Phi-4-reasoning-plus Deployment Script
# Deploys with Q6_K_L quantization (12.28GB, near-perfect quality)

echo "🚀 IASO Scribe - Phi-4-reasoning-plus Deployment"
echo "================================================"
echo "Model: microsoft/Phi-4-reasoning-plus"
echo "Quantization: Q6_K_L GGUF (12.28GB)"
echo "Quality: Near-perfect with Q8_0 embed/output weights"
echo ""

# Configuration
RUNPOD_API_KEY=${RUNPOD_API_KEY:-""}
DEPLOYMENT_NAME="iaso-scribe-phi4-reasoning"
DOCKER_USER=${DOCKER_USER:-""}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker.${NC}"
    exit 1
fi

if [ -z "$RUNPOD_API_KEY" ]; then
    echo -e "${RED}❌ RUNPOD_API_KEY not set.${NC}"
    echo "Please export your API key:"
    echo "   export RUNPOD_API_KEY='your-api-key'"
    exit 1
fi

if [ -z "$DOCKER_USER" ]; then
    read -p "Docker Hub username: " DOCKER_USER
fi

echo ""
echo -e "${BLUE}📋 Deployment Options:${NC}"
echo "1. Quick Deploy - Use pre-quantized model (recommended)"
echo "2. Build with model included - Larger image, faster cold starts"
echo "3. RunPod Template - Use existing template"
echo ""
read -p "Select option (1-3): " option

case $option in
    1)
        echo -e "${GREEN}✅ Quick Deploy Mode${NC}"
        echo "Building minimal image (model downloaded at runtime)..."
        
        # Build the image
        docker build -t ${DOCKER_USER}/iaso-scribe-phi4:latest \
            --build-arg DOWNLOAD_MODELS=false \
            --build-arg DOWNLOAD_PHI4=false \
            .
        
        echo -e "${BLUE}Pushing to Docker Hub...${NC}"
        docker push ${DOCKER_USER}/iaso-scribe-phi4:latest
        
        echo ""
        echo -e "${GREEN}✅ Image pushed successfully!${NC}"
        echo ""
        echo "Deploy on RunPod:"
        echo "1. Go to: https://runpod.io/console/serverless"
        echo "2. Click 'New Endpoint'"
        echo "3. Container Image: ${DOCKER_USER}/iaso-scribe-phi4:latest"
        echo "4. GPU Configuration:"
        echo "   - GPU Type: RTX A4000 (16GB) or better"
        echo "   - Min Workers: 0"
        echo "   - Max Workers: 5"
        echo "5. Environment Variables:"
        echo "   - PHI_MODEL_PATH: /models/Phi-4-reasoning-plus-Q6_K_L.gguf"
        echo ""
        echo -e "${BLUE}Note: First request will download the 12.28GB model${NC}"
        ;;
        
    2)
        echo -e "${GREEN}✅ Build with Model Included${NC}"
        echo -e "${RED}Warning: This will create a ~15GB Docker image${NC}"
        read -p "Continue? (y/n): " confirm
        
        if [ "$confirm" = "y" ]; then
            docker build -t ${DOCKER_USER}/iaso-scribe-phi4:full \
                --build-arg DOWNLOAD_MODELS=true \
                --build-arg DOWNLOAD_PHI4=true \
                .
            
            echo -e "${BLUE}Pushing large image to Docker Hub...${NC}"
            docker push ${DOCKER_USER}/iaso-scribe-phi4:full
            
            echo ""
            echo -e "${GREEN}✅ Full image pushed!${NC}"
            echo "Deploy with image: ${DOCKER_USER}/iaso-scribe-phi4:full"
        fi
        ;;
        
    3)
        echo -e "${GREEN}✅ RunPod Template Instructions${NC}"
        echo ""
        echo "1. Use the 'Text Generation Inference' template"
        echo "2. Modify the startup command to:"
        echo "   python handler.py"
        echo "3. Set environment variables:"
        echo "   - MODEL_ID: bartowski/microsoft_Phi-4-reasoning-plus-GGUF"
        echo "   - QUANTIZE: gguf"
        echo "   - MAX_BATCH_PREFILL_TOKENS: 4096"
        ;;
esac

echo ""
echo -e "${BLUE}📝 Test your deployment:${NC}"
cat > test_deployment.sh << 'EOF'
#!/bin/bash
ENDPOINT_ID="your-endpoint-id"
RUNPOD_API_KEY="your-api-key"

curl -X POST "https://api.runpod.ai/v2/${ENDPOINT_ID}/runsync" \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "audio": "https://example.com/medical-audio.wav",
      "language": "en",
      "generate_insights": true
    }
  }'
EOF

chmod +x test_deployment.sh
echo "Created test_deployment.sh - update with your endpoint ID"

echo ""
echo -e "${GREEN}✅ Deployment script complete!${NC}"
echo ""
echo -e "${BLUE}Key Features of Phi-4-reasoning-plus:${NC}"
echo "• Advanced medical reasoning capabilities"
echo "• Q6_K_L quantization - near-perfect quality"
echo "• 12.28GB model size (fits on 16GB GPUs)"
echo "• Superior clinical documentation generation"
echo "• Optimized for RunPod serverless deployment"