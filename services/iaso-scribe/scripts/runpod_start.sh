#!/bin/bash
# RunPod startup script for IasoScribe

echo "Starting IasoScribe on RunPod..."

# Set environment variables
export PYTHONPATH=/app/src:$PYTHONPATH
export DEPLOYMENT_MODE=runpod
export MODEL_PATH=/models

# Download models if not present
if [ ! -d "/models/faster-whisper-medium" ]; then
    echo "Downloading Whisper Medium model..."
    python -c "from faster_whisper import WhisperModel; WhisperModel('medium', device='cuda', download_root='/models')"
fi

# Start the RunPod handler
cd /app/src
python medical_whisper_handler.py