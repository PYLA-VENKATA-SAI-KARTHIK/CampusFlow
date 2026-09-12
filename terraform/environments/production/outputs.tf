output "project_id" {
  description = "GCP Project ID."
  value       = module.production_infrastructure.project_id
}

output "region" {
  description = "GCP Region."
  value       = module.production_infrastructure.region
}

output "artifact_registry_repository" {
  description = "Artifact Registry Docker repository URL."
  value       = module.production_infrastructure.artifact_registry_repository
}

output "cloud_sql_instance_name" {
  description = "Cloud SQL Instance name."
  value       = module.production_infrastructure.cloud_sql_instance_name
}

output "cloud_sql_private_ip" {
  description = "Cloud SQL Private IP Address."
  value       = module.production_infrastructure.cloud_sql_private_ip
}

output "storage_bucket_name" {
  description = "Resume GCS Storage Bucket name."
  value       = module.production_infrastructure.storage_bucket_name
}

output "cloud_tasks_queue_name" {
  description = "Cloud Tasks Notifications Queue name."
  value       = module.production_infrastructure.cloud_tasks_queue_name
}

output "api_service_url" {
  description = "Cloud Run API Service public URL."
  value       = module.production_infrastructure.api_service_url
}

output "worker_service_url" {
  description = "Cloud Run Worker Service internal URL."
  value       = module.production_infrastructure.worker_service_url
}
