resource "google_artifact_registry_repository" "campusflow" {
  provider      = google
  location      = var.region
  repository_id = var.repository_id != "" ? var.repository_id : "campusflow-${var.environment}"
  description   = "CampusFlow container image repository for ${var.environment}"
  format        = "DOCKER"

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}
