# CampusFlow — Database Schema

> **Version:** 2.2 | **Updated:** 2026-08-27 (all pre-Phase-1 decisions finalized)  
> **Database:** PostgreSQL 15 (Cloud SQL) | **ORM:** SQLAlchemy 2.0 async | **Migrations:** Alembic

---

## 1. Design Principles

| Principle | Implementation |
|---|---|
| UUID primary keys | `gen_random_uuid()` on all tables — never expose sequential IDs in URLs |
| Timezone-aware timestamps | All timestamps use `TIMESTAMPTZ` — no naive datetimes ever |
| Soft deletes | `users.is_active = FALSE` — never hard delete user records |
| Immutable audit trail | `audit_logs` and `student_profile_history` are insert-only |
| Extensible eligibility | Criteria stored as `JSONB` — new criteria types require no schema migration |
| Snapshot at registration | Resume GCS path snapshotted at registration time |
| Denormalization for hot paths | `stage_assignments.drive_id` denormalized for analytics queries |
| Row-level security ready | `user_id` foreign key on all student data tables enables future RLS |

---

## 2. Entity Relationship Diagram

```mermaid
erDiagram
    USERS {
        uuid id PK
        varchar email UK
        varchar password_hash
        varchar role
        varchar full_name
        boolean is_active
        boolean must_change_password
        timestamptz last_login_at
        timestamptz created_at
        timestamptz updated_at
    }

    ACCOUNT_ACTIVATIONS {
        uuid id PK
        uuid user_id FK UK
        varchar token_hash UK
        timestamptz expires_at
        boolean used
        smallint resend_count
        timestamptz last_resent_at
        timestamptz created_at
    }

    BRANCHES {
        uuid id PK
        varchar code UK
        varchar name
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    REFRESH_TOKENS {
        uuid id PK
        uuid user_id FK
        varchar token_hash UK
        timestamptz expires_at
        boolean revoked
        timestamptz created_at
    }

    STUDENT_PROFILES {
        uuid id PK
        uuid user_id FK UK
        varchar roll_number UK
        varchar branch_code FK
        smallint batch_year
        numeric cgpa
        smallint active_backlogs
        varchar phone_number
        varchar gender
        text resume_gcs_path
        timestamptz resume_uploaded_at
        text avatar_gcs_path
        timestamptz created_at
        timestamptz updated_at
    }

    STUDENT_PROFILE_HISTORY {
        uuid id PK
        uuid student_profile_id FK
        uuid changed_by_user_id FK
        varchar field_name
        text old_value
        text new_value
        timestamptz created_at
    }

    COMPANIES {
        uuid id PK
        varchar name
        text website
        text logo_gcs_path
        varchar industry
        text description
        uuid created_by_user_id FK
        timestamptz created_at
        timestamptz updated_at
    }

    PLACEMENT_DRIVES {
        uuid id PK
        uuid company_id FK
        varchar title
        varchar job_role
        text description
        numeric ctc_lpa
        numeric stipend_monthly
        varchar location
        text bond_details
        timestamptz registration_deadline
        varchar status
        uuid created_by_user_id FK
        timestamptz published_at
        timestamptz created_at
        timestamptz updated_at
    }

    ELIGIBILITY_CRITERIA {
        uuid id PK
        uuid drive_id FK UK
        jsonb criteria
        timestamptz created_at
        timestamptz updated_at
    }

    DRIVE_REGISTRATIONS {
        uuid id PK
        uuid drive_id FK
        uuid student_user_id FK
        text resume_snapshot_gcs_path
        varchar status
        timestamptz registered_at
        timestamptz updated_at
    }

    PLACEMENT_STAGES {
        uuid id PK
        uuid drive_id FK
        varchar name
        varchar stage_type
        smallint sequence_order
        timestamptz scheduled_at
        text location_or_link
        text instructions
        boolean is_published
        timestamptz created_at
        timestamptz updated_at
    }

    STAGE_ASSIGNMENTS {
        uuid id PK
        uuid stage_id FK
        uuid student_user_id FK
        uuid drive_id FK
        varchar status
        text result_notes
        timestamptz assigned_at
        timestamptz updated_at
    }

    NOTIFICATIONS {
        uuid id PK
        uuid user_id FK
        varchar title
        text body
        varchar notification_type
        uuid reference_id
        varchar reference_type
        boolean is_read
        boolean push_sent
        timestamptz push_sent_at
        timestamptz created_at
    }

    PUSH_SUBSCRIPTIONS {
        uuid id PK
        uuid user_id FK
        text endpoint UK
        text p256dh_key
        text auth_key
        text user_agent
        boolean is_active
        timestamptz created_at
        timestamptz last_used_at
    }

    AUDIT_LOGS {
        uuid id PK
        uuid performed_by_user_id FK
        varchar action
        varchar entity_type
        uuid entity_id
        jsonb old_state
        jsonb new_state
        inet ip_address
        text user_agent
        timestamptz created_at
    }

    SYSTEM_CONFIG {
        varchar key PK
        text value
        text description
        uuid updated_by_user_id FK
        timestamptz updated_at
    }

    USERS ||--o| STUDENT_PROFILES : "has profile"
    USERS ||--o{ REFRESH_TOKENS : "has sessions"
    USERS ||--o| ACCOUNT_ACTIVATIONS : "activated via"
    USERS ||--o{ DRIVE_REGISTRATIONS : "registers"
    USERS ||--o{ STAGE_ASSIGNMENTS : "assigned to"
    USERS ||--o{ NOTIFICATIONS : "receives"
    USERS ||--o{ PUSH_SUBSCRIPTIONS : "subscribes"
    USERS ||--o{ AUDIT_LOGS : "performs"
    USERS ||--o{ COMPANIES : "creates"
    USERS ||--o{ PLACEMENT_DRIVES : "creates"

    STUDENT_PROFILES ||--o{ STUDENT_PROFILE_HISTORY : "versioned by"

    COMPANIES ||--o{ PLACEMENT_DRIVES : "has drives"
    PLACEMENT_DRIVES ||--|| ELIGIBILITY_CRITERIA : "has criteria"
    PLACEMENT_DRIVES ||--o{ DRIVE_REGISTRATIONS : "receives registrations"
    PLACEMENT_DRIVES ||--o{ PLACEMENT_STAGES : "has stages"
    PLACEMENT_DRIVES ||--o{ STAGE_ASSIGNMENTS : "tracks assignments"

    PLACEMENT_STAGES ||--o{ STAGE_ASSIGNMENTS : "has participants"
    BRANCHES ||--o{ STUDENT_PROFILES : "categorises"
```

