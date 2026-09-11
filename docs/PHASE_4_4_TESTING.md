# Phase 4.4 — Test Automation, E2E & Load Validation Guide

This document outlines the testing architecture, configurations, and procedures introduced in **Phase 4.4** of the CampusFlow project.

---

## 1. Overview & Architecture

Phase 4.4 establishes an automated testing framework covering:
- **Playwright Browser E2E Automation**: End-to-end user workflows across Student, Officer, and Admin personas, verifying client-side routing, notification interactions, and UI states.
- **Locust Load Testing Suite**: Realistic multi-user simulation with weighted traffic distribution (Student 80%, Officer 15%, Admin 5%) designed specifically for local machine execution (16 GB RAM).
- **Synthetic Test Data Seeder**: Deterministic seeding of isolated synthetic test accounts, placement drives, and notifications without any real student PII.
- **API Security & RBAC Regression**: Strict verification of role boundaries, IDOR protections, academic field immutability, audit log immutability triggers, and exact deadline scheduler window boundaries (24h, 6h, 1h).

```
CampusFlow Testing Architecture
├── backend/
│   ├── locustfile.py                              # Locust user load test scenarios
│   ├── scripts/
│   │   ├── run_locust_smoke.py                    # Headless runner for Tier 1/2 local validation
│   │   └── seed_test_env.py                       # Deterministic test environment seeder
│   └── tests/
│       └── integration/
│           ├── test_phase4_rbac_security.py       # RBAC, IDOR & academic field immutability tests
│           └── test_phase4_scheduler_boundaries.py# Exact 24h, 6h, 1h window boundary tests
├── frontend/
│   ├── playwright.config.ts                       # Playwright test runner configuration
│   └── e2e/
│       ├── auth.spec.ts                           # Login, logout, redirects, error alert tests
│       ├── student.spec.ts                        # Student dashboard, notification center tests
│       ├── officer.spec.ts                        # Officer tools, broadcast composer, analytics tests
│       ├── admin.spec.ts                          # User management, bulk import, audit logs tests
│       └── rbac.spec.ts                           # Client-side protected route guards
└── docs/
    └── PHASE_4_4_TESTING.md                       # This guide
```

---

## 2. Safety & Security Invariants

1. **Synthetic Data Only**: All test users use the `@campusflow.edu` domain with synthetic names, roll numbers (`SYN26...`), and sample records. No real student PII is ever used.
2. **No Committed Secrets**: Test passwords use test credentials (`TestAdmin@123`, `TestOfficer@123`, `TestStudent@123`) and mock JWT keys. No production secrets or GCP credentials exist in the codebase.
3. **No Weakening of Security**: Tests verify real backend authorization middleware, role-based checks, and PostgreSQL immutability triggers without bypassing security layers.
4. **Hardware-Aware Local Execution**: Local load tests are bounded to lightweight tiers (10, 25, 50 users) with realistic think times (1–5s) to avoid machine resource exhaustion on 16 GB RAM laptops.

---

## 3. Test Execution Instructions

### A. Backend Pytest Suite

Run all backend tests including unit, integration, RBAC, hardening, and scheduler boundary validations:

```bash
cd backend
venv\Scripts\pytest -v
```

To run only the newly added Phase 4.4 security and boundary tests:

```bash
venv\Scripts\pytest tests/integration/test_phase4_rbac_security.py tests/integration/test_phase4_scheduler_boundaries.py -v
```

### B. Seeding the Test Environment

To seed deterministic synthetic test data for local manual testing or load validation:

```bash
cd backend
venv\Scripts\python scripts/seed_test_env.py
```

This populates:
- **Admin**: `admin@campusflow.edu` / `TestAdmin@123`
- **Officer**: `officer@campusflow.edu` / `TestOfficer@123`
- **Students**: `student1@campusflow.edu` through `student5@campusflow.edu` / `TestStudent@123`
- Standard Branches: CSE, ECE, MECH, CIVIL, IT
- 2 Placement Drives: 1 Published active drive (Acme Tech), 1 Draft drive (Global Motors)
- Sample In-App Notifications

### C. Playwright E2E Browser Tests

From the `frontend/` directory:

1. **Run in Headless Mode**:
   ```bash
   cd frontend
   npm run test:e2e
   ```

2. **Run in Headed (Visible Browser) Mode**:
   ```bash
   npx playwright test --headed
   ```

3. **Run with Playwright UI**:
   ```bash
   npx playwright test --ui
   ```

4. **Run a Specific Spec**:
   ```bash
   npx playwright test e2e/auth.spec.ts
   ```

### D. Locust Load Testing

Run automated lightweight load tests using the headless smoke runner:

1. **Tier 1 Validation (10 concurrent users, spawn rate 2/s, duration 15s)**:
   ```bash
   cd backend
   venv\Scripts\python scripts/run_locust_smoke.py --tier 1
   ```

2. **Tier 2 Validation (25 concurrent users, spawn rate 5/s, duration 25s)**:
   ```bash
   venv\Scripts\python scripts/run_locust_smoke.py --tier 2
   ```

3. **Interactive Web UI Mode**:
   ```bash
   locust -f locustfile.py --host http://127.0.0.1:8000
   ```
   Open `http://localhost:8089` in your browser.

---

## 4. Verification Checklist

- [x] Backend tests: 267 passed, 0 failed, 0 errors
- [x] Frontend production build: `npm run build` succeeds
- [x] Alembic migration heads: exactly 1 head (`0007_audit_logs_immutability`)
- [x] Playwright E2E suites: auth, student, officer, admin, and rbac specs configured
- [x] Locust scenarios: Student (80%), Officer (15%), Admin (5%)
- [x] Zero production credentials or secrets
- [x] Intact Phase 4.1, 4.2, and 4.3 baselines
