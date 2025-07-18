# Supporting Services Module - MeiliSearch and Qdrant

locals {
  app_name = var.project_name
}

# MeiliSearch Deployment
resource "kubernetes_deployment" "meilisearch" {
  metadata {
    name      = "${local.app_name}-meilisearch"
    namespace = var.namespace
    labels    = merge(var.common_labels, {
      component = "meilisearch"
      tier      = "storage"
    })
  }
  
  spec {
    replicas = 1
    
    selector {
      match_labels = {
        app       = local.app_name
        component = "meilisearch"
      }
    }
    
    template {
      metadata {
        labels = merge(var.common_labels, {
          app       = local.app_name
          component = "meilisearch"
          tier      = "storage"
        })
      }
      
      spec {
        container {
          name  = "meilisearch"
          image = "getmeili/meilisearch:v1.5"
          
          port {
            container_port = 7700
            protocol       = "TCP"
          }
          
          env {
            name  = "MEILI_MASTER_KEY"
            value = var.meilisearch_master_key
          }
          
          env {
            name  = "MEILI_NO_ANALYTICS"
            value = "true"
          }
          
          env {
            name  = "MEILI_ENV"
            value = "production"
          }
          
          volume_mount {
            name       = "meilisearch-data"
            mount_path = "/meili_data"
          }
          
          resources {
            requests = {
              cpu    = "250m"
              memory = "512Mi"
            }
            limits = {
              cpu    = "1000m"
              memory = "2Gi"
            }
          }
          
          liveness_probe {
            http_get {
              path = "/health"
              port = 7700
            }
            initial_delay_seconds = 30
            period_seconds        = 10
          }
          
          readiness_probe {
            http_get {
              path = "/health"
              port = 7700
            }
            initial_delay_seconds = 10
            period_seconds        = 5
          }
        }
        
        volume {
          name = "meilisearch-data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.meilisearch_pvc.metadata[0].name
          }
        }
      }
    }
  }
}

# MeiliSearch Service
resource "kubernetes_service" "meilisearch" {
  metadata {
    name      = "${local.app_name}-meilisearch"
    namespace = var.namespace
    labels    = merge(var.common_labels, {
      component = "meilisearch"
    })
  }
  
  spec {
    selector = {
      app       = local.app_name
      component = "meilisearch"
    }
    
    port {
      port        = 7700
      target_port = 7700
      protocol    = "TCP"
    }
    
    type = "ClusterIP"
  }
}

# MeiliSearch PVC
resource "kubernetes_persistent_volume_claim" "meilisearch_pvc" {
  metadata {
    name      = "${local.app_name}-meilisearch-pvc"
    namespace = var.namespace
    labels    = var.common_labels
  }
  
  spec {
    access_modes = ["ReadWriteOnce"]
    
    resources {
      requests = {
        storage = var.meilisearch_storage_size
      }
    }
    
    storage_class_name = var.storage_class
  }
}

# Qdrant Deployment
resource "kubernetes_deployment" "qdrant" {
  metadata {
    name      = "${local.app_name}-qdrant"
    namespace = var.namespace
    labels    = merge(var.common_labels, {
      component = "qdrant"
      tier      = "storage"
    })
  }
  
  spec {
    replicas = 1
    
    selector {
      match_labels = {
        app       = local.app_name
        component = "qdrant"
      }
    }
    
    template {
      metadata {
        labels = merge(var.common_labels, {
          app       = local.app_name
          component = "qdrant"
          tier      = "storage"
        })
      }
      
      spec {
        container {
          name  = "qdrant"
          image = "qdrant/qdrant:v1.7.4"
          
          port {
            name           = "http"
            container_port = 6333
            protocol       = "TCP"
          }
          
          port {
            name           = "grpc"
            container_port = 6334
            protocol       = "TCP"
          }
          
          env {
            name  = "QDRANT__SERVICE__HTTP_PORT"
            value = "6333"
          }
          
          env {
            name  = "QDRANT__SERVICE__GRPC_PORT"
            value = "6334"
          }
          
          env {
            name  = "QDRANT__LOG_LEVEL"
            value = "INFO"
          }
          
          volume_mount {
            name       = "qdrant-data"
            mount_path = "/qdrant/storage"
          }
          
          resources {
            requests = {
              cpu    = "500m"
              memory = "1Gi"
            }
            limits = {
              cpu    = "2000m"
              memory = "4Gi"
            }
          }
          
          liveness_probe {
            http_get {
              path = "/health"
              port = 6333
            }
            initial_delay_seconds = 30
            period_seconds        = 10
          }
          
          readiness_probe {
            http_get {
              path = "/health"
              port = 6333
            }
            initial_delay_seconds = 10
            period_seconds        = 5
          }
        }
        
        volume {
          name = "qdrant-data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.qdrant_pvc.metadata[0].name
          }
        }
      }
    }
  }
}

# Qdrant Service
resource "kubernetes_service" "qdrant" {
  metadata {
    name      = "${local.app_name}-qdrant"
    namespace = var.namespace
    labels    = merge(var.common_labels, {
      component = "qdrant"
    })
  }
  
  spec {
    selector = {
      app       = local.app_name
      component = "qdrant"
    }
    
    port {
      name        = "http"
      port        = 6333
      target_port = 6333
      protocol    = "TCP"
    }
    
    port {
      name        = "grpc"
      port        = 6334
      target_port = 6334
      protocol    = "TCP"
    }
    
    type = "ClusterIP"
  }
}

# Qdrant PVC
resource "kubernetes_persistent_volume_claim" "qdrant_pvc" {
  metadata {
    name      = "${local.app_name}-qdrant-pvc"
    namespace = var.namespace
    labels    = var.common_labels
  }
  
  spec {
    access_modes = ["ReadWriteOnce"]
    
    resources {
      requests = {
        storage = var.qdrant_storage_size
      }
    }
    
    storage_class_name = var.storage_class
  }
}