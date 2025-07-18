# IASO Clinical AI Services Module

locals {
  app_name = var.project_name
  
  # Service specific configurations
  services = {
    clinical_ai = {
      name     = "clinical"
      port     = 8002
      replicas = var.service_replicas.clinical_ai
      resources = var.service_resources.clinical_ai
    }
    terminology = {
      name     = "terminology"
      port     = 8001
      replicas = var.service_replicas.terminology
      resources = var.service_resources.terminology
    }
    knowledge = {
      name     = "knowledge"
      port     = 8004
      replicas = var.service_replicas.knowledge
      resources = var.service_resources.knowledge
    }
    template = {
      name     = "template"
      port     = 8003
      replicas = var.service_replicas.template
      resources = var.service_resources.template
    }
    api_gateway = {
      name     = "api-gateway"
      port     = 8080
      replicas = var.service_replicas.api_gateway
      resources = var.service_resources.api_gateway
    }
  }
}

# Deploy each clinical service
resource "kubernetes_deployment" "clinical_services" {
  for_each = local.services
  
  metadata {
    name      = "${local.app_name}-${each.value.name}"
    namespace = var.namespace
    labels = merge(var.common_labels, {
      component = each.value.name
      tier      = "clinical"
    })
  }
  
  spec {
    replicas = each.value.replicas
    
    selector {
      match_labels = {
        app       = local.app_name
        component = each.value.name
      }
    }
    
    template {
      metadata {
        labels = merge(var.common_labels, {
          app       = local.app_name
          component = each.value.name
          tier      = "clinical"
        })
      }
      
      spec {
        service_account_name = var.service_account_name
        
        # Anti-affinity for high availability
        affinity {
          pod_anti_affinity {
            preferred_during_scheduling_ignored_during_execution {
              weight = 100
              pod_affinity_term {
                label_selector {
                  match_expressions {
                    key      = "component"
                    operator = "In"
                    values   = [each.value.name]
                  }
                }
                topology_key = "kubernetes.io/hostname"
              }
            }
          }
        }
        
        container {
          name  = each.value.name
          image = "${var.image_registry}/${local.app_name}-${each.value.name}:${var.image_tag}"
          
          port {
            container_port = each.value.port
            protocol       = "TCP"
          }
          
          # Environment from ConfigMaps
          env_from {
            config_map_ref {
              name = var.database_config_name
            }
          }
          
          env_from {
            config_map_ref {
              name = var.redis_config_name
            }
          }
          
          env_from {
            config_map_ref {
              name = var.service_urls_config_name
            }
          }
          
          env_from {
            config_map_ref {
              name = var.common_env_config_name
            }
          }
          
          # Secrets
          env_from {
            secret_ref {
              name = var.database_secret_name
            }
          }
          
          env_from {
            secret_ref {
              name = var.redis_secret_name
            }
          }
          
          # Service-specific environment variables
          env {
            name  = "SERVICE_NAME"
            value = each.value.name
          }
          
          env {
            name  = "SERVICE_PORT"
            value = tostring(each.value.port)
          }
          
          # Health checks
          liveness_probe {
            http_get {
              path = "/health"
              port = each.value.port
            }
            initial_delay_seconds = 30
            period_seconds        = 10
            timeout_seconds       = 5
            failure_threshold     = 3
          }
          
          readiness_probe {
            http_get {
              path = "/ready"
              port = each.value.port
            }
            initial_delay_seconds = 10
            period_seconds        = 5
            timeout_seconds       = 3
            failure_threshold     = 3
          }
          
          # Resources
          resources {
            requests = {
              cpu    = each.value.resources.cpu_request
              memory = each.value.resources.memory_request
            }
            limits = {
              cpu    = each.value.resources.cpu_limit
              memory = each.value.resources.memory_limit
            }
          }
          
          # Security context
          security_context {
            allow_privilege_escalation = false
            read_only_root_filesystem  = true
            run_as_non_root           = true
            run_as_user               = 1000
          }
        }
      }
    }
  }
}

# Services
resource "kubernetes_service" "clinical_services" {
  for_each = local.services
  
  metadata {
    name      = "${local.app_name}-${each.value.name}"
    namespace = var.namespace
    labels = merge(var.common_labels, {
      component = each.value.name
      tier      = "clinical"
    })
  }
  
  spec {
    selector = {
      app       = local.app_name
      component = each.value.name
    }
    
    port {
      port        = each.value.port
      target_port = each.value.port
      protocol    = "TCP"
    }
    
    type = "ClusterIP"
  }
}

# HPA for autoscaling
resource "kubernetes_horizontal_pod_autoscaler_v2" "clinical_services" {
  for_each = var.enable_autoscaling ? local.services : {}
  
  metadata {
    name      = "${local.app_name}-${each.value.name}-hpa"
    namespace = var.namespace
  }
  
  spec {
    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = "${local.app_name}-${each.value.name}"
    }
    
    min_replicas = var.autoscaling_config.min_replicas
    max_replicas = var.autoscaling_config.max_replicas
    
    metric {
      type = "Resource"
      resource {
        name = "cpu"
        target {
          type                = "Utilization"
          average_utilization = var.autoscaling_config.target_cpu_percent
        }
      }
    }
    
    metric {
      type = "Resource"
      resource {
        name = "memory"
        target {
          type                = "Utilization"
          average_utilization = var.autoscaling_config.target_memory_percent
        }
      }
    }
    
    behavior {
      scale_up {
        stabilization_window_seconds = 60
        select_policy               = "Max"
        policy {
          type          = "Percent"
          value         = 100
          period_seconds = 15
        }
      }
      
      scale_down {
        stabilization_window_seconds = 300
        select_policy               = "Min"
        policy {
          type          = "Percent"
          value         = 10
          period_seconds = 60
        }
      }
    }
  }
}