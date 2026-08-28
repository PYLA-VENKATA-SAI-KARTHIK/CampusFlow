# CampusFlow — API Architecture

> **Version:** 2.2 | **Updated:** 2026-08-27 (all pre-Phase-1 decisions finalized)  
> **Style:** Logical API boundaries — NOT an implementation spec.  
> This document defines responsibilities, authorization requirements, major operations, and data flows for each API domain.

---

## 1. API Design Standards

| Standard | Decision |
|---|---|
| Protocol | REST over HTTPS |
| Base URL | Environment-configured (no hardcoded domain in MVP — uses managed Cloud Run URL or `localhost` in dev) |
| Versioning | URL path versioning (`/api/v1/`) |
| Auth | `Authorization: Bearer <access_token>` header on all protected routes |
| Format | JSON request/response bodies |
| Errors | RFC 7807 Problem Details (`type`, `title`, `status`, `detail`, `instance`) |
| Pagination | Page-based (`page`, `page_size`) returning `{items, total, page, page_size, has_next}` |
| Docs | Auto-generated OpenAPI at `/docs` (Swagger) and `/redoc` |
| Internal | Internal endpoints (Cloud Tasks/Scheduler) at `/internal/` — not publicly accessible |

### Standard Error Response
```json
{
  "type": "https://campusflow.college/errors/forbidden",
  "title": "Access Forbidden",
  "status": 403,
  "detail": "You are not eligible for this placement drive.",
  "instance": "/api/v1/drives/abc-123/register",
  "reasons": ["CGPA 6.8 is below required 7.0", "Branch ECE not in eligible list"]
}
```

---

## 2. API Domain Map

```
/api/v1/
├── /auth/                    → Authentication & Session Management
├── /students/                → Student Self-Service
├── /officers/students/       → Officer Access to Student Data
├── /branches/                → Branch Vocabulary Management
├── /companies/               → Company Management
├── /drives/                  → Placement Drive Lifecycle
│   └── /:driveId/
│       ├── /eligibility-check
│       ├── /register
│       ├── /registrations    → Officer: view registrations
│       ├── /stages/          → Stage management
│       │   └── /:stageId/
│       │       ├── /shortlist
│       │       ├── /assignments
│       │       └── /publish-results
│       └── /notify           → Manual notification blast
├── /applications/            → Student: My registrations
├── /notifications/           → Notification management + push subscriptions
├── /documents/               → Resume upload + download URL generation
├── /admin/                   → Admin-only: users, audit logs, config
└── /internal/                → Internal: Cloud Tasks + Cloud Scheduler handlers
```

---

## 3. Domain Specifications

---

### 3.1 Authentication (`/auth`)

**Responsibility:** Establish, maintain, and terminate authenticated sessions.

**Authorization:** Public (login, refresh). Authenticated for logout and password change.

**Major Operations:**

| Operation | Method | Path | Auth | Description |
|---|---|---|---|---|
| Login | POST | `/auth/login` | Public | Verify credentials, return JWT pair |
| Refresh token | POST | `/auth/refresh` | Public | Exchange refresh token for new access token |
| Logout | POST | `/auth/logout` | Any auth'd user | Revoke refresh token |
| Change password | POST | `/auth/change-password` | Any auth'd user | Update password, revoke all refresh tokens |
| **Activate account** | **POST** | **`/auth/activate`** | **Public** | **First-time login: validate activation token, set new password** |
| JWKS | GET | `/.well-known/jwks.json` | Public | Returns public key set for JWT signature verification |

**Data flows:**

*Standard login:*
1. Client POSTs email + password
2. Backend: verify `must_change_password = FALSE`, bcrypt verify → generate access_token (15m) + refresh_token (7d) → store refresh token hash in DB
3. Client stores tokens; `user.must_change_password` flag checked — if TRUE, redirect to forced-change screen
4. On 401 from any endpoint: Axios interceptor automatically calls `/auth/refresh` → retries request

*Account activation (first-time, Decision 2):*
1. Admin/Officer imports student via CSV → system creates user with `is_active=FALSE`, `must_change_password=TRUE`, generates activation token (UUID, 72h expiry)
2. Student receives activation email with link: `/activate?token=<token>`
3. Student POSTs `{activation_token, new_password}` to `/auth/activate`
4. Backend: validate token not expired + not used → set `is_active=TRUE`, `must_change_password=FALSE`, hash new password, mark token used
5. Student is redirected to login with their new credentials

