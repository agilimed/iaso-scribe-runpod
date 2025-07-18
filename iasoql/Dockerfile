# IASOQL RunPod Docker Image
# Build: 2025-07-18-v3 - Force rebuild with IASOQL handler
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# Force cache invalidation  
ARG CACHEBUST=4

# Set working directory
WORKDIR /

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in the correct order
RUN pip install --upgrade pip

# Install PyTorch first with CUDA support
RUN pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cu118

# Install core dependencies
RUN pip install --no-cache-dir \
    accelerate>=0.21.0 \
    transformers>=4.37.0 \
    huggingface-hub \
    safetensors \
    sentencepiece==0.1.99 \
    protobuf==3.20.3 \
    tiktoken

# Install bitsandbytes separately (requires CUDA)
RUN pip install --no-cache-dir bitsandbytes==0.41.3

# Install RunPod
RUN pip install --no-cache-dir runpod==1.6.2

# Verify installations
RUN python -c "import torch; print(f'PyTorch version: {torch.__version__}, CUDA available: {torch.cuda.is_available()}')"
RUN python -c "import accelerate; print(f'Accelerate version: {accelerate.__version__}')"
RUN python -c "import transformers; print(f'Transformers version: {transformers.__version__}')"
RUN python -c "import bitsandbytes; print(f'Bitsandbytes loaded successfully')"

# Copy handler from iasoql subdirectory
# RunPod always builds from repository root, regardless of Dockerfile location
COPY iasoql/handler.py /handler.py

# Verify correct handler was copied
RUN echo "=== VERIFYING IASOQL HANDLER ===" && head -n 20 /handler.py && echo "=== END VERIFICATION ==="

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Start handler
CMD ["python", "-u", "/handler.py"]