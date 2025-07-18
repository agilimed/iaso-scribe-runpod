# IASO AI Services for RunPod

Multi-service AI deployment on RunPod serverless infrastructure.

## Services

### 1. Whisper Service (`/whisper`)
- Speech-to-text using Whisper Medium
- GPU accelerated with faster-whisper
- ~0.8s processing for 10s audio

### 2. Phi-4 Service (`/phi4`)
- Medical reasoning using Phi-4-reasoning-plus Q6_K_L
- 16K context window
- GPU accelerated with llama-cpp-python

### 3. Orchestrator Service (`/orchestrator`)
- Combines Whisper + Phi-4 for complete pipeline
- Handles audio → transcription → medical insights

## Deployment

Each service can be deployed independently to RunPod:

1. **Whisper**: Build from `/whisper` directory
2. **Phi-4**: Build from `/phi4` directory  
3. **Orchestrator**: Build from `/orchestrator` directory

## RunPod Configuration

Configure your RunPod endpoint to build from the specific subdirectory:
- Build Context: `/whisper`, `/phi4`, or `/orchestrator`
- Dockerfile Path: `Dockerfile` (relative to subdirectory)