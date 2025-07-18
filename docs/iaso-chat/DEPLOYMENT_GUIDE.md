# IasoChat Deployment Guide

This guide provides step-by-step instructions for building and deploying IasoChat to AWS EKS Fargate.

## Prerequisites

### Local Environment
- **Docker Desktop** installed and running
- **AWS CLI** configured with appropriate permissions
- **kubectl** installed and configured
- **Git** for version control

### AWS Environment
- **EKS Cluster** with Fargate support
- **ECR Repositories** for Docker images
- **IAM Roles** for EKS and Fargate
- **VPC** with proper subnets

### Required Permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:CreateRepository",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "eks:DescribeCluster",
        "eks:ListClusters",
        "eks:CreateFargateProfile",
        "eks:DescribeFargateProfile"
      ],
      "Resource": "*"
    }
  ]
}
```

## Environment Setup

### 1. Configure AWS CLI
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter your default region (e.g., us-east-1)
# Enter your default output format (json)
```

### 2. Set Environment Variables
```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=us-east-1
export CLUSTER_NAME=iaso-platform
export RUNPOD_API_KEY=your-runpod-api-key-here
```

### 3. Configure kubectl for EKS
```bash
aws eks update-kubeconfig --name $CLUSTER_NAME --region $AWS_REGION
```

## Build and Deploy

### Option 1: Automated Deployment (Recommended)
```bash
cd /Users/vivekkrishnan/dev/iaso
./scripts/iaso-chat/build-and-deploy.sh
```

### Option 2: Step-by-Step Manual Deployment

#### Step 1: Build Docker Images Locally
```bash
cd /Users/vivekkrishnan/dev/iaso/services/iaso-chat

# Build RASA Actions image
docker build -t iaso/rasa-actions-medical:latest -f Dockerfile.actions .

# Build RASA MCP image
cd /Users/vivekkrishnan/dev/iaso/services/iaso-scribe/runpod/mcp
docker build -t iaso/rasa-mcp:latest -f Dockerfile.rasa .
```

#### Step 2: Create ECR Repositories
```bash
# Create repositories
aws ecr create-repository --repository-name iaso/rasa-actions-medical --region $AWS_REGION
aws ecr create-repository --repository-name iaso/rasa-mcp --region $AWS_REGION

# Get ECR login
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

#### Step 3: Tag and Push Images
```bash
# Tag images
docker tag iaso/rasa-actions-medical:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/iaso/rasa-actions-medical:latest
docker tag iaso/rasa-mcp:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/iaso/rasa-mcp:latest

# Push images
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/iaso/rasa-actions-medical:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/iaso/rasa-mcp:latest
```

#### Step 4: Deploy to EKS
```bash
cd /Users/vivekkrishnan/dev/iaso

# Deploy IasoChat
./scripts/iaso-chat/deploy-eks-fargate.sh $CLUSTER_NAME $AWS_REGION
```

## Deployment Architecture

### EKS Fargate Configuration
```yaml
# Fargate Profile
apiVersion: eks.aws.amazon.com/v1alpha1
kind: FargateProfile
metadata:
  name: iaso-chat
spec:
  clusterName: iaso-platform
  subnets:
    - subnet-xxxxxxxx  # Private subnet 1
    - subnet-yyyyyyyy  # Private subnet 2
  selectors:
    - namespace: iaso-chat
  podExecutionRoleArn: arn:aws:iam::ACCOUNT-ID:role/eks-fargate-pod-execution-role
```

### Resource Allocation
| Component | CPU Request | Memory Request | CPU Limit | Memory Limit |
|-----------|-------------|----------------|-----------|--------------|
| RASA Server | 500m | 1Gi | 1 | 2Gi |
| Actions Server | 500m | 1Gi | 1 | 2Gi |
| MCP Server | 250m | 512Mi | 500m | 1Gi |
| Redis | 100m | 128Mi | 200m | 256Mi |

### Networking
- **ClusterIP Services**: Internal communication
- **Ingress Controller**: External access (optional)
- **Service Mesh**: Istio integration (optional)

## Monitoring and Logging

### CloudWatch Integration
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: amazon-cloudwatch
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         1
        Log_Level     info
        Daemon        off
        Parsers_File  parsers.conf
        HTTP_Server   On
        HTTP_Listen   0.0.0.0
        HTTP_Port     2020
    
    [INPUT]
        Name              tail
        Tag               application.*
        Path              /var/log/containers/*iaso-chat*.log
        Parser            docker
        DB                /var/log/flb_kube.db
        Mem_Buf_Limit     50MB
        Skip_Long_Lines   On
        Refresh_Interval  10
    
    [OUTPUT]
        Name                cloudwatch_logs
        Match               application.*
        region              us-east-1
        log_group_name      /aws/eks/iaso-chat
        log_stream_prefix   fargate-
        auto_create_group   true
```

### Prometheus Metrics
```yaml
apiVersion: v1
kind: Service
metadata:
  name: rasa-server-metrics
  namespace: iaso-chat
  labels:
    app: rasa-server
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "5005"
    prometheus.io/path: "/metrics"
spec:
  selector:
    app: rasa-server
  ports:
  - name: metrics
    port: 5005
    targetPort: 5005
```

## Scaling Configuration

### Horizontal Pod Autoscaler
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: rasa-server-hpa
  namespace: iaso-chat
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: rasa-server
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Vertical Pod Autoscaler
```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: rasa-server-vpa
  namespace: iaso-chat
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: rasa-server
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: rasa-server
      minAllowed:
        cpu: 100m
        memory: 512Mi
      maxAllowed:
        cpu: 2
        memory: 4Gi
```

## Security Configuration

### Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: iaso-chat-network-policy
  namespace: iaso-chat
