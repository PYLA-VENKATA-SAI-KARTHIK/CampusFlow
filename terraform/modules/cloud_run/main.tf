# ==============================================================================
# 1. CampusFlow API Cloud Run Service (Public / Ingress-Facing)
# ==============================================================================
resource "google_cloud_run_v2_service" "api" {
  name     = "campusflow-api-${var.environment}"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = var.api_sa_email

    scaling {
      min_instance_count = var.api_min_instances
      max_instance_count = var.api_max_instances
    }

    vpc_access {
      connector = var.vpc_connector_name
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = var.container_image_api

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = "1000m"
          memory = "1024Mi"
        }
      }

      # Non-sensitive runtime application configuration
      env {
        name  = "APP_ENV"
        value = var.environment
      }
      env {
        name  = "APP_NAME"
        value = "CampusFlow"
      }
      env {
        name  = "STORAGE_PROVIDER"
        value = "gcs"
      }
      env {
        name  = "GCS_BUCKET_NAME"
        value = var.gcs_bucket_name
      }
      env {
        name  = "NOTIFICATION_TASK_PROVIDER"
        value = "cloud_tasks"
      }
      env {
        name  = "CLOUD_TASKS_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "CLOUD_TASKS_LOCATION"
        value = var.region
      }
      env {
        name  = "CLOUD_TASKS_QUEUE_NAME"
        value = var.cloud_tasks_queue_name
      }
      env {
        name  = "CLOUD_TASKS_SERVICE_ACCOUNT_EMAIL"
        value = var.tasks_sa_email
      }
      env {
        name  = "INTERNAL_SERVICE_URL"
        value = google_cloud_run_v2_service.worker.uri
      }
      env {
        name  = "PUSH_PROVIDER"
        value = "webpush"
      }
      env {
        name  = "CORS_ALLOWED_ORIGINS"
        value = var.cors_allowed_origins
      }
      env {
        name  = "FRONTEND_BASE_URL"
        value = var.frontend_base_url
      }
      env {
        name  = "RUN_MIGRATIONS"
        value = "true"
      }

      # Sensitive runtime secrets from Secret Manager
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = var.secret_ids["database-url"]
            version = "latest"
          }
        }
      }
      env {
        name = "JWT_PRIVATE_KEY_BASE64"
        value_source {
          secret_key_ref {
            secret  = var.secret_ids["jwt-private-key-base64"]
            version = "latest"
          }
        }
      }
      env {
        name = "JWT_PUBLIC_KEY_BASE64"
        value_source {
          secret_key_ref {
            secret  = var.secret_ids["jwt-public-key-base64"]
            version = "latest"
          }
        }
      }
      env {
        name = "VAPID_PRIVATE_KEY"
        value_source {
          secret_key_ref {
            secret  = var.secret_ids["vapid-private-key"]
            version = "latest"
          }
        }
      }
      env {
        name = "VAPID_PUBLIC_KEY"
        value_source {
          secret_key_ref {
            secret  = var.secret_ids["vapid-public-key"]
            version = "latest"
          }
        }
      }
      env {
        name = "SENDGRID_API_KEY"
        value_source {
          secret_key_ref {
            secret  = var.secret_ids["sendgrid-api-key"]
            version = "latest"
          }
        }
      }
      env {
        name = "INTERNAL_TASK_AUTH_SECRET"
        value_source {
          secret_key_ref {
            secret  = var.secret_ids["internal-task-auth-secret"]
            version = "latest"
          }
        }
      }

      startup_probe {
        http_get {
          path = "/api/v1/health"
          port = 8000
        }
        initial_delay_seconds = 10
        period_seconds        = 10
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = "/api/v1/health"
          port = 8000
        }
        period_seconds = 15
      }
    }
  }

  labels = {
    environment = var.environment
    service     = "api"
    managed_by  = "terraform"
  }
}

# API Public Ingress Permission (or via external Load Balancer)
resource "google_cloud_run_v2_service_iam_member" "api_public_invoker" {
  location = google_cloud_run_v2_service.api.location
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# API Scheduler Invocation Permission (for authenticated Cloud Scheduler jobs)
resource "google_cloud_run_v2_service_iam_member" "api_scheduler_invoker" {
  location = google_cloud_run_v2_service.api.location
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.scheduler_sa_email}"
}


# ==============================================================================
# 2. CampusFlow Worker Cloud Run Service (INTERNAL ONLY — Never Public)
# ==============================================================================
resource "google_cloud_run_v2_service" "worker" {
  name     = "campusflow-worker-${var.environment}"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"

  template {
    service_account = var.worker_sa_email

    scaling {
      min_instance_count = var.worker_min_instances
      max_instance_count = var.worker_max_instances
    }

    vpc_access {
      connector = var.vpc_connector_name
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = var.container_image_worker

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = "1000m"
          memory = "1024Mi"
        }
      }

      env {
        name  = "APP_ENV"
        value = var.environment
      }
      env {
        name  = "APP_NAME"
        value = "CampusFlow-Worker"
      }
      env {
        name  = "RUN_MIGRATIONS"
        value = "false" # Worker never runs Alembic migrations
      }
      env {
        name  = "PUSH_PROVIDER"
        value = "webpush"
      }

      # Secrets
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = var.secret_ids["database-url"]
            version = "latest"
          }
        }
      }
      env {
        name = "VAPID_PRIVATE_KEY"
        value_source {
          secret_key_ref {
            secret  = var.secret_ids["vapid-private-key"]
            version = "latest"
          }
        }
      }
      env {
        name = "VAPID_PUBLIC_KEY"
        value_source {
          secret_key_ref {
            secret  = var.secret_ids["vapid-public-key"]
            version = "latest"
          }
        }
      }
      env {
        name = "SENDGRID_API_KEY"
        value_source {
          secret_key_ref {
            secret  = var.secret_ids["sendgrid-api-key"]
            version = "latest"
          }
        }
      }
      env {
        name = "INTERNAL_TASK_AUTH_SECRET"
        value_source {
          secret_key_ref {
            secret  = var.secret_ids["internal-task-auth-secret"]
            version = "latest"
          }
        }
      }

      startup_probe {
        http_get {
          path = "/api/v1/health"
          port = 8000
        }
        initial_delay_seconds = 10
        period_seconds        = 10
      }
    }
  }

  labels = {
    environment = var.environment
    service     = "worker"
    managed_by  = "terraform"
  }
}

# Worker Invoker: Restricted STRICTLY to Cloud Tasks Service Account via OIDC
resource "google_cloud_run_v2_service_iam_member" "worker_tasks_invoker" {
  location = google_cloud_run_v2_service.worker.location
  name     = google_cloud_run_v2_service.worker.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.tasks_sa_email}"
}
