# Use RunPod's base image with CUDA support
FROM runpod/base:0.4.0-cuda12.1.0

# Install system dependencies including build tools for llama.cpp
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with CUDA support for llama-cpp-python
ENV CMAKE_ARGS="-DLLAMA_CUBLAS=on"
ENV FORCE_CMAKE=1
RUN pip install --no-cache-dir -r requirements.txt

# Copy handler
COPY handler.py .

# Create models directory
RUN mkdir -p /models

# Download models during build (optional - can be done at runtime)
# This increases image size but reduces cold start time
ARG DOWNLOAD_MODELS=false
ARG DOWNLOAD_PHI4=false

RUN if [ "$DOWNLOAD_MODELS" = "true" ]; then \
    python -c "from faster_whisper import WhisperModel; WhisperModel('large-v3', device='cpu', compute_type='int8')"; \
    fi

# Note: Model will be downloaded at runtime to avoid hitting RunPod's build limits
# This keeps the image small and fast to build

# Set environment variables
ENV WHISPER_MODEL=large-v3
ENV PHI_MODEL_PATH=/models/Phi-4-reasoning-plus-Q6_K_L.gguf
ENV PYTHONUNBUFFERED=1

# RunPod handler
CMD ["python", "-u", "handler.py"]