**Security:**
- Rate limited: 10 login attempts / IP / minute
- No user enumeration: identical response for "wrong password" vs "user not found"
- Refresh token stored as SHA-256 hash only — raw token never persisted
- Password change immediately revokes all active refresh tokens
- Activation email sent via abstracted `EmailService` (SendGrid in MVP — Decision A); credentials stored in Secret Manager only, never in source control or frontend

---

### 3.2 Student Self-Service (`/students/me`)

**Responsibility:** Allow students to view their own profile, update **non-academic** contact fields, upload their resume, and track their applications.

**Authorization:** STUDENT role only. All operations scoped to the authenticated student.

**Major Operations:**

| Operation | Method | Path | Description |
|---|---|---|---|
| Get own profile | GET | `/students/me` | Full profile + resume upload status |
| Update profile | PATCH | `/students/me` | Phone number, gender, avatar only. **CGPA and backlogs are read-only for students.** |
| Get resume upload URL | GET | `/students/me/resume-upload-url` | Returns signed GCS PUT URL (15 min) |
| Confirm resume upload | POST | `/students/me/resume-confirm` | Verifies GCS object exists; updates profile |
| Get resume download URL | GET | `/students/me/resume-download-url` | Returns signed GCS GET URL (15 min) |
| List my applications | GET | `/students/me/applications` | All registrations + current stage status |

**Data flow (profile update):**
1. Student PATCHes non-academic profile fields (phone, gender, avatar)
2. Backend enforces: any attempt to set `cgpa` or `active_backlogs` returns `403 Forbidden`
3. Academic data (`cgpa`, `active_backlogs`, `branch`, `batch_year`, `roll_number`) is **read-only** for students

**IDOR protection:**
- Every query is scoped with `WHERE user_id = current_user.id` from the verified JWT
- No URL path contains a student ID for self-service routes — always uses `/me`

---

### 3.3 Officer Access to Students (`/officers/students`)

**Responsibility:** Allow placement officers to search, view, and download documents for student profiles.

**Authorization:** OFFICER or ADMIN role.

**Major Operations:**

| Operation | Method | Path | Description |
|---|---|---|---|
| List students | GET | `/officers/students` | Paginated; filterable by branch, batch_year, min_cgpa, search |
| Get student profile | GET | `/officers/students/{studentId}` | Full profile (no resume URL) |
| Get student resume URL | GET | `/officers/students/{studentId}/resume-download-url` | Signed URL; audit logged |

**Data flow (resume download):**
1. Officer requests download URL for student
2. Backend verifies role = OFFICER|ADMIN
3. Backend generates signed GCS URL (15 min)
4. Audit log written: `action=RESUME_DOWNLOADED, entity_id=student_id, performed_by=officer_id`
5. Returns URL — officer's browser fetches file directly from GCS

---

### 3.4 Companies (`/companies`)

**Responsibility:** Manage company profiles that are linked to placement drives.

**Authorization:** Read = all authenticated users. Create/Update = OFFICER, ADMIN.

**Major Operations:**

| Operation | Method | Path | Auth | Description |
|---|---|---|---|---|
| List companies | GET | `/companies` | Any | Paginated, searchable |
| Get company | GET | `/companies/{companyId}` | Any | Full company detail |
| Create company | POST | `/companies` | OFFICER, ADMIN | Creates company + optional logo upload |
| Update company | PATCH | `/companies/{companyId}` | OFFICER, ADMIN | Updates name, website, etc. |
| Get logo upload URL | GET | `/companies/{companyId}/logo-upload-url` | OFFICER, ADMIN | Signed GCS PUT URL for logo |

**Notes:**
- Companies are not deletable (drives reference them)
- Logo stored in the **public-assets** bucket (unlike resumes which are private)

---

### 3.5 Branches (`/branches`)

**Responsibility:** Manage the controlled vocabulary of academic branches used by student profiles and eligibility criteria. Branches are a domain entity — not generic configuration (Decision C).

**Authorization:** Read = all authenticated users. Create/Update/Deactivate = ADMIN, OFFICER.

**Major Operations:**

| Operation | Method | Path | Auth | Description |
|---|---|---|---|---|
| List branches | GET | `/branches` | Any | All active branches; optionally include inactive with `?include_inactive=true` |
| Get branch | GET | `/branches/{code}` | Any | Single branch detail |
| Create branch | POST | `/branches` | ADMIN | Add a new branch (e.g., new department opening) |
| Update branch | PATCH | `/branches/{code}` | ADMIN | Update display name |
| Deactivate branch | DELETE | `/branches/{code}` | ADMIN | Sets `is_active=FALSE`; does not delete (student profiles reference it) |