---

## 3. Table Definitions

**Purpose:** Single identity table for all user types. Role stored here — no separate role table needed at this scale.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Never expose in URLs — use as internal FK only |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | Lowercase enforced at application layer |
| `password_hash` | VARCHAR(255) | NOT NULL | bcrypt output, cost=12; set to random hash until account activated |
| `role` | VARCHAR(20) | NOT NULL, CHECK(`STUDENT`,`OFFICER`,`ADMIN`) | Enforced by enum constraint |
| `full_name` | VARCHAR(255) | NOT NULL | |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT **FALSE** | Set to TRUE on account activation; FALSE = pending activation or suspended |
| `must_change_password` | BOOLEAN | NOT NULL, DEFAULT TRUE | TRUE until student sets their own password via `/auth/activate` |
| `last_login_at` | TIMESTAMPTZ | NULL | Updated on every successful login |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Updated by trigger |

**Indexes:** `users_email_idx` UNIQUE, `users_role_idx`, `users_is_active_idx`

**Constraints:**
```sql
CONSTRAINT users_role_check CHECK (role IN ('STUDENT', 'OFFICER', 'ADMIN'))
CONSTRAINT users_email_lower CHECK (email = LOWER(email))
```

> **Note on onboarding flow:** When Admin/Officer imports a student via CSV, the user row is created with `is_active=FALSE` and `must_change_password=TRUE`. The account is only activated when the student completes the `/auth/activate` flow. The student cannot log in until `is_active=TRUE`.

---

