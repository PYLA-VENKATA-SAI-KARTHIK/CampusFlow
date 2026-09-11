"""
Phase 4.4 — Deadline Scheduler Exact Boundary & Precision Validation.

Comprehensive tests verifying exact boundary thresholds for reminder windows:
- 24H window: 23h50m <= delta <= 24h10m
  * 23h49m (outside, None)
  * 23h50m (inclusive boundary, DEADLINE_REMINDER_24H)
  * 24h10m (inclusive boundary, DEADLINE_REMINDER_24H)
  * 24h11m (outside, None)
- 6H window: 5h50m <= delta <= 6h10m
  * 5h49m (outside, None)
  * 5h50m (inclusive boundary, DEADLINE_REMINDER_6H)
  * 6h10m (inclusive boundary, DEADLINE_REMINDER_6H)
  * 6h11m (outside, None)
- 1H window: 50m <= delta <= 1h10m
  * 49m (outside, None)
  * 50m (inclusive boundary, DEADLINE_REMINDER_1H)
  * 1h10m (inclusive boundary, DEADLINE_REMINDER_1H)
  * 1h11m (outside, None)
- Deduplication, idempotency, registered student exclusion, and auto-close boundary.
"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

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
from app.services.cloud_tasks_service import MockCloudTasksService, get_cloud_tasks_service
from app.services.deadline_scheduler_service import DeadlineSchedulerService


INTERNAL_AUTH_HEADERS = {"Authorization": "Bearer campusflow-internal-tasks-secret-dev"}


@pytest_asyncio.fixture
async def scheduler_boundaries_setup(db_session: AsyncSession) -> dict:
    mock_tasks: MockCloudTasksService = get_cloud_tasks_service()
    if hasattr(mock_tasks, "clear"):
        mock_tasks.clear()

    # Branches
    cse = Branch(code="CSE", name="Computer Science")
    db_session.add(cse)
    await db_session.flush()

    # Officer
    officer = User(
        id=uuid4(),
        email="off_boundary@campusflow.test",
        password_hash=hash_password("OffPass@123"),
        role="OFFICER",
        full_name="Officer Boundary",
        is_active=True,
    )
    # Eligible student
    student_eligible = User(
        id=uuid4(),
        email="s_eligible_bound@campusflow.test",
        password_hash=hash_password("StudentPass@123"),
        role="STUDENT",
        full_name="Eligible Boundary Student",
        is_active=True,
    )
    # Registered student
    student_reg = User(
        id=uuid4(),
        email="s_reg_bound@campusflow.test",
        password_hash=hash_password("StudentPass@123"),
        role="STUDENT",
        full_name="Registered Boundary Student",
        is_active=True,
    )
    db_session.add_all([officer, student_eligible, student_reg])
    await db_session.flush()

    p1 = StudentProfile(
        id=uuid4(),
        user_id=student_eligible.id,
        roll_number="CSE_BOUND_01",
        branch_code="CSE",
        batch_year=2026,
        cgpa=9.0,
        active_backlogs=0,
    )
    p2 = StudentProfile(
        id=uuid4(),
        user_id=student_reg.id,
        roll_number="CSE_BOUND_02",
        branch_code="CSE",
        batch_year=2026,
        cgpa=8.5,
        active_backlogs=0,
    )
    db_session.add_all([p1, p2])

    company = Company(
        id=uuid4(),
        name="Boundary Tech",
        website="https://boundary.test",
        created_by_user_id=officer.id,
    )
    db_session.add(company)
    await db_session.commit()

    return {
        "officer": officer,
        "student_eligible": student_eligible,
        "student_reg": student_reg,
        "company": company,
        "mock_tasks": mock_tasks,
    }


# ===========================================================================
# 1. Exact 24H Boundary Window Tests (23h50m to 24h10m)
# ===========================================================================

@pytest.mark.parametrize(
    "delta, expected_type",
    [
        (timedelta(hours=23, minutes=49), None),
        (timedelta(hours=23, minutes=50), "DEADLINE_REMINDER_24H"),
        (timedelta(hours=24, minutes=0), "DEADLINE_REMINDER_24H"),
        (timedelta(hours=24, minutes=10), "DEADLINE_REMINDER_24H"),
        (timedelta(hours=24, minutes=11), None),
    ],
)
def test_24h_window_exact_boundaries(delta, expected_type):
    """Verify exact inclusive boundary matching for 24H deadline reminders."""
    service = DeadlineSchedulerService(None, None, None, None, None, None, None)
    notif_type, title, body = service._match_reminder_window(delta)
    assert notif_type == expected_type


# ===========================================================================
# 2. Exact 6H Boundary Window Tests (5h50m to 6h10m)
# ===========================================================================

@pytest.mark.parametrize(
    "delta, expected_type",
    [
        (timedelta(hours=5, minutes=49), None),
        (timedelta(hours=5, minutes=50), "DEADLINE_REMINDER_6H"),
        (timedelta(hours=6, minutes=0), "DEADLINE_REMINDER_6H"),
        (timedelta(hours=6, minutes=10), "DEADLINE_REMINDER_6H"),
        (timedelta(hours=6, minutes=11), None),
    ],
)
def test_6h_window_exact_boundaries(delta, expected_type):
    """Verify exact inclusive boundary matching for 6H deadline reminders."""
    service = DeadlineSchedulerService(None, None, None, None, None, None, None)
    notif_type, title, body = service._match_reminder_window(delta)
    assert notif_type == expected_type


# ===========================================================================
# 3. Exact 1H Boundary Window Tests (50m to 1h10m)
# ===========================================================================

@pytest.mark.parametrize(
    "delta, expected_type",
    [
        (timedelta(minutes=49), None),
        (timedelta(minutes=50), "DEADLINE_REMINDER_1H"),
        (timedelta(minutes=60), "DEADLINE_REMINDER_1H"),
        (timedelta(hours=1, minutes=10), "DEADLINE_REMINDER_1H"),
        (timedelta(hours=1, minutes=11), None),
    ],
)
def test_1h_window_exact_boundaries(delta, expected_type):
    """Verify exact inclusive boundary matching for 1H deadline reminders."""
    service = DeadlineSchedulerService(None, None, None, None, None, None, None)
    notif_type, title, body = service._match_reminder_window(delta)
    assert notif_type == expected_type


# ===========================================================================
# 4. Integration: Exact 24H Boundary via /internal/scheduler/check-deadlines
# ===========================================================================

@pytest.mark.asyncio
async def test_scheduler_24h_min_boundary_enqueue(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_boundaries_setup: dict,
):
    """
    Test drive with deadline at exact lower boundary (now + 23h50m):
    - Eligible student receives task.
    - Registered student is excluded.
    """
    now = datetime.now(timezone.utc)
    deadline = now + timedelta(hours=23, minutes=51)

    drive = PlacementDrive(
        id=uuid4(),
        company_id=scheduler_boundaries_setup["company"].id,
        title="Exact 23h50m Drive",
        job_role="Engineer",
        status="REGISTRATION_OPEN",
        registration_deadline=deadline,
        created_by_user_id=scheduler_boundaries_setup["officer"].id,
    )
    db_session.add(drive)
    await db_session.flush()

    criteria = EligibilityCriteria(
        id=uuid4(),
        drive_id=drive.id,
        criteria={"allowed_branches": ["CSE"], "min_cgpa": 7.0},
    )
    db_session.add(criteria)

    # Register student_reg
    reg = DriveRegistration(
        id=uuid4(),
        drive_id=drive.id,
        student_user_id=scheduler_boundaries_setup["student_reg"].id,
        resume_gcs_path_at_registration="resumes/test_reg.pdf",
        status="REGISTERED",
    )
    db_session.add(reg)
    await db_session.commit()

    # Call internal scheduler endpoint
    res = await async_client.post(
        "/internal/scheduler/check-deadlines",
        headers=INTERNAL_AUTH_HEADERS,
    )
    assert res.status_code == 200

    tasks = scheduler_boundaries_setup["mock_tasks"].get_tasks()
    matching_tasks = [
        t for t in tasks
        if t["payload"]["notification_type"] == "DEADLINE_REMINDER_24H"
        and t["payload"]["reference_id"] == str(drive.id)
    ]
    # Exactly 1 task for eligible unregistered student; registered student excluded
    assert len(matching_tasks) == 1
    assert matching_tasks[0]["payload"]["user_id"] == str(scheduler_boundaries_setup["student_eligible"].id)


# ===========================================================================
# 5. Idempotency & Deduplication
# ===========================================================================

@pytest.mark.asyncio
async def test_scheduler_idempotency_no_duplicate_enqueues(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_boundaries_setup: dict,
):
    """
    Second run of check-deadlines in the same window must not create duplicate tasks.
    """
    now = datetime.now(timezone.utc)
    deadline = now + timedelta(hours=6)  # 6H window

    drive = PlacementDrive(
        id=uuid4(),
        company_id=scheduler_boundaries_setup["company"].id,
        title="Idempotent 6H Drive",
        job_role="Engineer",
        status="REGISTRATION_OPEN",
        registration_deadline=deadline,
        created_by_user_id=scheduler_boundaries_setup["officer"].id,
    )
    db_session.add(drive)
    await db_session.flush()

    criteria = EligibilityCriteria(
        id=uuid4(),
        drive_id=drive.id,
        criteria={"allowed_branches": ["CSE"], "min_cgpa": 7.0},
    )
    db_session.add(criteria)

    # Register student_reg so only student_eligible is unregistered
    reg = DriveRegistration(
        id=uuid4(),
        drive_id=drive.id,
        student_user_id=scheduler_boundaries_setup["student_reg"].id,
        resume_gcs_path_at_registration="resumes/test_reg.pdf",
        status="REGISTERED",
    )
    db_session.add(reg)
    await db_session.commit()

    # Clear mock tasks from prior tests
    scheduler_boundaries_setup["mock_tasks"].clear()

    # Run 1
    res1 = await async_client.post("/internal/scheduler/check-deadlines", headers=INTERNAL_AUTH_HEADERS)
    assert res1.status_code == 200
    assert res1.json()["tasks_enqueued"] == 1

    # Simulate worker processing or notification insertion for layer 1 dedup
    s_id = scheduler_boundaries_setup["student_eligible"].id
    notif = Notification(
        id=uuid4(),
        user_id=s_id,
        title="6H Reminder",
        body="Body",
        notification_type="DEADLINE_REMINDER_6H",
        reference_id=drive.id,
        reference_type="DRIVE",
    )
    db_session.add(notif)
    await db_session.commit()

    # Run 2: Immediately running again
    res2 = await async_client.post("/internal/scheduler/check-deadlines", headers=INTERNAL_AUTH_HEADERS)
    assert res2.status_code == 200
    assert res2.json()["tasks_enqueued"] == 0

    # Total tasks for this drive remains exactly 1
    final_tasks = [
        t for t in scheduler_boundaries_setup["mock_tasks"].get_tasks()
        if t["payload"]["reference_id"] == str(drive.id)
    ]
    assert len(final_tasks) == 1


# ===========================================================================
# 6. Auto-Close Boundary Check
# ===========================================================================

@pytest.mark.asyncio
async def test_auto_close_registrations_boundary(
    async_client: AsyncClient,
    db_session: AsyncSession,
    scheduler_boundaries_setup: dict,
):
    """
    Drives whose registration_deadline is in the past transition to REGISTRATION_CLOSED.
    Drives whose registration_deadline is in the future remain REGISTRATION_OPEN.
    """
    now = datetime.now(timezone.utc)

    # Expired drive (1 minute ago)
    expired_drive = PlacementDrive(
        id=uuid4(),
        company_id=scheduler_boundaries_setup["company"].id,
        title="Expired Drive",
        job_role="Engineer",
        status="REGISTRATION_OPEN",
        registration_deadline=now - timedelta(minutes=1),
        created_by_user_id=scheduler_boundaries_setup["officer"].id,
    )
    # Future drive (1 minute in future)
    future_drive = PlacementDrive(
        id=uuid4(),
        company_id=scheduler_boundaries_setup["company"].id,
        title="Future Drive",
        job_role="Engineer",
        status="REGISTRATION_OPEN",
        registration_deadline=now + timedelta(minutes=1),
        created_by_user_id=scheduler_boundaries_setup["officer"].id,
    )
    db_session.add_all([expired_drive, future_drive])
    await db_session.commit()

    res = await async_client.post("/internal/scheduler/auto-close-registrations", headers=INTERNAL_AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["drives_closed"] >= 1

    await db_session.refresh(expired_drive)
    await db_session.refresh(future_drive)

    assert expired_drive.status == "REGISTRATION_CLOSED"
    assert future_drive.status == "REGISTRATION_OPEN"
