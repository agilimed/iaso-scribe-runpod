# RunPod Deployment Instructions

## Key Fixes Applied

1. **CUDA/cuDNN Compatibility**: Updated to use `nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04` base image (matching RunPod's official template)
2. **Faster-Whisper Version**: Updated to v1.1.0 (from 1.0.0) for better stability
3. **VAD Parameters**: Added safer VAD parameters to prevent crashes
4. **Python Version**: Using Python 3.10 as recommended

## Build and Deploy Steps

### 1. Build Docker Image Locally (if Docker is running)
```bash
docker build -t iaso-scribe-runpod .
```

### 2. Tag for RunPod Registry
```bash
docker tag iaso-scribe-runpod registry.runpod.ai/rntxttrdl8uv3i/iaso-scribe:latest
```

### 3. Login to RunPod Registry
```bash
echo $RUNPOD_API_KEY | docker login registry.runpod.ai -u rntxttrdl8uv3i --password-stdin
```

### 4. Push to RunPod
```bash
docker push registry.runpod.ai/rntxttrdl8uv3i/iaso-scribe:latest
```

## Alternative: Direct Deployment via RunPod UI

1. Go to RunPod dashboard
2. Navigate to your endpoint (rntxttrdl8uv3i)
3. Update the Docker image to use the official faster-whisper base
4. Or use our custom image after pushing

## Testing After Deployment

Use the async test script:
```bash
python3 test_async.py
```

Or test synchronously:
```bash
python3 test_simple.py
```

## Key Changes Made

1. **Dockerfile**:
   - Base image: `nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04`
   - Python 3.10 installation
   - Proper CUDA libraries

2. **Handler**:
   - Added GPU memory logging
   - Safer VAD parameters
   - Better error handling
   - Removed problematic transcription parameters

3. **Requirements**:
   - `runpod~=1.7.9`
   - `faster-whisper==1.1.0`
   - Removed ctranslate2 pin (let faster-whisper handle it)

## Expected Behavior

- Models load without crashes
- Whisper transcription works with VAD enabled
- GPU memory is properly utilized (24-32GB is more than sufficient)
- No exit code 134 errors