output "instance_name" {
  description = "The name of the Cloud SQL instance."
  value       = google_sql_database_instance.instance.name
}

output "connection_name" {
  description = "The connection name of the Cloud SQL instance to be used in connection strings."
  value       = google_sql_database_instance.instance.connection_name
}

output "private_ip_address" {
  description = "The first private IPv4 address assigned to the Cloud SQL instance."
  value       = google_sql_database_instance.instance.private_ip_address
}

output "database_name" {
  description = "The name of the application database."
  value       = google_sql_database.database.name
}

output "database_user" {
  description = "The application database username."
  value       = google_sql_user.user.name
}

output "database_password" {
  description = "The generated database password (sensitive)."
  value       = random_password.db_password.result
  sensitive   = true
}

output "async_database_url" {
  description = "SQLAlchemy async PostgreSQL connection URL using private IP."
  value       = "postgresql+asyncpg://${google_sql_user.user.name}:${random_password.db_password.result}@${google_sql_database_instance.instance.private_ip_address}:5432/${google_sql_database.database.name}"
  sensitive   = true
}
