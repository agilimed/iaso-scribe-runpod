#!/bin/bash

# Deploy RASA on Kubernetes
# Usage: ./deploy-rasa.sh [cluster-type]
# cluster-type: gke, eks, or local (default: local)

set -e

CLUSTER_TYPE=${1:-local}
NAMESPACE="iasovoice"

echo "Deploying RASA to $CLUSTER_TYPE cluster..."

# Function to wait for deployment
wait_for_deployment() {
    local deployment=$1
    echo "Waiting for $deployment to be ready..."
    kubectl -n $NAMESPACE rollout status deployment/$deployment --timeout=300s
}

# Function to check if resource exists
resource_exists() {
    kubectl -n $NAMESPACE get $1 $2 &> /dev/null
}

# Create namespace if it doesn't exist
if ! kubectl get namespace $NAMESPACE &> /dev/null; then
    echo "Creating namespace $NAMESPACE..."
    kubectl apply -f namespace.yaml
else
    echo "Namespace $NAMESPACE already exists"
fi

# Deploy Redis
echo "Deploying Redis session store..."
kubectl apply -f redis-deployment.yaml
wait_for_deployment redis-session-store

# Deploy ConfigMaps
echo "Creating RASA configuration..."
kubectl apply -f configmap.yaml

# Deploy RASA Server
echo "Deploying RASA server..."
kubectl apply -f rasa-server-deployment.yaml
wait_for_deployment rasa-server

# Deploy Action Server
echo "Deploying RASA action server..."
kubectl apply -f rasa-action-server-deployment.yaml
wait_for_deployment rasa-action-server

# Deploy MCP Server
echo "Deploying RASA MCP server..."
kubectl apply -f rasa-mcp-deployment.yaml
wait_for_deployment rasa-mcp-server

# Check deployment status
echo ""
echo "Checking deployment status..."
kubectl -n $NAMESPACE get deployments
echo ""
kubectl -n $NAMESPACE get pods
echo ""
kubectl -n $NAMESPACE get services

# For GKE, create an ingress
if [ "$CLUSTER_TYPE" == "gke" ]; then
    echo ""
    echo "Creating GKE Ingress..."
    cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: rasa-ingress
  namespace: $NAMESPACE
  annotations:
    kubernetes.io/ingress.class: "gce"
    kubernetes.io/ingress.global-static-ip-name: "rasa-ip"
spec:
  rules:
  - http:
      paths:
      - path: /rasa/*
        pathType: ImplementationSpecific
        backend:
          service:
            name: rasa-server
            port:
              number: 5005
      - path: /actions/*
        pathType: ImplementationSpecific
        backend:
          service:
            name: rasa-action-server
            port:
              number: 5055
      - path: /mcp/*
        pathType: ImplementationSpecific
        backend:
          service:
            name: rasa-mcp-server
            port:
              number: 8091
EOF
fi

# For local development, set up port forwarding
if [ "$CLUSTER_TYPE" == "local" ]; then
    echo ""
    echo "Setting up port forwarding for local development..."
    echo "Run these commands in separate terminals:"
    echo "  kubectl -n $NAMESPACE port-forward svc/rasa-server 5005:5005"
    echo "  kubectl -n $NAMESPACE port-forward svc/rasa-action-server 5055:5055"
    echo "  kubectl -n $NAMESPACE port-forward svc/rasa-mcp-server 8091:8091"
    echo "  kubectl -n $NAMESPACE port-forward svc/redis-session-store 6379:6379"
fi

echo ""
echo "RASA deployment complete!"
echo ""
echo "Next steps:"
echo "1. Update the secret 'redis-secret' with a secure password"
echo "2. Update the secret 'runpod-secret' with your RunPod API key"
echo "3. Build and push the Docker images:"
echo "   - iaso/rasa-actions-medical:latest"
echo "   - iaso/rasa-mcp:latest"
echo "4. Train and upload your RASA model"
echo ""
echo "To train a model:"
echo "  rasa train --config config.yml --domain domain.yml --data data/"
echo ""
echo "To test the deployment:"
echo "  curl http://localhost:5005/status"