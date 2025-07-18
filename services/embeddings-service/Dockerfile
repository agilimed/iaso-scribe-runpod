# IASO Embeddings Service Dockerfile
FROM node:18-slim

# Install system dependencies for ONNX
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./
RUN npm ci --only=production

# Copy application code
COPY . .

# Build TypeScript if needed
RUN npm run build || true

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Download models (optional - can be done at runtime)
# RUN npm run download-models

# Expose ports
EXPOSE 8050
EXPOSE 50051

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8050/health || exit 1

# Run the service
CMD ["npm", "start"]