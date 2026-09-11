"""
CampusFlow — Phase 3.2 Event -> Async Notifications Integration Tests

Tests covering:
1. DRAFT -> PUBLISHED enqueues DRIVE_PUBLISHED tasks for eligible students only.
2. Non-publication transition does not enqueue DRIVE_PUBLISHED.
3. Registration enqueues exactly one REGISTRATION_CONFIRMED task.
4. Shortlisting enqueues SHORTLISTED tasks for newly shortlisted students.
5. Published stage update enqueues STAGE_UPDATED tasks.
6. Draft/unpublished stage update does not enqueue STAGE_UPDATED.
7. Result publication enqueues RESULT_PUBLISHED tasks for assigned students.
8. Post-commit Cloud Tasks failure does not rollback the already committed business state.
9. Worker processes queued tasks and creates Notification rows.
10. Reprocessing the same task is idempotent and creates no duplicate Notification.
11. Correct user, reference_id, reference_type payloads for all 5 events.
12. Ineligible students receive no DRIVE_PUBLISHED task.
"""
from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.branch import Branch
from app.models.company import Company
from app.models.notification import Notification
from app.models.placement_drive import PlacementDrive
from app.models.placement_stage import PlacementStage
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import NotificationTaskPayload
from app.services.cloud_tasks_service import (
    MockCloudTasksService,
    get_cloud_tasks_service,
)
from app.services.notification_worker import NotificationWorkerService


@pytest_asyncio.fixture
async def setup_data(db_session: AsyncSession, async_client: AsyncClient) -> dict:
    mock_tasks: MockCloudTasksService = get_cloud_tasks_service()
    if hasattr(mock_tasks, "clear"):
        mock_tasks.clear()

    # Create Branch
    branch = Branch(code="CSE", name="Computer Science")
    branch_ece = Branch(code="ECE", name="Electronics")
    db_session.add_all([branch, branch_ece])
    await db_session.commit()

    # Create Users
    officer = User(
        email="officer_p32@campusflow.com",
        password_hash=hash_password("password123"),
        role="OFFICER",
        full_name="Officer Phase32",
        is_active=True,
    )
    student_eligible_1 = User(
        email="s1_p32@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Student 1 Eligible",
        is_active=True,
    )
    student_eligible_2 = User(
        email="s2_p32@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Student 2 Eligible",
        is_active=True,
    )
    student_ineligible = User(
        email="s3_p32@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Student 3 Ineligible",
        is_active=True,
    )

    db_session.add_all([officer, student_eligible_1, student_eligible_2, student_ineligible])
    await db_session.commit()
    await db_session.refresh(officer)
    await db_session.refresh(student_eligible_1)
    await db_session.refresh(student_eligible_2)
    await db_session.refresh(student_ineligible)

    # Create Profiles
    prof1 = StudentProfile(
        user_id=student_eligible_1.id,
        roll_number="CSE001",
        branch_code="CSE",
        batch_year=2025,
        cgpa=8.5,
        active_backlogs=0,
        gender="MALE",
        resume_gcs_path="resumes/s1/resume.pdf",
    )
    prof2 = StudentProfile(
        user_id=student_eligible_2.id,
        roll_number="CSE002",
        branch_code="CSE",
        batch_year=2025,
        cgpa=7.8,
        active_backlogs=0,
        gender="FEMALE",
        resume_gcs_path="resumes/s2/resume.pdf",
    )
    prof3 = StudentProfile(
        user_id=student_ineligible.id,
        roll_number="ECE001",
        branch_code="ECE",
        batch_year=2025,
        cgpa=5.5,  # Low CGPA + Wrong branch
        active_backlogs=2,
        gender="MALE",
        resume_gcs_path="resumes/s3/resume.pdf",
    )
    db_session.add_all([prof1, prof2, prof3])

    # Create Company
    company = Company(
        name="Google",
        website="https://google.com",
        industry="Technology",
        description="Search & Cloud",
        created_by_user_id=officer.id,
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)


    # Login
    r_officer = await async_client.post(
        "/api/v1/auth/login",
        json={"email": officer.email, "password": "password123"},
    )
    r_s1 = await async_client.post(
        "/api/v1/auth/login",
        json={"email": student_eligible_1.email, "password": "password123"},
    )
    r_s2 = await async_client.post(
        "/api/v1/auth/login",
        json={"email": student_eligible_2.email, "password": "password123"},
    )

    return {
        "officer_headers": {"Authorization": f"Bearer {r_officer.json()['access_token']}"},
        "s1_headers": {"Authorization": f"Bearer {r_s1.json()['access_token']}"},
        "s2_headers": {"Authorization": f"Bearer {r_s2.json()['access_token']}"},
        "officer": officer,
        "s1": student_eligible_1,
        "s2": student_eligible_2,
        "s3": student_ineligible,
        "company": company,
        "mock_tasks": mock_tasks,
    }


