# Phi-4 Service Dockerfile
FROM runpod/pytorch:2.2.0-py3.10-cuda12.1.1-devel-ubuntu22.04

WORKDIR /

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install \
    runpod \
    llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121 \
    requests \
    torch

# Add handler
COPY phi4/handler.py /handler.py

# Environment
ENV PYTHONUNBUFFERED=1

# Run handler
CMD ["python", "-u", "/handler.py"]