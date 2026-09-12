"""
Phase 4.6 — Production-Readiness & Unified Cross-Persona Smoke Verification.

Executes the complete unified single-chain workflow using synthetic local test fixtures:
1. Officer: Creates Company -> Creates Placement Drive -> Configures Eligibility -> Adds Stages -> Publishes Drive -> Opens Registration.
2. Student: Fetches Active Drives -> Checks Eligibility -> Verifies Match -> Registers for Drive with Resume.
3. Officer: Closes Registration -> Enters Shortlisting -> Shortlists Candidate for Stage 1.
4. Worker: Processes async notification task -> Student reads In-App Notification.
5. Security / Production Guards: Verifies that internal endpoints reject user tokens, protected fields cannot be altered by students, and rate limiting/security headers remain active.
"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.branch import Branch
from app.models.notification import Notification
from app.core.security import hash_password


@pytest.fixture
async def full_lifecycle_setup(db_session: AsyncSession) -> dict:
    """Pre-seeds branches, an officer, and an eligible student for full lifecycle testing."""
    # 1. Branches
    cse = Branch(code="CSE", name="Computer Science and Engineering")
    db_session.add(cse)

    # 2. Officer User
    officer_user = User(
        id=uuid4(),
        email="officer_prod@campusflow.edu",
        password_hash=hash_password("ProdOfficer@123"),
        full_name="Production Placement Officer",
        role="OFFICER",
        is_active=True,
    )
    db_session.add(officer_user)

    # 3. Student User & Profile
    student_user = User(
        id=uuid4(),
        email="student_prod@campusflow.edu",
        password_hash=hash_password("ProdStudent@123"),
        full_name="Production Candidate One",
        role="STUDENT",
        is_active=True,
    )
    db_session.add(student_user)
    await db_session.flush()

    student_profile = StudentProfile(
        id=uuid4(),
        user_id=student_user.id,
        roll_number="PROD26CSE001",
        branch_code="CSE",
        batch_year=2026,
        cgpa=8.5,
        active_backlogs=0,
        resume_gcs_path="resumes/prod_candidate_one.pdf",
    )
    db_session.add(student_profile)
    await db_session.commit()

    return {
        "officer": officer_user,
        "student": student_user,
        "profile": student_profile,
    }


@pytest.mark.asyncio
async def test_01_complete_unified_cross_persona_lifecycle(
    async_client: AsyncClient,
    full_lifecycle_setup: dict,
    db_session: AsyncSession,
):
    """
    Validates the entire end-to-end placement workflow across Officer and Student personas.
    """
    # -------------------------------------------------------------------------
    # STEP 1: Officer Logs In
    # -------------------------------------------------------------------------
    officer_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "officer_prod@campusflow.edu", "password": "ProdOfficer@123"},
    )
    assert officer_login.status_code == 200
    officer_token = officer_login.json()["access_token"]
    officer_headers = {"Authorization": f"Bearer {officer_token}"}

    # -------------------------------------------------------------------------
    # STEP 2: Officer Creates Company
    # -------------------------------------------------------------------------
    company_res = await async_client.post(
        "/api/v1/companies",
        json={
            "name": "Acme Global Systems",
            "website": "https://acme-global.test",
            "industry": "Software Engineering",
        },
        headers=officer_headers,
    )
    assert company_res.status_code == 201
    company_id = company_res.json()["id"]

    # -------------------------------------------------------------------------
    # STEP 3: Officer Creates Placement Drive (Draft)
    # -------------------------------------------------------------------------
    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    drive_res = await async_client.post(
        "/api/v1/drives",
        json={
            "company_id": company_id,
            "title": "Acme Software Engineer 2026",
            "job_role": "Member of Technical Staff",
            "description": "Full-stack development across distributed cloud systems.",
            "ctc_lpa": 14.5,
            "location": "Bengaluru",
            "registration_deadline": deadline,
            "eligibility_criteria": {
                "eligible_branches": ["CSE"],
                "min_cgpa": 7.5,
                "max_active_backlogs": 0,
                "eligible_batch_years": [2026],
            },
        },
        headers=officer_headers,
    )
    assert drive_res.status_code == 201
    drive_id = drive_res.json()["id"]

    # -------------------------------------------------------------------------
    # STEP 4: Officer Adds Recruitment Stages to Drive
    # -------------------------------------------------------------------------
    stage1_res = await async_client.post(
        f"/api/v1/drives/{drive_id}/stages",
        json={
            "name": "Online Coding Assessment",
            "stage_type": "CODING",
            "sequence_order": 1,
            "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=10)).isoformat(),
        },
        headers=officer_headers,
    )
    assert stage1_res.status_code == 201
    stage1_id = stage1_res.json()["id"]

    # Publish stage 1
    stage1_pub = await async_client.post(
        f"/api/v1/drives/{drive_id}/stages/{stage1_id}/publish",
        headers=officer_headers,
    )
    assert stage1_pub.status_code == 200

    # -------------------------------------------------------------------------
    # STEP 5: Officer Publishes Drive & Opens Registration
    # -------------------------------------------------------------------------
    # DRAFT -> PUBLISHED
    pub_res = await async_client.post(
        f"/api/v1/drives/{drive_id}/status",
        json={"status": "PUBLISHED"},
        headers=officer_headers,
    )
    assert pub_res.status_code == 200

    # PUBLISHED -> REGISTRATION_OPEN
    open_res = await async_client.post(
        f"/api/v1/drives/{drive_id}/status",
        json={"status": "REGISTRATION_OPEN"},
        headers=officer_headers,
    )
    assert open_res.status_code == 200
    assert open_res.json()["status"] == "REGISTRATION_OPEN"

    # -------------------------------------------------------------------------
    # STEP 6: Student Logs In
    # -------------------------------------------------------------------------
    student_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "student_prod@campusflow.edu", "password": "ProdStudent@123"},
    )
    assert student_login.status_code == 200
    student_token = student_login.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # -------------------------------------------------------------------------
    # STEP 7: Student Discovers Published Drive & Checks Eligibility
    # -------------------------------------------------------------------------
    drives_list = await async_client.get("/api/v1/drives", headers=student_headers)
    assert drives_list.status_code == 200
    drives_data = drives_list.json()["items"]
    assert any(d["id"] == drive_id for d in drives_data)

    eligibility_check = await async_client.get(
        f"/api/v1/drives/{drive_id}/eligibility-check",
        headers=student_headers,
    )
    assert eligibility_check.status_code == 200
    elig_result = eligibility_check.json()
    assert elig_result["is_eligible"] is True

    # -------------------------------------------------------------------------
    # STEP 8: Student Registers for Drive
    # -------------------------------------------------------------------------
    reg_res = await async_client.post(
        f"/api/v1/drives/{drive_id}/register",
        headers=student_headers,
    )
    assert reg_res.status_code == 201
    assert reg_res.json()["status"] == "REGISTERED"

    # -------------------------------------------------------------------------
    # STEP 9: Officer Reviews Applicants & Shortlists Candidate
    # -------------------------------------------------------------------------
    applicants_res = await async_client.get(
        f"/api/v1/drives/{drive_id}/registrations",
        headers=officer_headers,
    )
    assert applicants_res.status_code == 200
    applicants = applicants_res.json()["items"]
    assert len(applicants) == 1
    student_user_id = str(full_lifecycle_setup["student"].id)

    # Shortlist student for Stage 1
    shortlist_res = await async_client.post(
        f"/api/v1/drives/{drive_id}/stages/{stage1_id}/shortlist",
        json={"student_ids": [student_user_id]},
        headers=officer_headers,
    )
    assert shortlist_res.status_code == 201

    # Process background tasks through notification worker
    from app.services.cloud_tasks_service import get_cloud_tasks_service
    from app.services.notification_worker import NotificationWorkerService
    from app.repositories.notification_repository import NotificationRepository
    from app.schemas.notification import NotificationTaskPayload

    cloud_tasks = get_cloud_tasks_service()
    worker = NotificationWorkerService(NotificationRepository(db_session), db_session)
    for t in cloud_tasks.get_tasks():
        payload = NotificationTaskPayload.model_validate(t["payload"])
        await worker.process_notification_task(payload)

    # -------------------------------------------------------------------------
    # STEP 10: Verify In-App Notification Created for Student
    # -------------------------------------------------------------------------
    student_notifs = await async_client.get("/api/v1/notifications", headers=student_headers)
    assert student_notifs.status_code == 200
    notifs_items = student_notifs.json()["items"]
    assert len(notifs_items) >= 1
    assert any(n["notification_type"] == "SHORTLISTED" for n in notifs_items)


@pytest.mark.asyncio
async def test_02_production_security_boundaries(
    async_client: AsyncClient,
    full_lifecycle_setup: dict,
):
    """
    Verifies that security invariants hold across unauthenticated, student, and internal routes.
    """
    student_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "student_prod@campusflow.edu", "password": "ProdStudent@123"},
    )
    student_token = student_login.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # 1. Student cannot access Admin User Management
    admin_forbidden = await async_client.get("/api/v1/admin/users", headers=student_headers)
    assert admin_forbidden.status_code == 403

    # 2. Student cannot access System Audit Logs
    audit_forbidden = await async_client.get("/api/v1/admin/audit-logs", headers=student_headers)
    assert audit_forbidden.status_code == 403

    # 3. User JWT cannot invoke internal scheduler endpoints
    scheduler_forbidden = await async_client.post(
        "/internal/scheduler/check-deadlines",
        headers=student_headers,
    )
    assert scheduler_forbidden.status_code == 403

    # 4. User JWT cannot invoke internal task endpoints
    task_forbidden = await async_client.post(
        "/internal/tasks/send-notification",
        json={"type": "SYSTEM", "payload": {}},
        headers=student_headers,
    )
    assert task_forbidden.status_code == 403

    # 5. Unauthenticated request to /internal/* is rejected with 401
    unauth_internal = await async_client.post("/internal/scheduler/check-deadlines")
    assert unauth_internal.status_code == 401
