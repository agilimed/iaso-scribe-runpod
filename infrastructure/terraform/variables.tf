# Cloud-agnostic variables for IASO deployment

variable "cloud_provider" {
  description = "Cloud provider to deploy to"
  type        = string
  validation {
    condition     = contains(["aws", "gcp", "azure", "local"], var.cloud_provider)
    error_message = "Cloud provider must be one of: aws, gcp, azure, local"
  }
}

variable "environment" {
  description = "Environment name"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod"
  }
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "iaso"
}

variable "region" {
  description = "Cloud region"
  type        = string
}

# Kubernetes Configuration
variable "kubernetes_namespace" {
  description = "Kubernetes namespace for IASO services"
  type        = string
  default     = "iaso"
}

variable "create_namespace" {
  description = "Whether to create the Kubernetes namespace"
  type        = bool
  default     = true
}

# Database Configuration (Existing Resources)
variable "database_config" {
  description = "Database configuration for existing PostgreSQL"
  type = object({
    host     = string
    port     = number
    name     = string
    username = string
    password = string  # Should be provided via environment variable
  })
  sensitive = true
}

# Redis Configuration (Existing Resources)
variable "redis_config" {
  description = "Redis configuration for existing instance"
  type = object({
    host     = string
    port     = number
    password = string  # Should be provided via environment variable
  })
  sensitive = true
}

# Service Configurations
variable "enable_clinical_ai" {
  description = "Enable Clinical AI services"
  type        = bool
  default     = true
}

variable "enable_infrastructure_ai" {
  description = "Enable Infrastructure AI services"
  type        = bool
  default     = true
}

variable "enable_monitoring" {
  description = "Enable monitoring stack (Prometheus, Grafana)"
  type        = bool
  default     = true
}

# Resource Configurations
variable "service_resources" {
  description = "Resource requirements for services"
  type = map(object({
    cpu_request    = string
    memory_request = string
    cpu_limit      = string
    memory_limit   = string
    replicas       = number
  }))
  default = {
    clinical_ai = {
      cpu_request    = "500m"
      memory_request = "1Gi"
      cpu_limit      = "2000m"
      memory_limit   = "4Gi"
      replicas       = 2
    }
    terminology = {
      cpu_request    = "250m"
      memory_request = "512Mi"
      cpu_limit      = "1000m"
      memory_limit   = "2Gi"
      replicas       = 2
    }
    knowledge = {
      cpu_request    = "250m"
      memory_request = "512Mi"
      cpu_limit      = "1000m"
      memory_limit   = "2Gi"
      replicas       = 2
    }
    api_gateway = {
      cpu_request    = "500m"
      memory_request = "1Gi"
      cpu_limit      = "2000m"
      memory_limit   = "4Gi"
      replicas       = 3
    }
    embeddings = {
      cpu_request    = "1000m"
      memory_request = "2Gi"
      cpu_limit      = "4000m"
      memory_limit   = "8Gi"
      replicas       = 2
    }
  }
}

# Storage Configuration
variable "storage_class" {
  description = "Kubernetes storage class to use"
  type        = string
  default     = "gp3"
}

variable "persistent_volume_sizes" {
  description = "Sizes for persistent volumes"
  type = map(string)
  default = {
    meilisearch = "10Gi"
    qdrant      = "50Gi"
    models      = "100Gi"
  }
}

# Network Configuration
variable "enable_ingress" {
  description = "Enable ingress controller"
  type        = bool
  default     = true
}

variable "ingress_class" {
  description = "Ingress class to use"
  type        = string
  default     = "nginx"
}

variable "domain_name" {
  description = "Domain name for services (optional)"
  type        = string
  default     = ""
}

variable "enable_tls" {
  description = "Enable TLS for ingress"
  type        = bool
  default     = true
}

# Autoscaling Configuration
variable "enable_autoscaling" {
  description = "Enable horizontal pod autoscaling"
  type        = bool
  default     = true
}

variable "autoscaling_config" {
  description = "Autoscaling configuration"
  type = object({
    min_replicas         = number
    max_replicas         = number
    target_cpu_percent   = number
    target_memory_percent = number
  })
  default = {
    min_replicas         = 1
    max_replicas         = 10
    target_cpu_percent   = 70
    target_memory_percent = 80
  }
}

# Tags
variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    ManagedBy = "Terraform"
    Project   = "IASO"
  }
}

# Feature Flags
variable "enable_gpu_nodes" {
  description = "Enable GPU nodes for ML workloads"
  type        = bool
  default     = false
}

variable "enable_spot_instances" {
  description = "Enable spot instances for cost optimization"
  type        = bool
  default     = false
}

variable "enable_service_mesh" {
  description = "Enable service mesh (Istio)"
  type        = bool
  default     = false
}