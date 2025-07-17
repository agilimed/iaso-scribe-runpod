# Use NVIDIA CUDA development image with cuDNN 9 for compilation support
FROM nvidia/cuda:12.3.2-cudnn9-devel-ubuntu22.04

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
    apt-get install --yes --no-install-recommends \
        sudo ca-certificates git wget curl bash libgl1 libx11-6 \
        software-properties-common ffmpeg build-essential cmake ninja-build \
        python3.10 python3.10-dev python3.10-venv python3-pip \
        cuda-nvcc-12-3 cuda-cudart-dev-12-3 libcublas-dev-12-3 -y && \
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

# Set CUDA paths
ENV CUDA_HOME=/usr/local/cuda-12.3
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# Verify CUDA installation
RUN nvcc --version && python3 -c "import torch; print(f'PyTorch CUDA: {torch.cuda.is_available()}')"

# Try pre-built wheel first, fallback to building from source
# Install llama-cpp-python with CUDA 12.1 support (closest to 12.3)
RUN pip install llama-cpp-python \
    --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121 \
    --force-reinstall --upgrade --no-cache-dir || \
    (echo "Pre-built wheel failed, building from source..." && \
    LLAMA_CUDA=1 CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=70;75;80;86;89;90" \
    FORCE_CMAKE=1 CUDACXX=/usr/local/cuda-12.3/bin/nvcc \
    pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir --verbose)

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