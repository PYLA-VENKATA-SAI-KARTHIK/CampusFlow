# ==============================================================================
# CampusFlow Root Terraform Configuration
# ==============================================================================

locals {
  services = [
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
    "cloudtasks.googleapis.com",
    "cloudscheduler.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "vpcaccess.googleapis.com",
    "servicenetworking.googleapis.com",
    "compute.googleapis.com",
    "iam.googleapis.com",
  ]
}

# 1. Enable Required GCP APIs
resource "google_project_service" "apis" {
  for_each           = toset(local.services)
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# 2. Artifact Registry
module "artifact_registry" {
  source      = "./modules/artifact_registry"
  project_id  = var.project_id
  region      = var.region
  environment = var.environment

  depends_on = [google_project_service.apis]
}

# 3. Dedicated VPC & Serverless Connector Networking
module "networking" {
  source      = "./modules/networking"
  project_id  = var.project_id
  region      = var.region
  environment = var.environment

  depends_on = [google_project_service.apis]
}

# 4. IAM & Least-Privilege Service Accounts
module "service_accounts" {
  source      = "./modules/service_accounts"
  project_id  = var.project_id
  environment = var.environment

  depends_on = [google_project_service.apis]
}

# 5. Secret Manager Containers
module "secrets" {
  source          = "./modules/secrets"
  project_id      = var.project_id
  environment     = var.environment
  api_sa_email    = module.service_accounts.api_sa_email
  worker_sa_email = module.service_accounts.worker_sa_email

  depends_on = [google_project_service.apis]
}

# 6. Cloud SQL PostgreSQL Instance (Private IP only)
module "cloud_sql" {
  source                  = "./modules/cloud_sql"
  project_id              = var.project_id
  region                  = var.region
  environment             = var.environment
  db_tier                 = var.db_tier
  db_disk_size_gb         = var.db_disk_size_gb
  db_deletion_protection  = var.db_deletion_protection
  network_id              = module.networking.network_id
  private_vpc_connection  = module.networking.private_vpc_connection

  depends_on = [google_project_service.apis]
}

# 7. Secure GCS Storage Bucket (Resumes)
module "storage" {
  source       = "./modules/storage"
  project_id   = var.project_id
  region       = var.region
  environment  = var.environment
  api_sa_email = module.service_accounts.api_sa_email
  cors_origins = [var.frontend_base_url]

  depends_on = [google_project_service.apis]
}

# 8. Cloud Tasks Queue (Async Notifications)
module "cloud_tasks" {
  source      = "./modules/cloud_tasks"
  project_id  = var.project_id
  region      = var.region
  environment = var.environment

  depends_on = [google_project_service.apis]
}

# 9. Cloud Run Services (Public API & Internal Worker)
module "cloud_run" {
  source                 = "./modules/cloud_run"
  project_id             = var.project_id
  region                 = var.region
  environment            = var.environment
  api_sa_email           = module.service_accounts.api_sa_email
  worker_sa_email        = module.service_accounts.worker_sa_email
  tasks_sa_email         = module.service_accounts.tasks_sa_email
  scheduler_sa_email     = module.service_accounts.scheduler_sa_email
  vpc_connector_name     = module.networking.vpc_connector_name
  container_image_api    = var.container_image_api
  container_image_worker = var.container_image_worker
  api_min_instances      = var.api_min_instances
  api_max_instances      = var.api_max_instances
  worker_min_instances   = var.worker_min_instances
  worker_max_instances   = var.worker_max_instances
  gcs_bucket_name        = module.storage.bucket_name
  cloud_tasks_queue_name = module.cloud_tasks.queue_name
  cors_allowed_origins   = var.cors_allowed_origins
  frontend_base_url      = var.frontend_base_url
  secret_ids             = module.secrets.secret_ids

  depends_on = [google_project_service.apis]
}

# 10. Cloud Scheduler Jobs (Deadline Reminders & Auto-Close)
module "scheduler" {
  source             = "./modules/scheduler"
  project_id         = var.project_id
  region             = var.region
  environment        = var.environment
  api_url            = module.cloud_run.api_url
  scheduler_sa_email = module.service_accounts.scheduler_sa_email

  depends_on = [google_project_service.apis]
}
