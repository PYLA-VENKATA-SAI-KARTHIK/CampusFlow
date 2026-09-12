variable "project_id" {
  description = "GCP Project ID for production."
  type        = string
}

variable "region" {
  description = "GCP Region for production resources."
  type        = string
  default     = "asia-south1"
}

variable "db_tier" {
  description = "Machine tier for production Cloud SQL instance."
  type        = string
  default     = "db-custom-2-7680" # 2 vCPU, 7.5 GB RAM
}

variable "db_disk_size_gb" {
  description = "Allocated storage size for production Cloud SQL in GB."
  type        = number
  default     = 20
}

variable "container_image_api" {
  description = "Production API container image."
  type        = string
}

variable "container_image_worker" {
  description = "Production Worker container image."
  type        = string
}

variable "api_min_instances" {
  description = "Minimum instances for production API Cloud Run (high availability / warm instances)."
  type        = number
  default     = 1
}

variable "api_max_instances" {
  description = "Maximum instances for production API Cloud Run."
  type        = number
  default     = 20
}

variable "worker_min_instances" {
  description = "Minimum instances for production Worker Cloud Run."
  type        = number
  default     = 0
}

variable "worker_max_instances" {
  description = "Maximum instances for production Worker Cloud Run."
  type        = number
  default     = 10
}

variable "cors_allowed_origins" {
  description = "CORS allowed origins for production."
  type        = string
}

variable "frontend_base_url" {
  description = "Frontend base URL for production."
  type        = string
}
