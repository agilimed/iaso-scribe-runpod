# Variables for IASO Clinical Module

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

# ConfigMap and Secret references
variable "database_config_name" {
  description = "Database ConfigMap name"
  type        = string
}

variable "redis_config_name" {
  description = "Redis ConfigMap name"
  type        = string
}

variable "service_urls_config_name" {
  description = "Service URLs ConfigMap name"
  type        = string
}

variable "common_env_config_name" {
  description = "Common environment ConfigMap name"
  type        = string
}

variable "database_secret_name" {
  description = "Database secret name"
  type        = string
}

variable "redis_secret_name" {
  description = "Redis secret name"
  type        = string
}

# Container configuration
variable "image_registry" {
  description = "Container image registry"
  type        = string
}

variable "image_tag" {
  description = "Container image tag"
  type        = string
  default     = "latest"
}

# Service configuration
variable "service_replicas" {
  description = "Number of replicas for each service"
  type = map(number)
  default = {
    clinical_ai = 2
    terminology = 2
    knowledge   = 2
    template    = 2
    api_gateway = 3
  }
}

variable "service_resources" {
  description = "Resource requirements for services"
  type = map(object({
    cpu_request    = string
    memory_request = string
    cpu_limit      = string
    memory_limit   = string
  }))
}

# Autoscaling
variable "enable_autoscaling" {
  description = "Enable horizontal pod autoscaling"
  type        = bool
  default     = true
}

variable "autoscaling_config" {
  description = "Autoscaling configuration"
  type = object({
    min_replicas          = number
    max_replicas          = number
    target_cpu_percent    = number
    target_memory_percent = number
  })
  default = {
    min_replicas          = 1
    max_replicas          = 10
    target_cpu_percent    = 70
    target_memory_percent = 80
  }
}

# Service account
variable "service_account_name" {
  description = "Kubernetes service account name"
  type        = string
  default     = "iaso-clinical"
}

# Node selector
variable "node_selector" {
  description = "Node selector for pod placement"
  type        = map(string)
  default     = {}
}

# Tolerations
variable "tolerations" {
  description = "Pod tolerations"
  type = list(object({
    key      = string
    operator = string
    value    = string
    effect   = string
  }))
  default = []
}