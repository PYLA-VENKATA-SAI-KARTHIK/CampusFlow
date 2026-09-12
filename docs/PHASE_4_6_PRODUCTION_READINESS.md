# Phase 4.6 — Production Readiness & Cost-Free Architecture Guide

This guide outlines the production-readiness state, security posture, configuration matrix, and zero-cost local architecture for **CampusFlow**.

---

## 1. Zero-Cost Policy & Current Environment State

> [!IMPORTANT]
> **CampusFlow development operates at strict ₹0 cloud cost.**
> - GCP Project: `campusflow-staging`
> - GCP Billing Status: **`billingEnabled: false`**
> - Cloud Resources Provisioned: **0**
> - Terraform Deployment: **Not executed (`terraform apply` has NOT been run)**
>
> All development, test execution, end-to-end simulation, and security validations run completely offline or against local synthetic fixtures without generating any cloud financial liability.

---

## 2. Architecture & Service Topology

```
+-------------------------------------------------------------------------------+
|                            PRODUCTION GCP ARCHITECTURE                        |
|                                                                               |
|                             Internet / HTTPS                                  |
|                                    |                                          |
|                        Cloud Run: campusflow-api                              |
|                       (Public / Ingress-Facing)                               |
|                                    |                                          |
|             +----------------------+----------------------+                    |
|             |                      |                      |                   |
|        VPC Connector          GCS Bucket             Cloud Tasks              |
|        (Private IP)        (Resumes / Docs)        (Notifications)            |
|             |                                             |                   |
|       Cloud SQL PostgreSQL                        OIDC Authenticated          |
|       (Private IP only)                                   |                   |
|                                                           v                   |
|                                               Cloud Run: campusflow-worker    |
|                                                   (INTERNAL ONLY)             |
|                                                           |                   |
|                                                   Web Push / SendGrid         |
|                                                                               |
| Cloud Scheduler (Every 30m)                                                   |
|        |                                                                      |
|   OIDC Token                                                                  |
|        v                                                                      |
| campusflow-api (/internal/scheduler/*)                                        |
+-------------------------------------------------------------------------------+
|                             LOCAL DEVELOPMENT MODE                            |
|                                                                               |
|   Frontend (Vite :5173) ----> Backend (FastAPI :8000) ----> PostgreSQL (:5432)|
|                                    |                                          |
|                          MockStorageService (In-memory)                       |
|                          MockCloudTasksService (In-memory)                    |
|                          MockPushSenderService (In-memory)                    |
+-------------------------------------------------------------------------------+
```

---

## 3. Configuration & Environment Matrix

| Parameter | Local Development | Staging Environment | Production Environment |
|---|---|---|---|
| `APP_ENV` | `development` | `staging` | `production` |
| `DEBUG` | `true` | `false` | `false` |
| `LOG_LEVEL` | `DEBUG` | `INFO` | `INFO` |
| `DATABASE_URL` | Local PostgreSQL container | Cloud SQL (Private IP) | Cloud SQL (Private IP, HA) |
| `STORAGE_PROVIDER` | `mock` | `gcs` | `gcs` |
| `GCS_BUCKET_NAME` | `campusflow-resumes` | `campusflow-resumes-staging-...` | `campusflow-resumes-production-...` |
| `NOTIFICATION_TASK_PROVIDER` | `mock` | `cloud_tasks` | `cloud_tasks` |
| `CLOUD_TASKS_QUEUE_NAME` | `campusflow-notifications` | `campusflow-notifications-staging` | `campusflow-notifications-production` |
| `INTERNAL_SERVICE_URL` | `http://localhost:8000` | Cloud Run Worker URI | Cloud Run Worker URI |
| `PUSH_PROVIDER` | `mock` | `webpush` | `webpush` |
| `EMAIL_PROVIDER` | `mock` | `sendgrid` | `sendgrid` |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Staging web origin | Production web origin |

---

## 4. Security & Hardening Controls

An OWASP-aligned security audit verified the following defense-in-depth protections:

