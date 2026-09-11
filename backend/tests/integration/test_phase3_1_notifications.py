"""
CampusFlow — Phase 3.1 Async Notification Foundation Integration Tests

Tests covering:
- Cloud Tasks abstraction (mock enqueue, payload structure, factory configuration)
- NotificationDispatcher service (single & bulk dispatch, idempotency key generation)
- Internal Task endpoint authentication & security (401 on unauthenticated, 403 on student/officer/admin JWT, 200 on internal auth)
- Internal Task endpoint payload validation (422 on invalid payload)
- NotificationWorkerService idempotency & DB persistence (unique constraint preservation, duplicate skipping)
"""
from __future__ import annotations

from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import hash_password
from app.models.notification import Notification
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import NotificationTaskPayload
from app.services.cloud_tasks_service import (
    MockCloudTasksService,
    create_cloud_tasks_service,
)
from app.services.notification_dispatcher import NotificationDispatcher
from app.services.notification_worker import NotificationWorkerService


@pytest_asyncio.fixture
async def sample_users(db_session: AsyncSession) -> dict[str, User]:
    student = User(
        email="p31_student@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Phase31 Student",
        is_active=True,
    )
    officer = User(
        email="p31_officer@campusflow.com",
        password_hash=hash_password("password123"),
        role="OFFICER",
        full_name="Phase31 Officer",
        is_active=True,
    )
    admin = User(
        email="p31_admin@campusflow.com",
        password_hash=hash_password("password123"),
        role="ADMIN",
        full_name="Phase31 Admin",
        is_active=True,
    )
    db_session.add_all([student, officer, admin])
    await db_session.commit()
    await db_session.refresh(student)
    await db_session.refresh(officer)
    await db_session.refresh(admin)

    return {"student": student, "officer": officer, "admin": admin}


@pytest_asyncio.fixture
async def user_tokens(
    async_client: AsyncClient,
    sample_users: dict[str, User],
) -> dict[str, str]:
    res_student = await async_client.post(
        "/api/v1/auth/login",
        json={"email": sample_users["student"].email, "password": "password123"},
    )
    res_officer = await async_client.post(
        "/api/v1/auth/login",
        json={"email": sample_users["officer"].email, "password": "password123"},
    )
    res_admin = await async_client.post(
        "/api/v1/auth/login",
        json={"email": sample_users["admin"].email, "password": "password123"},
    )

    return {
        "student": res_student.json()["access_token"],
        "officer": res_officer.json()["access_token"],
        "admin": res_admin.json()["access_token"],
    }


# -----------------------------------------------------------------------------
# 1. Cloud Tasks Abstraction Tests
# -----------------------------------------------------------------------------


class TestCloudTasksAbstraction:
    @pytest.mark.asyncio
    async def test_mock_cloud_tasks_enqueue_succeeds(self):
        service = MockCloudTasksService(
            queue_name="test-queue",
            location="asia-south1",
            project_id="test-project",
        )
        payload = {
            "user_id": str(uuid4()),
            "title": "Test Drive",
            "body": "Test Body",
            "notification_type": "DRIVE_PUBLISHED",
        }

        task_id = await service.enqueue_notification_task(payload=payload)
        assert task_id.startswith("projects/test-project/locations/asia-south1/queues/test-queue/tasks/")

        tasks = service.get_tasks()
        assert len(tasks) == 1
        assert tasks[0]["payload"] == payload
        assert tasks[0]["queue"] == "test-queue"

    def test_factory_creates_mock_service(self):
        settings = Settings(
            DATABASE_URL="postgresql+asyncpg://mock:mock@localhost:5432/mock",
            JWT_PRIVATE_KEY_BASE64="mock",
            JWT_PUBLIC_KEY_BASE64="mock",
            NOTIFICATION_TASK_PROVIDER="mock",
            CLOUD_TASKS_QUEUE_NAME="my-queue",
        )
        service = create_cloud_tasks_service(provider="mock", settings=settings)
        assert isinstance(service, MockCloudTasksService)
        assert service.queue_name == "my-queue"

    def test_factory_invalid_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown notification task provider"):
            create_cloud_tasks_service(provider="invalid_provider")


# -----------------------------------------------------------------------------
# 2. Notification Dispatcher Tests
# -----------------------------------------------------------------------------