### 3.2 `account_activations`

**Purpose:** Stores one-time activation tokens sent to newly-imported students via email. Used for the initial password-set flow.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → `users.id` ON DELETE CASCADE, UNIQUE, NOT NULL | One pending activation per user |
| `token_hash` | VARCHAR(64) | UNIQUE, NOT NULL | SHA-256 of the raw token — raw token sent in email only |
| `expires_at` | TIMESTAMPTZ | NOT NULL | 72 hours from creation |
| `used` | BOOLEAN | NOT NULL, DEFAULT FALSE | Set to TRUE immediately on successful activation |
| `resend_count` | SMALLINT | NOT NULL, DEFAULT 0 | Incremented on each resend; rate limit enforced at service layer |
| `last_resent_at` | TIMESTAMPTZ | NULL | Timestamp of most recent resend; used to enforce minimum gap between resends |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:** `account_activations_user_id_idx` UNIQUE, `account_activations_token_hash_idx` UNIQUE

**Security (resend — Decision D):**
- Token is a cryptographically random UUID (`secrets.token_urlsafe(32)`); stored as SHA-256 hash only
- Expired or already-used tokens return the same generic error (no information leakage)
- Resend (`POST /admin/users/{id}/resend-activation`) invalidates previous token (overwrites `token_hash` + `expires_at`) and resets `used = FALSE`
- Rate limits on resend (enforced at service layer):
  - Max 5 resends per user total (`resend_count <= 5`)
  - Min 10 minutes between resends (`last_resent_at + 10min < NOW()`)
  - Raw token is **never logged** — only the SHA-256 hash is ever written to the database or logs
- Activation link format: `{FRONTEND_BASE_URL}/activate?token={raw_token}`
  `FRONTEND_BASE_URL` is environment-configured — not hardcoded (Decision 3)

---

### 3.2 `refresh_tokens`

**Purpose:** Enables server-side session revocation. Access tokens are stateless (no DB lookup); refresh tokens are not.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → `users.id` ON DELETE CASCADE, NOT NULL | |
| `token_hash` | VARCHAR(64) | UNIQUE, NOT NULL | SHA-256 of the raw token — raw token never stored |
| `expires_at` | TIMESTAMPTZ | NOT NULL | 7 days from issuance |
| `revoked` | BOOLEAN | NOT NULL, DEFAULT FALSE | Set to TRUE on logout / password change |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:** `refresh_tokens_hash_idx` UNIQUE, `refresh_tokens_user_idx`

**Cleanup:** A scheduled job or Alembic migration can purge rows where `expires_at < NOW()` to prevent table bloat.

---

### 3.4 `branches`

**Purpose:** Controlled vocabulary of academic branches/departments. Referenced by `student_profiles` and validated against when setting `eligibility_criteria.criteria.eligible_branches`. Exists as a domain entity rather than generic config because it participates in data relationships (Decision C).

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `code` | VARCHAR(20) | UNIQUE, NOT NULL | Short identifier used throughout the system, e.g., `CSE`, `ECE`, `IT`, `MECH` |
| `name` | VARCHAR(100) | NOT NULL | Full display name, e.g., `Computer Science & Engineering` |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Inactive branches cannot be used in new eligibility criteria |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:** `branches_code_idx` UNIQUE

**Seed data (initial migration):**
```sql
INSERT INTO branches (code, name) VALUES
  ('CSE',   'Computer Science & Engineering'),
  ('ECE',   'Electronics & Communication Engineering'),
  ('IT',    'Information Technology'),
  ('MECH',  'Mechanical Engineering'),
  ('CIVIL', 'Civil Engineering'),
  ('EEE',   'Electrical & Electronics Engineering'),
  ('AI',    'Artificial Intelligence & Machine Learning'),
  ('DS',    'Data Science');
-- Admins add/deactivate branches via the /branches API — no migration needed
```

**Usage in Eligibility Engine:**
```
 criteria.eligible_branches = ["CSE", "IT", "AI"]
 student.branch_code = "CSE"
 BranchEvaluator: student.branch_code in criteria.eligible_branches  →  PASS
 (case-insensitive comparison; both values come from branches.code)
```

