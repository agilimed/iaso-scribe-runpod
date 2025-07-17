#!/bin/bash

# IASO Scribe RunPod Endpoint Test

ENDPOINT_ID="rntxttrdl8uv3i"
RUNPOD_API_KEY="${RUNPOD_API_KEY:-your-api-key-here}"

echo "🚀 IASO Scribe - RunPod Endpoint Test"
echo "====================================="
echo "Endpoint: https://api.runpod.ai/v2/${ENDPOINT_ID}"
echo ""

if [ "$RUNPOD_API_KEY" = "your-api-key-here" ]; then
    echo "⚠️  Please set your RunPod API key:"
    echo "export RUNPOD_API_KEY='your-actual-api-key'"
    exit 1
fi

echo "1️⃣ Checking health..."
curl -s -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
    https://api.runpod.ai/v2/${ENDPOINT_ID}/health
echo -e "\n"

echo "2️⃣ Checking status..."
curl -s -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
    https://api.runpod.ai/v2/${ENDPOINT_ID}/status | python3 -m json.tool
echo ""

echo "3️⃣ Testing transcription..."
echo "Sending audio file for transcription..."

curl -X POST https://api.runpod.ai/v2/${ENDPOINT_ID}/runsync \
    -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
    -H "Content-Type: application/json" \
    -d '{
        "input": {
            "audio": "https://www2.cs.uic.edu/~i101/SoundFiles/StarWars60.wav",
            "language": "en",
            "generate_insights": true,
            "return_segments": false
        }
    }' | python3 -m json.tool

echo ""
echo "✅ Test complete!"
echo ""
echo "📝 Note: First run downloads models (~14GB), may take 10-15 minutes"
echo "   Subsequent runs will be much faster (30-60 seconds)"