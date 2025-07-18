# IASO Development Environment Configuration
# Based on actual AWS resources discovered

# AWS Configuration
aws_region = "us-west-2"

# Existing EKS Cluster
eks_cluster_name = "nexuscare-eks-dev"

# Existing RDS Configuration
rds_instance_identifier = "nexuscare-db-dev"
database_name          = "nexuscare_dev"
database_username      = "nexus_admin"
# database_password = set via TF_VAR_database_password environment variable

# Redis Configuration - Using in-cluster Redis
redis_cluster_id = ""  # Not using ElastiCache
# Instead, we'll connect to the Redis service in nexuscare-prod namespace

# Network Configuration
vpc_id = "vpc-0e2270777823943c5"
private_subnet_ids = [
  "subnet-045f86ba81697ea68",
  "subnet-0fa3c88ceaf931a23",
  "subnet-044928363bc3bb6b0",
  "subnet-0e99f0ff3fd438adb"
]

# Kubernetes Configuration
kubernetes_namespace = "iaso"  # New namespace for IASO services
create_namespace    = true

# Container Registry
ecr_repository_url = "727646479986.dkr.ecr.us-west-2.amazonaws.com/iaso"
image_tag          = "latest"

# Storage Configuration
storage_class = "gp2"  # Using gp2 as per cluster config

# Feature Flags
enable_infrastructure_ai = true
enable_monitoring       = true
enable_ingress         = true

# Domain Configuration
domain_name = ""  # Will use ALB DNS

# Node Groups Available:
# - cpu-spot: For cost-effective CPU workloads
# - gpu-ondemand: For GPU workloads (ML models)
# - gpu-spot-multi: For cost-effective GPU workloads
# - system-controllers: For system components
# - system-ng: For critical system workloads

# Tags
tags = {
  Team        = "AI"
  CostCenter  = "Development"
  Project     = "IASO"
  Environment = "dev"
}