output "bucket_name" {
  description = "The name of the resume storage bucket."
  value       = google_storage_bucket.resumes.name
}

output "bucket_url" {
  description = "The URI of the created bucket."
  value       = google_storage_bucket.resumes.url
}
