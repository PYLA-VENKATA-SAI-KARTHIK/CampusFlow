output "api_service_id" {
  description = "The ID of the API Cloud Run service."
  value       = google_cloud_run_v2_service.api.id
}

output "api_service_name" {
  description = "The name of the API Cloud Run service."
  value       = google_cloud_run_v2_service.api.name
}

output "api_url" {
  description = "The public URL of the API Cloud Run service."
  value       = google_cloud_run_v2_service.api.uri
}

output "worker_service_id" {
  description = "The ID of the Worker Cloud Run service."
  value       = google_cloud_run_v2_service.worker.id
}

output "worker_service_name" {
  description = "The name of the Worker Cloud Run service."
  value       = google_cloud_run_v2_service.worker.name
}

output "worker_url" {
  description = "The internal URL of the Worker Cloud Run service."
  value       = google_cloud_run_v2_service.worker.uri
}
