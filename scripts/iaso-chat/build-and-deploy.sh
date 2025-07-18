#!/bin/bash

# Build Docker images, push to ECR, and deploy IasoChat to EKS Fargate
# Usage: ./build-and-deploy.sh [aws-account-id] [region] [cluster-name]

set -e

# Configuration
AWS_ACCOUNT_ID=${1:-$(aws sts get-caller-identity --query Account --output text)}
REGION=${2:-us-east-1}
CLUSTER_NAME=${3:-iaso-platform}
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

# Image names
RASA_ACTIONS_IMAGE="iaso/rasa-actions-medical"
RASA_MCP_IMAGE="iaso/rasa-mcp"

echo "🚀 Building and deploying IasoChat to EKS Fargate..."
echo "AWS Account: $AWS_ACCOUNT_ID"
echo "Region: $REGION"
echo "Cluster: $CLUSTER_NAME"
echo "ECR Registry: $ECR_REGISTRY"

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI"
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker"
    exit 1
fi

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure'"
    exit 1
fi

# Check kubectl configuration
if ! kubectl cluster-info &> /dev/null; then
    echo "⚠️  kubectl not configured. Configuring for EKS cluster..."
    aws eks update-kubeconfig --name $CLUSTER_NAME --region $REGION
fi

# Create ECR repositories if they don't exist
echo "📦 Creating ECR repositories..."

create_ecr_repo() {
    local repo_name=$1
    if ! aws ecr describe-repositories --repository-names $repo_name --region $REGION &> /dev/null; then
        echo "Creating ECR repository: $repo_name"
        aws ecr create-repository --repository-name $repo_name --region $REGION
        # Set lifecycle policy to keep only last 10 images
        aws ecr put-lifecycle-policy \
            --repository-name $repo_name \
            --lifecycle-policy-text '{
                "rules": [
                    {
                        "rulePriority": 1,
                        "selection": {
                            "tagStatus": "untagged",
                            "countType": "sinceImagePushed",
                            "countUnit": "days",
                            "countNumber": 7
                        },
                        "action": {
                            "type": "expire"
                        }
                    },
                    {
                        "rulePriority": 2,
                        "selection": {
                            "tagStatus": "any",
                            "countType": "imageCountMoreThan",
                            "countNumber": 10
                        },
                        "action": {
                            "type": "expire"
                        }
                    }
                ]
            }' \
            --region $REGION
    else
        echo "ECR repository already exists: $repo_name"
    fi
}

create_ecr_repo $RASA_ACTIONS_IMAGE
create_ecr_repo $RASA_MCP_IMAGE

# Login to ECR
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Build timestamp for tagging
BUILD_TAG=$(date +%Y%m%d-%H%M%S)
COMMIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "local")

echo "🏗️  Building Docker images..."
echo "Build tag: $BUILD_TAG"
echo "Commit SHA: $COMMIT_SHA"

# Build RASA Actions image
echo "📦 Building RASA Actions image..."
cd /Users/vivekkrishnan/dev/iaso/services/iaso-chat

# Update Dockerfile.actions with better practices
cat > Dockerfile.actions << 'EOF'
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements-actions.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-actions.txt

# Copy application code
COPY actions/ /app/actions/
COPY domain.yml /app/

# Change ownership to app user
RUN chown -R app:app /app

# Switch to app user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5055/health || exit 1

# Expose port
EXPOSE 5055

# Run action server
CMD ["rasa", "run", "actions", "--port", "5055", "--debug"]
EOF

# Build actions image
docker build -t $RASA_ACTIONS_IMAGE:$BUILD_TAG -f Dockerfile.actions .
docker tag $RASA_ACTIONS_IMAGE:$BUILD_TAG $RASA_ACTIONS_IMAGE:latest
docker tag $RASA_ACTIONS_IMAGE:$BUILD_TAG $ECR_REGISTRY/$RASA_ACTIONS_IMAGE:$BUILD_TAG
docker tag $RASA_ACTIONS_IMAGE:$BUILD_TAG $ECR_REGISTRY/$RASA_ACTIONS_IMAGE:latest

# Build RASA MCP image
echo "📦 Building RASA MCP image..."
cd /Users/vivekkrishnan/dev/iaso/services/iaso-scribe/runpod/mcp

# Create Dockerfile for MCP server
cat > Dockerfile.rasa << 'EOF'
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy MCP server code
COPY rasa_mcp_server.py .

# Change ownership to app user
RUN chown -R app:app /app

# Switch to app user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8091/health || exit 1

# Expose port
EXPOSE 8091

# Run MCP server
CMD ["python", "rasa_mcp_server.py"]
EOF

# Build MCP image
docker build -t $RASA_MCP_IMAGE:$BUILD_TAG -f Dockerfile.rasa .
docker tag $RASA_MCP_IMAGE:$BUILD_TAG $RASA_MCP_IMAGE:latest
docker tag $RASA_MCP_IMAGE:$BUILD_TAG $ECR_REGISTRY/$RASA_MCP_IMAGE:$BUILD_TAG
docker tag $RASA_MCP_IMAGE:$BUILD_TAG $ECR_REGISTRY/$RASA_MCP_IMAGE:latest

# Push images to ECR
echo "⬆️  Pushing images to ECR..."

push_image() {
    local image_name=$1
    local tag=$2
    echo "Pushing $ECR_REGISTRY/$image_name:$tag"
    docker push $ECR_REGISTRY/$image_name:$tag
}

# Push actions image
push_image $RASA_ACTIONS_IMAGE $BUILD_TAG
push_image $RASA_ACTIONS_IMAGE latest

