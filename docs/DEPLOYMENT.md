# IASO AWS EKS Deployment Guide

This guide walks through deploying IASO services to your existing AWS EKS cluster.

## Prerequisites

- AWS CLI configured with appropriate credentials
- kubectl configured for your EKS cluster
- Docker installed for building images
- Terraform >= 1.5
- Access to the following AWS resources:
  - EKS cluster: `nexuscare-eks-dev`
  - RDS PostgreSQL: `nexuscare-db-dev`
  - VPC: `vpc-0e2270777823943c5`

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   AWS EKS Cluster                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐        ┌─────────────────┐            │
│  │  IASO Namespace │        │ nexuscare-prod  │            │
│  │                 │        │   namespace     │            │
│  │  - Clinical AI  │───────▶│  - Redis        │            │
│  │  - Terminology  │        │  - ClickHouse   │            │
│  │  - Knowledge    │        │  - Kafka        │            │
│  │  - API Gateway  │        └─────────────────┘            │
│  │  - MeiliSearch  │                                        │
│  │  - Qdrant       │                                        │
│  └─────────────────┘                                        │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────┐                                        │
│  │   AWS RDS       │                                        │
│  │  PostgreSQL     │                                        │
│  └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
```

## Quick Deployment

For a quick deployment, run:

```bash
./scripts/deploy-to-eks.sh
```

This script will:
1. Configure kubectl
2. Create the IASO namespace
3. Build and push Docker images
4. Deploy with Terraform
5. Set up ingress (optional)

## Step-by-Step Deployment

### 1. Configure Environment

Create `.env` file from the template (already created):
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 2. Build Docker Images

Build and push all service images to ECR:

```bash
./scripts/build-and-push-ecr.sh
```

This creates ECR repositories and pushes images for:
- `iaso-clinical-ai`
- `iaso-terminology`
- `iaso-knowledge`
- `iaso-template`
- `iaso-slm`
- `iaso-api-gateway`
- `iaso-embeddings`

### 3. Deploy with Terraform

```bash
cd infrastructure/terraform

# Set environment variables
export TF_VAR_database_password="postgres123"
export TF_VAR_redis_password=""

# Deploy
./deploy.sh -e dev -a plan
./deploy.sh -e dev -a apply -y
```

### 4. Verify Deployment

Check pod status:
```bash
kubectl -n iaso get pods
kubectl -n iaso get svc
```

### 5. Access Services

#### Local Port Forwarding

```bash
# API Gateway
kubectl port-forward -n iaso svc/iaso-api-gateway 8080:8080

# Clinical AI Service
kubectl port-forward -n iaso svc/iaso-clinical 8002:8002

# Terminology Service
kubectl port-forward -n iaso svc/iaso-terminology 8001:8001
```

#### Create ALB Ingress

```bash
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: iaso-ingress
  namespace: iaso
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
spec:
  rules:
    - http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: iaso-api-gateway
                port:
                  number: 8080
EOF
```

## Service Endpoints

Once deployed, services are available at:

| Service | Internal URL | Port |
|---------|-------------|------|
| API Gateway | http://iaso-api-gateway.iaso.svc.cluster.local | 8080 |
| Clinical AI | http://iaso-clinical.iaso.svc.cluster.local | 8002 |
| Terminology | http://iaso-terminology.iaso.svc.cluster.local | 8001 |
| Knowledge | http://iaso-knowledge.iaso.svc.cluster.local | 8004 |
| Template | http://iaso-template.iaso.svc.cluster.local | 8003 |
| MeiliSearch | http://iaso-meilisearch.iaso.svc.cluster.local | 7700 |
| Qdrant | http://iaso-qdrant.iaso.svc.cluster.local | 6333 |

## Configuration

### Database Connection

IASO services connect to your existing RDS instance:
- Host: `nexuscare-db-dev.ct8s6oiosa0a.us-west-2.rds.amazonaws.com`
- Database: `nexuscare_dev`
- User: `nexus_admin`

### Redis Connection

Using existing Redis in the cluster:
- Host: `redis-service.nexuscare-prod.svc.cluster.local`
- Port: 6379

### Security

1. **JWT Authentication**: Enabled by default
   - Set `JWT_SECRET` in production
   - Default expiration: 24 hours

2. **Rate Limiting**: Redis-backed
   - Default: 100 requests per minute
   - Configurable per endpoint

3. **CORS**: Configured for local development
   - Update `CORS_ORIGINS` for production

## Monitoring

### Health Checks

All services expose health endpoints:
```bash
curl http://localhost:8080/health
curl http://localhost:8002/health
curl http://localhost:8001/health
```

### Logs

View service logs:
```bash
kubectl logs -n iaso -l app=iaso -f
```

### Metrics

Prometheus metrics available at `/metrics` on each service.

## Troubleshooting

### Pod Issues

```bash
# Describe pod for details
kubectl describe pod <pod-name> -n iaso

# Check pod logs
kubectl logs <pod-name> -n iaso

# Execute into pod
kubectl exec -it <pod-name> -n iaso -- /bin/bash
```

### Database Connection

Test RDS connectivity:
```bash
kubectl run -it --rm psql-test --image=postgres:14 --restart=Never -n iaso -- \
  psql -h nexuscare-db-dev.ct8s6oiosa0a.us-west-2.rds.amazonaws.com \
  -U nexus_admin -d nexuscare_dev
```

### Image Pull Issues

Ensure ECR login:
```bash
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin \
  727646479986.dkr.ecr.us-west-2.amazonaws.com
```

## Scaling

### Manual Scaling

```bash
kubectl scale deployment iaso-clinical --replicas=3 -n iaso
```

### Auto-scaling

HPA is configured for services. Adjust in Terraform:
```hcl
autoscaling_config = {
  min_replicas = 2
  max_replicas = 10
  target_cpu_percent = 70
}
```

## Cleanup

To remove all IASO resources:

```bash
cd infrastructure/terraform
./deploy.sh -e dev -a destroy -y
```

## Next Steps

1. **Configure SSL/TLS**: Add ACM certificate for HTTPS
2. **Set up monitoring**: Deploy Prometheus/Grafana
3. **Configure backups**: Enable automated RDS backups
4. **Implement CI/CD**: GitHub Actions for automated deployments
5. **Add WAF**: Protect API endpoints with AWS WAF