# CampusFlow — Product Requirements Document

## 1. Overview

**Product Name:** CampusFlow  
**Type:** College Placement Management & Opportunity Assurance Platform  
**Version:** 1.0 (Blueprint)  
**Date:** 2026-08-27

### 1.1 Problem Statement

College placements are currently managed through an informal, fragmented workflow:

- **Announcements** are sent via WhatsApp groups, where important messages get buried.
- **Registrations** are collected via Google Forms with no automatic eligibility filtering.
- **Tracking** is done manually by placement officers, error-prone and non-scalable.
- **Students miss opportunities** due to notification overload in WhatsApp, missed deadlines, or unawareness of eligibility status.

### 1.2 Product Goal

CampusFlow becomes the **single, persistent source of truth** for all campus placement activity. It:

- Centralizes placement drive information.
- Automates eligibility evaluation based on placement officer–defined criteria.
- Ensures students receive timely, actionable notifications through reliable channels.
- Gives placement officers a structured pipeline to manage the full placement lifecycle.
- Provides administrators with governance, audit, and control capabilities.

### 1.3 What CampusFlow Is NOT

CampusFlow is explicitly **not**:

- A public job portal or internship aggregator
- A LinkedIn-style professional network
- A general recruitment platform (e.g., Unstop)
- An AI chatbot for placement advice
- A replacement for WhatsApp (initially) — WhatsApp continues as an external channel directing students to CampusFlow

---

## 2. User Roles

### 2.1 Student

| Capability | Description |
|---|---|
| Authentication | Log in with college credentials (email + password or SSO) |
| Profile Management | Maintain personal, academic, and resume details |
| Placement Feed | View all published placement drives |
| Eligibility Status | See eligibility per drive with clear reasoning (why eligible / not eligible) |
| Registration | Register for eligible drives within the deadline |
| Resume Upload | Upload resume; stored securely in cloud storage |
| Notifications | Receive in-app and browser push notifications |
| Application Tracking | Track status across all registered drives |
| Stage Updates | View assessment/interview schedules and instructions |
| Results | View placement outcomes |

### 2.2 Placement Officer

| Capability | Description |
|---|---|
| Company Management | Create and manage company profiles |
| Drive Creation | Create placement drives linked to companies |
| Eligibility Configuration | Define dynamic, per-drive eligibility criteria |
| Publishing | Publish drives (controls student visibility) |
| Registrations | View list of students who registered |
| Eligible Student View | View all eligible students before registration deadline |
| Shortlisting | Select students for next stages |
| Stage Management | Create and sequence placement stages (Assessment, Interview, etc.) |
| Scheduling | Set date/time/location/instructions per stage |
| Results Publication | Publish selected/rejected outcomes |
| Notifications | Trigger manual push notifications to eligible students or registered students |
| Analytics | View dashboards on registrations, placement rates, stage funnels |

### 2.3 Admin

| Capability | Description |
|---|---|
| User Management | Create, deactivate, and manage all user accounts |
| Role Assignment | Assign roles: Student, Placement Officer, Admin |
| Permission Management | Control feature-level access per role |
| System Configuration | Manage global settings (institution name, academic year, etc.) |
| Audit Logs | View a complete audit trail of all system actions |

---

## 3. Functional Requirements

### 3.1 Authentication & Authorization

- FR-AUTH-01: All users must authenticate before accessing any resource.
- FR-AUTH-02: Passwords must be hashed using bcrypt (never stored in plaintext).
- FR-AUTH-03: Sessions must use short-lived JWT access tokens + long-lived refresh tokens.
- FR-AUTH-04: Every protected API endpoint must verify the JWT and user role server-side.
- FR-AUTH-05: Students must never be able to access another student's profile or documents.
- FR-AUTH-06: Role-based access must be enforced at the API layer, not only the frontend.

### 3.2 Student Profile

- FR-PROFILE-01: Student profile includes: full name, college roll number, branch, batch year, CGPA, active backlogs, phone number, profile picture.
- FR-PROFILE-02: CGPA and backlog counts must be updatable but versioned (history retained).
- FR-PROFILE-03: Students can upload a resume (PDF only, max 5MB).
- FR-PROFILE-04: Resume files must be stored in Google Cloud Storage with private access (no public URLs).

### 3.3 Placement Drive

- FR-DRIVE-01: A placement drive is linked to exactly one company.
- FR-DRIVE-02: Drives follow the lifecycle: DRAFT → PUBLISHED → REGISTRATION_OPEN → REGISTRATION_CLOSED → SHORTLISTING → ASSESSMENT → INTERVIEW → RESULT → COMPLETED.
- FR-DRIVE-03: Drive details include: job role, description, CTC/stipend, location, bond details, registration deadline, and eligibility criteria.
- FR-DRIVE-04: Only PUBLISHED or later drives are visible to students.
- FR-DRIVE-05: Drives can only move forward through the lifecycle, never backward (except DRAFT → no transition).

