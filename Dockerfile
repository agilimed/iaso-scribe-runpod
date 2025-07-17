# Use NVIDIA's official CUDA image with cuDNN 9 - same as RunPod's official faster-whisper
# This image has cuDNN 9 built-in, which CTranslate2 needs
FROM nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04

# Remove any third-party apt sources to avoid issues with expiring keys.
RUN rm -f /etc/apt/sources.list.d/*.list

# Set shell and noninteractive environment variables
SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive
ENV SHELL=/bin/bash

# Set CUDA environment variables for proper library loading
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=$CUDA_HOME/bin:$PATH
ENV LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

# Set working directory
WORKDIR /app

# Layer 1: System packages and Python (NVIDIA base doesn't include Python)
RUN apt-get update -y && \
    apt-get install --yes --no-install-recommends \
        python3.10 python3.10-dev python3.10-venv python3-pip \
        ffmpeg libgl1 libx11-6 wget curl build-essential && \
    ln -s /usr/bin/python3.10 /usr/bin/python && \
    ln -s /usr/bin/python3.10 /usr/bin/python3 && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

# Layer 2: Python setup verification
RUN python3 --version && pip3 --version

# Upgrade pip
RUN python3 -m pip install --upgrade pip setuptools wheel

# Layer 3: Copy requirements early for better caching
COPY requirements.txt .

# Install Python dependencies from requirements.txt
# Install PyTorch with CUDA 12.1 support (compatible with CUDA 12.3 runtime)
RUN pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu121 --no-cache-dir
RUN pip install --no-cache-dir -r requirements.txt

# Verify CUDA is available (RunPod base should have it configured)
RUN nvcc --version && python3 -c "import torch; print(f'PyTorch CUDA: {torch.cuda.is_available()}')"

# Layer 4: Install llama-cpp-python with CUDA 12.4 support
# Use pre-built wheels for CUDA 12.4 to match our base image
RUN pip install llama-cpp-python \
    --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124 \
    --force-reinstall --upgrade --no-cache-dir || \
    (echo "Pre-built wheel failed, building from source..." && \
    LLAMA_CUDA=1 CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --no-cache-dir)

# Copy handler and download script
COPY handler.py download_models.py ./

# Create fallback models directory and check disk space
RUN mkdir -p /models /models/whisper && \
    df -h / && \
    echo "Disk space available: $(df -h / | awk 'NR==2 {print $4}')"

# Optional: Pre-download models during build (set to true for production)
# This significantly increases image size but eliminates runtime downloads
ARG DOWNLOAD_MODELS=false
RUN if [ "$DOWNLOAD_MODELS" = "true" ]; then \
        echo "Pre-downloading models..." && \
        python3 download_models.py; \
    else \
        echo "Skipping model download. Models will be downloaded at runtime."; \
    fi

# Set environment variables
ENV WHISPER_MODEL=medium
ENV PHI_MODEL_PATH=/runpod-volume/models/microsoft_Phi-4-reasoning-plus-Q6_K_L.gguf
ENV PYTHONUNBUFFERED=1

# Pre-download Whisper model to speed up cold starts (optional)
ARG DOWNLOAD_WHISPER=false
RUN if [ "$DOWNLOAD_WHISPER" = "true" ]; then \
    python3 -c "from faster_whisper import WhisperModel; WhisperModel('medium', device='cpu', compute_type='int8', download_root='/models/whisper')"; \
    fi

# Clean up to reduce image size
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    find /usr/local/lib/python*/dist-packages -name "*.pyc" -delete && \
    find /usr/local/lib/python*/dist-packages -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Note: Phi-4 model (12.28GB) will be downloaded at runtime to network volume

# RunPod handler
CMD ["python3", "-u", "handler.py"]