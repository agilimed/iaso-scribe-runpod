#!/bin/bash

# Deploy IasoChat to EKS Fargate
# Usage: ./deploy-eks-fargate.sh [cluster-name] [region]

set -e

CLUSTER_NAME=${1:-nexuscare-eks-dev}
REGION=${2:-us-west-2}
NAMESPACE="iaso-chat"

echo "🚀 Deploying IasoChat to EKS Fargate..."
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "Namespace: $NAMESPACE"

# Check if kubectl is configured
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ kubectl not configured. Please run 'aws eks update-kubeconfig --name $CLUSTER_NAME --region $REGION'"
    exit 1
fi

# Check if cluster is Fargate-enabled
echo "🔍 Checking EKS Fargate configuration..."
if ! aws eks describe-fargate-profile --cluster-name $CLUSTER_NAME --fargate-profile-name default --region $REGION &> /dev/null; then
    echo "⚠️  No default Fargate profile found. Creating one..."
    
    # Create Fargate profile for IasoChat
    aws eks create-fargate-profile \
        --cluster-name $CLUSTER_NAME \
        --fargate-profile-name iaso-chat \
        --pod-execution-role-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/AmazonEKSFargatePodExecutionRole \
        --selectors namespace=$NAMESPACE \
        --region $REGION
    
    echo "⏳ Waiting for Fargate profile to be active..."
    aws eks wait fargate-profile-active --cluster-name $CLUSTER_NAME --fargate-profile-name iaso-chat --region $REGION
fi

# Create namespace
echo "📁 Creating namespace..."
kubectl apply -f ../../infrastructure/kubernetes/iaso-chat/namespace.yaml

# Wait for namespace to be ready
kubectl wait --for=condition=Ready namespace/$NAMESPACE --timeout=60s

# Create Redis secret with secure password
echo "🔐 Creating Redis secret..."
REDIS_PASSWORD=$(openssl rand -base64 32)
kubectl create secret generic redis-secret \
    --from-literal=password="$REDIS_PASSWORD" \
    --namespace=$NAMESPACE \
    --dry-run=client -o yaml | kubectl apply -f -

# Create RunPod secret
echo "🔐 Creating RunPod secret..."
if [ -z "$RUNPOD_API_KEY" ]; then
    echo "❌ RUNPOD_API_KEY environment variable not set"
    echo "Please set your RunPod API key: export RUNPOD_API_KEY=your-api-key"
    exit 1
fi

kubectl create secret generic runpod-secret \
    --from-literal=api-key="$RUNPOD_API_KEY" \
    --namespace=$NAMESPACE \
    --dry-run=client -o yaml | kubectl apply -f -

# Deploy ConfigMaps
echo "📝 Deploying configuration..."
kubectl apply -f ../../infrastructure/kubernetes/iaso-chat/configmap.yaml

# Deploy Redis
echo "🗄️  Deploying Redis session store..."
kubectl apply -f ../../infrastructure/kubernetes/iaso-chat/redis-deployment.yaml

# Wait for Redis to be ready
echo "⏳ Waiting for Redis to be ready..."
kubectl wait --for=condition=Ready pod -l app=redis-session-store --namespace=$NAMESPACE --timeout=300s

# Deploy RASA Action Server
echo "🎭 Deploying RASA Action Server..."
kubectl apply -f ../../infrastructure/kubernetes/iaso-chat/rasa-actions-deployment.yaml

# Deploy RASA Server
echo "🧠 Deploying RASA Server..."
kubectl apply -f ../../infrastructure/kubernetes/iaso-chat/rasa-server-deployment.yaml

# Wait for deployments to be ready
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=Available deployment/rasa-action-server --namespace=$NAMESPACE --timeout=600s
kubectl wait --for=condition=Available deployment/rasa-server --namespace=$NAMESPACE --timeout=600s

# Check deployment status
echo "📊 Checking deployment status..."
kubectl get deployments,pods,services -n $NAMESPACE

# Create ingress for external access (optional)
if [ "$3" = "--with-ingress" ]; then
    echo "🌐 Creating ingress..."
    cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: iaso-chat-ingress
  namespace: $NAMESPACE
  annotations:
    kubernetes.io/ingress.class: "alb"
    alb.ingress.kubernetes.io/scheme: "internet-facing"
    alb.ingress.kubernetes.io/target-type: "ip"
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS":443}]'
    alb.ingress.kubernetes.io/certificate-arn: "$SSL_CERT_ARN"
    alb.ingress.kubernetes.io/ssl-redirect: "443"
spec:
  rules:
  - host: chat.iaso.ai
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: rasa-server
            port:
              number: 5005
EOF
fi

# Test the deployment
echo "🧪 Testing deployment..."
kubectl port-forward service/rasa-server 5005:5005 -n $NAMESPACE &
PF_PID=$!

sleep 5

# Test health endpoint
if curl -s http://localhost:5005/status | grep -q "available"; then
    echo "✅ IasoChat deployment successful!"
else
    echo "❌ Deployment test failed"
    kill $PF_PID
    exit 1
fi

kill $PF_PID

# Display connection information
echo ""
echo "🎉 IasoChat deployment completed successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "  • Namespace: $NAMESPACE"
echo "  • RASA Server: rasa-server:5005"
echo "  • Action Server: rasa-action-server:5055"
echo "  • Redis: redis-session-store:6379"
echo ""
echo "🔗 Connection Commands:"
echo "  • Port forward RASA: kubectl port-forward service/rasa-server 5005:5005 -n $NAMESPACE"
echo "  • Port forward Actions: kubectl port-forward service/rasa-action-server 5055:5055 -n $NAMESPACE"
echo "  • View logs: kubectl logs -l app=rasa-server -n $NAMESPACE -f"
echo ""
echo "🧪 Test API:"
echo "  curl -X POST http://localhost:5005/webhooks/rest/webhook \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"sender\": \"test\", \"message\": \"hello\"}'"
echo ""
echo "📊 Monitor:"
echo "  kubectl get pods -n $NAMESPACE -w"
echo "  kubectl top pods -n $NAMESPACE"
echo ""
echo "🔧 Scale:"
echo "  kubectl scale deployment rasa-server --replicas=3 -n $NAMESPACE"
echo "  kubectl scale deployment rasa-action-server --replicas=3 -n $NAMESPACE"