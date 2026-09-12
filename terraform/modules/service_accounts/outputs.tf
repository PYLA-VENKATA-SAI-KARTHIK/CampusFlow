output "api_sa_email" {
  description = "Email of the CampusFlow API runtime service account."
  value       = google_service_account.api_sa.email
}

output "api_sa_name" {
  description = "Fully qualified name of the API service account."
  value       = google_service_account.api_sa.name
}

output "worker_sa_email" {
  description = "Email of the CampusFlow Worker runtime service account."
  value       = google_service_account.worker_sa.email
}

output "worker_sa_name" {
  description = "Fully qualified name of the Worker service account."
  value       = google_service_account.worker_sa.name
}

output "tasks_sa_email" {
  description = "Email of the Cloud Tasks invoker service account."
  value       = google_service_account.tasks_sa.email
}

output "scheduler_sa_email" {
  description = "Email of the Cloud Scheduler invoker service account."
  value       = google_service_account.scheduler_sa.email
}
