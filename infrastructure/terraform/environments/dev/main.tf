# IASO Development Environment Deployment

terraform {
  required_version = ">= 1.5"
  
  # Configure backend for state storage
  backend "s3" {
    # Configure these values according to your setup
    # bucket = "your-terraform-state-bucket"
    # key    = "iaso/dev/terraform.tfstate"
    # region = "us-east-1"
    # encrypt = true
    # dynamodb_table = "terraform-state-lock"
  }
}

# Local variables
locals {
  environment = "dev"
  
  # Merge tags
  tags = merge(var.tags, {
    Environment = local.environment
    ManagedBy   = "Terraform"
  })
}

# Import AWS provider configuration
module "aws_provider" {
  source = "../../providers/aws"
  
  aws_region              = var.aws_region
  eks_cluster_name        = var.eks_cluster_name
  rds_instance_identifier = var.rds_instance_identifier
  redis_cluster_id        = var.redis_cluster_id
  vpc_id                  = var.vpc_id
  private_subnet_ids      = var.private_subnet_ids
  
  tags = local.tags
}

# Core IASO configuration
module "iaso_core" {
  source = "../../modules/iaso-core"
  
  project_name     = var.project_name
  environment      = local.environment
  namespace        = var.kubernetes_namespace
  create_namespace = var.create_namespace
  
  database_config = {
    host     = module.aws_provider.rds_endpoint
    port     = module.aws_provider.rds_port
    name     = var.database_name
    username = var.database_username
    password = var.database_password
  }
  
  redis_config = {
    host     = "redis-service.nexuscare-prod.svc.cluster.local"  # Using existing Redis in cluster
    port     = 6379
    password = var.redis_password
  }
  
  # Development settings
  log_level    = "DEBUG"
  debug_mode   = true
  cors_origins = "*"
  
  tags = local.tags
}

# Clinical AI Services
module "iaso_clinical" {
  source = "../../modules/iaso-clinical"
  
  project_name = var.project_name
  namespace    = var.kubernetes_namespace
  
  # Reference core module outputs
  database_config_name      = module.iaso_core.database_config_name
  redis_config_name         = module.iaso_core.redis_config_name
  service_urls_config_name  = module.iaso_core.service_urls_config_name
  common_env_config_name    = module.iaso_core.common_env_config_name
  database_secret_name      = module.iaso_core.database_secret_name
  redis_secret_name         = module.iaso_core.redis_secret_name
  
  # Container registry
  image_registry = var.ecr_repository_url != "" ? var.ecr_repository_url : "ghcr.io/nexuscare"
  image_tag      = var.image_tag
  
  # Service configuration
  service_replicas = {
    clinical_ai = 1
    terminology = 1
    knowledge   = 1
    template    = 1
    api_gateway = 2
  }
  
  service_resources = {
    clinical_ai = {
      cpu_request    = "250m"
      memory_request = "512Mi"
      cpu_limit      = "1000m"
      memory_limit   = "2Gi"
    }
    terminology = {
      cpu_request    = "100m"
      memory_request = "256Mi"
      cpu_limit      = "500m"
      memory_limit   = "1Gi"
    }
    knowledge = {
      cpu_request    = "100m"
      memory_request = "256Mi"
      cpu_limit      = "500m"
      memory_limit   = "1Gi"
    }
    template = {
      cpu_request    = "100m"
      memory_request = "256Mi"
      cpu_limit      = "500m"
      memory_limit   = "1Gi"
    }
    api_gateway = {
      cpu_request    = "250m"
      memory_request = "512Mi"
      cpu_limit      = "1000m"
      memory_limit   = "2Gi"
    }
  }
  
  # Autoscaling disabled for dev
  enable_autoscaling = false
  
  common_labels = local.tags
}

# Infrastructure AI Services (if enabled)
module "iaso_infrastructure" {
  count  = var.enable_infrastructure_ai ? 1 : 0
  source = "../../modules/iaso-infrastructure"
  
  project_name = var.project_name
  namespace    = var.kubernetes_namespace
  
  # Reference core module outputs
  database_config_name      = module.iaso_core.database_config_name
  redis_config_name         = module.iaso_core.redis_config_name
  service_urls_config_name  = module.iaso_core.service_urls_config_name
  common_env_config_name    = module.iaso_core.common_env_config_name
  database_secret_name      = module.iaso_core.database_secret_name
  redis_secret_name         = module.iaso_core.redis_secret_name
  
  # Container registry
  image_registry = var.ecr_repository_url != "" ? var.ecr_repository_url : "ghcr.io/nexuscare"
  image_tag      = var.image_tag
  
  common_labels = local.tags
}

# Supporting services (MeiliSearch, Qdrant)
module "supporting_services" {
  source = "../../modules/supporting-services"
  
  project_name = var.project_name
  namespace    = var.kubernetes_namespace
  
  # Storage configuration
  storage_class = var.storage_class
  meilisearch_storage_size = "5Gi"  # Smaller for dev
  qdrant_storage_size      = "10Gi" # Smaller for dev
  
  # Credentials from core module
  redis_config_name  = module.iaso_core.redis_config_name
  redis_secret_name  = module.iaso_core.redis_secret_name
  
  common_labels = local.tags
}

# Ingress configuration
module "ingress" {
  count  = var.enable_ingress ? 1 : 0
  source = "../../modules/ingress"
  
  project_name   = var.project_name
  namespace      = var.kubernetes_namespace
  domain_name    = var.domain_name
  enable_tls     = false  # Disabled for dev
  
  # Service endpoints from other modules
  service_endpoints = {
    api_gateway = {
      service_name = module.iaso_clinical.service_names["api_gateway"]
      service_port = 8080
      path         = "/"
    }
    clinical_ai = {
      service_name = module.iaso_clinical.service_names["clinical_ai"]
      service_port = 8002
      path         = "/clinical"
    }
    terminology = {
      service_name = module.iaso_clinical.service_names["terminology"]
      service_port = 8001
      path         = "/terminology"
    }
  }
  
  # AWS ALB configuration
  ingress_class       = "alb"
  alb_certificate_arn = ""  # No certificate for dev
  
  common_labels = local.tags
}

# Outputs
output "namespace" {
  description = "Kubernetes namespace"
  value       = var.kubernetes_namespace
}

output "service_urls" {
  description = "Service URLs"
  value = {
    api_gateway = var.enable_ingress ? "http://${var.domain_name != "" ? var.domain_name : module.ingress[0].load_balancer_dns}" : "kubectl port-forward required"
    clinical_ai = "http://${module.iaso_clinical.service_names["clinical_ai"]}:8002"
    terminology = "http://${module.iaso_clinical.service_names["terminology"]}:8001"
    knowledge   = "http://${module.iaso_clinical.service_names["knowledge"]}:8004"
  }
}

output "database_endpoint" {
  description = "RDS database endpoint"
  value       = module.aws_provider.rds_endpoint
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.aws_provider.redis_endpoint
}