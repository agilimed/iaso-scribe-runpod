# AWS Provider Outputs

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = data.aws_eks_cluster.existing.endpoint
}

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = data.aws_eks_cluster.existing.name
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = data.aws_db_instance.existing_rds.address
}

output "rds_port" {
  description = "RDS instance port"
  value       = data.aws_db_instance.existing_rds.port
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = var.redis_cluster_id != "" ? data.aws_elasticache_cluster.existing_redis[0].cache_nodes[0].address : "redis-service.nexuscare-prod.svc.cluster.local"
}

output "redis_port" {
  description = "Redis port"
  value       = var.redis_cluster_id != "" ? data.aws_elasticache_cluster.existing_redis[0].cache_nodes[0].port : 6379
}

output "vpc_id" {
  description = "VPC ID"
  value       = data.aws_eks_cluster.existing.resource_vpc_config[0].vpc_id
}

output "cluster_security_group_id" {
  description = "EKS cluster security group ID"
  value       = data.aws_eks_cluster.existing.resource_vpc_config[0].cluster_security_group_id
}