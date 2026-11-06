"""
CampusFlow — Placement Drive Email Notifications Integration Tests

Verifies:
1. When a drive is published (DRAFT -> PUBLISHED), DRIVE_PUBLISHED tasks with send_email=True
   are enqueued exclusively for eligible students (ineligible students are excluded).
2. NotificationWorkerService retrieves the student's primary university email (user.email)
   and drive details, and sends the drive announcement email via EmailService.
3. NotificationWorkerService deduplication prevents duplicate emails on retried/repeated tasks.
4. Email delivery failures are safely isolated without rolling back in-app notification creation.
"""
from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email import DriveNotificationEmailData, MockEmailAdapter
from app.core.security import hash_password
from app.models.branch import Branch
from app.models.company import Company
from app.models.notification import Notification
from app.models.placement_drive import PlacementDrive
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
async def drive_email_setup(db_session: AsyncSession, async_client: AsyncClient) -> dict:
    mock_tasks: MockCloudTasksService = get_cloud_tasks_service()
    if hasattr(mock_tasks, "clear"):
        mock_tasks.clear()

    # Create Branches
    branch_cse = Branch(code="CSE_EMAIL", name="Computer Science Email")
    branch_me = Branch(code="ME_EMAIL", name="Mechanical Email")
    db_session.add_all([branch_cse, branch_me])
    await db_session.commit()

    # Create Officer
    officer = User(
        email="officer_email_test@campusflow.com",
        password_hash=hash_password("DevPass123!"),
        role="OFFICER",
        full_name="Placement Officer Email Test",
        is_active=True,
    )
    # Create Eligible Student 1 (CSE, CGPA 8.5, 0 backlogs)
    s1_email = "99230040001@klu.ac.in"
    s1 = User(
        email=s1_email,
        password_hash=hash_password("DevPass123!"),
        role="STUDENT",
        full_name="Eligible Student One",
        is_active=True,
    )
    # Create Eligible Student 2 (CSE, CGPA 7.8, 0 backlogs)
    s2_email = "99230040002@klu.ac.in"
    s2 = User(
        email=s2_email,
        password_hash=hash_password("DevPass123!"),
        role="STUDENT",
        full_name="Eligible Student Two",
        is_active=True,
    )
    # Create Ineligible Student 3 (ME, CGPA 6.0, 1 backlog)
    s3_email = "99230040003@klu.ac.in"
    s3 = User(
        email=s3_email,
        password_hash=hash_password("DevPass123!"),
        role="STUDENT",
        full_name="Ineligible Student Three",
        is_active=True,
    )

    db_session.add_all([officer, s1, s2, s3])
    await db_session.commit()

    p1 = StudentProfile(
        user_id=s1.id,
        roll_number="99230040001",
        branch_code="CSE_EMAIL",
        batch_year=2026,
        cgpa=8.5,
        active_backlogs=0,
    )
    p2 = StudentProfile(
        user_id=s2.id,
        roll_number="99230040002",
        branch_code="CSE_EMAIL",
        batch_year=2026,
        cgpa=7.8,
        active_backlogs=0,
    )
    p3 = StudentProfile(
        user_id=s3.id,
        roll_number="99230040003",
        branch_code="ME_EMAIL",
        batch_year=2026,
        cgpa=6.0,
        active_backlogs=1,
    )

    company = Company(
        name="TechCorp Global",
        website="https://techcorp.com",
        industry="Technology",
        created_by_user_id=officer.id,
    )

    db_session.add_all([p1, p2, p3, company])
    await db_session.commit()

    # Login Officer
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "officer_email_test@campusflow.com", "password": "DevPass123!"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    officer_headers = {"Authorization": f"Bearer {token}"}

    return {
        "officer": officer,
        "officer_headers": officer_headers,
        "s1": s1,
        "s2": s2,
        "s3": s3,
        "p1": p1,
        "p2": p2,
        "p3": p3,
        "company": company,
        "mock_tasks": mock_tasks,
    }


