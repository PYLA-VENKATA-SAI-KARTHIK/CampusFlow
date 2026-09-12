variable "project_id" {
  description = "GCP Project ID."
  type        = string
}

variable "region" {
  description = "GCP Region for Cloud SQL instance."
  type        = string
}

variable "environment" {
  description = "Deployment environment (staging, production)."
  type        = string
}

variable "db_tier" {
  description = "Machine tier for Cloud SQL PostgreSQL instance."
  type        = string
  default     = "db-f1-micro"
}

variable "db_disk_size_gb" {
  description = "Initial disk size in GB."
  type        = number
  default     = 10
}

variable "db_deletion_protection" {
  description = "Whether deletion protection is enabled on Cloud SQL instance."
  type        = bool
  default     = true
}

variable "network_id" {
  description = "ID of the VPC network for private IP connectivity."
  type        = string
}

variable "private_vpc_connection" {
  description = "Dependency on the private VPC connection peering."
  type        = any
}
