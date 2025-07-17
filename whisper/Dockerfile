# RunPod Official faster-whisper approach
FROM nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04

# Remove third-party apt sources
RUN rm -f /etc/apt/sources.list.d/*.list

# Set environment
SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /

# Install system packages and Python
RUN apt-get update -y && \
    apt-get install --yes --no-install-recommends \
    python3.10 python3.10-dev python3-pip \
    ffmpeg build-essential && \
    ln -s /usr/bin/python3.10 /usr/bin/python && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install \
    runpod \
    faster-whisper \
    requests \
    numpy

# Add handler
COPY handler.py /

# Environment
ENV PYTHONUNBUFFERED=1

# Run handler
CMD ["python", "-u", "/handler.py"]