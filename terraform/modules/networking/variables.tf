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

variable "subnet_cidr" {
  description = "CIDR range for the primary application subnet."
  type        = string
  default     = "10.0.0.0/24"
}

variable "connector_cidr" {
  description = "CIDR range (/28) for the Serverless VPC Access connector."
  type        = string
  default     = "10.8.0.0/28"
}