@pytest.mark.asyncio
async def test_drive_published_enqueues_email_for_eligible_students_only(
    async_client: AsyncClient,
    drive_email_setup: dict,
):
    """When a drive transitions DRAFT -> PUBLISHED, email tasks are enqueued for eligible students only."""
    mock_tasks: MockCloudTasksService = drive_email_setup["mock_tasks"]
    mock_tasks.clear()

    # 1. Create drive in DRAFT
    drive_payload = {
        "company_id": str(drive_email_setup["company"].id),
        "title": "Full Stack Engineer 2026",
        "job_role": "Software Engineer",
        "ctc_lpa": 14.5,
        "location": "Hyderabad",
        "registration_deadline": "2026-12-31T23:59:59Z",
        "eligibility_criteria": {
            "min_cgpa": 7.5,
            "max_active_backlogs": 0,
            "eligible_branches": ["CSE_EMAIL"],
        },
    }
    create_resp = await async_client.post(
        "/api/v1/drives",
        json=drive_payload,
        headers=drive_email_setup["officer_headers"],
    )
    assert create_resp.status_code == 201
    drive_id = create_resp.json()["id"]

    assert len(mock_tasks.get_tasks()) == 0

    # 2. Transition DRAFT -> PUBLISHED
    pub_resp = await async_client.post(
        f"/api/v1/drives/{drive_id}/status",
        json={"status": "PUBLISHED"},
        headers=drive_email_setup["officer_headers"],
    )
    assert pub_resp.status_code == 200

    # 3. Verify DRIVE_PUBLISHED tasks enqueued for s1 and s2 (CSE, CGPA >= 7.5), NOT s3
    tasks = mock_tasks.get_tasks()
    drive_tasks = [t for t in tasks if t["payload"]["notification_type"] == "DRIVE_PUBLISHED"]
    assert len(drive_tasks) == 2

    task_user_ids = {t["payload"]["user_id"] for t in drive_tasks}
    assert str(drive_email_setup["s1"].id) in task_user_ids
    assert str(drive_email_setup["s2"].id) in task_user_ids
    assert str(drive_email_setup["s3"].id) not in task_user_ids

    # Verify send_email flag is True
    for t in drive_tasks:
        assert t["payload"]["send_email"] is True
        assert t["payload"]["reference_id"] == drive_id
        assert t["payload"]["reference_type"] == "DRIVE"


@pytest.mark.asyncio
async def test_notification_worker_sends_email_to_student_mail_id(
    db_session: AsyncSession,
    drive_email_setup: dict,
):
    """NotificationWorkerService sends email with correct drive metadata to student's mail ID."""
    mock_email = MockEmailAdapter()
    worker = NotificationWorkerService(
        notification_repo=NotificationRepository(db_session),
        session=db_session,
        email_service=mock_email,
    )

    # Create a published drive in DB
    drive = PlacementDrive(
        company_id=drive_email_setup["company"].id,
        title="AI Engineer 2026",
        job_role="AI Specialist",
        ctc_lpa=18.0,
        location="Bengaluru",
        status="PUBLISHED",
        created_by_user_id=drive_email_setup["officer"].id,
    )
    db_session.add(drive)
    await db_session.commit()
    await db_session.refresh(drive)

    s1_user = drive_email_setup["s1"]
    task = NotificationTaskPayload(
        user_id=s1_user.id,
        title="New Placement Drive: AI Engineer 2026",
        body="TechCorp Global is hiring for AI Specialist.",
        notification_type="DRIVE_PUBLISHED",
        reference_id=drive.id,
        reference_type="DRIVE",
        send_email=True,
    )

    response = await worker.process_notification_task(task)
    assert response.status == "processed"

    # Verify email was sent via mock_email
    assert len(mock_email.sent_drive_emails) == 1
    sent_email = mock_email.sent_drive_emails[0]

    assert sent_email.recipient_email == s1_user.email
    assert sent_email.recipient_name == s1_user.full_name
    assert sent_email.drive_title == "AI Engineer 2026"
    assert sent_email.company_name == "TechCorp Global"
    assert sent_email.job_role == "AI Specialist"
    assert sent_email.ctc_lpa == 18.0
    assert sent_email.location == "Bengaluru"
    assert str(drive.id) in sent_email.drive_url