**Notes:**
- Branch codes are used directly in `eligibility_criteria.criteria.eligible_branches` JSONB
- Deactivating a branch prevents it from being selected for new eligibility rules; existing drives are unaffected
- The BranchEvaluator in the Eligibility Engine compares `student.branch_code` against the list in criteria using case-insensitive match

---

### 3.5 Placement Drives (`/drives`)

**Responsibility:** The core domain. Manages the full placement drive lifecycle from creation to completion.

**Authorization:**
- DRAFT drives: visible to OFFICER, ADMIN only
- PUBLISHED+ drives: visible to all authenticated users
- All write operations: OFFICER, ADMIN only
- **Drive ownership: any authorized Officer may manage any drive** (Decision B). Drives are not scoped to their creating officer. All management actions are audit-logged.

**Major Operations:**

| Operation | Method | Path | Auth | Description |
|---|---|---|---|---|
| List drives | GET | `/drives` | All (filtered by role) | Returns drives with `my_eligibility` for students |
| Get drive | GET | `/drives/{driveId}` | All | Drive detail + student's eligibility + registration status |
| Create drive | POST | `/drives` | OFFICER, ADMIN | Creates drive in DRAFT + eligibility criteria |
| Update drive | PATCH | `/drives/{driveId}` | OFFICER, ADMIN | Only allowed in DRAFT status |
| Advance status | POST | `/drives/{driveId}/transition` | OFFICER, ADMIN | Advance lifecycle state (validated state machine) |
| Eligibility check | GET | `/drives/{driveId}/eligibility-check` | STUDENT | Returns `{is_eligible, reasons}` |
| Eligible students | GET | `/drives/{driveId}/eligible-students` | OFFICER, ADMIN | All eligible students before registration close |
| View registrations | GET | `/drives/{driveId}/registrations` | OFFICER, ADMIN | All registrations with student summaries |
| Register | POST | `/drives/{driveId}/register` | STUDENT | Eligibility-gated; requires resume on file |
| Manual notify | POST | `/drives/{driveId}/notify` | OFFICER, ADMIN | Async blast to eligible/registered/shortlisted |

**Drive state transition validation (service layer):**
```
ALLOWED_TRANSITIONS = {
  DRAFT                → PUBLISHED,
  PUBLISHED            → REGISTRATION_OPEN,
  REGISTRATION_OPEN    → REGISTRATION_CLOSED,
  REGISTRATION_CLOSED  → SHORTLISTING,
  SHORTLISTING         → ASSESSMENT,
  ASSESSMENT           → INTERVIEW,
  INTERVIEW            → RESULT,
  RESULT               → COMPLETED
}

TRANSITION_PRECONDITIONS = {
  REGISTRATION_OPEN: requires registration_deadline is not null,
  ASSESSMENT:        requires at least 1 placement stage exists,
  PUBLISHED:         triggers async: notify eligible students,
  REGISTRATION_OPEN: triggers: schedule deadline reminders,
  REGISTRATION_CLOSED: triggers: cancel pending reminder tasks,
  COMPLETED:         triggers async: notify registered students with final result
}
```

**Eligibility evaluation at GET `/drives/{driveId}`:**
- Only evaluated for role = STUDENT
- EligibilityEngine.evaluate() called in-process (< 1ms)
- Result included inline in drive response — no separate call needed in most cases

---

### 3.6 Placement Stages (`/drives/{driveId}/stages`)

**Responsibility:** Manage assessment/interview stages within a drive; track student participation and results.

**Authorization:** Read = STUDENT (if shortlisted for stage). Write = OFFICER, ADMIN.

**Major Operations:**

| Operation | Method | Path | Auth | Description |
|---|---|---|---|---|
| Create stage | POST | `/drives/{driveId}/stages` | OFFICER, ADMIN | Add stage with type, order, schedule |
| List stages | GET | `/drives/{driveId}/stages` | Role-filtered | Students see only published stages they're assigned to |
| Update stage | PATCH | `/drives/{driveId}/stages/{stageId}` | OFFICER, ADMIN | Triggers "stage updated" notification if published |
| Publish stage | POST | `/drives/{driveId}/stages/{stageId}/publish` | OFFICER, ADMIN | Makes stage visible to shortlisted students |
| Shortlist students | POST | `/drives/{driveId}/stages/{stageId}/shortlist` | OFFICER, ADMIN | Batch shortlist: `{student_ids: []}` |
| Update assignment | PATCH | `/drives/{driveId}/stages/{stageId}/assignments/{studentId}` | OFFICER, ADMIN | Set APPEARED, SELECTED, or REJECTED |
| Publish results | POST | `/drives/{driveId}/stages/{stageId}/publish-results` | OFFICER, ADMIN | Notifies all assigned students |

