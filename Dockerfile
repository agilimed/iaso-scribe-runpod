# Use NVIDIA CUDA image with cuDNN 9 for faster-whisper turbo support
FROM nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04

# Remove any third-party apt sources to avoid issues with expiring keys.
RUN rm -f /etc/apt/sources.list.d/*.list

# Set shell and noninteractive environment variables
SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive
ENV SHELL=/bin/bash

# Set working directory
WORKDIR /app

# Update and upgrade the system packages
RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install --yes --no-install-recommends sudo ca-certificates git wget curl bash libgl1 libx11-6 software-properties-common ffmpeg build-essential python3.10 python3.10-dev python3.10-venv python3-pip -y && \
    ln -s /usr/bin/python3.10 /usr/bin/python && \
    rm -f /usr/bin/python3 && \
    ln -s /usr/bin/python3.10 /usr/bin/python3 && \
    apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python3 -m pip install --upgrade pip setuptools wheel

# Copy requirements
COPY requirements.txt .

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install llama-cpp-python with CUDA support
# The nvidia/cuda base image already has CUDA runtime and dev tools
ENV LLAMA_CUDA=1
ENV CMAKE_ARGS="-DGGML_CUDA=on"
ENV FORCE_CMAKE=1
ENV CUDA_DOCKER_ARCH=all

# Install with CUDA support
RUN pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir --verbose

# Copy handler and download script
COPY handler.py download_models.py ./

# Create models directory and check disk space
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
ENV PHI_MODEL_PATH=/models/microsoft_Phi-4-reasoning-plus-Q6_K_L.gguf
ENV PYTHONUNBUFFERED=1

# Pre-download Whisper model to speed up cold starts (optional)
ARG DOWNLOAD_WHISPER=false
RUN if [ "$DOWNLOAD_WHISPER" = "true" ]; then \
    python3 -c "from faster_whisper import WhisperModel; WhisperModel('medium', device='cpu', compute_type='int8', download_root='/models/whisper')"; \
    fi

# Note: Phi-4 model (12.28GB) will be downloaded at runtime

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python3 -c "import runpod; import llama_cpp; print('Health check passed')" || exit 1

# RunPod handler
CMD ["python3", "-u", "handler.py"]