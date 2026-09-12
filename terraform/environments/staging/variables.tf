variable "project_id" {
  description = "GCP Project ID for staging."
  type        = string
}

variable "region" {
  description = "GCP Region for staging resources."
  type        = string
  default     = "asia-south1"
}

variable "db_tier" {
  description = "Machine tier for staging Cloud SQL instance (cost-optimized)."
  type        = string
  default     = "db-f1-micro"
}

variable "container_image_api" {
  description = "Staging API container image."
  type        = string
  default     = "gcr.io/cloudrun/hello"
}

variable "container_image_worker" {
  description = "Staging Worker container image."
  type        = string
  default     = "gcr.io/cloudrun/hello"
}

variable "cors_allowed_origins" {
  description = "CORS allowed origins for staging."
  type        = string
  default     = "http://localhost:5173"
}

variable "frontend_base_url" {
  description = "Frontend base URL for staging."
  type        = string
  default     = "http://localhost:5173"
}
