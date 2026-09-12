terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0.0, < 6.0.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 5.0.0, < 6.0.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.5.0"
    }
  }

  # Uncomment and configure remote state backend when GCS state bucket is provisioned:
  # backend "gcs" {
  #   bucket = "campusflow-tfstate-staging"
  #   prefix = "terraform/state"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

module "staging_infrastructure" {
  source = "../../"

  project_id             = var.project_id
  region                 = var.region
  environment            = "staging"
  db_tier                = var.db_tier
  db_disk_size_gb        = 10
  db_deletion_protection = false # Staging can be safely torn down
  api_min_instances      = 0     # Cost saving: scale to zero on idle
  api_max_instances      = 5
  worker_min_instances   = 0     # Cost saving: scale to zero on idle
  worker_max_instances   = 3
  container_image_api    = var.container_image_api
  container_image_worker = var.container_image_worker
  cors_allowed_origins   = var.cors_allowed_origins
  frontend_base_url      = var.frontend_base_url
}
