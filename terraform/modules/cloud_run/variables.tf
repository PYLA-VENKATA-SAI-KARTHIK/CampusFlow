variable "project_id" {
  description = "GCP Project ID."
  type        = string
}

variable "region" {
  description = "GCP Region."
  type        = string
}

variable "environment" {
  description = "Deployment environment (staging, production)."
  type        = string
}

variable "api_sa_email" {
  description = "Service account email for the API service."
  type        = string
}

variable "worker_sa_email" {
  description = "Service account email for the Worker service."
  type        = string
}

variable "tasks_sa_email" {
  description = "Service account email for Cloud Tasks (invoker of Worker)."
  type        = string
}

variable "scheduler_sa_email" {
  description = "Service account email for Cloud Scheduler (invoker of API scheduler endpoints)."
  type        = string
}

variable "vpc_connector_name" {
  description = "Serverless VPC Access connector name for private Cloud SQL connectivity."
  type        = string
}

variable "container_image_api" {
  description = "Container image URI for the API service."
  type        = string
  default     = "gcr.io/cloudrun/hello"
}

variable "container_image_worker" {
  description = "Container image URI for the Worker service."
  type        = string
  default     = "gcr.io/cloudrun/hello"
}

variable "api_min_instances" {
  description = "Minimum instances for API Cloud Run."
  type        = number
  default     = 0
}

variable "api_max_instances" {
  description = "Maximum instances for API Cloud Run."
  type        = number
  default     = 10
}

variable "worker_min_instances" {
  description = "Minimum instances for Worker Cloud Run."
  type        = number
  default     = 0
}

variable "worker_max_instances" {
  description = "Maximum instances for Worker Cloud Run."
  type        = number
  default     = 5
}

variable "gcs_bucket_name" {
  description = "GCS bucket name for student resumes."
  type        = string
}

variable "cloud_tasks_queue_name" {
  description = "Cloud Tasks queue name."
  type        = string
}

variable "cors_allowed_origins" {
  description = "Allowed CORS origins for the frontend."
  type        = string
  default     = "http://localhost:5173"
}

variable "frontend_base_url" {
  description = "Frontend base URL."
  type        = string
  default     = "http://localhost:5173"
}

variable "secret_ids" {
  description = "Map of secret keys to Secret Manager secret IDs."
  type        = map(string)
}