# -----------------------------------------------------------------------------
# 1. DRIVE_PUBLISHED Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_drive_published_enqueues_tasks_for_eligible_students_only(
    async_client: AsyncClient,
    setup_data: dict,
):
    mock_tasks: MockCloudTasksService = setup_data["mock_tasks"]
    mock_tasks.clear()

    # 1. Create drive in DRAFT
    drive_payload = {
        "company_id": str(setup_data["company"].id),
        "title": "Software Engineer 2025",
        "job_role": "SDE",
        "registration_deadline": "2026-12-31T23:59:59Z",
        "eligibility_criteria": {
            "min_cgpa": 7.0,
            "max_active_backlogs": 0,
            "eligible_branches": ["CSE"],
        },
    }
    create_resp = await async_client.post(
        "/api/v1/drives",
        json=drive_payload,
        headers=setup_data["officer_headers"],
    )
    assert create_resp.status_code == 201
    drive_id = create_resp.json()["id"]

    assert len(mock_tasks.get_tasks()) == 0

    # 2. Transition DRAFT -> PUBLISHED
    pub_resp = await async_client.post(
        f"/api/v1/drives/{drive_id}/status",
        json={"status": "PUBLISHED"},
        headers=setup_data["officer_headers"],
    )
    assert pub_resp.status_code == 200

    # 3. Verify exactly 2 DRIVE_PUBLISHED tasks enqueued (for s1 and s2, NOT s3)
    tasks = mock_tasks.get_tasks()
    drive_tasks = [t for t in tasks if t["payload"]["notification_type"] == "DRIVE_PUBLISHED"]
    assert len(drive_tasks) == 2

    task_user_ids = {t["payload"]["user_id"] for t in drive_tasks}
    assert str(setup_data["s1"].id) in task_user_ids
    assert str(setup_data["s2"].id) in task_user_ids
    assert str(setup_data["s3"].id) not in task_user_ids

    # Verify task payload content
    first_task = drive_tasks[0]["payload"]
    assert first_task["reference_id"] == drive_id
    assert first_task["reference_type"] == "DRIVE"
    assert first_task["title"] == "New Placement Drive: Software Engineer 2025"
    assert "Google is hiring for SDE" in first_task["body"]


@pytest.mark.asyncio
async def test_non_publish_transition_does_not_enqueue_drive_published(
    async_client: AsyncClient,
    setup_data: dict,
):
    mock_tasks: MockCloudTasksService = setup_data["mock_tasks"]
    mock_tasks.clear()

    # Create drive and publish it
    drive_payload = {
        "company_id": str(setup_data["company"].id),
        "title": "Data Analyst 2025",
        "job_role": "DA",
        "registration_deadline": "2026-12-31T23:59:59Z",
        "eligibility_criteria": {},
    }
    r = await async_client.post("/api/v1/drives", json=drive_payload, headers=setup_data["officer_headers"])
    drive_id = r.json()["id"]

    await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "PUBLISHED"}, headers=setup_data["officer_headers"])
    mock_tasks.clear()

    # Transition PUBLISHED -> REGISTRATION_OPEN
    r_open = await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "REGISTRATION_OPEN"}, headers=setup_data["officer_headers"])
    assert r_open.status_code == 200

    # No DRIVE_PUBLISHED tasks should be enqueued on this transition
    drive_tasks = [t for t in mock_tasks.get_tasks() if t["payload"]["notification_type"] == "DRIVE_PUBLISHED"]
    assert len(drive_tasks) == 0


