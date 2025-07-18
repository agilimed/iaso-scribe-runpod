# Core IASO Module - Cloud Agnostic

locals {
  app_name = var.project_name
  
  # Common labels for all resources
  common_labels = merge(var.tags, {
    app         = local.app_name
    environment = var.environment
    managed-by  = "terraform"
  })
  
  # Service ports
  service_ports = {
    clinical_ai  = 8002
    terminology  = 8001
    knowledge    = 8004
    template     = 8003
    slm          = 8007
    iasoql       = 8008
    api_gateway  = 8080
    embeddings   = 8050
    embeddings_grpc = 50051
  }
}

# Kubernetes namespace
resource "kubernetes_namespace" "iaso" {
  count = var.create_namespace ? 1 : 0
  
  metadata {
    name = var.namespace
    labels = local.common_labels
  }
}

# ConfigMap for database configuration
resource "kubernetes_config_map" "database_config" {
  metadata {
    name      = "${local.app_name}-db-config"
    namespace = var.namespace
    labels    = local.common_labels
  }
  
  data = {
    POSTGRES_HOST = var.database_config.host
    POSTGRES_PORT = tostring(var.database_config.port)
    POSTGRES_DB   = var.database_config.name
    PG_HOST_SRC   = var.database_config.host
    PG_PORT       = tostring(var.database_config.port)
  }
}

# ConfigMap for Redis configuration
resource "kubernetes_config_map" "redis_config" {
  metadata {
    name      = "${local.app_name}-redis-config"
    namespace = var.namespace
    labels    = local.common_labels
  }
  
  data = {
    REDIS_HOST    = var.redis_config.host
    REDIS_PORT    = tostring(var.redis_config.port)
    KEYDB_HOST    = var.redis_config.host
    KEYDB_PORT    = tostring(var.redis_config.port)
  }
}

# Secret for database credentials
resource "kubernetes_secret" "database_secret" {
  metadata {
    name      = "${local.app_name}-db-secret"
    namespace = var.namespace
    labels    = local.common_labels
  }
  
  data = {
    POSTGRES_USER     = base64encode(var.database_config.username)
    POSTGRES_PASSWORD = base64encode(var.database_config.password)
  }
  
  type = "Opaque"
}

# Secret for Redis credentials
resource "kubernetes_secret" "redis_secret" {
  metadata {
    name      = "${local.app_name}-redis-secret"
    namespace = var.namespace
    labels    = local.common_labels
  }
  
  data = {
    REDIS_PASSWORD = base64encode(var.redis_config.password)
    KEYDB_PASSWORD = base64encode(var.redis_config.password)
  }
  
  type = "Opaque"
}

# ConfigMap for service URLs
resource "kubernetes_config_map" "service_urls" {
  metadata {
    name      = "${local.app_name}-service-urls"
    namespace = var.namespace
    labels    = local.common_labels
  }
  
  data = {
    TERMINOLOGY_SERVICE_URL = "http://${local.app_name}-terminology:${local.service_ports.terminology}"
    KNOWLEDGE_SERVICE_URL   = "http://${local.app_name}-knowledge:${local.service_ports.knowledge}/api/v1"
    TEMPLATE_SERVICE_URL    = "http://${local.app_name}-template:${local.service_ports.template}"
    CLINICAL_AI_SERVICE_URL = "http://${local.app_name}-clinical:${local.service_ports.clinical_ai}"
    LLM_SERVICE_URL        = "http://${local.app_name}-slm:${local.service_ports.slm}"
    API_GATEWAY_URL        = "http://${local.app_name}-api-gateway:${local.service_ports.api_gateway}"
    EMBEDDINGS_SERVICE_URL = "http://${local.app_name}-embeddings:${local.service_ports.embeddings}"
  }
}

# ConfigMap for common environment variables
resource "kubernetes_config_map" "common_env" {
  metadata {
    name      = "${local.app_name}-common-env"
    namespace = var.namespace
    labels    = local.common_labels
  }
  
  data = {
    LOG_LEVEL              = var.log_level
    DEBUG_MODE             = tostring(var.debug_mode)
    CORS_ORIGINS          = var.cors_origins
    ENVIRONMENT           = var.environment
    
    # Feature flags
    ENABLE_CLINICAL_BERT  = tostring(var.enable_clinical_bert)
    ENABLE_ENTITY_CACHE   = tostring(var.enable_entity_cache)
    ENABLE_RATE_LIMITING  = tostring(var.enable_rate_limiting)
    
    # Performance settings
    MAX_TEXT_LENGTH              = tostring(var.max_text_length)
    ENTITY_CONFIDENCE_THRESHOLD  = tostring(var.entity_confidence_threshold)
    ASYNC_TIMEOUT_SECONDS       = tostring(var.async_timeout_seconds)
  }
}