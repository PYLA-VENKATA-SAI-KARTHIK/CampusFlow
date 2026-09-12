variable "project_id" {
  description = "GCP Project ID."
  type        = string
}

variable "region" {
  description = "GCP Region for GCS bucket."
  type        = string
}

variable "environment" {
  description = "Deployment environment (staging, production)."
  type        = string
}

variable "api_sa_email" {
  description = "Email of the API service account for bucket object access."
  type        = string
}

variable "cors_origins" {
  description = "List of allowed CORS origins for signed URL browser uploads."
  type        = list(string)
  default     = ["http://localhost:5173"]
}

variable "versioning_enabled" {
  description = "Whether object versioning is enabled on the bucket."
  type        = bool
  default     = true
}
