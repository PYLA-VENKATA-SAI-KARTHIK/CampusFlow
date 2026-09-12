output "queue_id" {
  description = "The fully qualified ID of the Cloud Tasks queue."
  value       = google_cloud_tasks_queue.notifications.id
}

output "queue_name" {
  description = "The name of the Cloud Tasks queue."
  value       = google_cloud_tasks_queue.notifications.name
}

output "queue_location" {
  description = "The location of the Cloud Tasks queue."
  value       = google_cloud_tasks_queue.notifications.location
}
