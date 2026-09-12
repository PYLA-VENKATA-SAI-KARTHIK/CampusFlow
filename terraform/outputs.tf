output "project_id" {
  description = "GCP Project ID."
  value       = var.project_id
}

output "region" {
  description = "GCP Region."
  value       = var.region
}

output "environment" {
  description = "Deployment Environment."
  value       = var.environment
}

output "artifact_registry_repository" {
  description = "Artifact Registry Docker repository URL."
  value       = module.artifact_registry.repository_url
}

output "vpc_network_name" {
  description = "VPC Network name."
  value       = module.networking.network_name
}

output "vpc_connector_name" {
  description = "Serverless VPC Access connector name."
  value       = module.networking.vpc_connector_name
}

output "cloud_sql_instance_name" {
  description = "Cloud SQL Instance name."
  value       = module.cloud_sql.instance_name
}

output "cloud_sql_private_ip" {
  description = "Cloud SQL Private IP Address."
  value       = module.cloud_sql.private_ip_address
}

output "storage_bucket_name" {
  description = "Resume GCS Storage Bucket name."
  value       = module.storage.bucket_name
}

output "cloud_tasks_queue_name" {
  description = "Cloud Tasks Notifications Queue name."
  value       = module.cloud_tasks.queue_name
}

output "api_service_name" {
  description = "Cloud Run API Service name."
  value       = module.cloud_run.api_service_name
}

output "api_service_url" {
  description = "Cloud Run API Service public URL."
  value       = module.cloud_run.api_url
}

output "worker_service_name" {
  description = "Cloud Run Worker Service name."
  value       = module.cloud_run.worker_service_name
}

output "worker_service_url" {
  description = "Cloud Run Worker Service internal URL."
  value       = module.cloud_run.worker_url
}

output "scheduler_deadline_job" {
  description = "Cloud Scheduler deadline reminder job name."
  value       = module.scheduler.deadline_job_name
}

output "scheduler_auto_close_job" {
  description = "Cloud Scheduler auto-close registrations job name."
  value       = module.scheduler.auto_close_job_name
}
