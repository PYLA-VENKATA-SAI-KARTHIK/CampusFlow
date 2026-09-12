# 1. Deadline Reminders Notification Dispatcher (every 30 mins)
resource "google_cloud_scheduler_job" "deadline_reminders" {
  name             = "campusflow-deadline-reminders-${var.environment}"
  description      = "Periodically checks upcoming placement drive deadlines and dispatches reminder tasks (${var.environment})"
  schedule         = "*/30 * * * *"
  time_zone        = var.timezone
  attempt_deadline = "300s"
  region           = var.region

  http_target {
    http_method = "POST"
    uri         = "${rtrim(var.api_url, "/")}/internal/scheduler/check-deadlines"
    headers = {
      "Content-Type" = "application/json"
    }

    oidc_token {
      service_account_email = var.scheduler_sa_email
      audience              = var.api_url
    }
  }

  retry_config {
    retry_count          = 3
    min_backoff_duration = "5s"
    max_backoff_duration = "60s"
  }
}

# 2. Auto-Close Registrations Job (every 30 mins, offset)
resource "google_cloud_scheduler_job" "auto_close_registrations" {
  name             = "campusflow-auto-close-drives-${var.environment}"
  description      = "Transitions expired open drives to REGISTRATION_CLOSED status (${var.environment})"
  schedule         = "5,35 * * * *"
  time_zone        = var.timezone
  attempt_deadline = "300s"
  region           = var.region

  http_target {
    http_method = "POST"
    uri         = "${rtrim(var.api_url, "/")}/internal/scheduler/auto-close-registrations"
    headers = {
      "Content-Type" = "application/json"
    }

    oidc_token {
      service_account_email = var.scheduler_sa_email
      audience              = var.api_url
    }
  }

  retry_config {
    retry_count          = 3
    min_backoff_duration = "5s"
    max_backoff_duration = "60s"
  }
}
