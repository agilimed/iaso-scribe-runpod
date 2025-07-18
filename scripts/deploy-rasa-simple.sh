#!/bin/bash

# Deploy RASA services using Docker Compose
# Usage: ./deploy-rasa-simple.sh

set -e

PROJECT_ROOT="/Users/vivekkrishnan/dev/iaso/services/iaso-scribe/runpod"
RASA_DIR="$PROJECT_ROOT/rasa"

echo "Deploying RASA services using Docker Compose..."

# Create Docker Compose file
cat > "$RASA_DIR/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data

  rasa-server:
    image: rasa/rasa:3.6.0
    ports:
      - "5005:5005"
    volumes:
      - ./:/app
    command: >
      bash -c "
        rasa train --domain domain.yml --config config.yml --data data/ --out models/ &&
        rasa run --enable-api --cors '*' --debug --endpoints endpoints.yml --credentials credentials.yml
      "
    depends_on:
      - redis

  rasa-actions:
    build:
      context: .
      dockerfile: Dockerfile.actions
    ports:
      - "5055:5055"
    volumes:
      - ./actions:/app/actions
      - ./domain.yml:/app/domain.yml
    environment:
      - RUNPOD_API_KEY=${RUNPOD_API_KEY}
      - WHISPER_ENDPOINT_ID=${WHISPER_ENDPOINT_ID}
      - PHI4_ENDPOINT_ID=${PHI4_ENDPOINT_ID}
      - CLINICAL_AI_URL=${CLINICAL_AI_URL:-http://localhost:8002}

volumes:
  redis-data:
EOF

# Update endpoints.yml for Docker network
cat > "$RASA_DIR/endpoints.yml" << 'EOF'
action_endpoint:
  url: "http://rasa-actions:5055/webhook"

tracker_store:
  type: redis
  url: "redis://redis:6379"
  db: 0

models:
  url: "http://rasa-server:5005/models"
  wait_time_between_pulls: 10
EOF

# Create environment file
cat > "$RASA_DIR/.env" << 'EOF'
RUNPOD_API_KEY=your-runpod-api-key-here
WHISPER_ENDPOINT_ID=rntxttrdl8uv3i
PHI4_ENDPOINT_ID=tmmwa4q8ax5sg4
CLINICAL_AI_URL=http://localhost:8002
EOF

# Deploy using Docker Compose
cd "$RASA_DIR"
echo "Starting RASA services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 30

# Check service status
echo "Checking service status..."
docker-compose ps

# Test the RASA API
echo "Testing RASA API..."
sleep 10
curl -X POST http://localhost:5005/webhooks/rest/webhook \
  -H 'Content-Type: application/json' \
  -d '{"sender": "test", "message": "hello"}' || echo "API test failed - service may still be starting"

echo ""
echo "✅ RASA deployment completed!"
echo ""
echo "Services:"
echo "- RASA Server: http://localhost:5005"
echo "- RASA Actions: http://localhost:5055"
echo "- Redis: redis://localhost:6379"
echo ""
echo "To test the API:"
echo "curl -X POST http://localhost:5005/webhooks/rest/webhook -H 'Content-Type: application/json' -d '{\"sender\": \"test\", \"message\": \"hello\"}'"
echo ""
echo "To view logs:"
echo "docker-compose logs -f rasa-server"
echo ""
echo "To stop services:"
echo "docker-compose down"