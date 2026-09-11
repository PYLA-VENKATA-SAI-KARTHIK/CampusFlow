"""
Integration tests for Phase 2.5 — Shortlisting & Results API.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.branch import Branch
from app.models.drive_registration import DriveRegistration
from app.models.notification import Notification
from app.models.placement_drive import PlacementDrive
from app.models.placement_stage import PlacementStage
from app.models.stage_assignment import StageAssignment
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.core.security import hash_password


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def auth_users(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> dict:
    """Create a student and an officer, returning their auth headers."""
    student = User(
        email="short_student@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Short Student",
        is_active=True,
    )
    officer = User(
        email="short_officer@campusflow.com",
        password_hash=hash_password("password123"),
        role="OFFICER",
        full_name="Short Officer",
        is_active=True,
    )
    db_session.add_all([student, officer])
    await db_session.commit()
    await db_session.refresh(student)
    await db_session.refresh(officer)

    r_student = await async_client.post(
        "/api/v1/auth/login",
        json={"email": student.email, "password": "password123"},
    )
    r_officer = await async_client.post(
        "/api/v1/auth/login",
        json={"email": officer.email, "password": "password123"},
    )

    return {
        "student": {"Authorization": f"Bearer {r_student.json()['access_token']}"},
        "officer": {"Authorization": f"Bearer {r_officer.json()['access_token']}"},
        "student_obj": student,
        "officer_obj": officer,
    }


@pytest_asyncio.fixture
async def test_company(async_client: AsyncClient, auth_users: dict) -> str:
    response = await async_client.post(
        "/api/v1/companies",
        json={"name": "Short Company", "industry": "Tech"},
        headers=auth_users["officer"],
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


@pytest_asyncio.fixture
async def published_drive(
    async_client: AsyncClient,
    auth_users: dict,
    test_company: str,
) -> str:
    """Create a drive and advance it to PUBLISHED status."""
    create_resp = await async_client.post(
        "/api/v1/drives",
        json={
            "company_id": test_company,
            "title": "Shortlist Drive",
            "job_role": "SDE",
            "eligibility_criteria": {},
        },
        headers=auth_users["officer"],
    )
    assert create_resp.status_code == 201, create_resp.text
    drive_id = create_resp.json()["id"]

    # DRAFT → REGISTRATION_OPEN
    await async_client.post(
        f"/api/v1/drives/{drive_id}/status",
        json={"status": "REGISTRATION_OPEN"},
        headers=auth_users["officer"],
    )

    return drive_id


@pytest_asyncio.fixture
async def student_registration(
    db_session: AsyncSession,
    auth_users: dict,
    published_drive: str,
) -> User:
    """Create a student profile and register the student for the drive."""
    student = auth_users["student_obj"]

    branch = Branch(code="SHT", name="Short Branch")
    db_session.add(branch)
    await db_session.commit()

    profile = StudentProfile(
        user_id=student.id,
        roll_number="SHT001",
        branch_code="SHT",
        batch_year=2024,
        cgpa=8.0,
        active_backlogs=0,
        resume_gcs_path="gs://bucket/resume.pdf",
    )
    db_session.add(profile)

    reg = DriveRegistration(
        drive_id=published_drive,
        student_user_id=student.id,
        resume_gcs_path_at_registration="gs://bucket/resume.pdf",
        status="REGISTERED",
    )
    db_session.add(reg)
    await db_session.commit()

    return student


@pytest_asyncio.fixture
async def active_stage(
    async_client: AsyncClient,
    auth_users: dict,
    published_drive: str,
) -> dict:
    """Create and publish a placement stage for the drive."""
    create_resp = await async_client.post(
        f"/api/v1/drives/{published_drive}/stages",
        json={"name": "Aptitude Test", "stage_type": "APTITUDE", "sequence_order": 1},
        headers=auth_users["officer"],
    )
    assert create_resp.status_code == 201, create_resp.text
    stage_id = create_resp.json()["id"]

    pub_resp = await async_client.post(
        f"/api/v1/drives/{published_drive}/stages/{stage_id}/publish",
        headers=auth_users["officer"],
    )
    assert pub_resp.status_code == 200, pub_resp.text

    return {"id": stage_id, "drive_id": published_drive}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_shortlist_students_success(
    async_client: AsyncClient,
    auth_users: dict,
    published_drive: str,
    active_stage: dict,
    student_registration: User,
    db_session: AsyncSession,
):
    """Officer can shortlist a registered student; creates assignment + notification."""
    student_id = str(student_registration.id)

    response = await async_client.post(
        f"/api/v1/drives/{published_drive}/stages/{active_stage['id']}/shortlist",
        headers=auth_users["officer"],
        json={"student_ids": [student_id]},
    )

    assert response.status_code == 201, response.text

    # Assignment created with SHORTLISTED status
    assignment = (await db_session.execute(select(StageAssignment))).scalar_one()
    assert assignment.status == "SHORTLISTED"

    # Process enqueued tasks through the worker service
    from app.services.cloud_tasks_service import get_cloud_tasks_service
    from app.services.notification_worker import NotificationWorkerService
    from app.repositories.notification_repository import NotificationRepository
    from app.schemas.notification import NotificationTaskPayload

    cloud_tasks = get_cloud_tasks_service()
    worker = NotificationWorkerService(NotificationRepository(db_session), db_session)
    for t in cloud_tasks.get_tasks():
        payload = NotificationTaskPayload.model_validate(t["payload"])
        await worker.process_notification_task(payload)

    # Notification created
    notif = (await db_session.execute(select(Notification))).scalar_one()
    assert notif.notification_type == "SHORTLISTED"



@pytest.mark.asyncio
async def test_shortlist_students_not_registered(
    async_client: AsyncClient,
    auth_users: dict,
    published_drive: str,
    active_stage: dict,
):
    """Shortlisting a student who is not registered for the drive should fail with 422."""
    # student_obj is authenticated but NOT registered (student_registration fixture not used)
    student_id = str(auth_users["student_obj"].id)

    response = await async_client.post(
        f"/api/v1/drives/{published_drive}/stages/{active_stage['id']}/shortlist",
        headers=auth_users["officer"],
        json={"student_ids": [student_id]},
    )

    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_update_stage_assignment_success(
    async_client: AsyncClient,
    auth_users: dict,
    published_drive: str,
    active_stage: dict,
    student_registration: User,
    db_session: AsyncSession,
):
    """Officer can update an assignment status and add result notes."""
    student_id = str(student_registration.id)

    # First shortlist the student
    await async_client.post(
        f"/api/v1/drives/{published_drive}/stages/{active_stage['id']}/shortlist",
        headers=auth_users["officer"],
        json={"student_ids": [student_id]},
    )

    # Update assignment to SELECTED
    response = await async_client.patch(
        f"/api/v1/drives/{published_drive}/stages/{active_stage['id']}/assignments/{student_id}",
        headers=auth_users["officer"],
        json={"status": "SELECTED", "result_notes": "Great performance"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "SELECTED"
    assert data["result_notes"] == "Great performance"


@pytest.mark.asyncio
async def test_update_assignment_student_forbidden(
    async_client: AsyncClient,
    auth_users: dict,
    published_drive: str,
    active_stage: dict,
    student_registration: User,
):
    """Students cannot update assignment statuses."""
    student_id = str(student_registration.id)

    # First shortlist
    await async_client.post(
        f"/api/v1/drives/{published_drive}/stages/{active_stage['id']}/shortlist",
        headers=auth_users["officer"],
        json={"student_ids": [student_id]},
    )

    # Student tries to update own assignment
    response = await async_client.patch(
        f"/api/v1/drives/{published_drive}/stages/{active_stage['id']}/assignments/{student_id}",
        headers=auth_users["student"],
        json={"status": "SELECTED"},
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_publish_results_creates_notifications(
    async_client: AsyncClient,
    auth_users: dict,
    published_drive: str,
    active_stage: dict,
    student_registration: User,
    db_session: AsyncSession,
):
    """publish-results dispatches RESULT_PUBLISHED notifications; calling again is idempotent."""
    from app.services.cloud_tasks_service import get_cloud_tasks_service
    from app.services.notification_worker import NotificationWorkerService
    from app.repositories.notification_repository import NotificationRepository
    from app.schemas.notification import NotificationTaskPayload

    cloud_tasks = get_cloud_tasks_service()
    if hasattr(cloud_tasks, "clear"):
        cloud_tasks.clear()

    student_id = str(student_registration.id)

    # Shortlist the student (dispatches SHORTLISTED notification task)
    await async_client.post(
        f"/api/v1/drives/{published_drive}/stages/{active_stage['id']}/shortlist",
        headers=auth_users["officer"],
        json={"student_ids": [student_id]},
    )

    # Publish results (dispatches RESULT_PUBLISHED notification task)
    response = await async_client.post(
        f"/api/v1/drives/{published_drive}/stages/{active_stage['id']}/publish-results",
        headers=auth_users["officer"],
    )

    assert response.status_code == 200, response.text

    # Process all enqueued tasks through the worker service
    worker = NotificationWorkerService(NotificationRepository(db_session), db_session)
    for t in cloud_tasks.get_tasks():
        payload = NotificationTaskPayload.model_validate(t["payload"])
        await worker.process_notification_task(payload)

    # Verify both notification types exist in DB
    notifs = (await db_session.execute(select(Notification))).scalars().all()
    types = [n.notification_type for n in notifs]
    assert "SHORTLISTED" in types
    assert "RESULT_PUBLISHED" in types

    # Calling publish-results again is idempotent (no duplicate notifications)
    response2 = await async_client.post(
        f"/api/v1/drives/{published_drive}/stages/{active_stage['id']}/publish-results",
        headers=auth_users["officer"],
    )
    assert response2.status_code == 200, response2.text

    for t in cloud_tasks.get_tasks():
        payload = NotificationTaskPayload.model_validate(t["payload"])
        await worker.process_notification_task(payload)

    notifs_after = (await db_session.execute(select(Notification))).scalars().all()
    result_published_notifs = [n for n in notifs_after if n.notification_type == "RESULT_PUBLISHED"]
    assert len(result_published_notifs) == 1  # idempotent — still only one



@pytest.mark.asyncio
async def test_publish_results_student_forbidden(
    async_client: AsyncClient,
    auth_users: dict,
    published_drive: str,
    active_stage: dict,
):
    """Students cannot call publish-results."""
    response = await async_client.post(
        f"/api/v1/drives/{published_drive}/stages/{active_stage['id']}/publish-results",
        headers=auth_users["student"],
    )
    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_stage_assignment_idor_protection(
    async_client: AsyncClient,
    auth_users: dict,
    published_drive: str,
    student_registration: User,
    active_stage: dict,
    test_company: str,
    db_session: AsyncSession,
):
    """Shortlisting a student for a stage belonging to a different drive should fail."""
    student_id = str(student_registration.id)

    # Create a second drive and a stage on it
    other_drive_resp = await async_client.post(
        "/api/v1/drives",
        json={
            "company_id": test_company,
            "title": "Other IDOR Drive",
            "job_role": "QA",
            "eligibility_criteria": {},
        },
        headers=auth_users["officer"],
    )
    assert other_drive_resp.status_code == 201, other_drive_resp.text
    other_drive_id = other_drive_resp.json()["id"]

    other_stage_resp = await async_client.post(
        f"/api/v1/drives/{other_drive_id}/stages",
        json={"name": "Other Stage", "stage_type": "APTITUDE", "sequence_order": 1},
        headers=auth_users["officer"],
    )
    assert other_stage_resp.status_code == 201, other_stage_resp.text
    other_stage_id = other_stage_resp.json()["id"]

    # Attempt to shortlist for other_stage_id under published_drive (wrong drive context)
    response = await async_client.post(
        f"/api/v1/drives/{published_drive}/stages/{other_stage_id}/shortlist",
        headers=auth_users["officer"],
        json={"student_ids": [student_id]},
    )

    # Stage does not belong to published_drive → 404
    assert response.status_code == 404, response.text
