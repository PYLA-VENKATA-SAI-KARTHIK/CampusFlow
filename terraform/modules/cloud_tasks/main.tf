resource "google_cloud_tasks_queue" "notifications" {
  name     = var.queue_name != "" ? var.queue_name : "campusflow-notifications-${var.environment}"
  location = var.region

  rate_limits {
    max_dispatches_per_second = var.max_dispatches_per_second
    max_concurrent_dispatches = var.max_concurrent_dispatches
  }

  retry_config {
    max_attempts       = 5
    min_backoff        = "0.5s"
    max_backoff        = "60s"
    max_doublings      = 3
    max_retry_duration = "3600s"
  }
}