**Authorization on student access:**
```
Student can view stage details ONLY IF:
  1. stage.is_published = TRUE
  2. A stage_assignment exists WHERE stage_id = stage.id AND student_user_id = current_user.id
```

**Notification side effects (all async via Cloud Tasks):**
- `shortlist`: each shortlisted student gets `SHORTLISTED` notification
- `update stage schedule`: each shortlisted student gets `STAGE_UPDATED` notification
- `publish-results`: each assigned student gets `RESULT_PUBLISHED` notification

---

### 3.7 Notifications (`/notifications`)

**Responsibility:** Deliver and manage in-app notifications; manage browser push subscriptions.

**Authorization:** All authenticated users (scoped to own notifications).

**Major Operations:**

| Operation | Method | Path | Auth | Description |
|---|---|---|---|---|
| List notifications | GET | `/notifications` | All | Paginated; `?is_read=false` filter |
| Mark read | POST | `/notifications/{notifId}/read` | All | Marks single notification read |
| Mark all read | POST | `/notifications/mark-all-read` | All | Marks all unread as read |
| Register push | POST | `/notifications/push-subscription` | All | Store browser push subscription |
| Remove push | DELETE | `/notifications/push-subscription` | All | Remove subscription by endpoint |
| Get VAPID key | GET | `/notifications/vapid-public-key` | Public | Returns VAPID public key for Service Worker |

**Authorization on notification access:**
- `GET /notifications`: `WHERE user_id = current_user.id` — strictly own notifications
- `POST /notifications/{id}/read`: verifies `notification.user_id == current_user.id` before update

**Note on delivery:** Notifications are never sent synchronously from these endpoints. They are written to DB and pushed via the async worker pipeline. These endpoints only manage the stored records.

---

### 3.8 Documents (`/documents`)

**Responsibility:** Generate secure signed URLs for private document upload and download.

**Authorization:** Student = own documents only. Officer/Admin = any student's documents (audit logged).

**Major Operations:**

| Operation | Method | Path | Auth | Description |
|---|---|---|---|---|
| Get resume upload URL | GET | `/documents/resume-upload-url` | STUDENT | Returns signed PUT URL for GCS (PDF, ≤5MB, 15min) |
| Confirm resume upload | POST | `/documents/resume-confirm` | STUDENT | Verifies GCS object, updates profile |
| Get own resume URL | GET | `/documents/resume-download-url` | STUDENT | Signed GET URL for own resume |
| Get student resume URL | GET | `/documents/students/{studentId}/resume-url` | OFFICER, ADMIN | Signed GET URL; audit logged |

**Upload security flow:**
1. Backend generates signed upload URL with constraints: `content-type=application/pdf`, `max-bytes=5242880`, `expiry=900s`
2. GCS enforces these constraints at upload time — no bypass possible
3. After upload, `/documents/resume-confirm` verifies object exists and is a valid PDF before updating the profile

**File naming:**
- `resumes/{user_id}/{uuid}.pdf` — no original filename used (prevents path traversal)
- Signed URLs never reveal the underlying bucket structure

---

### 3.9 Admin (`/admin`)

**Responsibility:** System governance — user management, role assignment, audit visibility, system configuration.

**Authorization:** ADMIN role only on all endpoints in this domain.

**Major Operations:**

| Operation | Method | Path | Description |
|---|---|---|---|
| List users | GET | `/admin/users` | All users; filterable by role, active status, search |
| Create user | POST | `/admin/users` | Create officer or admin accounts |
| Get user | GET | `/admin/users/{userId}` | Full user + profile detail |
| Update user | PATCH | `/admin/users/{userId}` | Change role or is_active status |
| Bulk import students | POST | `/admin/students/bulk-import` | CSV upload → async processing |
| List audit logs | GET | `/admin/audit-logs` | Filterable by user, entity, action, date range |
| Get config | GET | `/admin/config` | System configuration key-value pairs |
| Update config | PATCH | `/admin/config/{key}` | Update a config value |
| Analytics overview | GET | `/admin/analytics` | Platform-wide placement statistics |

