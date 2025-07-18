# Variables for IASO Core Module

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
}

variable "create_namespace" {
  description = "Whether to create namespace"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

# Database configuration
variable "database_config" {
  description = "Database configuration"
  type = object({
    host     = string
    port     = number
    name     = string
    username = string
    password = string
  })
  sensitive = true
}

# Redis configuration
variable "redis_config" {
  description = "Redis configuration"
  type = object({
    host     = string
    port     = number
    password = string
  })
  sensitive = true
}

# Logging configuration
variable "log_level" {
  description = "Log level for services"
  type        = string
  default     = "INFO"
}

variable "debug_mode" {
  description = "Enable debug mode"
  type        = bool
  default     = false
}

# CORS configuration
variable "cors_origins" {
  description = "CORS allowed origins"
  type        = string
  default     = "*"
}

# Feature flags
variable "enable_clinical_bert" {
  description = "Enable ClinicalBERT"
  type        = bool
  default     = true
}

variable "enable_entity_cache" {
  description = "Enable entity caching"
  type        = bool
  default     = true
}

variable "enable_rate_limiting" {
  description = "Enable rate limiting"
  type        = bool
  default     = false
}

# Performance settings
variable "max_text_length" {
  description = "Maximum text length to process"
  type        = number
  default     = 100000
}

variable "entity_confidence_threshold" {
  description = "Entity confidence threshold"
  type        = number
  default     = 0.5
}

variable "async_timeout_seconds" {
  description = "Async operation timeout in seconds"
  type        = number
  default     = 120
}