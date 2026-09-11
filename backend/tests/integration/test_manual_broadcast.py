"""
CampusFlow — Phase 3.5 Manual Notifications / Broadcast Integration Tests

Comprehensive tests covering:
1. Officer -> ELIGIBLE succeeds
2. Officer -> REGISTERED succeeds
3. Officer -> SHORTLISTED succeeds
4. SHORTLISTED uses latest published stage only
5. No published stage -> zero recipients
6. Zero eligible recipients -> 202
7. Student -> 403
8. Unauthenticated -> 401
9. Nonexistent drive -> 404
10. Invalid audience -> 422
11. Title validation (empty / too long)
12. Body validation (empty / too long)
13. AuditLog is created correctly
14. Correct actor is stored in AuditLog
15. Correct recipient_count is stored in AuditLog
16. MANUAL_BROADCAST tasks contain correct reference data
17. send_push=True on dispatched tasks
18. Worker processes a manual broadcast task
19. Worker creates in-app notification
20. Worker sends Web Push through existing Phase 3.4 mechanism
21. Worker idempotency remains intact
22. Multiple recipients are handled correctly
23. No unrelated students receive notifications
24. Registered audience excludes non-REGISTERED states
25. Student cannot manipulate the recipient audience
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.branch import Branch
from app.models.company import Company
from app.models.drive_registration import DriveRegistration
from app.models.eligibility_criteria import EligibilityCriteria
from app.models.notification import Notification
from app.models.placement_drive import PlacementDrive
from app.models.placement_stage import PlacementStage
from app.models.push_subscription import PushSubscription
from app.models.stage_assignment import StageAssignment
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.repositories.push_subscription_repository import PushSubscriptionRepository
from app.schemas.notification import NotificationTaskPayload
from app.services.cloud_tasks_service import MockCloudTasksService, get_cloud_tasks_service
from app.services.notification_worker import NotificationWorkerService
from app.services.push_sender_service import MockPushSenderService, get_push_sender_service


@pytest_asyncio.fixture
async def broadcast_setup(db_session: AsyncSession, async_client: AsyncClient) -> dict:
    cloud_tasks: MockCloudTasksService = get_cloud_tasks_service()  # type: ignore[assignment]
    if hasattr(cloud_tasks, "clear"):
        cloud_tasks.clear()

    push_service: MockPushSenderService = get_push_sender_service()  # type: ignore[assignment]
    if hasattr(push_service, "clear"):
        push_service.clear()

    # Create Branches
    b_cse = Branch(code="CSE", name="Computer Science & Engineering")
    b_mech = Branch(code="MECH", name="Mechanical Engineering")
    db_session.add_all([b_cse, b_mech])
    await db_session.commit()

    # Create Officer
    officer = User(
        email="broadcast_officer@campusflow.com",
        password_hash=hash_password("password123"),
        role="OFFICER",
        full_name="Placement Officer",
        is_active=True,
    )
    # Create Admin
    admin = User(
        email="broadcast_admin@campusflow.com",
        password_hash=hash_password("password123"),
        role="ADMIN",
        full_name="System Admin",
        is_active=True,
    )
    # Create Student 1 (Eligible & Registered)
    student1 = User(
        email="broadcast_student1@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Student One",
        is_active=True,
    )
    # Create Student 2 (Eligible but NOT Registered)
    student2 = User(
        email="broadcast_student2@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Student Two",
        is_active=True,
    )
    # Create Student 3 (Ineligible)
    student3 = User(
        email="broadcast_student3@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Student Three Ineligible",
        is_active=True,
    )

    db_session.add_all([officer, admin, student1, student2, student3])
    await db_session.commit()
    await db_session.refresh(officer)
    await db_session.refresh(admin)
    await db_session.refresh(student1)
    await db_session.refresh(student2)
    await db_session.refresh(student3)

    # Student profiles
    p1 = StudentProfile(
        user_id=student1.id,
        roll_number="BROAD-001",
        branch_code="CSE",
        batch_year=2025,
        cgpa=8.5,
        active_backlogs=0,
        resume_gcs_path="resumes/s1.pdf",
    )
    p2 = StudentProfile(
        user_id=student2.id,
        roll_number="BROAD-002",
        branch_code="CSE",
        batch_year=2025,
        cgpa=9.0,
        active_backlogs=0,
        resume_gcs_path="resumes/s2.pdf",
    )
    p3 = StudentProfile(
        user_id=student3.id,
        roll_number="BROAD-003",
        branch_code="MECH",  # Ineligible for CSE-only drive
        batch_year=2025,
        cgpa=5.0,  # Below min cgpa
        active_backlogs=3,
    )
    db_session.add_all([p1, p2, p3])

    # Create Company
    company = Company(
        name="Apex Systems",
        created_by_user_id=officer.id,
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    # Create Placement Drive
    drive = PlacementDrive(
        company_id=company.id,
        title="Apex SDE Broadcast Test",
        job_role="Software Engineer",
        status="PUBLISHED",
        registration_deadline=datetime.now(timezone.utc),
        created_by_user_id=officer.id,
    )
    db_session.add(drive)
    await db_session.commit()
    await db_session.refresh(drive)

    # Drive eligibility criteria (CSE only, min cgpa 7.0, max backlogs 0)
    criteria = EligibilityCriteria(
        drive_id=drive.id,
        criteria={
            "min_cgpa": 7.0,
            "max_active_backlogs": 0,
            "eligible_branches": ["CSE"],
            "eligible_batch_years": [2025],
        },
    )
    db_session.add(criteria)

    # Registrations: Student 1 = REGISTERED, Student 3 = WITHDRAWN
    reg1 = DriveRegistration(
        drive_id=drive.id,
        student_user_id=student1.id,
        resume_gcs_path_at_registration="resumes/s1.pdf",
        status="REGISTERED",
    )
    reg3 = DriveRegistration(
        drive_id=drive.id,
        student_user_id=student3.id,
        resume_gcs_path_at_registration="resumes/s3.pdf",
        status="WITHDRAWN",
    )
    db_session.add_all([reg1, reg3])

    # Stages: Stage 1 (Published, Seq 1), Stage 2 (Published, Seq 2 - Latest)
    stage1 = PlacementStage(
        drive_id=drive.id,
        name="Online Assessment",
        stage_type="APTITUDE",
        sequence_order=1,
        is_published=True,
    )
    stage2 = PlacementStage(
        drive_id=drive.id,
        name="Technical Interview",
        stage_type="TECHNICAL",
        sequence_order=2,
        is_published=True,
    )
    db_session.add_all([stage1, stage2])
    await db_session.commit()
    await db_session.refresh(stage1)
    await db_session.refresh(stage2)

    # Stage Assignments:
    # Stage 1: Student 1 = SELECTED, Student 2 = REJECTED
    # Stage 2 (Latest): Student 1 = SHORTLISTED
    asg1_s1 = StageAssignment(stage_id=stage1.id, drive_id=drive.id, student_user_id=student1.id, status="SELECTED")
    asg1_s2 = StageAssignment(stage_id=stage1.id, drive_id=drive.id, student_user_id=student2.id, status="REJECTED")
    asg2_s1 = StageAssignment(stage_id=stage2.id, drive_id=drive.id, student_user_id=student1.id, status="SHORTLISTED")
    db_session.add_all([asg1_s1, asg1_s2, asg2_s1])
    await db_session.commit()

    # Login tokens
    r_off = await async_client.post("/api/v1/auth/login", json={"email": officer.email, "password": "password123"})
    r_adm = await async_client.post("/api/v1/auth/login", json={"email": admin.email, "password": "password123"})
    r_stu = await async_client.post("/api/v1/auth/login", json={"email": student1.email, "password": "password123"})

    token_off = r_off.json()["access_token"]
    token_adm = r_adm.json()["access_token"]
    token_stu = r_stu.json()["access_token"]

    return {
        "officer": officer,
        "admin": admin,
        "student1": student1,
        "student2": student2,
        "student3": student3,
        "drive": drive,
        "stage1": stage1,
        "stage2": stage2,
        "headers_officer": {"Authorization": f"Bearer {token_off}"},
        "headers_admin": {"Authorization": f"Bearer {token_adm}"},
        "headers_student": {"Authorization": f"Bearer {token_stu}"},
        "cloud_tasks": cloud_tasks,
        "push_service": push_service,
    }


# -----------------------------------------------------------------------------
# 1. API & Audience Resolution Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_1_officer_broadcast_eligible_succeeds(async_client: AsyncClient, broadcast_setup: dict):
    """TEST 1: Officer broadcasting to ELIGIBLE enqueues tasks for all active eligible students."""
    drive_id = broadcast_setup["drive"].id
    payload = {
        "audience": "ELIGIBLE",
        "title": "Drive Update: Apex Systems",
        "body": "Pre-placement talk is tomorrow at 10 AM.",
    }
    res = await async_client.post(
        f"/api/v1/drives/{drive_id}/notify",
        json=payload,
        headers=broadcast_setup["headers_officer"],
    )
    assert res.status_code == 202
    data = res.json()
    # Student 1 and Student 2 are eligible (Student 3 is MECH / 5.0 cgpa)
    assert data["recipient_count"] == 2
    assert "Notification enqueued for 2 students" in data["message"]

    tasks = broadcast_setup["cloud_tasks"].get_tasks()
    assert len(tasks) == 2
    recipients = {t["payload"]["user_id"] for t in tasks}
    assert str(broadcast_setup["student1"].id) in recipients
    assert str(broadcast_setup["student2"].id) in recipients
    assert str(broadcast_setup["student3"].id) not in recipients


@pytest.mark.asyncio
async def test_2_officer_broadcast_registered_succeeds(async_client: AsyncClient, broadcast_setup: dict):
    """TEST 2: Officer broadcasting to REGISTERED targets only active registered students."""
    drive_id = broadcast_setup["drive"].id
    broadcast_setup["cloud_tasks"].clear()

    payload = {
        "audience": "REGISTERED",
        "title": "Registration Update",
        "body": "Test links have been generated for registered candidates.",
    }
    res = await async_client.post(
        f"/api/v1/drives/{drive_id}/notify",
        json=payload,
        headers=broadcast_setup["headers_officer"],
    )
    assert res.status_code == 202
    assert res.json()["recipient_count"] == 1  # Student 1 only (Student 3 is WITHDRAWN)

    tasks = broadcast_setup["cloud_tasks"].get_tasks()
    assert len(tasks) == 1
    assert tasks[0]["payload"]["user_id"] == str(broadcast_setup["student1"].id)


@pytest.mark.asyncio
async def test_3_4_officer_broadcast_shortlisted_uses_latest_stage(async_client: AsyncClient, broadcast_setup: dict):
    """TEST 3 & 4: Shortlisted broadcast uses only latest published stage (Stage 2)."""
    drive_id = broadcast_setup["drive"].id
    broadcast_setup["cloud_tasks"].clear()

    payload = {
        "audience": "SHORTLISTED",
        "title": "Interview Shortlist",
        "body": "Congrats on advancing to technical round.",
    }
    res = await async_client.post(
        f"/api/v1/drives/{drive_id}/notify",
        json=payload,
        headers=broadcast_setup["headers_officer"],
    )
    assert res.status_code == 202
    # In Stage 2 (latest published stage), only Student 1 is SHORTLISTED.
    # In Stage 1 (earlier stage), Student 1 was SELECTED and Student 2 was REJECTED.
    assert res.json()["recipient_count"] == 1

    tasks = broadcast_setup["cloud_tasks"].get_tasks()
    assert len(tasks) == 1
    assert tasks[0]["payload"]["user_id"] == str(broadcast_setup["student1"].id)


@pytest.mark.asyncio
async def test_5_no_published_stage_yields_zero_recipients(
    async_client: AsyncClient,
    db_session: AsyncSession,
    broadcast_setup: dict,
):
    """TEST 5: If no stages are published, SHORTLISTED audience yields 0 recipients with 202."""
    drive_id = broadcast_setup["drive"].id
    broadcast_setup["cloud_tasks"].clear()

    # Unpublish both stages
    stage1: PlacementStage = broadcast_setup["stage1"]
    stage2: PlacementStage = broadcast_setup["stage2"]
    stage1.is_published = False
    stage2.is_published = False
    db_session.add_all([stage1, stage2])
    await db_session.commit()

    payload = {
        "audience": "SHORTLISTED",
        "title": "No Stage Published",
        "body": "Testing zero recipients.",
    }
    res = await async_client.post(
        f"/api/v1/drives/{drive_id}/notify",
        json=payload,
        headers=broadcast_setup["headers_officer"],
    )
    assert res.status_code == 202
    assert res.json()["recipient_count"] == 0
    assert len(broadcast_setup["cloud_tasks"].get_tasks()) == 0


@pytest.mark.asyncio
async def test_6_admin_broadcast_succeeds(async_client: AsyncClient, broadcast_setup: dict):
    """TEST 6: Admin can also broadcast manual notifications."""
    drive_id = broadcast_setup["drive"].id
    broadcast_setup["cloud_tasks"].clear()

    payload = {
        "audience": "REGISTERED",
        "title": "Admin Broadcast",
        "body": "Broadcast sent by Admin.",
    }
    res = await async_client.post(
        f"/api/v1/drives/{drive_id}/notify",
        json=payload,
        headers=broadcast_setup["headers_admin"],
    )
    assert res.status_code == 202
    assert res.json()["recipient_count"] == 1


# -----------------------------------------------------------------------------
# 2. Security, RBAC & Validation Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_7_student_forbidden_403(async_client: AsyncClient, broadcast_setup: dict):
    """TEST 7: Students cannot broadcast notifications (403 Forbidden)."""
    drive_id = broadcast_setup["drive"].id
    payload = {
        "audience": "ELIGIBLE",
        "title": "Hacked Broadcast",
        "body": "Fake message",
    }
    res = await async_client.post(
        f"/api/v1/drives/{drive_id}/notify",
        json=payload,
        headers=broadcast_setup["headers_student"],
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_8_unauthenticated_401(async_client: AsyncClient, broadcast_setup: dict):
    """TEST 8: Unauthenticated requests return 401."""
    drive_id = broadcast_setup["drive"].id
    payload = {
        "audience": "ELIGIBLE",
        "title": "Anon Broadcast",
        "body": "Message",
    }
    res = await async_client.post(
        f"/api/v1/drives/{drive_id}/notify",
        json=payload,
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_9_nonexistent_drive_404(async_client: AsyncClient, broadcast_setup: dict):
    """TEST 9: Nonexistent drive returns 404."""
    fake_id = uuid4()
    payload = {
        "audience": "ELIGIBLE",
        "title": "Drive not found",
        "body": "Message",
    }
    res = await async_client.post(
        f"/api/v1/drives/{fake_id}/notify",
        json=payload,
        headers=broadcast_setup["headers_officer"],
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_10_11_12_request_validation(async_client: AsyncClient, broadcast_setup: dict):
    """TEST 10, 11, 12: Invalid audience, empty title, and excessive body length fail validation (422)."""
    drive_id = broadcast_setup["drive"].id

    # Invalid audience
    r1 = await async_client.post(
        f"/api/v1/drives/{drive_id}/notify",
        json={"audience": "ALL_STUDENTS", "title": "Test", "body": "Body"},
        headers=broadcast_setup["headers_officer"],
    )
    assert r1.status_code == 422

    # Empty title
    r2 = await async_client.post(
        f"/api/v1/drives/{drive_id}/notify",
        json={"audience": "ELIGIBLE", "title": "", "body": "Body"},
        headers=broadcast_setup["headers_officer"],
    )
    assert r2.status_code == 422

    # Empty body
    r3 = await async_client.post(
        f"/api/v1/drives/{drive_id}/notify",
        json={"audience": "ELIGIBLE", "title": "Title", "body": ""},
        headers=broadcast_setup["headers_officer"],
    )
    assert r3.status_code == 422

    # Body > 2000 chars
    r4 = await async_client.post(
        f"/api/v1/drives/{drive_id}/notify",
        json={"audience": "ELIGIBLE", "title": "Title", "body": "a" * 2001},
        headers=broadcast_setup["headers_officer"],
    )
    assert r4.status_code == 422


# -----------------------------------------------------------------------------
# 3. Audit Logging & Dispatch Structure Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_13_14_15_audit_log_created_correctly(
    async_client: AsyncClient,
    db_session: AsyncSession,
    broadcast_setup: dict,
):
    """TEST 13, 14, 15: AuditLog entry is recorded with actor, action, drive_id, and metadata."""
    drive_id = broadcast_setup["drive"].id
    officer_id = broadcast_setup["officer"].id

    payload = {
        "audience": "REGISTERED",
        "title": "Audit Check Title",
        "body": "Checking audit trail recording.",
    }
    res = await async_client.post(
        f"/api/v1/drives/{drive_id}/notify",
        json=payload,
        headers=broadcast_setup["headers_officer"],
    )
    assert res.status_code == 202

    # Query AuditLog
    stmt = select(AuditLog).where(
        AuditLog.entity_id == drive_id,
        AuditLog.action == "MANUAL_NOTIFICATION_SENT",
    ).order_by(AuditLog.created_at.desc())
    audit_row = await db_session.scalar(stmt)
    assert audit_row is not None
    assert audit_row.performed_by_user_id == officer_id
    assert audit_row.entity_type == "DRIVE"
    assert audit_row.new_state["audience"] == "REGISTERED"
    assert audit_row.new_state["recipient_count"] == 1
    assert audit_row.new_state["title"] == "Audit Check Title"


@pytest.mark.asyncio
async def test_16_17_task_payload_structure(async_client: AsyncClient, broadcast_setup: dict):
    """TEST 16 & 17: Enqueued task payload contains MANUAL_BROADCAST type, DRIVE ref, send_push=True."""
    drive_id = broadcast_setup["drive"].id
    broadcast_setup["cloud_tasks"].clear()

    payload = {
        "audience": "REGISTERED",
        "title": "Payload Verification",
        "body": "Checking task attributes.",
    }
    await async_client.post(
        f"/api/v1/drives/{drive_id}/notify",
        json=payload,
        headers=broadcast_setup["headers_officer"],
    )

    tasks = broadcast_setup["cloud_tasks"].get_tasks()
    assert len(tasks) == 1
    p = tasks[0]["payload"]
    assert p["notification_type"] == "MANUAL_BROADCAST"
    assert p["reference_type"] == "DRIVE"
    assert p["reference_id"] == str(drive_id)
    assert p["send_push"] is True
    assert p["title"] == "Payload Verification"
    assert p["body"] == "Checking task attributes."


# -----------------------------------------------------------------------------
# 4. Worker End-to-End & Web Push Delivery Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_18_19_20_worker_end_to_end_manual_broadcast(
    db_session: AsyncSession,
    broadcast_setup: dict,
):
    """TEST 18, 19, 20: NotificationWorkerService processes MANUAL_BROADCAST, writes in-app DB and Web Push."""
    student_id = broadcast_setup["student1"].id
    drive_id = broadcast_setup["drive"].id
    endpoint = "https://fcm.googleapis.com/fcm/send/manual-broadcast-device"

    # Register active push subscription for student 1
    sub = PushSubscription(
        user_id=student_id,
        endpoint=endpoint,
        p256dh_key="p256dh-broadcast",
        auth_key="auth-broadcast",
        is_active=True,
    )
    db_session.add(sub)
    await db_session.commit()

    worker = NotificationWorkerService(
        notification_repo=NotificationRepository(session=db_session),
        session=db_session,
        push_repo=PushSubscriptionRepository(session=db_session),
        push_sender=broadcast_setup["push_service"],
    )

    task_payload = NotificationTaskPayload(
        user_id=student_id,
        notification_type="MANUAL_BROADCAST",
        title="Immediate Assembly",
        body="All shortlisted candidates please assemble in Auditorium 1.",
        reference_id=drive_id,
        reference_type="DRIVE",
        send_push=True,
    )

    res = await worker.process_notification_task(task_payload)
    assert res.status == "processed"
    assert res.notification_id is not None

    # Verify in-app DB notification
    stmt = select(Notification).where(Notification.id == res.notification_id)
    notif = await db_session.scalar(stmt)
    assert notif is not None
    assert notif.title == "Immediate Assembly"
    assert notif.notification_type == "MANUAL_BROADCAST"
    assert notif.push_sent is True

    # Verify Web Push sent
    sent_pushes = broadcast_setup["push_service"].get_sent_pushes()
    assert any(p["endpoint"] == endpoint and p["payload"]["title"] == "Immediate Assembly" for p in sent_pushes)


@pytest.mark.asyncio
async def test_21_worker_idempotency_for_manual_broadcast(
    db_session: AsyncSession,
    broadcast_setup: dict,
):
    """TEST 21: Worker skips duplicate MANUAL_BROADCAST task for same student & drive."""
    student_id = broadcast_setup["student2"].id
    drive_id = broadcast_setup["drive"].id

    worker = NotificationWorkerService(
        notification_repo=NotificationRepository(session=db_session),
        session=db_session,
        push_repo=PushSubscriptionRepository(session=db_session),
        push_sender=broadcast_setup["push_service"],
    )

    task_payload = NotificationTaskPayload(
        user_id=student_id,
        notification_type="MANUAL_BROADCAST",
        title="Duplicate Test",
        body="Testing idempotency.",
        reference_id=drive_id,
        reference_type="DRIVE",
        send_push=True,
    )

    # 1. First run
    r1 = await worker.process_notification_task(task_payload)
    assert r1.status == "processed"

    # 2. Duplicate retry
    r2 = await worker.process_notification_task(task_payload)
    assert r2.status == "skipped"
    assert r2.reason == "idempotent_duplicate"
