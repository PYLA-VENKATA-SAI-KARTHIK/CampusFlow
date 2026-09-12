resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# Secure GCS Bucket for Resumes & Student Documents
resource "google_storage_bucket" "resumes" {
  name                        = "campusflow-resumes-${var.environment}-${random_id.bucket_suffix.hex}"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = var.environment == "staging" ? true : false

  versioning {
    enabled = var.versioning_enabled
  }

  cors {
    origin          = var.cors_origins
    method          = ["GET", "PUT", "HEAD", "OPTIONS"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      num_newer_versions = 3
      days_since_noncurrent_time = 30
      with_state        = "ARCHIVED"
    }
  }

  lifecycle_rule {
    action {
      type = "AbortIncompleteMultipartUpload"
    }
    condition {
      age = 7
    }
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

# Grant API Service Account Object Admin on Resumes Bucket
resource "google_storage_bucket_iam_member" "api_object_admin" {
  bucket = google_storage_bucket.resumes.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.api_sa_email}"
}
