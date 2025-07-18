FROM rasa/rasa:3.6.0

# Switch to root user for installing packages
USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Switch back to rasa user
USER 1001

# Set working directory
WORKDIR /app

# Copy RASA configuration files
COPY config.yml /app/
COPY domain.yml /app/
COPY credentials.yml /app/
COPY endpoints.yml /app/

# Copy training data
COPY data/ /app/data/

# Copy trained model (if exists)
COPY models/ /app/models/ 2>/dev/null || true

# Expose RASA server port
EXPOSE 5005

# Train model and start server
CMD ["run", "--enable-api", "--cors", "*", "--debug"]