# Push MCP image
push_image $RASA_MCP_IMAGE $BUILD_TAG
push_image $RASA_MCP_IMAGE latest

echo "✅ Images pushed successfully!"

# Update Kubernetes manifests with ECR images
echo "📝 Updating Kubernetes manifests..."

# Update actions deployment
sed -i.bak "s|image: iaso/rasa-actions-medical:latest|image: $ECR_REGISTRY/$RASA_ACTIONS_IMAGE:$BUILD_TAG|g" \
    /Users/vivekkrishnan/dev/iaso/infrastructure/kubernetes/iaso-chat/rasa-actions-deployment.yaml

# Create MCP deployment
cat > /Users/vivekkrishnan/dev/iaso/infrastructure/kubernetes/iaso-chat/rasa-mcp-deployment.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rasa-mcp-server
  namespace: iaso-chat
  labels:
    app: rasa-mcp-server
    component: mcp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: rasa-mcp-server
  template:
    metadata:
      labels:
        app: rasa-mcp-server
        component: mcp
    spec:
      containers:
      - name: mcp-server
        image: $ECR_REGISTRY/$RASA_MCP_IMAGE:$BUILD_TAG
        ports:
        - containerPort: 8091
          name: http
        env:
        - name: RASA_SERVER_URL
          value: "http://rasa-server:5005"
        - name: RASA_ACTION_SERVER_URL
          value: "http://rasa-action-server:5055"
        - name: PYTHONUNBUFFERED
          value: "1"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8091
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8091
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: rasa-mcp-server
  namespace: iaso-chat
  labels:
    app: rasa-mcp-server
    component: mcp
spec:
  selector:
    app: rasa-mcp-server
  ports:
  - port: 8091
    targetPort: 8091
    name: http
  type: ClusterIP
EOF

# Deploy to EKS Fargate
echo "🚀 Deploying to EKS Fargate..."

# Export environment variables for deployment script
export RUNPOD_API_KEY=${RUNPOD_API_KEY}
export AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID
export REGION=$REGION

# Run deployment script
bash /Users/vivekkrishnan/dev/iaso/scripts/iaso-chat/deploy-eks-fargate.sh $CLUSTER_NAME $REGION

# Deploy MCP server
echo "🧠 Deploying MCP server..."
kubectl apply -f /Users/vivekkrishnan/dev/iaso/infrastructure/kubernetes/iaso-chat/rasa-mcp-deployment.yaml

# Wait for MCP deployment
kubectl wait --for=condition=Available deployment/rasa-mcp-server --namespace=iaso-chat --timeout=600s

# Get deployment status
echo "📊 Final deployment status..."
kubectl get deployments,pods,services -n iaso-chat

# Test the deployment
echo "🧪 Testing deployment..."
kubectl port-forward service/rasa-server 5005:5005 -n iaso-chat &
PF_PID=$!

sleep 10

# Test API
if curl -s http://localhost:5005/status | grep -q "available"; then
    echo "✅ RASA Server is healthy!"
else
    echo "⚠️  RASA Server health check failed"
fi

# Test conversation
echo "🗣️  Testing conversation..."
RESPONSE=$(curl -s -X POST http://localhost:5005/webhooks/rest/webhook \
    -H 'Content-Type: application/json' \
    -d '{"sender": "test", "message": "hello"}')

if echo "$RESPONSE" | grep -q "text"; then
    echo "✅ Conversation test successful!"
    echo "Response: $RESPONSE"
else
    echo "⚠️  Conversation test failed"
fi

kill $PF_PID

# Display final summary
echo ""
echo "🎉 IasoChat deployment completed successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "  • Build Tag: $BUILD_TAG"
echo "  • Commit SHA: $COMMIT_SHA"
echo "  • ECR Registry: $ECR_REGISTRY"
echo "  • Cluster: $CLUSTER_NAME"
echo "  • Region: $REGION"
echo ""
echo "🏷️  Images:"
echo "  • Actions: $ECR_REGISTRY/$RASA_ACTIONS_IMAGE:$BUILD_TAG"
echo "  • MCP: $ECR_REGISTRY/$RASA_MCP_IMAGE:$BUILD_TAG"
echo ""
echo "🔗 Services:"
echo "  • RASA Server: rasa-server.iaso-chat.svc.cluster.local:5005"
echo "  • Action Server: rasa-action-server.iaso-chat.svc.cluster.local:5055"
echo "  • MCP Server: rasa-mcp-server.iaso-chat.svc.cluster.local:8091"
echo "  • Redis: redis-session-store.iaso-chat.svc.cluster.local:6379"
echo ""
echo "🧪 Quick Test:"
echo "  kubectl port-forward service/rasa-server 5005:5005 -n iaso-chat"
echo "  curl -X POST http://localhost:5005/webhooks/rest/webhook -H 'Content-Type: application/json' -d '{\"sender\": \"test\", \"message\": \"hello\"}'"
echo ""
echo "📊 Monitor:"
echo "  kubectl get pods -n iaso-chat -w"
echo "  kubectl logs -l app=rasa-server -n iaso-chat -f"
echo ""
echo "🔧 Scale:"
echo "  kubectl scale deployment rasa-server --replicas=3 -n iaso-chat"
echo ""
echo "🗑️  Cleanup:"
echo "  kubectl delete namespace iaso-chat"
echo "  aws ecr delete-repository --repository-name $RASA_ACTIONS_IMAGE --region $REGION --force"
echo "  aws ecr delete-repository --repository-name $RASA_MCP_IMAGE --region $REGION --force"