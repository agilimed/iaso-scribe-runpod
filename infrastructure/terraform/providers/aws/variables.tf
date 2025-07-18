# AWS-specific variables

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "eks_cluster_name" {
  description = "Name of existing EKS cluster"
  type        = string
}

variable "rds_instance_identifier" {
  description = "Identifier of existing RDS instance"
  type        = string
}

variable "redis_cluster_id" {
  description = "ID of existing ElastiCache Redis cluster"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where resources will be deployed"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for deployment"
  type        = list(string)
}

variable "ecr_repository_prefix" {
  description = "ECR repository prefix for container images"
  type        = string
  default     = ""
}

# Node group configuration for GPU workloads
variable "gpu_node_group_config" {
  description = "Configuration for GPU node group"
  type = object({
    instance_types = list(string)
    min_size      = number
    max_size      = number
    desired_size  = number
  })
  default = {
    instance_types = ["g4dn.xlarge"]
    min_size      = 0
    max_size      = 3
    desired_size  = 0
  }
}

# Fargate configuration
variable "enable_fargate" {
  description = "Enable Fargate for serverless workloads"
  type        = bool
  default     = true
}

variable "fargate_profiles" {
  description = "Fargate profiles configuration"
  type = map(object({
    namespace = string
    selectors = list(object({
      labels = map(string)
    }))
  }))
  default = {
    iaso_serverless = {
      namespace = "iaso"
      selectors = [{
        labels = {
          "workload-type" = "serverless"
        }
      }]
    }
  }
}

# S3 bucket for model storage
variable "s3_model_bucket" {
  description = "S3 bucket name for model storage"
  type        = string
  default     = ""
}

variable "create_s3_bucket" {
  description = "Whether to create S3 bucket for models"
  type        = bool
  default     = true
}

# IAM configuration
variable "create_service_accounts" {
  description = "Whether to create IAM roles for service accounts"
  type        = bool
  default     = true
}

variable "iam_role_prefix" {
  description = "Prefix for IAM role names"
  type        = string
  default     = "iaso"
}

# ALB configuration
variable "alb_certificate_arn" {
  description = "ACM certificate ARN for ALB HTTPS"
  type        = string
  default     = ""
}

variable "alb_ingress_class" {
  description = "Ingress class for AWS ALB"
  type        = string
  default     = "alb"
}

# CloudWatch configuration
variable "enable_cloudwatch_logging" {
  description = "Enable CloudWatch logging for pods"
  type        = bool
  default     = true
}

variable "cloudwatch_retention_days" {
  description = "CloudWatch logs retention in days"
  type        = number
  default     = 30
}

# EFS configuration for shared storage
variable "efs_file_system_id" {
  description = "EFS file system ID for shared storage"
  type        = string
  default     = ""
}

variable "create_efs" {
  description = "Whether to create EFS for shared storage"
  type        = bool
  default     = false
}