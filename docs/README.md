# CampusFlow — Engineering Blueprint

> **Status:** Planning phase complete. Approved for implementation.  
> **Last Updated:** 2026-08-27

CampusFlow is a College Placement Management & Opportunity Assurance Platform that replaces the WhatsApp + Google Forms workflow with a centralized, structured system.

---

## 📄 Blueprint Documents

| Document | Description |
|---|---|
| [REQUIREMENTS.md](./REQUIREMENTS.md) | User roles, functional requirements, NFRs, out-of-scope |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | GCP topology, component breakdown, system diagrams, data flows |
| [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) | 14 PostgreSQL tables, ERD diagram, JSONB eligibility design |
| [API_SPEC.md](./API_SPEC.md) | ~40 REST endpoints with request/response schemas |
| [SECURITY.md](./SECURITY.md) | Auth, RBAC, file security, OWASP mitigations, audit logging |
| [NOTIFICATION_ARCHITECTURE.md](./NOTIFICATION_ARCHITECTURE.md) | Cloud Tasks async pipeline, deadline reminders, VAPID browser push |
| [DEVELOPMENT_PLAN.md](./DEVELOPMENT_PLAN.md) | 4 phases, Gantt chart, repo structure, tech stack, Definition of Done |
| [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) | Master summary, architecture risks, open questions, approval record |

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript + Vite |
| Backend | FastAPI + Python 3.11 |
| Database | PostgreSQL 15 (Cloud SQL) |
| File Storage | Google Cloud Storage (private) |
| Task Queue | Google Cloud Tasks |
| Scheduler | Google Cloud Scheduler |
| Compute | Google Cloud Run (stateless, containerized) |
| Secrets | Google Secret Manager |
| Auth | JWT RS256 + bcrypt |

---

## 🚀 Development Phases

| Phase | Focus | Duration |
|---|---|---|
| Phase 1 | Auth · Profiles · Companies · Drives · Eligibility Engine | ~6 weeks |
| Phase 2 | Registration · Resume Upload · Stages · Shortlisting · Results | ~5 weeks |
| Phase 3 | Async Notifications · Deadline Reminders · Browser Push · Analytics | ~5 weeks |
| Phase 4 | Security Audit · Load Testing · Staging · Production Launch | ~4 weeks |

---

## ⚠️ Key Architectural Decisions

- **Eligibility Engine** is purely deterministic (no AI). Criteria stored as JSONB per drive.
- **Notifications** are fully asynchronous via Cloud Tasks — no synchronous fan-out.
- **Student documents** are stored in a private GCS bucket; access is always via signed URLs.
- **Authorization** is enforced server-side on every endpoint — frontend auth is UI-only.
- **WhatsApp is not removed immediately** — CampusFlow becomes the source of truth first.