# -----------------------------------------------------------------------------
# 2. REGISTRATION_CONFIRMED Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_registration_confirmed_enqueues_task(
    async_client: AsyncClient,
    setup_data: dict,
):
    mock_tasks: MockCloudTasksService = setup_data["mock_tasks"]
    mock_tasks.clear()

    # Create and open drive
    drive_payload = {
        "company_id": str(setup_data["company"].id),
        "title": "Frontend Engineer 2025",
        "job_role": "Frontend",
        "registration_deadline": "2026-12-31T23:59:59Z",
        "eligibility_criteria": {},
    }
    r = await async_client.post("/api/v1/drives", json=drive_payload, headers=setup_data["officer_headers"])
    drive_id = r.json()["id"]

    await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "PUBLISHED"}, headers=setup_data["officer_headers"])
    await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "REGISTRATION_OPEN"}, headers=setup_data["officer_headers"])
    mock_tasks.clear()

    # Student 1 registers
    r_reg = await async_client.post(f"/api/v1/drives/{drive_id}/register", headers=setup_data["s1_headers"])
    assert r_reg.status_code == 201

    # Exactly 1 REGISTRATION_CONFIRMED task enqueued
    reg_tasks = [t for t in mock_tasks.get_tasks() if t["payload"]["notification_type"] == "REGISTRATION_CONFIRMED"]
    assert len(reg_tasks) == 1
    task_payload = reg_tasks[0]["payload"]
    assert task_payload["user_id"] == str(setup_data["s1"].id)
    assert task_payload["reference_id"] == drive_id
    assert task_payload["reference_type"] == "DRIVE"
    assert task_payload["title"] == "Registration Confirmed: Frontend Engineer 2025"
    assert "successfully registered" in task_payload["body"]


# -----------------------------------------------------------------------------
# 3. SHORTLISTED Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_shortlisting_enqueues_shortlisted_tasks(
    async_client: AsyncClient,
    setup_data: dict,
):
    mock_tasks: MockCloudTasksService = setup_data["mock_tasks"]
    mock_tasks.clear()

    # Setup drive + registrations
    drive_payload = {
        "company_id": str(setup_data["company"].id),
        "title": "Backend Engineer 2025",
        "job_role": "Backend",
        "registration_deadline": "2026-12-31T23:59:59Z",
        "eligibility_criteria": {},
    }
    r = await async_client.post("/api/v1/drives", json=drive_payload, headers=setup_data["officer_headers"])
    drive_id = r.json()["id"]
    await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "PUBLISHED"}, headers=setup_data["officer_headers"])
    await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "REGISTRATION_OPEN"}, headers=setup_data["officer_headers"])

    # Register both s1 and s2
    await async_client.post(f"/api/v1/drives/{drive_id}/register", headers=setup_data["s1_headers"])
    await async_client.post(f"/api/v1/drives/{drive_id}/register", headers=setup_data["s2_headers"])

    # Create stage
    r_stage = await async_client.post(
        f"/api/v1/drives/{drive_id}/stages",
        json={"name": "Coding Assessment", "stage_type": "CODING", "sequence_order": 1},
        headers=setup_data["officer_headers"],
    )
    stage_id = r_stage.json()["id"]

    mock_tasks.clear()

    # Shortlist both s1 and s2
    r_short = await async_client.post(
        f"/api/v1/drives/{drive_id}/stages/{stage_id}/shortlist",
        json={"student_ids": [str(setup_data["s1"].id), str(setup_data["s2"].id)]},
        headers=setup_data["officer_headers"],
    )
    assert r_short.status_code == 201

    short_tasks = [t for t in mock_tasks.get_tasks() if t["payload"]["notification_type"] == "SHORTLISTED"]
    assert len(short_tasks) == 2
    recipients = {t["payload"]["user_id"] for t in short_tasks}
    assert str(setup_data["s1"].id) in recipients
    assert str(setup_data["s2"].id) in recipients
    assert short_tasks[0]["payload"]["reference_id"] == stage_id
    assert short_tasks[0]["payload"]["reference_type"] == "PLACEMENT_STAGE"
    assert "Shortlisted: Coding Assessment" in short_tasks[0]["payload"]["title"]


