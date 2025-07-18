# IASO Clinical Module Outputs

output "service_names" {
  description = "Service names for all clinical services"
  value = {
    for k, v in local.services : k => kubernetes_service.clinical_services[k].metadata[0].name
  }
}

output "service_endpoints" {
  description = "Internal service endpoints"
  value = {
    for k, v in local.services : k => "${kubernetes_service.clinical_services[k].metadata[0].name}.${var.namespace}.svc.cluster.local:${v.port}"
  }
}

output "deployment_names" {
  description = "Deployment names for all clinical services"
  value = {
    for k, v in local.services : k => kubernetes_deployment.clinical_services[k].metadata[0].name
  }
}