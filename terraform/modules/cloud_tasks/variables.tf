variable "project_id" {
  description = "GCP Project ID."
  type        = string
}

variable "region" {
  description = "GCP Region for Cloud Tasks queue."
  type        = string
}

variable "environment" {
  description = "Deployment environment (staging, production)."
  type        = string
}

variable "queue_name" {
  description = "Name of the Cloud Tasks queue for asynchronous notifications."
  type        = string
  default     = ""
}

variable "max_dispatches_per_second" {
  description = "Maximum task dispatches per second."
  type        = number
  default     = 50
}

variable "max_concurrent_dispatches" {
  description = "Maximum concurrent task dispatches."
  type        = number
  default     = 20
}