1. **Authentication & Token Management**:
   - Asymmetric RS256 JWT signatures for access and refresh tokens.
   - Distinct expiration windows (15 minutes for access tokens; 7 days for refresh tokens).
   - Single-use password activation tokens with SHA-256 hash digests.
2. **Role-Based Access Control (RBAC)**:
   - Three distinct persona levels (`STUDENT`, `OFFICER`, `ADMIN`).
   - Strict server-side route guards enforcing least privilege.
   - Client-side navigation route barriers redirecting unauthorized roles to `/unauthorized`.
3. **Internal Endpoint Protection**:
   - `/internal/*` routes (Scheduler, Tasks) strictly reject user JWTs with HTTP 403.
   - Production mode requires valid Google OIDC ID tokens matching the authorized invoker service account email.
4. **Data Protection & Field Immutability**:
   - Academic profile fields (`cgpa`, `roll_number`, `branch_code`, `active_backlogs`) are strictly read-only for student users and can only be modified via admin/officer onboarding.
   - Database trigger on `audit_logs` raises an exception upon any `UPDATE` or `DELETE` attempt, guaranteeing immutable compliance logs.
5. **Private Storage & Network Isolation**:
   - Resume GCS bucket enforces `uniform_bucket_level_access` and `public_access_prevention = "enforced"`.
   - Cloud SQL has public IPv4 disabled; accessible only via private VPC peering.
   - Worker Cloud Run service enforces `INGRESS_TRAFFIC_INTERNAL_ONLY`.

---

## 5. Local Execution & Testing Runbook

### A. Backend Pytest Suite
```powershell
cd backend
.\venv\Scripts\pytest.exe -v
```

### B. Frontend Production Build
```powershell
cd frontend
npm run build
```

### C. Database Migration Head Verification
```powershell
cd backend
.\venv\Scripts\alembic.exe heads
```

### D. Playwright Browser E2E Automation
```powershell
cd frontend
npm run test:e2e
```

### E. Lightweight Locust Load Validation
```powershell
cd backend
.\venv\Scripts\python.exe scripts/run_locust_smoke.py --tier 1
```

---

## 6. GCP Deployment Prerequisites (For Future Funded Phase)

When project funding is authorized and deployment to Google Cloud is scheduled:

1. **Enable GCP Billing**:
   ```bash
   gcloud billing projects link campusflow-staging --billing-account=YOUR_BILLING_ACCOUNT_ID
   ```
2. **Bootstrap Remote State Storage (One-Time)**:
   ```bash
   gcloud storage buckets create gs://campusflow-tfstate-staging --location=asia-south1 --uniform-bucket-level-access
   ```
3. **Initialize and Plan Terraform**:
   ```bash
   cd terraform/environments/staging
   cp terraform.tfvars.example terraform.tfvars
   # Fill in project_id in terraform.tfvars
   terraform init
   terraform plan -out=staging.tfplan
   ```
4. **Apply Infrastructure**:
   ```bash
   terraform apply staging.tfplan
   ```
5. **Inject Secret Payloads into Secret Manager**:
   ```bash
   gcloud secrets versions add campusflow-staging-database-url --data-file=db-url.txt
   gcloud secrets versions add campusflow-staging-jwt-private-key-base64 --data-file=jwt_private.b64
   gcloud secrets versions add campusflow-staging-jwt-public-key-base64 --data-file=jwt_public.b64
   gcloud secrets versions add campusflow-staging-vapid-private-key --data-file=vapid_private.txt
   gcloud secrets versions add campusflow-staging-vapid-public-key --data-file=vapid_public.txt
   gcloud secrets versions add campusflow-staging-sendgrid-api-key --data-file=sendgrid.txt
   gcloud secrets versions add campusflow-staging-internal-task-auth-secret --data-file=internal_secret.txt
   ```
6. **Rollback Strategy**:
   - Container revisions can be rolled back instantaneously in Cloud Run:
     ```bash
     gcloud run services update-traffic campusflow-api-staging --to-revisions=PREVIOUS_REVISION=100
     ```
   - Cloud SQL point-in-time recovery (PITR) allows restoration to any second within the 7-day log retention window.
