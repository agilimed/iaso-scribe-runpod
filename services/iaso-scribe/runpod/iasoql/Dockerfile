# IASOQL RunPod Docker Image
# Optimized for healthcare SQL generation with Qwen2-based model
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Set working directory
WORKDIR /

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create symlink for python
RUN ln -sf /usr/bin/python3.10 /usr/bin/python

# Upgrade pip
RUN python -m pip install --upgrade pip

# Set CUDA environment variables
ENV CUDA_HOME=/usr/local/cuda
ENV LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
ENV PATH=$CUDA_HOME/bin:$PATH

# Install PyTorch with CUDA 12.1 support
RUN pip install torch==2.1.2+cu121 torchvision==0.16.2+cu121 torchaudio==2.1.2+cu121 \
    -f https://download.pytorch.org/whl/cu121/torch_stable.html

# Install core ML dependencies in the correct order
RUN pip install --no-cache-dir \
    numpy==1.24.3 \
    scipy==1.11.4 \
    transformers==4.37.2 \
    accelerate==0.26.1 \
    safetensors==0.4.1 \
    sentencepiece==0.1.99 \
    protobuf==3.20.3 \
    tiktoken==0.5.2 \
    huggingface-hub==0.20.3

# Install bitsandbytes with CUDA support
# Set environment variable to help bitsandbytes find CUDA
ENV BNB_CUDA_VERSION=121
RUN pip install --no-cache-dir bitsandbytes==0.42.0

# Install RunPod SDK
RUN pip install --no-cache-dir runpod==1.6.2

# Set environment variables for RunPod
ENV PYTHONUNBUFFERED=1
ENV TOKENIZERS_PARALLELISM=false
ENV RUNPOD_DEBUG_LEVEL=INFO

# GPU memory optimization
ENV PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Model caching configuration
ENV HF_HOME=/runpod-volume/huggingface
ENV TRANSFORMERS_CACHE=/runpod-volume/huggingface
ENV HUGGINGFACE_HUB_CACHE=/runpod-volume/huggingface/hub

# Verify installations
RUN python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}, Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}')"
RUN python -c "import transformers; print(f'Transformers: {transformers.__version__}')"
RUN python -c "import accelerate; print(f'Accelerate: {accelerate.__version__}')"
RUN python -c "import bitsandbytes as bnb; print(f'Bitsandbytes: {bnb.__version__}')"

# Copy handler
COPY iasoql/handler.py /handler.py

# Pre-download model weights (optional - comment out if you want to load at runtime)
# This speeds up cold starts but increases image size
# ARG HUGGINGFACE_TOKEN
# ENV HUGGINGFACE_TOKEN=$HUGGINGFACE_TOKEN
# RUN python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; \
#     import os; \
#     token = os.environ.get('HUGGINGFACE_TOKEN'); \
#     AutoTokenizer.from_pretrained('vivkris/iasoql-7B', token=token); \
#     AutoModelForCausalLM.from_pretrained('vivkris/iasoql-7B', torch_dtype=torch.float16, token=token)"

# Start handler
CMD ["python", "-u", "/handler.py"]