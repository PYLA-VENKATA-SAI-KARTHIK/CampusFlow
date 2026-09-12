variable "project_id" {
  description = "GCP Project ID."
  type        = string
}

variable "region" {
  description = "GCP Region for Cloud Scheduler jobs."
  type        = string
}

variable "environment" {
  description = "Deployment environment (staging, production)."
  type        = string
}

variable "api_url" {
  description = "The target API Cloud Run URL."
  type        = string
}

variable "scheduler_sa_email" {
  description = "The service account email used by Cloud Scheduler for OIDC authentication."
  type        = string
}

variable "timezone" {
  description = "Timezone for scheduler jobs."
  type        = string
  default     = "Asia/Kolkata"
}
