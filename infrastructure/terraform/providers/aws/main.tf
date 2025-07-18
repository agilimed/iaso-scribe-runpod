# AWS Provider Configuration for IASO

terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }
}

# AWS Provider
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = merge(var.tags, {
      Environment = var.environment
      CloudProvider = "AWS"
    })
  }
}

# Data source for existing EKS cluster
data "aws_eks_cluster" "existing" {
  name = var.eks_cluster_name
}

data "aws_eks_cluster_auth" "existing" {
  name = var.eks_cluster_name
}

# Kubernetes Provider
provider "kubernetes" {
  host                   = data.aws_eks_cluster.existing.endpoint
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.existing.certificate_authority[0].data)
  token                  = data.aws_eks_cluster_auth.existing.token
}

# Helm Provider
provider "helm" {
  kubernetes {
    host                   = data.aws_eks_cluster.existing.endpoint
    cluster_ca_certificate = base64decode(data.aws_eks_cluster.existing.certificate_authority[0].data)
    token                  = data.aws_eks_cluster_auth.existing.token
  }
}

# Data sources for existing resources
data "aws_db_instance" "existing_rds" {
  db_instance_identifier = var.rds_instance_identifier
}

data "aws_elasticache_cluster" "existing_redis" {
  count      = var.redis_cluster_id != "" ? 1 : 0
  cluster_id = var.redis_cluster_id
}