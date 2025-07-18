# Variables for Supporting Services Module

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
}

variable "common_labels" {
  description = "Common labels for resources"
  type        = map(string)
  default     = {}
}

# Storage configuration
variable "storage_class" {
  description = "Storage class for persistent volumes"
  type        = string
  default     = "gp2"
}

variable "meilisearch_storage_size" {
  description = "Storage size for MeiliSearch"
  type        = string
  default     = "10Gi"
}

variable "qdrant_storage_size" {
  description = "Storage size for Qdrant"
  type        = string
  default     = "50Gi"
}

# MeiliSearch configuration
variable "meilisearch_master_key" {
  description = "MeiliSearch master key"
  type        = string
  sensitive   = true
  default     = "kDbL0cAlD3vP@ssw0rd!"  # Change in production
}

# Redis configuration references
variable "redis_config_name" {
  description = "Redis ConfigMap name"
  type        = string
}

variable "redis_secret_name" {
  description = "Redis secret name"
  type        = string
}