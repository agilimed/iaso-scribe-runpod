# Development Environment Variables

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "iaso"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# EKS Configuration
variable "eks_cluster_name" {
  description = "Name of existing EKS cluster"
  type        = string
}

# RDS Configuration
variable "rds_instance_identifier" {
  description = "RDS instance identifier"
  type        = string
}

variable "database_name" {
  description = "Database name in RDS"
  type        = string
  default     = "nexus_dev_db"
}

variable "database_username" {
  description = "Database username"
  type        = string
  default     = "nexus_admin"
}

variable "database_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

# Redis Configuration
variable "redis_cluster_id" {
  description = "ElastiCache Redis cluster ID"
  type        = string
}

variable "redis_password" {
  description = "Redis password"
  type        = string
  sensitive   = true
  default     = ""
}

# Network Configuration
variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs"
  type        = list(string)
}

# Kubernetes Configuration
variable "kubernetes_namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "iaso-dev"
}

variable "create_namespace" {
  description = "Create namespace if it doesn't exist"
  type        = bool
  default     = true
}

# Container Registry
variable "ecr_repository_url" {
  description = "ECR repository URL (optional)"
  type        = string
  default     = ""
}

variable "image_tag" {
  description = "Container image tag"
  type        = string
  default     = "latest"
}

# Storage
variable "storage_class" {
  description = "Storage class for persistent volumes"
  type        = string
  default     = "gp3"
}

# Feature Flags
variable "enable_infrastructure_ai" {
  description = "Enable infrastructure AI services"
  type        = bool
  default     = true
}

variable "enable_monitoring" {
  description = "Enable monitoring stack"
  type        = bool
  default     = false
}

variable "enable_ingress" {
  description = "Enable ingress"
  type        = bool
  default     = true
}

# Domain Configuration
variable "domain_name" {
  description = "Domain name for services"
  type        = string
  default     = ""
}

# Tags
variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default = {
    Team        = "AI"
    CostCenter  = "Development"
  }
}