# Use RunPod's base image with CUDA support
FROM runpod/base:0.4.0-cuda12.1.0

# Install system dependencies including build tools for llama.cpp
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    cmake \
    python3-dev \
    libcublas-dev-12-1 \
    cuda-toolkit-12-1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Set CUDA paths for building
ENV CUDA_HOME=/usr/local/cuda-12.1
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# Copy requirements first for better caching
COPY requirements.txt .

# Upgrade pip and install build tools
RUN python3 -m pip install --upgrade pip setuptools wheel

# Install Python dependencies with proper CUDA support for llama-cpp-python
# Build llama-cpp-python from source with CUDA support
ENV CMAKE_ARGS="-DLLAMA_CUBLAS=on -DCMAKE_CUDA_ARCHITECTURES=all"
ENV FORCE_CMAKE=1
ENV LLAMA_CUBLAS=1
ENV CUDACXX=/usr/local/cuda-12.1/bin/nvcc

# Install dependencies in stages for better error handling
RUN pip install --no-cache-dir runpod>=1.3.0 faster-whisper>=1.0.0 torch>=2.0.0 requests>=2.31.0 numpy>=1.24.0 huggingface-hub>=0.20.0

# Build and install llama-cpp-python separately with verbose output
RUN pip install --no-cache-dir --verbose llama-cpp-python>=0.2.0

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