**Why not store in `system_config`?**
- Branches are a first-class domain entity: student profiles carry a FK to `branches.code`
- The eligibility engine validates against them
- They have their own `is_active` lifecycle
- Future: placement analytics grouped by branch require a proper entity

---

### 3.5 `student_profiles`

**Purpose:** Extended academic and personal data for students. One-to-one with `users` where `role = 'STUDENT'`.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → `users.id`, UNIQUE, NOT NULL | 1:1 with users |
| `roll_number` | VARCHAR(50) | UNIQUE, NOT NULL | College roll number — institution-assigned |
| `branch_code` | VARCHAR(20) | FK → `branches.code`, NOT NULL | Validated against active branches; e.g., `CSE`, `ECE` |
| `batch_year` | SMALLINT | NOT NULL | Graduation year e.g., 2025, 2026 |
| `cgpa` | NUMERIC(4,2) | NOT NULL, CHECK(0 ≤ cgpa ≤ 10) | 2 decimal places |
| `active_backlogs` | SMALLINT | NOT NULL, DEFAULT 0, CHECK(≥ 0) | Count of active backlogs |
| `phone_number` | VARCHAR(15) | NULL | E.164 format preferred |
| `gender` | VARCHAR(10) | NULL, CHECK(`MALE`,`FEMALE`,`OTHER`) | Optional, used for eligibility |
| `resume_gcs_path` | TEXT | NULL | Internal GCS path — never a public URL |
| `resume_uploaded_at` | TIMESTAMPTZ | NULL | |
| `avatar_gcs_path` | TEXT | NULL | Profile picture GCS path |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `student_profiles_user_id_idx` UNIQUE
- `student_profiles_roll_number_idx` UNIQUE
- `student_profiles_branch_idx`
- `student_profiles_batch_year_idx`
- `student_profiles_cgpa_idx` — supports eligibility bulk-filter queries

**Constraints:**
```sql
CONSTRAINT student_profiles_cgpa_range CHECK (cgpa >= 0 AND cgpa <= 10)
CONSTRAINT student_profiles_backlogs_positive CHECK (active_backlogs >= 0)
CONSTRAINT student_profiles_gender_check CHECK (gender IN ('MALE', 'FEMALE', 'OTHER'))
```

---

### 3.5 `student_profile_history`

**Purpose:** Immutable log of changes to CGPA and backlog count. Required for institutional compliance and audit. Only OFFICER and ADMIN actors appear in `changed_by_user_id` — students cannot produce entries here.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `student_profile_id` | UUID | FK → `student_profiles.id`, NOT NULL | |
| `changed_by_user_id` | UUID | FK → `users.id`, NOT NULL | Must be role=OFFICER or role=ADMIN — enforced at service layer |
| `field_name` | VARCHAR(50) | NOT NULL | `cgpa` or `active_backlogs` |
| `old_value` | TEXT | NULL | Null only for first-time set |
| `new_value` | TEXT | NOT NULL | |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

> **Insert-only table.** No UPDATE or DELETE allowed. Enforced by a PostgreSQL trigger that raises an exception on any non-INSERT operation.

**Indexes:** `profile_history_profile_id_idx`, `profile_history_created_at_idx`

---

### 3.5 `companies`

**Purpose:** Company profiles that placement drives are associated with.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `name` | VARCHAR(255) | NOT NULL | Company display name |
| `website` | TEXT | NULL | |
| `logo_gcs_path` | TEXT | NULL | Path in public-assets bucket |
| `industry` | VARCHAR(100) | NULL | e.g., `Technology`, `Finance`, `Core Engineering` |
| `description` | TEXT | NULL | Rich text (markdown) |
| `created_by_user_id` | UUID | FK → `users.id`, NOT NULL | Officer who created it |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:** `companies_name_idx`, `companies_created_by_idx`

---

### 3.6 `placement_drives`

