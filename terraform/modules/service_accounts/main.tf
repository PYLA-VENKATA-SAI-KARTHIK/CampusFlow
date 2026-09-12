# 1. API Service Account
resource "google_service_account" "api_sa" {
  account_id   = "cf-api-sa-${var.environment}"
  display_name = "CampusFlow API Service Account (${var.environment})"
  description  = "Runtime service account for CampusFlow API Cloud Run service"
}

# API SA: Cloud SQL Client
resource "google_project_iam_member" "api_cloudsql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.api_sa.email}"
}

# API SA: Cloud Tasks Enqueuer
resource "google_project_iam_member" "api_cloudtasks" {
  project = var.project_id
  role    = "roles/cloudtasks.enqueuer"
  member  = "serviceAccount:${google_service_account.api_sa.email}"
}


# 2. Worker Service Account
resource "google_service_account" "worker_sa" {
  account_id   = "cf-worker-sa-${var.environment}"
  display_name = "CampusFlow Worker Service Account (${var.environment})"
  description  = "Runtime service account for CampusFlow Worker Cloud Run service"
}

# Worker SA: Cloud SQL Client
resource "google_project_iam_member" "worker_cloudsql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.worker_sa.email}"
}


# 3. Cloud Tasks Invocation Service Account (OIDC caller for Worker)
resource "google_service_account" "tasks_sa" {
  account_id   = "cf-tasks-sa-${var.environment}"
  display_name = "CampusFlow Cloud Tasks Invoker SA (${var.environment})"
  description  = "Service account used by Cloud Tasks to invoke the internal Worker Cloud Run service"
}


# 4. Cloud Scheduler Invocation Service Account (OIDC caller for API)
resource "google_service_account" "scheduler_sa" {
  account_id   = "cf-sched-sa-${var.environment}"
  display_name = "CampusFlow Cloud Scheduler Invoker SA (${var.environment})"
  description  = "Service account used by Cloud Scheduler to invoke internal API deadline/scheduler endpoints"
}
