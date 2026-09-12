# Custom VPC Network
resource "google_compute_network" "vpc" {
  name                    = "campusflow-vpc-${var.environment}"
  auto_create_subnetworks = false
  description             = "CampusFlow dedicated VPC network for ${var.environment}"
}

# Regional Application Subnet
resource "google_compute_subnetwork" "subnet" {
  name                     = "campusflow-subnet-${var.environment}"
  ip_cidr_range            = var.subnet_cidr
  region                   = var.region
  network                  = google_compute_network.vpc.id
  private_ip_google_access = true
  description              = "CampusFlow private subnet for ${var.environment}"
}

# Reserved Global Internal IP Range for Private Service Networking (Cloud SQL)
resource "google_compute_global_address" "private_ip_range" {
  name          = "campusflow-psa-${var.environment}"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
  description   = "Peering range for Cloud SQL Private IP in ${var.environment}"
}

# Service Networking Connection (VPC Peering with Google Services for Cloud SQL)
resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_range.name]
}

# Serverless VPC Access Connector for Cloud Run to reach Cloud SQL privately
resource "google_vpc_access_connector" "connector" {
  name          = "cf-vpc-cx-${var.environment}"
  region        = var.region
  network       = google_compute_network.vpc.name
  ip_cidr_range = var.connector_cidr
  min_instances = 2
  max_instances = 3
  machine_type  = "e2-micro"

  depends_on = [
    google_compute_network.vpc
  ]
}