**Purpose:** Core entity. Represents one placement opportunity from one company.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `company_id` | UUID | FK → `companies.id`, NOT NULL | |
| `title` | VARCHAR(255) | NOT NULL | e.g., `SDE Intern — Summer 2025` |
| `job_role` | VARCHAR(255) | NOT NULL | e.g., `Software Development Engineer` |
| `description` | TEXT | NULL | Markdown supported |
| `ctc_lpa` | NUMERIC(6,2) | NULL | CTC in lakhs p.a. (null if internship) |
| `stipend_monthly` | NUMERIC(8,2) | NULL | Monthly stipend (null if full-time) |
| `location` | VARCHAR(255) | NULL | City or `Remote` |
| `bond_details` | TEXT | NULL | Bond terms if applicable |
| `registration_deadline` | TIMESTAMPTZ | NULL | Deadline; NULL allowed in DRAFT |
| `status` | VARCHAR(30) | NOT NULL, DEFAULT `DRAFT` | See status enum below |
| `created_by_user_id` | UUID | FK → `users.id`, NOT NULL | |
| `published_at` | TIMESTAMPTZ | NULL | Set when status → PUBLISHED |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Status Enum:**
```sql
CONSTRAINT drive_status_check CHECK (status IN (
  'DRAFT', 'PUBLISHED', 'REGISTRATION_OPEN', 'REGISTRATION_CLOSED',
  'SHORTLISTING', 'ASSESSMENT', 'INTERVIEW', 'RESULT', 'COMPLETED'
))
```

**Indexes:** `drives_company_id_idx`, `drives_status_idx`, `drives_deadline_idx`, `drives_created_by_idx`

**Business rule enforced at service layer:** `registration_deadline` must be set before transitioning to `REGISTRATION_OPEN`.

---

### 3.7 `eligibility_criteria`

**Purpose:** Per-drive eligibility rules stored as JSONB. One-to-one with `placement_drives`.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `drive_id` | UUID | FK → `placement_drives.id`, UNIQUE, NOT NULL | Exactly one criteria set per drive |
| `criteria` | JSONB | NOT NULL | Schema below |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Criteria JSONB Schema:**

```json
{
  "min_cgpa": 7.0,
  "max_active_backlogs": 0,
  "eligible_branches": ["CSE", "AI", "IT"],
  "eligible_batch_years": [2025, 2026],
  "gender": null,

  "tenth_min_percentage": null,
  "twelfth_min_percentage": null,
  "min_attendance_pct": null
}
```

**Why JSONB?**
- Absence of a key = "no constraint for this criterion" (engine skips it)
- New criteria types require zero schema migrations
- Existing drives are unaffected — they simply lack the new key
- JSONB is indexed, queryable, and type-safe in PostgreSQL

**Indexes:** `eligibility_criteria_drive_id_idx` UNIQUE, GIN index on `criteria` for bulk filter queries

---

### 3.8 `drive_registrations`

