# CampusFlow — Terraform GCP Infrastructure Foundation

This directory contains the Infrastructure-as-Code (IaC) configuration for **CampusFlow** on Google Cloud Platform (GCP).

---

## 1. Architecture Overview

```
                      Internet / CDN / HTTPS
                                |
                   Cloud Run: campusflow-api
                  (Public / LB-facing Ingress)
                                |
        +-----------------------+-----------------------+
        |                       |                       |
   VPC Connector           GCS Bucket             Cloud Tasks
   (Private IP)       (Resumes / Docs)          (Notifications)
        |                                               |
  Cloud SQL PostgreSQL                            OIDC Authenticated
  (Private Service Connect)                             |
                                                        v
                                             Cloud Run: campusflow-worker
                                                 (INTERNAL ONLY)
                                                        |
                                                Web Push / SendGrid

Cloud Scheduler (Every 30m)
        |
   OIDC Authenticated POST
        v
campusflow-api (/internal/scheduler/*)
```

---

## 2. Directory Structure

```
terraform/
├── README.md                              # This document
├── versions.tf                            # Terraform & Provider version constraints
├── providers.tf                           # GCP provider configuration
├── variables.tf                           # Root variable declarations
├── outputs.tf                             # Non-sensitive infrastructure outputs
├── main.tf                                # Root module orchestrating all submodules
├── modules/
│   ├── artifact_registry/                 # Docker container registry repository
│   ├── networking/                        # Dedicated VPC, subnet, private service peering & Serverless VPC Connector
│   ├── service_accounts/                  # Least-privilege IAM service accounts
│   ├── secrets/                           # Secret Manager secret containers & access policies
│   ├── cloud_sql/                         # Private PostgreSQL 16 instance, DB, user & automated backups
│   ├── storage/                           # GCS bucket with uniform access, public prevention & CORS
│   ├── cloud_tasks/                       # Asynchronous notification dispatch queue & retry configuration
│   ├── cloud_run/                         # API (public) & Worker (internal-only) Cloud Run services
│   └── scheduler/                         # Cloud Scheduler jobs with OIDC authentication
└── environments/
    ├── staging/                           # Staging environment instantiation (cost-optimized)
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── outputs.tf
    │   └── terraform.tfvars.example
    └── production/                        # Production environment instantiation (high availability)
        ├── main.tf
        ├── variables.tf
        ├── outputs.tf
        └── terraform.tfvars.example
```

---

## 3. Least Privilege & IAM Matrix

| Service Account | Role / Permissions | Scope / Target | Rationale |
|---|---|---|---|
| `cf-api-sa` | `roles/cloudsql.client` | Project | Allows API to connect to Cloud SQL |
| `cf-api-sa` | `roles/cloudtasks.enqueuer` | Project | Allows API to enqueue notification tasks |
| `cf-api-sa` | `roles/secretmanager.secretAccessor` | Secret Manager Secrets | Allows API to read runtime secrets |
| `cf-api-sa` | `roles/storage.objectAdmin` | Resume GCS Bucket | Generates V4 signed upload/download URLs |
| `cf-worker-sa` | `roles/cloudsql.client` | Project | Allows Worker to persist notifications to Cloud SQL |
| `cf-worker-sa` | `roles/secretmanager.secretAccessor` | DB/VAPID/SendGrid Secrets | Allows Worker to read delivery credentials |
| `cf-tasks-sa` | `roles/run.invoker` | `campusflow-worker` | OIDC caller for Cloud Tasks invoking internal Worker |
| `cf-sched-sa` | `roles/run.invoker` | `campusflow-api` | OIDC caller for Cloud Scheduler invoking `/internal/scheduler/*` |

> [!IMPORTANT]
> Zero `roles/owner` or `roles/editor` permissions are assigned. Cloud Run Worker has `INGRESS_TRAFFIC_INTERNAL_ONLY` and public invocation (`allUsers`) is explicitly forbidden.

---

## 4. Secret Management & Secure Deployment

Terraform creates the **Secret Manager containers** and assigns access permissions without storing raw secret values in code or state.

After running `terraform apply`, populate runtime secret values using the Google Cloud CLI:

```bash
# 1. Database URL (or generate during provisioning)
gcloud secrets versions add campusflow-staging-database-url --data-file=/path/to/db-url.txt

# 2. JWT RS256 Keypair (Base64 PEM)
gcloud secrets versions add campusflow-staging-jwt-private-key-base64 --data-file=/path/to/jwt_private.b64
gcloud secrets versions add campusflow-staging-jwt-public-key-base64 --data-file=/path/to/jwt_public.b64

# 3. VAPID Web Push Keys
gcloud secrets versions add campusflow-staging-vapid-private-key --data-file=/path/to/vapid_private.txt
gcloud secrets versions add campusflow-staging-vapid-public-key --data-file=/path/to/vapid_public.txt

# 4. SendGrid API Key (if EMAIL_PROVIDER=sendgrid)
gcloud secrets versions add campusflow-staging-sendgrid-api-key --data-file=/path/to/sendgrid.txt

# 5. Internal Task Auth Secret
gcloud secrets versions add campusflow-staging-internal-task-auth-secret --data-file=/path/to/internal_secret.txt
```

---

## 5. Usage & Deployment Workflows

### Staging Environment

1. Copy and configure variables:
   ```bash
   cd terraform/environments/staging
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with staging project ID
   ```

2. Initialize and validate:
   ```bash
   terraform init
   terraform validate
   ```

3. Review the execution plan:
   ```bash
   terraform plan -out=staging.tfplan
   ```

4. Apply (only when explicitly authorized):
   ```bash
   terraform apply staging.tfplan
   ```

---

## 6. Remote State Handling

To enable remote state storage in GCS:
1. Create an administrative GCS bucket: `gcloud storage buckets create gs://campusflow-tfstate-staging --location=asia-south1 --uniform-bucket-level-access`
2. Uncomment the `backend "gcs"` block in `environments/staging/main.tf` or `environments/production/main.tf`.
3. Run `terraform init -migrate-state`.
