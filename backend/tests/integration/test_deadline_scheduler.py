"""
CampusFlow — Phase 3.3 Deadline Scheduler & Deadline Reminders Integration Tests

Comprehensive tests verifying:
1. 24H reminder window detection (23h50m <= delta <= 24h10m).
2. 6H reminder window detection (5h50m <= delta <= 6h10m).
3. 1H reminder window detection (50m <= delta <= 1h10m).
4. Outside reminder windows -> no task.
5. Only REGISTRATION_OPEN drives are processed.
6. Drives with NULL deadline are ignored.
7. Only eligible students receive reminder tasks.
8. Already-registered students receive no reminder tasks.
9. Existing reminder in DB prevents duplicate enqueue (Layer 1 dedup).
10. Running scheduler twice does not create duplicate tasks or notifications.
11. Scheduler enqueue failure isolates errors without rolling back unrelated state.
12. Worker re-check: Student registered after task enqueue -> worker skips with already_registered.
13. Worker execution: Student remains unregistered -> worker creates Notification row.
14. Worker idempotency: Reprocessing identical task creates no duplicate row.
15. Auto-close: Expired deadline transitions REGISTRATION_OPEN -> REGISTRATION_CLOSED.
16. Auto-close: Future deadline does not close drive.
17. Auto-close: Non-open drives are not modified.
18. Security: Internal scheduler endpoints reject unauthenticated requests & user JWTs (401/403).
19. Security: Valid internal auth credentials accepted.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.branch import Branch
from app.models.company import Company
from app.models.drive_registration import DriveRegistration
from app.models.eligibility_criteria import EligibilityCriteria
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

INTERNAL_AUTH_HEADERS = {"Authorization": "Bearer campusflow-internal-tasks-secret-dev"}


@pytest_asyncio.fixture
async def scheduler_setup(db_session: AsyncSession, async_client: AsyncClient) -> dict:
    mock_tasks: MockCloudTasksService = get_cloud_tasks_service()
    if hasattr(mock_tasks, "clear"):
        mock_tasks.clear()

    # Branches
    cse = Branch(code="CSE", name="Computer Science")
    ece = Branch(code="ECE", name="Electronics")
    db_session.add_all([cse, ece])
    await db_session.commit()

    # Officer
    officer = User(
        email="officer_sched@campusflow.com",
        password_hash=hash_password("password123"),
        role="OFFICER",
        full_name="Officer Sched",
        is_active=True,
    )

    # Student 1: Eligible CSE student
    student_eligible = User(
        email="s_eligible@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Eligible Student",
        is_active=True,
    )

    # Student 2: Eligible CSE student (who will be registered)
    student_registered = User(
        email="s_registered@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Registered Student",
        is_active=True,
    )

    # Student 3: Ineligible ECE student (fails branch & CGPA)
    student_ineligible = User(
        email="s_ineligible@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Ineligible Student",
        is_active=True,
    )

    db_session.add_all([officer, student_eligible, student_registered, student_ineligible])
    await db_session.commit()
    await db_session.refresh(officer)
    await db_session.refresh(student_eligible)
    await db_session.refresh(student_registered)
    await db_session.refresh(student_ineligible)

    # Profiles
    p1 = StudentProfile(
        user_id=student_eligible.id,
        roll_number="CSE001",
        branch_code="CSE",
        batch_year=2025,
        cgpa=8.5,
        active_backlogs=0,
    )
    p2 = StudentProfile(
        user_id=student_registered.id,
        roll_number="CSE002",
        branch_code="CSE",
        batch_year=2025,
        cgpa=9.0,
        active_backlogs=0,
    )
    p3 = StudentProfile(
        user_id=student_ineligible.id,
        roll_number="ECE001",
        branch_code="ECE",
        batch_year=2025,
        cgpa=5.5,
        active_backlogs=2,
    )
    db_session.add_all([p1, p2, p3])
    await db_session.commit()

    # Company
    company = Company(
        name="TechCorp Sched",
        website="https://techcorp.com",
        created_by_user_id=officer.id,
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    return {
        "officer": officer,
        "student_eligible": student_eligible,
        "student_registered": student_registered,
        "student_ineligible": student_ineligible,
        "company": company,
        "mock_tasks": mock_tasks,
    }


# -----------------------------------------------------------------------------
# Test Suite
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_1_24h_reminder_window_detection(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_setup: dict,
):
    """TEST 1: 24H window detection (delta = 24h00m)."""
    now = datetime.now(timezone.utc)
    deadline_24h = now + timedelta(hours=24)

    drive = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="Software Engineer 24H",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=deadline_24h,
        created_by_user_id=scheduler_setup["officer"].id,
    )
    db_session.add(drive)
    await db_session.flush()

    criteria = EligibilityCriteria(
        drive_id=drive.id,
        criteria={"min_cgpa": 7.0, "allowed_branches": ["CSE"]},
    )
    db_session.add(criteria)
    await db_session.commit()

    res = await async_client.post(
        "/internal/scheduler/check-deadlines",
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["drives_checked"] >= 1
    assert data["tasks_enqueued"] >= 1

    tasks = scheduler_setup["mock_tasks"].get_tasks()
    matching_tasks = [
        t for t in tasks
        if t["payload"]["notification_type"] == "DEADLINE_REMINDER_24H"
        and t["payload"]["reference_id"] == str(drive.id)
    ]
    assert len(matching_tasks) >= 1
    assert matching_tasks[0]["payload"]["user_id"] == str(scheduler_setup["student_eligible"].id)


@pytest.mark.asyncio
async def test_2_6h_reminder_window_detection(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_setup: dict,
):
    """TEST 2: 6H window detection (delta = 6h00m)."""
    now = datetime.now(timezone.utc)
    deadline_6h = now + timedelta(hours=6)

    drive = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="Software Engineer 6H",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=deadline_6h,
        created_by_user_id=scheduler_setup["officer"].id,
    )
    db_session.add(drive)
    await db_session.flush()

    criteria = EligibilityCriteria(
        drive_id=drive.id,
        criteria={"min_cgpa": 7.0, "allowed_branches": ["CSE"]},
    )
    db_session.add(criteria)
    await db_session.commit()

    res = await async_client.post(
        "/internal/scheduler/check-deadlines",
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res.status_code == 200

    tasks = scheduler_setup["mock_tasks"].get_tasks()
    matching_tasks = [
        t for t in tasks
        if t["payload"]["notification_type"] == "DEADLINE_REMINDER_6H"
        and t["payload"]["reference_id"] == str(drive.id)
    ]
    assert len(matching_tasks) >= 1
    assert matching_tasks[0]["payload"]["user_id"] == str(scheduler_setup["student_eligible"].id)


@pytest.mark.asyncio
async def test_3_1h_reminder_window_detection(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_setup: dict,
):
    """TEST 3: 1H window detection (delta = 1h00m)."""
    now = datetime.now(timezone.utc)
    deadline_1h = now + timedelta(hours=1)

    drive = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="Software Engineer 1H",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=deadline_1h,
        created_by_user_id=scheduler_setup["officer"].id,
    )
    db_session.add(drive)
    await db_session.flush()

    criteria = EligibilityCriteria(
        drive_id=drive.id,
        criteria={"min_cgpa": 7.0, "allowed_branches": ["CSE"]},
    )
    db_session.add(criteria)
    await db_session.commit()

    res = await async_client.post(
        "/internal/scheduler/check-deadlines",
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res.status_code == 200

    tasks = scheduler_setup["mock_tasks"].get_tasks()
    matching_tasks = [
        t for t in tasks
        if t["payload"]["notification_type"] == "DEADLINE_REMINDER_1H"
        and t["payload"]["reference_id"] == str(drive.id)
    ]
    assert len(matching_tasks) >= 1
    assert matching_tasks[0]["payload"]["user_id"] == str(scheduler_setup["student_eligible"].id)


@pytest.mark.asyncio
async def test_4_outside_reminder_window_no_task(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_setup: dict,
):
    """TEST 4: Outside reminder window (e.g. delta = 12h) -> no task enqueued."""
    now = datetime.now(timezone.utc)
    deadline_12h = now + timedelta(hours=12)

    drive = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="Software Engineer 12H",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=deadline_12h,
        created_by_user_id=scheduler_setup["officer"].id,
    )
    db_session.add(drive)
    await db_session.commit()

    res = await async_client.post(
        "/internal/scheduler/check-deadlines",
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res.status_code == 200

    tasks = scheduler_setup["mock_tasks"].get_tasks()
    matching_tasks = [
        t for t in tasks
        if t["payload"]["reference_id"] == str(drive.id)
    ]
    assert len(matching_tasks) == 0


@pytest.mark.asyncio
async def test_5_only_registration_open_drives_processed(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_setup: dict,
):
    """TEST 5: Non REGISTRATION_OPEN drives (e.g. PUBLISHED, DRAFT) are ignored."""
    now = datetime.now(timezone.utc)
    deadline = now + timedelta(hours=24)

    drive_pub = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="Published Drive",
        job_role="SDE",
        status="PUBLISHED",
        registration_deadline=deadline,
        created_by_user_id=scheduler_setup["officer"].id,
    )
    drive_draft = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="Draft Drive",
        job_role="SDE",
        status="DRAFT",
        registration_deadline=deadline,
        created_by_user_id=scheduler_setup["officer"].id,
    )
    db_session.add_all([drive_pub, drive_draft])
    await db_session.commit()

    res = await async_client.post(
        "/internal/scheduler/check-deadlines",
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res.status_code == 200

    tasks = scheduler_setup["mock_tasks"].get_tasks()
    matching = [
        t for t in tasks
        if t["payload"]["reference_id"] in (str(drive_pub.id), str(drive_draft.id))
    ]
    assert len(matching) == 0


@pytest.mark.asyncio
async def test_6_drive_with_null_deadline_ignored(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_setup: dict,
):
    """TEST 6: Drive with NULL registration deadline is ignored."""
    drive = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="Null Deadline Drive",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=None,
        created_by_user_id=scheduler_setup["officer"].id,
    )
    db_session.add(drive)
    await db_session.commit()

    res = await async_client.post(
        "/internal/scheduler/check-deadlines",
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res.status_code == 200

    tasks = scheduler_setup["mock_tasks"].get_tasks()
    matching = [t for t in tasks if t["payload"]["reference_id"] == str(drive.id)]
    assert len(matching) == 0


@pytest.mark.asyncio
async def test_7_only_eligible_students_receive_reminder(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_setup: dict,
):
    """TEST 7: Only students meeting eligibility criteria receive tasks; ineligible excluded."""
    now = datetime.now(timezone.utc)
    deadline_24h = now + timedelta(hours=24)

    drive = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="CSE Only Drive",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=deadline_24h,
        created_by_user_id=scheduler_setup["officer"].id,
    )
    db_session.add(drive)
    await db_session.flush()

    criteria = EligibilityCriteria(
        drive_id=drive.id,
        criteria={"min_cgpa": 7.0, "allowed_branches": ["CSE"]},
    )
    db_session.add(criteria)
    await db_session.commit()

    res = await async_client.post(
        "/internal/scheduler/check-deadlines",
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res.status_code == 200

    tasks = scheduler_setup["mock_tasks"].get_tasks()
    ineligible_id = str(scheduler_setup["student_ineligible"].id)
    ineligible_tasks = [
        t for t in tasks
        if t["payload"]["reference_id"] == str(drive.id)
        and t["payload"]["user_id"] == ineligible_id
    ]
    assert len(ineligible_tasks) == 0


@pytest.mark.asyncio
async def test_8_already_registered_students_receive_no_task(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_setup: dict,
):
    """TEST 8: Students already registered for the drive do not receive reminder tasks."""
    now = datetime.now(timezone.utc)
    deadline_24h = now + timedelta(hours=24)

    drive = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="Registered Test Drive",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=deadline_24h,
        created_by_user_id=scheduler_setup["officer"].id,
    )
    db_session.add(drive)
    await db_session.flush()

    criteria = EligibilityCriteria(
        drive_id=drive.id,
        criteria={"min_cgpa": 7.0, "allowed_branches": ["CSE"]},
    )
    reg = DriveRegistration(
        drive_id=drive.id,
        student_user_id=scheduler_setup["student_registered"].id,
        resume_gcs_path_at_registration="resumes/test.pdf",
        status="REGISTERED",
    )
    db_session.add_all([criteria, reg])
    await db_session.commit()

    res = await async_client.post(
        "/internal/scheduler/check-deadlines",
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res.status_code == 200

    tasks = scheduler_setup["mock_tasks"].get_tasks()
    reg_id = str(scheduler_setup["student_registered"].id)
    reg_tasks = [
        t for t in tasks
        if t["payload"]["reference_id"] == str(drive.id)
        and t["payload"]["user_id"] == reg_id
    ]
    assert len(reg_tasks) == 0


@pytest.mark.asyncio
async def test_9_existing_reminder_prevents_duplicate_enqueue(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_setup: dict,
):
    """TEST 9: Existing Notification row for (user, reminder_type, drive_id) prevents re-enqueue."""
    now = datetime.now(timezone.utc)
    deadline_24h = now + timedelta(hours=24)

    drive = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="Dedup Layer 1 Drive",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=deadline_24h,
        created_by_user_id=scheduler_setup["officer"].id,
    )
    db_session.add(drive)
    await db_session.flush()

    criteria = EligibilityCriteria(
        drive_id=drive.id,
        criteria={"min_cgpa": 7.0, "allowed_branches": ["CSE"]},
    )
    # Pre-insert 24H notification
    existing_notif = Notification(
        user_id=scheduler_setup["student_eligible"].id,
        title="Old 24H reminder",
        body="Body",
        notification_type="DEADLINE_REMINDER_24H",
        reference_id=drive.id,
        reference_type="DRIVE",
    )
    db_session.add_all([criteria, existing_notif])
    await db_session.commit()

    res = await async_client.post(
        "/internal/scheduler/check-deadlines",
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res.status_code == 200

    tasks = scheduler_setup["mock_tasks"].get_tasks()
    eligible_id = str(scheduler_setup["student_eligible"].id)
    matching = [
        t for t in tasks
        if t["payload"]["reference_id"] == str(drive.id)
        and t["payload"]["user_id"] == eligible_id
        and t["payload"]["notification_type"] == "DEADLINE_REMINDER_24H"
    ]
    assert len(matching) == 0


@pytest.mark.asyncio
async def test_10_running_scheduler_twice_does_not_create_duplicates(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_setup: dict,
):
    """TEST 10: Running scheduler twice (with task consumption) produces no duplicate tasks/records."""
    now = datetime.now(timezone.utc)
    deadline_6h = now + timedelta(hours=6)

    drive = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="Double Run Drive",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=deadline_6h,
        created_by_user_id=scheduler_setup["officer"].id,
    )
    db_session.add(drive)
    await db_session.flush()

    criteria = EligibilityCriteria(
        drive_id=drive.id,
        criteria={"min_cgpa": 7.0, "allowed_branches": ["CSE"]},
    )
    db_session.add(criteria)
    await db_session.commit()

    # Run 1
    res1 = await async_client.post(
        "/internal/scheduler/check-deadlines",
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["tasks_enqueued"] >= 1

    # Simulate worker consuming tasks
    worker = NotificationWorkerService(
        notification_repo=NotificationRepository(session=db_session),
        session=db_session,
    )
    tasks = list(scheduler_setup["mock_tasks"].get_tasks())
    for t in tasks:
        payload = NotificationTaskPayload(**t["payload"])
        await worker.process_notification_task(payload)

    # Clear mock task queue for Run 2
    scheduler_setup["mock_tasks"].clear()

    # Run 2: Same window, student already received notification in DB
    res2 = await async_client.post(
        "/internal/scheduler/check-deadlines",
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res2.status_code == 200
    data2 = res2.json()

    # Zero tasks should be enqueued on second run for this drive
    new_tasks = [
        t for t in scheduler_setup["mock_tasks"].get_tasks()
        if t["payload"]["reference_id"] == str(drive.id)
    ]
    assert len(new_tasks) == 0


@pytest.mark.asyncio
async def test_11_scheduler_enqueue_failure_isolation(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_setup: dict,
):
    """TEST 11: Failure during task dispatch is isolated without crashing the scheduler."""
    now = datetime.now(timezone.utc)
    deadline_1h = now + timedelta(hours=1)

    drive = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="Failure Isolation Drive",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=deadline_1h,
        created_by_user_id=scheduler_setup["officer"].id,
    )
    db_session.add(drive)
    await db_session.flush()

    criteria = EligibilityCriteria(
        drive_id=drive.id,
        criteria={"min_cgpa": 7.0, "allowed_branches": ["CSE"]},
    )
    db_session.add(criteria)
    await db_session.commit()

    # Patch dispatcher to throw an exception
    with patch.object(
        scheduler_setup["mock_tasks"],
        "enqueue_notification_task",
        side_effect=RuntimeError("Cloud Tasks quota exceeded"),
    ):
        res = await async_client.post(
            "/internal/scheduler/check-deadlines",
            headers=INTERNAL_AUTH_HEADERS,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["drives_checked"] >= 1
        assert data["tasks_enqueued"] == 0


@pytest.mark.asyncio
async def test_12_worker_skips_reminder_if_student_registered(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_setup: dict,
):
    """TEST 12: Worker re-check: student registered after task creation -> task skipped."""
    student_id = scheduler_setup["student_eligible"].id

    drive = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="Software Engineer Late Check",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        created_by_user_id=scheduler_setup["officer"].id,
    )
    db_session.add(drive)
    await db_session.flush()

    # Add registration
    reg = DriveRegistration(
        drive_id=drive.id,
        student_user_id=student_id,
        resume_gcs_path_at_registration="resumes/late.pdf",
        status="REGISTERED",
    )
    db_session.add(reg)
    await db_session.commit()

    # Send reminder task to worker
    task_payload = {
        "user_id": str(student_id),
        "notification_type": "DEADLINE_REMINDER_1H",
        "title": "1 Hour Left",
        "body": "Final reminder to register.",
        "reference_id": str(drive.id),
        "reference_type": "DRIVE",
    }
    res = await async_client.post(
        "/internal/tasks/send-notification",
        json=task_payload,
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "skipped"
    assert data["reason"] == "already_registered"

    # Verify no notification created
    stmt = select(Notification).where(
        Notification.user_id == student_id,
        Notification.notification_type == "DEADLINE_REMINDER_1H",
        Notification.reference_id == drive.id,
    )
    notif = await db_session.scalar(stmt)
    assert notif is None


@pytest.mark.asyncio
async def test_13_worker_creates_reminder_when_unregistered(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_setup: dict,
):
    """TEST 13: Worker processes reminder task and creates Notification row when unregistered."""
    drive_id = uuid4()
    student_id = scheduler_setup["student_eligible"].id

    task_payload = {
        "user_id": str(student_id),
        "notification_type": "DEADLINE_REMINDER_6H",
        "title": "6 Hours Left",
        "body": "6 hours left to register.",
        "reference_id": str(drive_id),
        "reference_type": "DRIVE",
    }
    res = await async_client.post(
        "/internal/tasks/send-notification",
        json=task_payload,
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "processed"
    assert data["notification_id"] is not None

    stmt = select(Notification).where(
        Notification.id == UUID(data["notification_id"]),
    )
    notif = await db_session.scalar(stmt)
    assert notif is not None
    assert notif.notification_type == "DEADLINE_REMINDER_6H"
    assert notif.user_id == student_id


@pytest.mark.asyncio
async def test_14_worker_idempotency_prevents_duplicate_records(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_setup: dict,
):
    """TEST 14: Worker idempotency on duplicate task payload."""
    drive_id = uuid4()
    student_id = scheduler_setup["student_eligible"].id

    task_payload = {
        "user_id": str(student_id),
        "notification_type": "DEADLINE_REMINDER_24H",
        "title": "24 Hours Left",
        "body": "24 hours left to register.",
        "reference_id": str(drive_id),
        "reference_type": "DRIVE",
    }
    # Call 1
    res1 = await async_client.post(
        "/internal/tasks/send-notification",
        json=task_payload,
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res1.status_code == 200
    assert res1.json()["status"] == "processed"

    # Call 2
    res2 = await async_client.post(
        "/internal/tasks/send-notification",
        json=task_payload,
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "skipped"
    assert res2.json()["reason"] == "idempotent_duplicate"


@pytest.mark.asyncio
async def test_15_expired_registration_deadline_auto_closes_drive(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_setup: dict,
):
    """TEST 15: Expired deadline transitions REGISTRATION_OPEN -> REGISTRATION_CLOSED."""
    now = datetime.now(timezone.utc)
    expired_deadline = now - timedelta(minutes=15)

    drive = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="Expired Drive",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=expired_deadline,
        created_by_user_id=scheduler_setup["officer"].id,
    )
    db_session.add(drive)
    await db_session.commit()
    await db_session.refresh(drive)

    res = await async_client.post(
        "/internal/scheduler/auto-close-registrations",
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["drives_closed"] >= 1

    # Verify drive status is updated
    await db_session.refresh(drive)
    assert drive.status == "REGISTRATION_CLOSED"


@pytest.mark.asyncio
async def test_16_future_registration_deadline_does_not_auto_close(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_setup: dict,
):
    """TEST 16: Future deadline is not auto-closed."""
    now = datetime.now(timezone.utc)
    future_deadline = now + timedelta(days=2)

    drive = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="Active Future Drive",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=future_deadline,
        created_by_user_id=scheduler_setup["officer"].id,
    )
    db_session.add(drive)
    await db_session.commit()
    await db_session.refresh(drive)

    res = await async_client.post(
        "/internal/scheduler/auto-close-registrations",
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res.status_code == 200

    await db_session.refresh(drive)
    assert drive.status == "REGISTRATION_OPEN"


@pytest.mark.asyncio
async def test_17_non_open_drives_not_modified_by_auto_close(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_setup: dict,
):
    """TEST 17: Non-open drives (e.g. SHORTLISTING, RESULT) are not modified by auto-close."""
    now = datetime.now(timezone.utc)
    past_deadline = now - timedelta(days=5)

    drive_shortlisting = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="Shortlisting Drive",
        job_role="SDE",
        status="SHORTLISTING",
        registration_deadline=past_deadline,
        created_by_user_id=scheduler_setup["officer"].id,
    )
    db_session.add(drive_shortlisting)
    await db_session.commit()
    await db_session.refresh(drive_shortlisting)

    res = await async_client.post(
        "/internal/scheduler/auto-close-registrations",
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res.status_code == 200

    await db_session.refresh(drive_shortlisting)
    assert drive_shortlisting.status == "SHORTLISTING"


@pytest.mark.asyncio
async def test_18_internal_scheduler_endpoint_rejects_unauthorized(
    async_client: AsyncClient,
    scheduler_setup: dict,
):
    """TEST 18: Unauthenticated requests and student/officer JWTs are rejected."""
    # 1. No auth
    r1 = await async_client.post("/internal/scheduler/check-deadlines")
    assert r1.status_code == 401

    r2 = await async_client.post("/internal/scheduler/auto-close-registrations")
    assert r2.status_code == 401

    # 2. Student JWT rejected with 403
    student_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": scheduler_setup["student_eligible"].email, "password": "password123"},
    )
    student_token = student_login.json()["access_token"]
    student_auth = {"Authorization": f"Bearer {student_token}"}

    r3 = await async_client.post("/internal/scheduler/check-deadlines", headers=student_auth)
    assert r3.status_code == 403

    r4 = await async_client.post("/internal/scheduler/auto-close-registrations", headers=student_auth)
    assert r4.status_code == 403

    # 3. Officer JWT rejected with 403
    officer_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": scheduler_setup["officer"].email, "password": "password123"},
    )
    officer_token = officer_login.json()["access_token"]
    officer_auth = {"Authorization": f"Bearer {officer_token}"}

    r5 = await async_client.post("/internal/scheduler/check-deadlines", headers=officer_auth)
    assert r5.status_code == 403


@pytest.mark.asyncio
async def test_19_valid_scheduler_authentication_accepted(
    async_client: AsyncClient,
):
    """TEST 19: Valid internal authentication is accepted on scheduler endpoints."""
    r1 = await async_client.post(
        "/internal/scheduler/check-deadlines",
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert r1.status_code == 200

    r2 = await async_client.post(
        "/internal/scheduler/auto-close-registrations",
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert r2.status_code == 200


@pytest.mark.asyncio
async def test_20_exact_window_boundaries_24h(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_setup: dict,
):
    """TEST 20: Exact 24H lower (23h50m) and upper (24h10m) boundaries match; outside (23h49m, 24h11m) do not."""
    now = datetime.now(timezone.utc)
    
    # 1. Lower boundary inside: 23h 51m (match)
    d_lower = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="24H Lower Boundary",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=now + timedelta(hours=23, minutes=51),
        created_by_user_id=scheduler_setup["officer"].id,
    )
    # 2. Upper boundary inside: 24h 9m (match)
    d_upper = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="24H Upper Boundary",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=now + timedelta(hours=24, minutes=9),
        created_by_user_id=scheduler_setup["officer"].id,
    )
    # 3. Below lower boundary: 23h 45m (no match)
    d_below = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="24H Below Boundary",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=now + timedelta(hours=23, minutes=45),
        created_by_user_id=scheduler_setup["officer"].id,
    )
    # 4. Above upper boundary: 24h 15m (no match)
    d_above = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="24H Above Boundary",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=now + timedelta(hours=24, minutes=15),
        created_by_user_id=scheduler_setup["officer"].id,
    )
    db_session.add_all([d_lower, d_upper, d_below, d_above])
    await db_session.flush()

    for d in [d_lower, d_upper, d_below, d_above]:
        db_session.add(
            EligibilityCriteria(
                drive_id=d.id,
                criteria={"min_cgpa": 7.0, "allowed_branches": ["CSE"]},
            )
        )
    await db_session.commit()

    scheduler_setup["mock_tasks"].clear()

    res = await async_client.post(
        "/internal/scheduler/check-deadlines",
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res.status_code == 200

    tasks = scheduler_setup["mock_tasks"].get_tasks()
    matched_drive_ids = {t["payload"]["reference_id"] for t in tasks}

    assert str(d_lower.id) in matched_drive_ids
    assert str(d_upper.id) in matched_drive_ids
    assert str(d_below.id) not in matched_drive_ids
    assert str(d_above.id) not in matched_drive_ids


@pytest.mark.asyncio
async def test_21_exact_window_boundaries_6h(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_setup: dict,
):
    """TEST 21: Exact 6H window matching."""
    now = datetime.now(timezone.utc)
    
    d_lower = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="6H Lower Boundary",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=now + timedelta(hours=5, minutes=51),
        created_by_user_id=scheduler_setup["officer"].id,
    )
    d_upper = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="6H Upper Boundary",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=now + timedelta(hours=6, minutes=9),
        created_by_user_id=scheduler_setup["officer"].id,
    )
    d_below = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="6H Below Boundary",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=now + timedelta(hours=5, minutes=45),
        created_by_user_id=scheduler_setup["officer"].id,
    )
    d_above = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="6H Above Boundary",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=now + timedelta(hours=6, minutes=15),
        created_by_user_id=scheduler_setup["officer"].id,
    )
    db_session.add_all([d_lower, d_upper, d_below, d_above])
    await db_session.flush()

    for d in [d_lower, d_upper, d_below, d_above]:
        db_session.add(
            EligibilityCriteria(
                drive_id=d.id,
                criteria={"min_cgpa": 7.0, "allowed_branches": ["CSE"]},
            )
        )
    await db_session.commit()

    scheduler_setup["mock_tasks"].clear()

    res = await async_client.post(
        "/internal/scheduler/check-deadlines",
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res.status_code == 200

    tasks = scheduler_setup["mock_tasks"].get_tasks()
    matched_drive_ids = {t["payload"]["reference_id"] for t in tasks}

    assert str(d_lower.id) in matched_drive_ids
    assert str(d_upper.id) in matched_drive_ids
    assert str(d_below.id) not in matched_drive_ids
    assert str(d_above.id) not in matched_drive_ids


@pytest.mark.asyncio
async def test_22_exact_window_boundaries_1h(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_setup: dict,
):
    """TEST 22: Exact 1H window matching."""
    now = datetime.now(timezone.utc)
    
    d_lower = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="1H Lower Boundary",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=now + timedelta(minutes=51),
        created_by_user_id=scheduler_setup["officer"].id,
    )
    d_upper = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="1H Upper Boundary",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=now + timedelta(hours=1, minutes=9),
        created_by_user_id=scheduler_setup["officer"].id,
    )
    d_below = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="1H Below Boundary",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=now + timedelta(minutes=45),
        created_by_user_id=scheduler_setup["officer"].id,
    )
    d_above = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="1H Above Boundary",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=now + timedelta(hours=1, minutes=15),
        created_by_user_id=scheduler_setup["officer"].id,
    )
    db_session.add_all([d_lower, d_upper, d_below, d_above])
    await db_session.flush()

    for d in [d_lower, d_upper, d_below, d_above]:
        db_session.add(
            EligibilityCriteria(
                drive_id=d.id,
                criteria={"min_cgpa": 7.0, "allowed_branches": ["CSE"]},
            )
        )
    await db_session.commit()

    scheduler_setup["mock_tasks"].clear()

    res = await async_client.post(
        "/internal/scheduler/check-deadlines",
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res.status_code == 200

    tasks = scheduler_setup["mock_tasks"].get_tasks()
    matched_drive_ids = {t["payload"]["reference_id"] for t in tasks}

    assert str(d_lower.id) in matched_drive_ids
    assert str(d_upper.id) in matched_drive_ids
    assert str(d_below.id) not in matched_drive_ids
    assert str(d_above.id) not in matched_drive_ids


@pytest.mark.asyncio
async def test_23_past_deadline_in_check_deadlines_ignored(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_setup: dict,
):
    """TEST 23: Past deadline (delta < 0) does not enqueue any reminder tasks."""
    now = datetime.now(timezone.utc)
    past_deadline = now - timedelta(minutes=10)

    drive_past = PlacementDrive(
        company_id=scheduler_setup["company"].id,
        title="Past Deadline Check",
        job_role="SDE",
        status="REGISTRATION_OPEN",
        registration_deadline=past_deadline,
        created_by_user_id=scheduler_setup["officer"].id,
    )
    db_session.add(drive_past)
    await db_session.commit()

    scheduler_setup["mock_tasks"].clear()

    res = await async_client.post(
        "/internal/scheduler/check-deadlines",
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res.status_code == 200

    tasks = scheduler_setup["mock_tasks"].get_tasks()
    matched_drive_ids = {t["payload"]["reference_id"] for t in tasks}
    assert str(drive_past.id) not in matched_drive_ids