**Purpose:** Records that a student registered for a drive. Also captures a point-in-time resume snapshot.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `drive_id` | UUID | FK → `placement_drives.id`, NOT NULL | |
| `student_user_id` | UUID | FK → `users.id`, NOT NULL | |
| `resume_snapshot_gcs_path` | TEXT | NOT NULL | GCS path at time of registration |
| `status` | VARCHAR(30) | NOT NULL, DEFAULT `REGISTERED` | |
| `registered_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Status Enum:**
```sql
CONSTRAINT registration_status_check CHECK (status IN ('REGISTERED', 'WITHDRAWN', 'CANCELLED'))
```

**Unique constraint:** `UNIQUE (drive_id, student_user_id)` — prevents duplicate registrations at DB level (application also checks)

**Indexes:** `registrations_drive_id_idx`, `registrations_student_idx`, `registrations_status_idx`

**Why resume snapshot?** A student may upload a newer resume after registering. The company evaluates the resume that was submitted at registration time, not the latest one.

---

### 3.9 `placement_stages`

**Purpose:** Defines the stages of a drive's selection process in order.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `drive_id` | UUID | FK → `placement_drives.id`, NOT NULL | |
| `name` | VARCHAR(255) | NOT NULL | e.g., `Aptitude Test`, `Technical Round 1` |
| `stage_type` | VARCHAR(50) | NOT NULL | Enum: `APTITUDE`, `TECHNICAL`, `HR`, `GD`, `CODING`, `OTHER` |
| `sequence_order` | SMALLINT | NOT NULL | 1-based; uniqueness enforced per drive |
| `scheduled_at` | TIMESTAMPTZ | NULL | Can be set later |
| `location_or_link` | TEXT | NULL | Room no., building, or Google Meet link |
| `instructions` | TEXT | NULL | What to bring, dress code, etc. |
| `is_published` | BOOLEAN | NOT NULL, DEFAULT FALSE | TRUE = visible to shortlisted students |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Unique constraint:** `UNIQUE (drive_id, sequence_order)` — prevents duplicate order numbers within a drive

**Indexes:** `stages_drive_id_idx`, `stages_drive_order_idx`

---

### 3.10 `stage_assignments`

**Purpose:** Tracks each student's shortlisting and outcome for each stage.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `stage_id` | UUID | FK → `placement_stages.id`, NOT NULL | |
| `student_user_id` | UUID | FK → `users.id`, NOT NULL | |
| `drive_id` | UUID | FK → `placement_drives.id`, NOT NULL | Denormalized for analytics |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT `SHORTLISTED` | |
| `result_notes` | TEXT | NULL | Optional officer feedback |
| `assigned_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Status Enum:**
```sql
CONSTRAINT assignment_status_check CHECK (status IN ('SHORTLISTED', 'APPEARED', 'SELECTED', 'REJECTED'))
```

**Unique constraint:** `UNIQUE (stage_id, student_user_id)`

**Indexes:** `assignments_stage_id_idx`, `assignments_student_idx`, `assignments_drive_id_idx`, `assignments_status_idx`

---

### 3.11 `notifications`

**Purpose:** Persistent record of all notifications for in-app display. Created before push delivery is attempted.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → `users.id`, NOT NULL | Recipient |
| `title` | VARCHAR(255) | NOT NULL | |
| `body` | TEXT | NOT NULL | |
| `notification_type` | VARCHAR(50) | NOT NULL | See types below |
| `reference_id` | UUID | NULL | ID of related entity (drive, stage) |
| `reference_type` | VARCHAR(50) | NULL | e.g., `DRIVE`, `STAGE` |
| `is_read` | BOOLEAN | NOT NULL, DEFAULT FALSE | |
| `push_sent` | BOOLEAN | NOT NULL, DEFAULT FALSE | |
| `push_sent_at` | TIMESTAMPTZ | NULL | |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Notification Types:**
`DRIVE_PUBLISHED`, `DEADLINE_REMINDER_24H`, `DEADLINE_REMINDER_6H`, `DEADLINE_REMINDER_1H`, `REGISTRATION_CONFIRMED`, `SHORTLISTED`, `STAGE_UPDATED`, `RESULT_PUBLISHED`, `MANUAL_BROADCAST`

**Deduplication index:** `UNIQUE (user_id, notification_type, reference_id)` — prevents the scheduler from inserting duplicate reminders

**Indexes:** `notifications_user_id_idx`, `notifications_is_read_idx`, `notifications_created_at_idx`, `notifications_type_ref_idx`

---

### 3.12 `push_subscriptions`

**Purpose:** Browser push subscription objects per user/device. One user can have multiple active subscriptions (multiple browsers/devices).

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → `users.id`, NOT NULL | |
| `endpoint` | TEXT | UNIQUE, NOT NULL | Browser-vendor push URL |
| `p256dh_key` | TEXT | NOT NULL | Browser's ECDH public key |
| `auth_key` | TEXT | NOT NULL | Auth secret |
| `user_agent` | TEXT | NULL | For debugging |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Set to FALSE when 410 Gone received |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `last_used_at` | TIMESTAMPTZ | NULL | Updated on every successful push |

**Indexes:** `push_subs_user_id_idx`, `push_subs_endpoint_idx` UNIQUE

---

### 3.13 `audit_logs`