class TestNotificationDispatcher:
    @pytest.mark.asyncio
    async def test_dispatch_single_notification(self):
        mock_tasks = MockCloudTasksService()
        dispatcher = NotificationDispatcher(cloud_tasks=mock_tasks)

        user_id = uuid4()
        ref_id = uuid4()
        task_id = await dispatcher.dispatch_notification(
            user_id=user_id,
            title="Drive Published",
            body="A new drive has been posted",
            notification_type="DRIVE_PUBLISHED",
            reference_id=ref_id,
            reference_type="DRIVE",
        )

        assert task_id is not None
        tasks = mock_tasks.get_tasks()
        assert len(tasks) == 1

        payload = tasks[0]["payload"]
        assert payload["user_id"] == str(user_id)
        assert payload["title"] == "Drive Published"
        assert payload["body"] == "A new drive has been posted"
        assert payload["notification_type"] == "DRIVE_PUBLISHED"
        assert payload["reference_id"] == str(ref_id)
        assert payload["reference_type"] == "DRIVE"
        assert payload["send_push"] is True
        assert payload["idempotency_key"] == f"DRIVE_PUBLISHED:{ref_id}:{user_id}"

    @pytest.mark.asyncio
    async def test_dispatch_bulk_notifications_creates_individual_tasks(self):
        mock_tasks = MockCloudTasksService()
        dispatcher = NotificationDispatcher(cloud_tasks=mock_tasks)

        user_id_1 = uuid4()
        user_id_2 = uuid4()
        ref_id = uuid4()

        items = [
            {
                "user_id": user_id_1,
                "title": "Stage Results",
                "body": "Results are out",
                "notification_type": "RESULT_PUBLISHED",
                "reference_id": ref_id,
                "reference_type": "PLACEMENT_STAGE",
            },
            {
                "user_id": user_id_2,
                "title": "Stage Results",
                "body": "Results are out",
                "notification_type": "RESULT_PUBLISHED",
                "reference_id": ref_id,
                "reference_type": "PLACEMENT_STAGE",
            },
        ]

        task_ids = await dispatcher.dispatch_bulk_notifications(items)
        assert len(task_ids) == 2
        assert len(mock_tasks.get_tasks()) == 2
        assert mock_tasks.get_tasks()[0]["payload"]["user_id"] == str(user_id_1)
        assert mock_tasks.get_tasks()[1]["payload"]["user_id"] == str(user_id_2)


# -----------------------------------------------------------------------------
# 3. Internal Endpoint Security & Authentication Tests
# -----------------------------------------------------------------------------