**Bulk import flow:**
1. Admin/Officer uploads CSV (email, full_name, roll_number, branch_code, batch_year, cgpa, active_backlogs)
2. Backend validates CSV structure (including branch_code against active branches table), returns `{job_id}` with `202 Accepted`
3. Processing happens in-process (for small files) or via Cloud Tasks (for large files)
4. Each row creates: `users` record (is_active=FALSE) + `student_profiles` record + `account_activations` record, sends activation email via `EmailService`
5. Import results (success count, error rows with reasons) stored and available at `GET /admin/imports/{job_id}`

**Resend activation (Decision D):**
- `POST /admin/users/{id}/resend-activation` (ADMIN, OFFICER)
- Validates: user exists, user role = STUDENT, user `is_active = FALSE`
- Checks rate limits: max 5 total resends, min 10-minute gap since last resend
- Generates new cryptographically secure token; invalidates previous token; extends expiry 72h from now
- Sends new activation email via `EmailService`
- Raw token is never logged — only SHA-256 hash stored
- Returns: `200 OK {message: "Activation email resent"}` or appropriate 429/400 on rate limit violation

**Academic data update (CGPA/backlogs correction):**
- OFFICER or ADMIN can PATCH `student_profiles.cgpa` and `active_backlogs`
- Any change to these fields is written to `student_profile_history` with `changed_by_user_id`
- An audit log entry is created; student cannot perform this update

---

### 3.10 Internal Endpoints (`/internal`)

**Responsibility:** Handle callbacks from Cloud Tasks (notification worker) and Cloud Scheduler (deadline checker).

**Authorization:** OIDC token verification. The token must be signed by a specific Google service account. These endpoints are on a Cloud Run service with `--ingress=internal` — they are not reachable from the public internet.

**Endpoints:**

| Operation | Method | Path | Caller | Description |
|---|---|---|---|---|
| Process notification task | POST | `/internal/tasks/send-notification` | Cloud Tasks | Writes DB record, sends push notification |
| Check deadlines | POST | `/internal/scheduler/check-deadlines` | Cloud Scheduler | Finds drives needing reminders, enqueues tasks |
| Auto-close registrations | POST | `/internal/scheduler/auto-close-registrations` | Cloud Scheduler | Moves REGISTRATION_OPEN drives past deadline to REGISTRATION_CLOSED |
| Cancel reminders | POST | `/internal/tasks/cancel-reminders` | Cloud Tasks | Marks reminder tasks for a student+drive as cancelled |

**OIDC verification:**
```python
# On every /internal/* request:
oidc_token = request.headers["Authorization"].replace("Bearer ", "")
claims = google.oauth2.id_token.verify_oauth2_token(oidc_token, request, audience=WORKER_URL)
assert claims["email"] == "campusflow-tasks-sa@project.iam.gserviceaccount.com"
```

---

## 4. Cross-Cutting API Behaviors

### 4.1 Authentication Dependency

Every protected route uses a FastAPI dependency:

```python
current_user = Depends(get_current_user)
# → Extracts Bearer token from header
# → Verifies JWT signature (RS256 public key)
# → Checks token expiry
# → Returns UserContext{id, role, email}
# → Raises HTTP 401 if any step fails
```

### 4.2 Role Authorization Dependency

```python
require_roles([Role.OFFICER, Role.ADMIN])
# → Checks current_user.role ∈ allowed_roles
# → Raises HTTP 403 if not authorized
# → Never trusts role from request body — always from JWT
```

### 4.3 Rate Limiting

| Endpoint Group | Limit |
|---|---|
| `POST /auth/login` | 10 / IP / minute |
| `POST /auth/refresh` | 20 / IP / minute |
| `POST /auth/activate` | 5 / IP / 15 minutes |
| `POST /admin/users/{id}/resend-activation` | 5 total per user (lifetime), 1 per 10 minutes |
| `GET /documents/resume-upload-url` | 5 / user / hour |
| All other public API | 120 / IP / minute |
| Internal endpoints | 500 / Cloud Tasks IP / minute |

Implemented via Cloud Armor security policy (IP-level) + application-level middleware (user-level).

### 4.4 Request/Response Conventions

- All `PATCH` operations use **partial update** semantics — only provided fields are updated
- All list endpoints support `page` (default 1) and `page_size` (default 20, max 100)
- Timestamps in responses are always **ISO 8601 with timezone** (e.g., `2025-01-15T09:30:00+05:30`)
- UUIDs in URLs are validated at the router level — invalid UUID format returns 422 immediately
- 404 responses never reveal whether a resource exists but is forbidden (use 403 for that)
