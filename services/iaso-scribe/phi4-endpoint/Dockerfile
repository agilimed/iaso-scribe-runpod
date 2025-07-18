# Phi-4 Reasoning Plus on RunPod
FROM runpod/pytorch:2.2.0-py3.10-cuda12.1.1-devel-ubuntu22.04

WORKDIR /

# Install llama-cpp-python with CUDA support
RUN pip install --upgrade pip && \
    CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --no-cache-dir && \
    pip install runpod requests

# Add handler
COPY handler.py /

# Environment
ENV PYTHONUNBUFFERED=1
ENV DEVICE=cuda

# Run handler
CMD ["python", "-u", "/handler.py"]