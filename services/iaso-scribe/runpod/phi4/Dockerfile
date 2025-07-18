# Phi-4 Reasoning Plus for RunPod
FROM runpod/pytorch:2.2.0-py3.10-cuda12.1.1-devel-ubuntu22.04

WORKDIR /

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install \
    runpod \
    llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121 \
    requests \
    torch

# Copy handler from phi4 subdirectory
# RunPod always builds from repository root, regardless of Dockerfile location
COPY phi4/handler.py /handler.py

# Verify correct handler was copied
RUN echo "=== VERIFYING PHI-4 HANDLER ===" && head -n 20 /handler.py && echo "=== END VERIFICATION ==="

# Environment
ENV PYTHONUNBUFFERED=1

# Run handler
CMD ["python", "-u", "/handler.py"]