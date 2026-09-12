variable "project_id" {
  description = "The Google Cloud Platform (GCP) project ID."
  type        = string
}

variable "region" {
  description = "The primary GCP region for all regional resources (Cloud Run, Cloud SQL, GCS, Cloud Tasks)."
  type        = string
  default     = "asia-south1"
}

variable "environment" {
  description = "Deployment environment name (staging or production)."
  type        = string
  default     = "staging"

  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be either 'staging' or 'production'."
  }
}

variable "db_tier" {
  description = "The machine tier / SKU for the Cloud SQL PostgreSQL instance."
  type        = string
  default     = "db-f1-micro"
}

variable "db_disk_size_gb" {
  description = "Allocated storage size for Cloud SQL in GB."
  type        = number
  default     = 10
}

variable "db_deletion_protection" {
  description = "Prevent accidental destruction of Cloud SQL database instance."
  type        = bool
  default     = true
}

variable "container_image_api" {
  description = "The container image URI for CampusFlow API Cloud Run service."
  type        = string
  default     = "gcr.io/cloudrun/hello" # Placeholder until built by CI/CD
}

variable "container_image_worker" {
  description = "The container image URI for CampusFlow Worker Cloud Run service."
  type        = string
  default     = "gcr.io/cloudrun/hello" # Placeholder until built by CI/CD
}

variable "api_min_instances" {
  description = "Minimum number of Cloud Run instances for API service (0 for cost saving in staging, >=1 in production)."
  type        = number
  default     = 0
}

variable "api_max_instances" {
  description = "Maximum number of Cloud Run instances for API service."
  type        = number
  default     = 10
}

variable "worker_min_instances" {
  description = "Minimum number of Cloud Run instances for Worker service."
  type        = number
  default     = 0
}

variable "worker_max_instances" {
  description = "Maximum number of Cloud Run instances for Worker service."
  type        = number
  default     = 5
}

variable "cors_allowed_origins" {
  description = "Comma-separated list of allowed CORS origins for the frontend."
  type        = string
  default     = "http://localhost:5173"
}

variable "frontend_base_url" {
  description = "Base URL of the frontend web application."
  type        = string
  default     = "http://localhost:5173"
}