spec:
  podSelector:
    matchLabels:
      app: rasa-server
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: iaso-voice
    - podSelector:
        matchLabels:
          app: voice-orchestrator
    ports:
    - protocol: TCP
      port: 5005
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: rasa-action-server
    ports:
    - protocol: TCP
      port: 5055
  - to:
    - podSelector:
        matchLabels:
          app: redis-session-store
    ports:
    - protocol: TCP
      port: 6379
```

### Pod Security Standards
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: iaso-chat
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

## Backup and Recovery

### Redis Backup
```bash
# Create backup
kubectl exec -n iaso-chat deployment/redis-session-store -- redis-cli --rdb /tmp/backup.rdb

# Restore backup
kubectl cp iaso-chat/redis-session-store-xxx:/tmp/backup.rdb ./backup.rdb
```

### Model Backup
```bash
# Backup models
kubectl exec -n iaso-chat deployment/rasa-server -- tar -czf /tmp/models-backup.tar.gz /app/models

# Copy backup
kubectl cp iaso-chat/rasa-server-xxx:/tmp/models-backup.tar.gz ./models-backup.tar.gz
```

## Troubleshooting

### Common Issues

#### 1. ImagePullBackOff
```bash
# Check ECR permissions
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Verify image exists
aws ecr list-images --repository-name iaso/rasa-actions-medical --region $AWS_REGION
```

#### 2. Pod Startup Issues
```bash
# Check pod logs
kubectl logs -n iaso-chat deployment/rasa-server -f

# Describe pod
kubectl describe pod -n iaso-chat -l app=rasa-server
```

#### 3. Service Discovery Issues
```bash
# Check service endpoints
kubectl get endpoints -n iaso-chat

# Test service connectivity
kubectl exec -n iaso-chat deployment/rasa-server -- curl http://rasa-action-server:5055/health
```

### Debugging Commands
```bash
# Get all resources
kubectl get all -n iaso-chat

# Check resource usage
kubectl top pods -n iaso-chat

# Check events
kubectl get events -n iaso-chat --sort-by=.metadata.creationTimestamp

# Port forward for testing
kubectl port-forward -n iaso-chat service/rasa-server 5005:5005

# Execute into pod
kubectl exec -it -n iaso-chat deployment/rasa-server -- bash
```

## Performance Optimization

### RASA Model Optimization
```python
# config.yml optimizations
policies:
  - name: TEDPolicy
    max_history: 3  # Reduced from 5
    epochs: 50      # Reduced from 100
    batch_size: 64  # Increased batch size
    model_confidence: linear_norm
```

### Redis Configuration
```yaml
# Redis optimizations
env:
- name: REDIS_MAXMEMORY
  value: "200mb"
- name: REDIS_MAXMEMORY_POLICY
  value: "allkeys-lru"
- name: REDIS_SAVE
  value: "900 1"  # Save every 15 minutes if at least 1 key changed
```

## Cost Optimization

### Fargate Pricing
- **vCPU**: $0.04048 per vCPU per hour
- **Memory**: $0.004445 per GB per hour
- **Storage**: $0.000111 per GB per hour

### Cost Estimation
| Component | vCPU | Memory | Monthly Cost |
|-----------|------|--------|--------------|
| RASA Server (2 pods) | 2 | 4 GB | ~$75 |
| Actions Server (2 pods) | 2 | 4 GB | ~$75 |
| MCP Server (2 pods) | 1 | 2 GB | ~$40 |
| Redis (1 pod) | 0.25 | 0.5 GB | ~$10 |
| **Total** | **5.25** | **10.5 GB** | **~$200** |

### Cost Reduction Strategies
1. **Right-sizing**: Use VPA to optimize resource allocation
2. **Spot Instances**: Use Fargate Spot for non-critical workloads
3. **Scheduled Scaling**: Scale down during off-hours
4. **Resource Quotas**: Set limits to prevent over-provisioning

## Maintenance

### Update Strategy
```bash
# Rolling update
kubectl set image deployment/rasa-server rasa-server=new-image:tag -n iaso-chat

# Check rollout status
kubectl rollout status deployment/rasa-server -n iaso-chat

# Rollback if needed
kubectl rollout undo deployment/rasa-server -n iaso-chat
```

### Health Checks
```bash
# Automated health check script
#!/bin/bash
NAMESPACE="iaso-chat"
SERVICES=("rasa-server" "rasa-action-server" "rasa-mcp-server" "redis-session-store")

for service in "${SERVICES[@]}"; do
    if kubectl get pods -n $NAMESPACE -l app=$service | grep -q "1/1.*Running"; then
        echo "✅ $service is healthy"
    else
        echo "❌ $service is unhealthy"
        kubectl describe pods -n $NAMESPACE -l app=$service
    fi
done
```

---

## Quick Reference

### Essential Commands
```bash
# Deploy
./scripts/iaso-chat/build-and-deploy.sh

# Test
curl -X POST http://localhost:5005/webhooks/rest/webhook -H 'Content-Type: application/json' -d '{"sender": "test", "message": "hello"}'

# Monitor
kubectl get pods -n iaso-chat -w

# Scale
kubectl scale deployment rasa-server --replicas=3 -n iaso-chat

# Cleanup
kubectl delete namespace iaso-chat
```

### Service Endpoints
- **RASA Server**: `http://rasa-server.iaso-chat.svc.cluster.local:5005`
- **Actions Server**: `http://rasa-action-server.iaso-chat.svc.cluster.local:5055`
- **MCP Server**: `http://rasa-mcp-server.iaso-chat.svc.cluster.local:8091`
- **Redis**: `redis://redis-session-store.iaso-chat.svc.cluster.local:6379`

---

**IasoChat**: Production-ready conversational AI for healthcare on EKS Fargate.