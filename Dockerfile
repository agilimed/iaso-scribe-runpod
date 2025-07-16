# Use RunPod's base image with CUDA support
FROM runpod/base:0.4.0-cuda12.1.0

# Set working directory
WORKDIR /app

# Install system dependencies including nvcc for CUDA compilation
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    cmake \
    python3-dev \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install build tools
RUN python3 -m pip install --upgrade pip setuptools wheel ninja

# Copy requirements
COPY requirements.txt .

# Install Python dependencies first (without llama-cpp-python)
RUN pip install --no-cache-dir \
    runpod>=1.3.0 \
    faster-whisper>=1.0.0 \
    torch>=2.0.0 \
    requests>=2.31.0 \
    numpy>=1.24.0 \
    huggingface-hub>=0.20.0

# Install llama-cpp-python using pre-built CUDA wheel
# This avoids compilation issues
RUN pip install llama-cpp-python \
    --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121 \
    --no-cache-dir

# Copy handler
COPY handler.py .

# Create models directory
RUN mkdir -p /models /models/whisper

# Set environment variables
ENV WHISPER_MODEL=large-v3
ENV PHI_MODEL_PATH=/models/Phi-4-reasoning-plus-Q6_K_L.gguf
ENV PYTHONUNBUFFERED=1

# Pre-download Whisper model to speed up cold starts (optional)
ARG DOWNLOAD_WHISPER=false
RUN if [ "$DOWNLOAD_WHISPER" = "true" ]; then \
    python3 -c "from faster_whisper import WhisperModel; WhisperModel('large-v3', device='cpu', compute_type='int8', download_root='/models/whisper')"; \
    fi

# Note: Phi-4 model (12.28GB) will be downloaded at runtime

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python3 -c "import runpod; import llama_cpp; print('Health check passed')" || exit 1

# RunPod handler
CMD ["python3", "-u", "handler.py"]