**Purpose:** Immutable forensic trail of all state-changing operations.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `performed_by_user_id` | UUID | FK → `users.id`, NULL | NULL for system/scheduler actions |
| `action` | VARCHAR(100) | NOT NULL | e.g., `DRIVE_PUBLISHED`, `STUDENT_REGISTERED` |
| `entity_type` | VARCHAR(50) | NOT NULL | e.g., `DRIVE`, `REGISTRATION`, `USER` |
| `entity_id` | UUID | NULL | ID of the primary affected entity |
| `old_state` | JSONB | NULL | State before the change |
| `new_state` | JSONB | NULL | State after the change |
| `ip_address` | INET | NULL | Client IP (from X-Forwarded-For via LB) |
| `user_agent` | TEXT | NULL | |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

> **Insert-only.** A PostgreSQL trigger raises `EXCEPTION` on any UPDATE or DELETE on this table.

**Indexes:** `audit_logs_user_id_idx`, `audit_logs_entity_idx` (entity_type, entity_id), `audit_logs_action_idx`, `audit_logs_created_at_idx`

---

### 3.14 `system_config`

**Purpose:** Key-value store for institution-level configuration managed by Admin.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `key` | VARCHAR(100) | PK | Config key |
| `value` | TEXT | NOT NULL | Stored as string; cast at application layer |
| `description` | TEXT | NULL | Human-readable explanation of the setting |
| `updated_by_user_id` | UUID | FK → `users.id`, NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Seed data:**

| key | value | description |
|---|---|---|
| `institution_name` | `"Engineering College"` | Displayed in UI and emails |
| `current_academic_year` | `"2025-26"` | Current academic year |
| `max_resume_size_bytes` | `"5242880"` | 5MB in bytes |
| `reminder_windows_hours` | `"[24,6,1]"` | JSON array of reminder windows |
| `registration_reminder_enabled` | `"true"` | Master switch for deadline reminders |

---

## 4. Key Query Patterns & Index Rationale

### Q1: Find all eligible students for a drive (bulk, for notification fan-out)
```sql
SELECT sp.*
FROM student_profiles sp
JOIN users u ON u.id = sp.user_id
WHERE u.is_active = TRUE
  AND u.role = 'STUDENT'
  AND sp.cgpa >= (ec.criteria->>'min_cgpa')::numeric
  AND sp.active_backlogs <= (ec.criteria->>'max_active_backlogs')::integer
  AND sp.branch = ANY(ARRAY(SELECT jsonb_array_elements_text(ec.criteria->'eligible_branches')))
  AND sp.batch_year = ANY(ARRAY(SELECT jsonb_array_elements_text(ec.criteria->'eligible_batch_years')::integer[]))
-- Joins eligibility_criteria for the drive
```
**Indexes used:** `student_profiles_cgpa_idx`, `student_profiles_branch_idx`, `student_profiles_batch_year_idx`

### Q2: Find eligible-but-unregistered students for deadline reminders
```sql
SELECT sp.user_id
FROM student_profiles sp
WHERE <eligibility_conditions>
  AND sp.user_id NOT IN (
    SELECT dr.student_user_id
    FROM drive_registrations dr
    WHERE dr.drive_id = :drive_id AND dr.status = 'REGISTERED'
  )
  AND sp.user_id NOT IN (
    SELECT n.user_id
    FROM notifications n
    WHERE n.notification_type = :reminder_type
      AND n.reference_id = :drive_id
  )
```
**Indexes used:** `registrations_drive_id_idx`, `notifications_type_ref_idx`

### Q3: Student's application dashboard
```sql
SELECT dr.*, pd.title, pd.status, c.name, sa.status as my_stage_status
FROM drive_registrations dr
JOIN placement_drives pd ON pd.id = dr.drive_id
JOIN companies c ON c.id = pd.company_id
LEFT JOIN stage_assignments sa ON sa.drive_id = dr.drive_id AND sa.student_user_id = dr.student_user_id
WHERE dr.student_user_id = :student_id
ORDER BY dr.registered_at DESC
```
**Indexes used:** `registrations_student_idx`, `assignments_drive_id_idx`
