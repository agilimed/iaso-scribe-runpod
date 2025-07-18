# IASOQL RunPod Docker Image
# Build: 2025-07-18-v3 - Force rebuild with IASOQL handler
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# Force cache invalidation
ARG CACHEBUST=3

# Set working directory
WORKDIR /

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir \
    runpod==1.6.2 \
    torch==2.1.0 \
    transformers==4.52.3 \
    accelerate==0.25.0 \
    sentencepiece==0.1.99 \
    protobuf==3.20.3 \
    bitsandbytes==0.41.3 \
    tiktoken

# Copy handler from iasoql subdirectory
# RunPod always builds from repository root, regardless of Dockerfile location
COPY iasoql/handler.py /handler.py

# Verify correct handler was copied
RUN echo "=== VERIFYING IASOQL HANDLER ===" && head -n 20 /handler.py && echo "=== END VERIFICATION ==="

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Start handler
CMD ["python", "-u", "/handler.py"]