### 3.4 Eligibility Engine

- FR-EE-01: Eligibility criteria must be fully configurable per drive by the placement officer.
- FR-EE-02: Supported criteria fields (Phase 1):
  - `min_cgpa` (decimal)
  - `max_active_backlogs` (integer, 0 = zero backlog)
  - `eligible_branches` (list of branch codes)
  - `eligible_batch_years` (list of integers)
  - `gender` (optional filter)
- FR-EE-03: The eligibility engine must evaluate all criteria against the student's profile.
- FR-EE-04: The engine must return: `is_eligible: bool` and `reasons: list[str]` (one reason per failing criterion).
- FR-EE-05: AI must NOT make the final eligibility decision. The engine is deterministic and rule-based.
- FR-EE-06: Eligibility is re-evaluated if a student updates their profile (e.g., CGPA correction) before the deadline.
- FR-EE-07: The eligibility schema must be extensible — new criteria types can be added without breaking existing drives.

### 3.5 Registration

- FR-REG-01: Only eligible students may register for a drive.
- FR-REG-02: Registration is only possible when drive status is `REGISTRATION_OPEN`.
- FR-REG-03: Registration requires a resume to be on file before submission.
- FR-REG-04: Once registered, a student cannot un-register (placement officer can cancel on request).
- FR-REG-05: Duplicate registration attempts must be rejected idempotently.

### 3.6 Placement Stages

- FR-STAGE-01: Placement officers define stages per drive (e.g., Aptitude Test, Technical Interview, HR Interview).
- FR-STAGE-02: Each stage has: name, type, scheduled datetime, location/link, instructions.
- FR-STAGE-03: Students are assigned to a stage when they are shortlisted for it.
- FR-STAGE-04: A student's stage assignment status: SHORTLISTED, APPEARED, SELECTED, REJECTED.
- FR-STAGE-05: Results (SELECTED / REJECTED) must be published per stage.

### 3.7 Notifications

- FR-NOTIF-01: Notifications must be delivered via in-app notifications (always) and browser push (when opted in).
- FR-NOTIF-02: Email and WhatsApp can be added in later phases.
- FR-NOTIF-03: Notification events include:
  - New drive published (eligible students only)
  - Registration deadline approaching (24h / 6h / 1h reminders)
  - Student shortlisted for a stage
  - Stage schedule updated
  - Result published
  - Manual notification from placement officer
- FR-NOTIF-04: Deadline reminders must stop once a student registers.
- FR-NOTIF-05: Notification delivery must be asynchronous — never block an HTTP response.
- FR-NOTIF-06: All notifications must be stored in the database for in-app display.
- FR-NOTIF-07: Browser push uses the Web Push Protocol (VAPID).

### 3.8 Analytics (Placement Officer)

- FR-ANALYTICS-01: Total registrations per drive.
- FR-ANALYTICS-02: Conversion funnel per drive (registered → shortlisted → selected).
- FR-ANALYTICS-03: Branch-wise placement statistics.
- FR-ANALYTICS-04: Overall batch placement percentage.

---

## 4. Non-Functional Requirements

### 4.1 Performance

- NFR-PERF-01: API response times under normal load must be < 500ms for the 95th percentile.
- NFR-PERF-02: Eligibility evaluation for a single student must complete in < 100ms.
- NFR-PERF-03: Bulk eligibility evaluation must be processed asynchronously via Cloud Tasks.

### 4.2 Scalability

- NFR-SCALE-01: The system must support up to 10,000 concurrent students without redesign.
- NFR-SCALE-02: Notification fan-out to thousands of students must use Cloud Tasks task queues.
- NFR-SCALE-03: Cloud Run instances must be stateless and horizontally scalable.

### 4.3 Security

- NFR-SEC-01: All traffic must be over HTTPS.
- NFR-SEC-02: Student documents must never be publicly accessible.
- NFR-SEC-03: Audit logs must capture all state-changing operations.
- NFR-SEC-04: Rate limiting must be enforced at the API gateway or Cloud Run level.
- NFR-SEC-05: Secrets managed via Google Secret Manager.
- NFR-SEC-06: No real student data during development — synthetic test data only.

### 4.4 Reliability

- NFR-REL-01: Target availability of 99.5% during placement seasons.
- NFR-REL-02: Daily database backups with point-in-time recovery enabled.
- NFR-REL-03: Failed notification tasks must be retried with exponential backoff.

### 4.5 Maintainability

- NFR-MAINT-01: All API endpoints documented via OpenAPI/Swagger auto-generation.
- NFR-MAINT-02: Codebase must follow consistent linting and formatting standards.
- NFR-MAINT-03: Database migrations version-controlled using Alembic.

---

## 5. Out of Scope (Phase 1)

- AI-powered features of any kind
- Email notifications (Phase 2)
- WhatsApp integration (Phase 2+)
- Public company job listings
- Alumni network features
- Video interview platform integration
- Offer letter management
- Multi-institution support (single college, Phase 1)
