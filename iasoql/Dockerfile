# IASOQL RunPod Docker Image
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

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
    transformers==4.36.0 \
    accelerate==0.25.0 \
    sentencepiece==0.1.99 \
    protobuf==3.20.3 \
    bitsandbytes==0.41.3 \
    boto3==1.28.0

# Copy handler
COPY handler.py /handler.py

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV MODEL_NAME=iasoql-7b
ENV MODEL_PATH=/runpod-volume/models
ENV AWS_REGION=us-west-2

# Start handler
CMD ["python", "-u", "/handler.py"]