class TestInternalTaskEndpointSecurity:
    @pytest.mark.asyncio
    async def test_unauthenticated_request_fails(
        self,
        async_client: AsyncClient,
        sample_users: dict[str, User],
    ):
        payload = {
            "user_id": str(sample_users["student"].id),
            "title": "Test",
            "body": "Test body",
            "notification_type": "DRIVE_PUBLISHED",
        }
        r = await async_client.post("/internal/tasks/send-notification", json=payload)
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_internal_token_fails(
        self,
        async_client: AsyncClient,
        sample_users: dict[str, User],
    ):
        payload = {
            "user_id": str(sample_users["student"].id),
            "title": "Test",
            "body": "Test body",
            "notification_type": "DRIVE_PUBLISHED",
        }
        headers = {"Authorization": "Bearer wrong-internal-secret-token"}
        r = await async_client.post(
            "/internal/tasks/send-notification",
            json=payload,
            headers=headers,
        )
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_student_jwt_rejected_from_internal_endpoint(
        self,
        async_client: AsyncClient,
        sample_users: dict[str, User],
        user_tokens: dict[str, str],
    ):
        payload = {
            "user_id": str(sample_users["student"].id),
            "title": "Test",
            "body": "Test body",
            "notification_type": "DRIVE_PUBLISHED",
        }
        headers = {"Authorization": f"Bearer {user_tokens['student']}"}
        r = await async_client.post(
            "/internal/tasks/send-notification",
            json=payload,
            headers=headers,
        )
        # Normal user JWT must be strictly rejected (403 Permission Denied)
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_officer_jwt_rejected_from_internal_endpoint(
        self,
        async_client: AsyncClient,
        sample_users: dict[str, User],
        user_tokens: dict[str, str],
    ):
        payload = {
            "user_id": str(sample_users["student"].id),
            "title": "Test",
            "body": "Test body",
            "notification_type": "DRIVE_PUBLISHED",
        }
        headers = {"Authorization": f"Bearer {user_tokens['officer']}"}
        r = await async_client.post(
            "/internal/tasks/send-notification",
            json=payload,
            headers=headers,
        )
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_jwt_rejected_from_internal_endpoint(
        self,
        async_client: AsyncClient,
        sample_users: dict[str, User],
        user_tokens: dict[str, str],
    ):
        payload = {
            "user_id": str(sample_users["student"].id),
            "title": "Test",
            "body": "Test body",
            "notification_type": "DRIVE_PUBLISHED",
        }
        headers = {"Authorization": f"Bearer {user_tokens['admin']}"}
        r = await async_client.post(
            "/internal/tasks/send-notification",
            json=payload,
            headers=headers,
        )
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_valid_internal_token_succeeds(
        self,
        async_client: AsyncClient,
        sample_users: dict[str, User],
    ):
        payload = {
            "user_id": str(sample_users["student"].id),
            "title": "New Drive Notification",
            "body": "A new placement drive has opened.",
            "notification_type": "DRIVE_PUBLISHED",
            "reference_id": str(uuid4()),
            "reference_type": "DRIVE",
        }
        headers = {"Authorization": "Bearer campusflow-internal-tasks-secret-dev"}
        r = await async_client.post(
            "/internal/tasks/send-notification",
            json=payload,
            headers=headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "processed"
        assert data["notification_id"] is not None


# -----------------------------------------------------------------------------
# 4. Internal Endpoint Validation Tests
# -----------------------------------------------------------------------------


class TestInternalTaskEndpointValidation:
    @pytest.mark.asyncio
    async def test_missing_required_fields_fails_validation(
        self,
        async_client: AsyncClient,
    ):
        headers = {"Authorization": "Bearer campusflow-internal-tasks-secret-dev"}
        # Missing title and notification_type
        payload = {"user_id": str(uuid4())}
        r = await async_client.post(
            "/internal/tasks/send-notification",
            json=payload,
            headers=headers,
        )
        assert r.status_code == 422


# -----------------------------------------------------------------------------
# 5. Worker Service & Idempotency Tests
# -----------------------------------------------------------------------------


class TestNotificationWorkerIdempotency:
    @pytest.mark.asyncio
    async def test_worker_creates_notification_and_skips_duplicates(
        self,
        db_session: AsyncSession,
        sample_users: dict[str, User],
    ):
        repo = NotificationRepository(session=db_session)
        worker = NotificationWorkerService(notification_repo=repo, session=db_session)

        student_id = sample_users["student"].id
        drive_id = uuid4()

        task = NotificationTaskPayload(
            user_id=student_id,
            title="Interview Scheduled",
            body="Your technical interview is scheduled for tomorrow.",
            notification_type="STAGE_UPDATED",
            reference_id=drive_id,
            reference_type="PLACEMENT_STAGE",
        )

        # 1. First execution — should process and create record
        res1 = await worker.process_notification_task(task)
        assert res1.status == "processed"
        assert res1.notification_id is not None
        assert res1.reason is None

        # Verify record in DB
        db_notif = await repo.get_by_id(res1.notification_id)
        assert db_notif is not None
        assert db_notif.user_id == student_id
        assert db_notif.title == "Interview Scheduled"
        assert db_notif.notification_type == "STAGE_UPDATED"
        assert db_notif.reference_id == drive_id
        assert db_notif.is_read is False
        assert db_notif.push_sent is False

        # 2. Second execution with same payload (Cloud Tasks retry simulation)
        res2 = await worker.process_notification_task(task)
        assert res2.status == "skipped"
        assert res2.reason == "idempotent_duplicate"
        assert res2.notification_id == res1.notification_id

        # Verify only 1 notification exists in DB
        stmt = select(Notification).where(
            Notification.user_id == student_id,
            Notification.notification_type == "STAGE_UPDATED",
            Notification.reference_id == drive_id,
        )
        result = await db_session.execute(stmt)
        all_notifs = result.scalars().all()
        assert len(all_notifs) == 1

    @pytest.mark.asyncio
    async def test_different_notification_type_or_ref_creates_separate_records(
        self,
        db_session: AsyncSession,
        sample_users: dict[str, User],
    ):
        repo = NotificationRepository(session=db_session)
        worker = NotificationWorkerService(notification_repo=repo, session=db_session)

        student_id = sample_users["student"].id
        drive_id_1 = uuid4()
        drive_id_2 = uuid4()

        task_1 = NotificationTaskPayload(
            user_id=student_id,
            title="Drive 1",
            body="Drive 1 published",
            notification_type="DRIVE_PUBLISHED",
            reference_id=drive_id_1,
        )
        task_2 = NotificationTaskPayload(
            user_id=student_id,
            title="Drive 2",
            body="Drive 2 published",
            notification_type="DRIVE_PUBLISHED",
            reference_id=drive_id_2,
        )

        res1 = await worker.process_notification_task(task_1)
        res2 = await worker.process_notification_task(task_2)

        assert res1.status == "processed"
        assert res2.status == "processed"
        assert res1.notification_id != res2.notification_id

    @pytest.mark.asyncio
    async def test_production_environment_strictly_rejects_mock_secret(
        self,
        async_client: AsyncClient,
        sample_users: dict[str, User],
        monkeypatch: pytest.MonkeyPatch,
    ):
        from app.core.config import get_settings
        from app.core.exceptions import AuthenticationError
        from app.core.internal_auth import verify_internal_task_auth
        from fastapi.security import HTTPAuthorizationCredentials

        # Simulate production environment
        settings = get_settings()
        monkeypatch.setattr(settings, "app_env", "production")
        monkeypatch.setattr(settings, "notification_task_provider", "cloud_tasks")

        creds = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="campusflow-internal-tasks-secret-dev",
        )

        # In production, providing the dev mock secret MUST fail
        with pytest.raises(AuthenticationError):
            await verify_internal_task_auth(credentials=creds)

