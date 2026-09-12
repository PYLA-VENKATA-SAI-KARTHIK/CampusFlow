resource "random_id" "db_suffix" {
  byte_length = 4
}

# Generate secure random database password for campusflow user
resource "random_password" "db_password" {
  length  = 24
  special = false # Avoid special characters that break URI parsing
}

# Cloud SQL PostgreSQL Instance
resource "google_sql_database_instance" "instance" {
  name             = "campusflow-db-${var.environment}-${random_id.db_suffix.hex}"
  database_version = "POSTGRES_16"
  region           = var.region

  deletion_protection = var.db_deletion_protection

  depends_on = [var.private_vpc_connection]

  settings {
    tier              = var.db_tier
    disk_size         = var.db_disk_size_gb
    disk_type         = "PD_SSD"
    disk_autoresize   = true
    availability_type = var.environment == "production" ? "REGIONAL" : "ZONAL"

    ip_configuration {
      ipv4_enabled                                  = false # Private IP only
      private_network                               = var.network_id
      enable_private_path_for_google_cloud_services = true
    }

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00" # UTC
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = var.environment == "production" ? 30 : 7
        retention_unit   = "COUNT"
      }
    }

    maintenance_window {
      day          = 7 # Sunday
      hour         = 4
      update_track = "stable"
    }

    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }
    database_flags {
      name  = "log_connections"
      value = "on"
    }
    database_flags {
      name  = "log_disconnections"
      value = "on"
    }
    database_flags {
      name  = "log_lock_waits"
      value = "on"
    }

    user_labels = {
      environment = var.environment
      managed_by  = "terraform"
    }
  }
}

# Main Application Database
resource "google_sql_database" "database" {
  name     = "campusflow"
  instance = google_sql_database_instance.instance.name
}

# Application User
resource "google_sql_user" "user" {
  name     = "campusflow"
  instance = google_sql_database_instance.instance.name
  password = random_password.db_password.result
}