# -----------------------------------------------------------------------------
# 4. STAGE_UPDATED Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stage_updated_enqueues_tasks_only_when_published(
    async_client: AsyncClient,
    setup_data: dict,
):
    mock_tasks: MockCloudTasksService = setup_data["mock_tasks"]
    mock_tasks.clear()

    # Create drive and stage
    drive_payload = {
        "company_id": str(setup_data["company"].id),
        "title": "DevOps Engineer 2025",
        "job_role": "DevOps",
        "registration_deadline": "2026-12-31T23:59:59Z",
        "eligibility_criteria": {},
    }
    r = await async_client.post("/api/v1/drives", json=drive_payload, headers=setup_data["officer_headers"])
    drive_id = r.json()["id"]
    await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "PUBLISHED"}, headers=setup_data["officer_headers"])
    await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "REGISTRATION_OPEN"}, headers=setup_data["officer_headers"])
    await async_client.post(f"/api/v1/drives/{drive_id}/register", headers=setup_data["s1_headers"])

    # Create stage in DRAFT
    r_stage = await async_client.post(
        f"/api/v1/drives/{drive_id}/stages",
        json={"name": "Tech Interview", "stage_type": "TECHNICAL", "sequence_order": 1},
        headers=setup_data["officer_headers"],
    )
    stage_id = r_stage.json()["id"]

    # Shortlist student
    await async_client.post(
        f"/api/v1/drives/{drive_id}/stages/{stage_id}/shortlist",
        json={"student_ids": [str(setup_data["s1"].id)]},
        headers=setup_data["officer_headers"],
    )
    mock_tasks.clear()

    # 1. Update stage while STILL UNPUBLISHED (DRAFT)
    r_update_draft = await async_client.patch(
        f"/api/v1/drives/{drive_id}/stages/{stage_id}",
        json={"location_or_link": "Room 101"},
        headers=setup_data["officer_headers"],
    )
    assert r_update_draft.status_code == 200
    # No STAGE_UPDATED tasks should be sent for draft stages
    stage_updated_tasks = [t for t in mock_tasks.get_tasks() if t["payload"]["notification_type"] == "STAGE_UPDATED"]
    assert len(stage_updated_tasks) == 0

    # 2. Publish stage
    await async_client.post(f"/api/v1/drives/{drive_id}/stages/{stage_id}/publish", headers=setup_data["officer_headers"])
    mock_tasks.clear()

    # 3. Update stage when PUBLISHED
    r_update_pub = await async_client.patch(
        f"/api/v1/drives/{drive_id}/stages/{stage_id}",
        json={"location_or_link": "Room 202 - Updated"},
        headers=setup_data["officer_headers"],
    )
    assert r_update_pub.status_code == 200

    # Now exactly 1 STAGE_UPDATED task should be enqueued for s1
    pub_stage_tasks = [t for t in mock_tasks.get_tasks() if t["payload"]["notification_type"] == "STAGE_UPDATED"]
    assert len(pub_stage_tasks) == 1
    assert pub_stage_tasks[0]["payload"]["user_id"] == str(setup_data["s1"].id)
    assert pub_stage_tasks[0]["payload"]["reference_id"] == stage_id
    assert pub_stage_tasks[0]["payload"]["reference_type"] == "PLACEMENT_STAGE"
    assert "Stage Schedule Updated: Tech Interview" in pub_stage_tasks[0]["payload"]["title"]


