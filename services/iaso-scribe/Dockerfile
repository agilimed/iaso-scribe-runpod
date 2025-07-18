# Multi-stage Dockerfile for IasoScribe
# Supports RunPod, AWS Lambda, and GKE deployments

# Stage 1: Base image with CUDA support
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04 AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Python alias
RUN ln -s /usr/bin/python3.10 /usr/bin/python

# Stage 2: Builder stage for dependencies
FROM base AS builder

WORKDIR /build

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download Whisper models during build
RUN python -c "from faster_whisper import WhisperModel; \
    WhisperModel('medium', device='cpu', download_root='/models')"

# Stage 3: RunPod deployment
FROM base AS runpod

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /models /models

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Set environment variables for RunPod
ENV PYTHONUNBUFFERED=1
ENV MODEL_PATH=/models
ENV DEPLOYMENT_MODE=runpod

# Install RunPod SDK
RUN pip install runpod

# RunPod handler script
COPY scripts/runpod_start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]

# Stage 4: AWS Lambda deployment
FROM public.ecr.aws/lambda/python:3.10 AS lambda

# Install system dependencies
RUN yum update -y && \
    yum install -y ffmpeg && \
    yum clean all

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.10/dist-packages ${LAMBDA_TASK_ROOT}/
COPY --from=builder /models ${LAMBDA_TASK_ROOT}/models

# Copy application code
COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY scripts/lambda_handler.py ${LAMBDA_TASK_ROOT}/

# Set environment variables
ENV MODEL_PATH=${LAMBDA_TASK_ROOT}/models
ENV DEPLOYMENT_MODE=lambda

CMD ["lambda_handler.handler"]

# Stage 5: GKE/Kubernetes deployment
FROM base AS kubernetes

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /models /models

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Install additional dependencies for K8s
RUN pip install \
    fastapi \
    uvicorn \
    prometheus-client \
    python-multipart

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV MODEL_PATH=/models
ENV DEPLOYMENT_MODE=kubernetes

# Expose ports
EXPOSE 8080 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start FastAPI server
CMD ["uvicorn", "src.api_server:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]

# Default stage (Kubernetes)
FROM kubernetes