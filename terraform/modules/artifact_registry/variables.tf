variable "project_id" {
  description = "GCP Project ID."
  type        = string
}

variable "region" {
  description = "GCP Region for Artifact Registry."
  type        = string
}

variable "environment" {
  description = "Environment name (staging, production)."
  type        = string
}

variable "repository_id" {
  description = "The repository ID for Artifact Registry."
  type        = string
  default     = ""
}
