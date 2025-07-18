# IASO Terraform Infrastructure

This directory contains Terraform configurations for deploying IASO services across multiple cloud providers.

## Architecture Decision: EKS vs ECS

We're using **EKS (Elastic Kubernetes Service)** instead of ECS because:
1. You already have an existing EKS cluster running
2. Better integration with existing PostgreSQL (RDS) and Redis services
3. Cloud-agnostic approach (Kubernetes runs on AWS, GKE, AKS)
4. Existing Helm charts can be leveraged
5. Better resource utilization and cost optimization

## Directory Structure

```
terraform/
├── modules/               # Reusable Terraform modules
│   ├── iaso-core/        # Core IASO services
│   ├── iaso-clinical/    # Clinical AI services
│   ├── iaso-infrastructure/ # Infrastructure AI services
│   ├── networking/       # Network configurations
│   ├── storage/          # Storage configurations
│   └── monitoring/       # Monitoring and logging
├── providers/            # Provider-specific configurations
│   ├── aws/             # AWS-specific resources
│   ├── gcp/             # GCP-specific resources
│   ├── azure/           # Azure-specific resources
│   └── local/           # Local development
└── environments/        # Environment-specific configurations
    ├── dev/            # Development environment
    ├── staging/        # Staging environment
    └── prod/           # Production environment
```

## Deployment Strategy

### AWS EKS Deployment
- Deploy to existing EKS cluster
- Use existing RDS PostgreSQL (nexus_dev_db)
- Use existing Redis/ElastiCache
- Deploy services as Kubernetes deployments
- Use Fargate for serverless workloads
- Use EC2 nodes for GPU workloads

### Service Architecture
```
┌─────────────────────────────────────────────────────────┐
│                   Existing Infrastructure                │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐        ┌─────────────┐                │
│  │  RDS        │        │  ElastiCache │                │
│  │ PostgreSQL  │        │    Redis     │                │
│  └──────┬──────┘        └──────┬───────┘                │
│         │                       │                        │
├─────────┼───────────────────────┼────────────────────────┤
│         │      New IASO Services│                        │
│  ┌──────▼───────────────────────▼─────────────────────┐ │
│  │              EKS Cluster                            │ │
│  │  ┌─────────────────┐  ┌─────────────────┐         │ │
│  │  │ Clinical AI     │  │ Infrastructure  │         │ │
│  │  │ Namespace       │  │ AI Namespace    │         │ │
│  │  │                 │  │                 │         │ │
│  │  │ - Clinical AI   │  │ - AI Gateway    │         │ │
│  │  │ - Terminology   │  │ - Whisper       │         │ │
│  │  │ - Knowledge     │  │ - RAG           │         │ │
│  │  │ - Template      │  │ - SLM           │         │ │
│  │  │ - API Gateway   │  │                 │         │ │
│  │  └─────────────────┘  └─────────────────┘         │ │
│  │                                                     │ │
│  │  ┌─────────────────┐  ┌─────────────────┐         │ │
│  │  │ Supporting      │  │ Monitoring      │         │ │
│  │  │ Services        │  │                 │         │ │
│  │  │                 │  │ - Prometheus    │         │ │
│  │  │ - MeiliSearch   │  │ - Grafana       │         │ │
│  │  │ - Qdrant        │  │ - CloudWatch    │         │ │
│  │  └─────────────────┘  └─────────────────┘         │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Terraform >= 1.5
- kubectl configured for your EKS cluster
- AWS CLI configured
- Existing EKS cluster
- Existing RDS PostgreSQL database
- Existing Redis/ElastiCache instance

### Deployment Steps

1. **Initialize Terraform:**
   ```bash
   cd environments/dev
   terraform init
   ```

2. **Configure variables:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

3. **Plan deployment:**
   ```bash
   terraform plan
   ```

4. **Apply configuration:**
   ```bash
   terraform apply
   ```

## Configuration

### Required Variables
- `eks_cluster_name`: Name of existing EKS cluster
- `rds_endpoint`: Endpoint of existing RDS PostgreSQL
- `redis_endpoint`: Endpoint of existing Redis/ElastiCache
- `aws_region`: AWS region
- `environment`: Environment name (dev/staging/prod)

### Optional Variables
- `enable_gpu_nodes`: Enable GPU nodes for ML workloads
- `enable_fargate`: Enable Fargate for serverless workloads
- `enable_monitoring`: Enable Prometheus/Grafana monitoring