# -----------------------------------------------------------------------------
# 5. RESULT_PUBLISHED Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_publish_results_enqueues_result_published_tasks(
    async_client: AsyncClient,
    setup_data: dict,
):
    mock_tasks: MockCloudTasksService = setup_data["mock_tasks"]
    mock_tasks.clear()

    # Setup drive, stage, registration, and shortlist
    drive_payload = {
        "company_id": str(setup_data["company"].id),
        "title": "Fullstack Engineer 2025",
        "job_role": "Fullstack",
        "registration_deadline": "2026-12-31T23:59:59Z",
        "eligibility_criteria": {},
    }
    r = await async_client.post("/api/v1/drives", json=drive_payload, headers=setup_data["officer_headers"])
    drive_id = r.json()["id"]
    await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "PUBLISHED"}, headers=setup_data["officer_headers"])
    await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "REGISTRATION_OPEN"}, headers=setup_data["officer_headers"])
    await async_client.post(f"/api/v1/drives/{drive_id}/register", headers=setup_data["s1_headers"])

    r_stage = await async_client.post(
        f"/api/v1/drives/{drive_id}/stages",
        json={"name": "HR Round", "stage_type": "HR", "sequence_order": 1},
        headers=setup_data["officer_headers"],
    )
    stage_id = r_stage.json()["id"]

    await async_client.post(
        f"/api/v1/drives/{drive_id}/stages/{stage_id}/shortlist",
        json={"student_ids": [str(setup_data["s1"].id)]},
        headers=setup_data["officer_headers"],
    )
    mock_tasks.clear()

    # Publish results
    r_pub_res = await async_client.post(
        f"/api/v1/drives/{drive_id}/stages/{stage_id}/publish-results",
        headers=setup_data["officer_headers"],
    )
    assert r_pub_res.status_code == 200

    result_tasks = [t for t in mock_tasks.get_tasks() if t["payload"]["notification_type"] == "RESULT_PUBLISHED"]
    assert len(result_tasks) == 1
    assert result_tasks[0]["payload"]["user_id"] == str(setup_data["s1"].id)
    assert result_tasks[0]["payload"]["reference_id"] == stage_id
    assert result_tasks[0]["payload"]["reference_type"] == "PLACEMENT_STAGE"
    assert "Stage Results Published: HR Round" in result_tasks[0]["payload"]["title"]


# -----------------------------------------------------------------------------
# 6. Post-Commit Error Isolation & Worker Idempotency
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_commit_enqueue_failure_does_not_rollback_db(
    async_client: AsyncClient,
    setup_data: dict,
    monkeypatch: pytest.MonkeyPatch,
    db_session: AsyncSession,
):
    mock_tasks: MockCloudTasksService = setup_data["mock_tasks"]

    # Mock enqueue_notification_task to simulate unexpected Cloud Tasks service failure
    async def mock_fail_enqueue(*args, **kwargs):
        raise RuntimeError("Cloud Tasks network timeout simulation")

    monkeypatch.setattr(mock_tasks, "enqueue_notification_task", mock_fail_enqueue)

    drive_payload = {
        "company_id": str(setup_data["company"].id),
        "title": "Cloud Engineer 2025",
        "job_role": "Cloud",
        "registration_deadline": "2026-12-31T23:59:59Z",
        "eligibility_criteria": {},
    }
    r = await async_client.post("/api/v1/drives", json=drive_payload, headers=setup_data["officer_headers"])
    drive_id = r.json()["id"]

    # Transition to PUBLISHED should succeed in DB even if task enqueue fails post-commit
    r_pub = await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "PUBLISHED"}, headers=setup_data["officer_headers"])
    assert r_pub.status_code == 200
    assert r_pub.json()["status"] == "PUBLISHED"


@pytest.mark.asyncio
async def test_end_to_end_worker_execution_and_idempotency(
    db_session: AsyncSession,
    setup_data: dict,
):
    worker = NotificationWorkerService(NotificationRepository(db_session), db_session)
    user_id = setup_data["s1"].id
    ref_id = uuid4()

    task = NotificationTaskPayload(
        user_id=user_id,
        title="New Drive: Test",
        body="Test notification body",
        notification_type="DRIVE_PUBLISHED",
        reference_id=ref_id,
        reference_type="DRIVE",
    )

    # 1. First execution creates DB record
    res1 = await worker.process_notification_task(task)
    assert res1.status == "processed"
    assert res1.notification_id is not None

    # 2. Duplicate retry skips without error
    res2 = await worker.process_notification_task(task)
    assert res2.status == "skipped"
    assert res2.reason == "idempotent_duplicate"
    assert res2.notification_id == res1.notification_id

    # Verify only 1 notification in DB
    stmt = select(Notification).where(
        Notification.user_id == user_id,
        Notification.notification_type == "DRIVE_PUBLISHED",
        Notification.reference_id == ref_id,
    )
    result = await db_session.execute(stmt)
    assert len(result.scalars().all()) == 1
