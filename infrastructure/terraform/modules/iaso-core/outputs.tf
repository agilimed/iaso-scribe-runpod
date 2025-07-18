# IASO Core Module Outputs

output "namespace" {
  description = "Kubernetes namespace"
  value       = var.namespace
}

output "database_config_name" {
  description = "Database ConfigMap name"
  value       = kubernetes_config_map.database_config.metadata[0].name
}

output "redis_config_name" {
  description = "Redis ConfigMap name"
  value       = kubernetes_config_map.redis_config.metadata[0].name
}

output "service_urls_config_name" {
  description = "Service URLs ConfigMap name"
  value       = kubernetes_config_map.service_urls.metadata[0].name
}

output "common_env_config_name" {
  description = "Common environment ConfigMap name"
  value       = kubernetes_config_map.common_env.metadata[0].name
}

output "database_secret_name" {
  description = "Database secret name"
  value       = kubernetes_secret.database_secret.metadata[0].name
}

output "redis_secret_name" {
  description = "Redis secret name"
  value       = kubernetes_secret.redis_secret.metadata[0].name
}