@pytest.mark.asyncio
async def test_notification_worker_skips_duplicate_email_on_retry(
    db_session: AsyncSession,
    drive_email_setup: dict,
):
    """Retrying the same notification task is idempotent and does NOT send duplicate emails."""
    mock_email = MockEmailAdapter()
    worker = NotificationWorkerService(
        notification_repo=NotificationRepository(db_session),
        session=db_session,
        email_service=mock_email,
    )

    drive_id = uuid4()
    s2_user = drive_email_setup["s2"]
    task = NotificationTaskPayload(
        user_id=s2_user.id,
        title="New Placement Drive: Cloud Architect 2026",
        body="TechCorp Global is hiring for Cloud Architect.",
        notification_type="DRIVE_PUBLISHED",
        reference_id=drive_id,
        reference_type="DRIVE",
        send_email=True,
    )

    # First attempt: processed, email sent
    res1 = await worker.process_notification_task(task)
    assert res1.status == "processed"
    assert len(mock_email.sent_drive_emails) == 1

    # Second attempt (duplicate/retry): skipped, NO additional email sent
    res2 = await worker.process_notification_task(task)
    assert res2.status == "skipped"
    assert res2.reason == "idempotent_duplicate"
    assert len(mock_email.sent_drive_emails) == 1


@pytest.mark.asyncio
async def test_email_failure_isolated_from_notification_persistence(
    db_session: AsyncSession,
    drive_email_setup: dict,
):
    """If email delivery raises an exception, in-app notification is still committed and created."""
    failing_email = MockEmailAdapter()
    failing_email.send_drive_notification_email = AsyncMock(
        side_effect=RuntimeError("SMTP or SendGrid connection error")
    )

    worker = NotificationWorkerService(
        notification_repo=NotificationRepository(db_session),
        session=db_session,
        email_service=failing_email,
    )

    drive_id = uuid4()
    s1_user = drive_email_setup["s1"]
    task = NotificationTaskPayload(
        user_id=s1_user.id,
        title="New Placement Drive: Reliability Engineer 2026",
        body="TechCorp Global is hiring.",
        notification_type="DRIVE_PUBLISHED",
        reference_id=drive_id,
        reference_type="DRIVE",
        send_email=True,
    )

    response = await worker.process_notification_task(task)
    # The worker handles the exception gracefully without failing the task
    assert response.status == "processed"
    assert response.notification_id is not None

    # In-app notification was successfully persisted in the database
    stmt = select(Notification).where(
        Notification.user_id == s1_user.id,
        Notification.notification_type == "DRIVE_PUBLISHED",
        Notification.reference_id == drive_id,
    )
    result = await db_session.execute(stmt)
    saved_notification = result.scalar_one_or_none()
    assert saved_notification is not None
    assert saved_notification.title == "New Placement Drive: Reliability Engineer 2026"


@pytest.mark.asyncio
async def test_drive_registration_open_enqueues_email_notifications(
    async_client: AsyncClient,
    drive_email_setup: dict,
):
    """When an officer updates a drive to REGISTRATION_OPEN, email tasks are dispatched for eligible students."""
    mock_tasks: MockCloudTasksService = drive_email_setup["mock_tasks"]
    mock_tasks.clear()

    drive_payload = {
        "company_id": str(drive_email_setup["company"].id),
        "title": "Cloud Architect 2026",
        "job_role": "Cloud Architect",
        "ctc_lpa": 16.0,
        "location": "Bengaluru",
        "registration_deadline": "2026-12-31T23:59:59Z",
        "eligibility_criteria": {
            "min_cgpa": 7.0,
            "max_active_backlogs": 0,
            "eligible_branches": ["CSE_EMAIL"],
        },
    }
    create_resp = await async_client.post(
        "/api/v1/drives",
        json=drive_payload,
        headers=drive_email_setup["officer_headers"],
    )
    assert create_resp.status_code == 201
    drive_id = create_resp.json()["id"]

    # 1. First Publish: DRAFT -> PUBLISHED
    pub_resp = await async_client.post(
        f"/api/v1/drives/{drive_id}/status",
        json={"status": "PUBLISHED"},
        headers=drive_email_setup["officer_headers"],
    )
    assert pub_resp.status_code == 200
    mock_tasks.clear()

    # 2. Transition PUBLISHED -> REGISTRATION_OPEN
    status_resp = await async_client.post(
        f"/api/v1/drives/{drive_id}/status",
        json={"status": "REGISTRATION_OPEN"},
        headers=drive_email_setup["officer_headers"],
    )
    assert status_resp.status_code == 200

    tasks = mock_tasks.get_tasks()
    # Both s1 and s2 are eligible (CSE, cgpa >= 7.0, 0 backlogs)
    assert len(tasks) == 2
    for t in tasks:
        p = t["payload"]
        assert p["notification_type"] == "REGISTRATION_OPEN"
        assert p["send_email"] is True
        assert "Registration Open" in p["title"]

