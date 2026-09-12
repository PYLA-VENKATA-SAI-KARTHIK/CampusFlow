output "network_id" {
  description = "The ID of the VPC network."
  value       = google_compute_network.vpc.id
}

output "network_name" {
  description = "The name of the VPC network."
  value       = google_compute_network.vpc.name
}

output "subnet_id" {
  description = "The ID of the subnetwork."
  value       = google_compute_subnetwork.subnet.id
}

output "vpc_connector_id" {
  description = "The ID of the Serverless VPC Access connector."
  value       = google_vpc_access_connector.connector.id
}

output "vpc_connector_name" {
  description = "The name of the Serverless VPC Access connector."
  value       = google_vpc_access_connector.connector.name
}

output "private_vpc_connection" {
  description = "The service networking connection resource dependency."
  value       = google_service_networking_connection.private_vpc_connection
}
