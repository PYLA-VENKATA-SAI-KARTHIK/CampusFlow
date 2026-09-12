output "deadline_job_name" {
  description = "Name of the deadline reminders scheduler job."
  value       = google_cloud_scheduler_job.deadline_reminders.name
}

output "auto_close_job_name" {
  description = "Name of the auto-close registrations scheduler job."
  value       = google_cloud_scheduler_job.auto_close_registrations.name
}
