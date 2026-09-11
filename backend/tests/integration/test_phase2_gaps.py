"""
Integration tests for Phase 2 Gap Closure:
  - Gap 1: Notifications API (list, mark-read, mark-all-read)
  - Gap 2: Stage type CODING / OTHER
  - Gap 3: Drive status preconditions (deadline, stages)
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.company import Company
from app.models.notification import Notification
from app.models.placement_drive import PlacementDrive
from app.models.user import User


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


async def _login(async_client: AsyncClient, email: str, password: str = "password123") -> dict:
    resp = await async_client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def officer_user(db_session: AsyncSession, async_client: AsyncClient):
    user = User(
        email="gap_officer@campusflow.com",
        password_hash=hash_password("password123"),
        role="OFFICER",
        full_name="Gap Officer",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    headers = await _login(async_client, user.email)
    return {"user": user, "headers": headers}


@pytest_asyncio.fixture
async def student_user(db_session: AsyncSession, async_client: AsyncClient):
    user = User(
        email="gap_student@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Gap Student",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    headers = await _login(async_client, user.email)
    return {"user": user, "headers": headers}


@pytest_asyncio.fixture
async def another_student(db_session: AsyncSession, async_client: AsyncClient):
    user = User(
        email="gap_student2@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Gap Student 2",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    headers = await _login(async_client, user.email)
    return {"user": user, "headers": headers}


@pytest_asyncio.fixture
async def company_and_drive(db_session: AsyncSession, officer_user):
    """Creates a company + DRAFT drive with a registration_deadline."""
    company = Company(
        name="Gap Corp",
        created_by_user_id=officer_user["user"].id,
    )
    db_session.add(company)
    await db_session.flush()

    drive = PlacementDrive(
        company_id=company.id,
        title="Gap Drive",
        job_role="SDE",
        status="DRAFT",
        created_by_user_id=officer_user["user"].id,
    )
    db_session.add(drive)
    await db_session.commit()
    await db_session.refresh(drive)
    return {"company": company, "drive": drive}


# ---------------------------------------------------------------------------
# Gap 1: Notifications API
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def student_with_notifications(db_session: AsyncSession, student_user):
    """Creates 3 notifications for the student (2 unread, 1 read)."""
    uid = student_user["user"].id
    notifs = [
        Notification(
            user_id=uid,
            title="Notif 1",
            body="You were shortlisted",
            notification_type="SHORTLISTED",
            reference_id=uid,  # use uid as dummy reference
            reference_type="PLACEMENT_STAGE",
            is_read=False,
            push_sent=False,
        ),
        Notification(
            user_id=uid,
            title="Notif 2",
            body="Results published",
            notification_type="RESULT_PUBLISHED",
            reference_id=uid,
            reference_type="PLACEMENT_STAGE",
            is_read=False,
            push_sent=False,
        ),
        Notification(
            user_id=uid,
            title="Notif 3",
            body="Already read",
            notification_type="SHORTLISTED",
            reference_id=None,  # no reference to avoid unique conflict
            reference_type=None,
            is_read=True,
            push_sent=False,
        ),
    ]
    db_session.add_all(notifs)
    await db_session.commit()
    for n in notifs:
        await db_session.refresh(n)
    return notifs


class TestListNotifications:
    async def test_empty_list(self, async_client: AsyncClient, student_user):
        resp = await async_client.get("/api/v1/notifications", headers=student_user["headers"])
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0

    async def test_list_returns_own_notifications(
        self, async_client: AsyncClient, student_user, student_with_notifications
    ):
        resp = await async_client.get("/api/v1/notifications", headers=student_user["headers"])
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 3
        assert len(body["items"]) == 3

    async def test_list_filter_unread(
        self, async_client: AsyncClient, student_user, student_with_notifications
    ):
        resp = await async_client.get(
            "/api/v1/notifications?is_read=false", headers=student_user["headers"]
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert all(not item["is_read"] for item in body["items"])

    async def test_list_filter_read(
        self, async_client: AsyncClient, student_user, student_with_notifications
    ):
        resp = await async_client.get(
            "/api/v1/notifications?is_read=true", headers=student_user["headers"]
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert all(item["is_read"] for item in body["items"])

    async def test_list_does_not_return_other_users_notifications(
        self, async_client: AsyncClient, another_student, student_with_notifications
    ):
        # another_student should see 0 notifications (they belong to student_user)
        resp = await async_client.get("/api/v1/notifications", headers=another_student["headers"])
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    async def test_list_requires_auth(self, async_client: AsyncClient):
        resp = await async_client.get("/api/v1/notifications")
        assert resp.status_code == 401

    async def test_pagination(
        self, async_client: AsyncClient, student_user, student_with_notifications
    ):
        resp = await async_client.get(
            "/api/v1/notifications?page=1&page_size=2", headers=student_user["headers"]
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 2
        assert body["has_next"] is True


class TestMarkNotificationRead:
    async def test_mark_read_success(
        self, async_client: AsyncClient, student_user, student_with_notifications
    ):
        notif_id = str(student_with_notifications[0].id)
        resp = await async_client.post(
            f"/api/v1/notifications/{notif_id}/read",
            headers=student_user["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["is_read"] is True

    async def test_mark_read_idempotent(
        self, async_client: AsyncClient, student_user, student_with_notifications
    ):
        notif_id = str(student_with_notifications[2].id)  # already read
        resp1 = await async_client.post(
            f"/api/v1/notifications/{notif_id}/read",
            headers=student_user["headers"],
        )
        resp2 = await async_client.post(
            f"/api/v1/notifications/{notif_id}/read",
            headers=student_user["headers"],
        )
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp1.json()["is_read"] is True
        assert resp2.json()["is_read"] is True

    async def test_mark_read_idor_protection(
        self, async_client: AsyncClient, another_student, student_with_notifications
    ):
        notif_id = str(student_with_notifications[0].id)  # belongs to student_user
        resp = await async_client.post(
            f"/api/v1/notifications/{notif_id}/read",
            headers=another_student["headers"],
        )
        assert resp.status_code == 403

    async def test_mark_read_not_found(
        self, async_client: AsyncClient, student_user
    ):
        import uuid
        resp = await async_client.post(
            f"/api/v1/notifications/{uuid.uuid4()}/read",
            headers=student_user["headers"],
        )
        assert resp.status_code == 404

    async def test_mark_read_requires_auth(
        self, async_client: AsyncClient, student_with_notifications
    ):
        notif_id = str(student_with_notifications[0].id)
        resp = await async_client.post(f"/api/v1/notifications/{notif_id}/read")
        assert resp.status_code == 401


class TestMarkAllRead:
    async def test_mark_all_read_success(
        self, async_client: AsyncClient, student_user, student_with_notifications
    ):
        resp = await async_client.post(
            "/api/v1/notifications/read-all", headers=student_user["headers"]
        )
        assert resp.status_code == 200
        assert resp.json()["marked_read"] == 2  # only the 2 unread ones

    async def test_mark_all_read_only_own(
        self, async_client: AsyncClient, another_student, student_with_notifications
    ):
        resp = await async_client.post(
            "/api/v1/notifications/read-all", headers=another_student["headers"]
        )
        assert resp.status_code == 200
        assert resp.json()["marked_read"] == 0  # another_student has none

    async def test_mark_all_read_idempotent(
        self, async_client: AsyncClient, student_user, student_with_notifications
    ):
        await async_client.post("/api/v1/notifications/read-all", headers=student_user["headers"])
        resp2 = await async_client.post(
            "/api/v1/notifications/read-all", headers=student_user["headers"]
        )
        assert resp2.status_code == 200
        assert resp2.json()["marked_read"] == 0  # nothing left to mark

    async def test_mark_all_read_requires_auth(self, async_client: AsyncClient):
        resp = await async_client.post("/api/v1/notifications/read-all")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Gap 2: Stage type CODING / OTHER
# ---------------------------------------------------------------------------


class TestStageTypeCodingOther:
    async def test_create_stage_coding(
        self, async_client: AsyncClient, officer_user, company_and_drive
    ):
        drive_id = str(company_and_drive["drive"].id)
        resp = await async_client.post(
            f"/api/v1/drives/{drive_id}/stages",
            json={"name": "Coding Round", "stage_type": "CODING", "sequence_order": 1},
            headers=officer_user["headers"],
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["stage_type"] == "CODING"

    async def test_create_stage_other(
        self, async_client: AsyncClient, officer_user, company_and_drive
    ):
        drive_id = str(company_and_drive["drive"].id)
        resp = await async_client.post(
            f"/api/v1/drives/{drive_id}/stages",
            json={"name": "Other Round", "stage_type": "OTHER", "sequence_order": 2},
            headers=officer_user["headers"],
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["stage_type"] == "OTHER"

    async def test_invalid_stage_type_rejected(
        self, async_client: AsyncClient, officer_user, company_and_drive
    ):
        drive_id = str(company_and_drive["drive"].id)
        resp = await async_client.post(
            f"/api/v1/drives/{drive_id}/stages",
            json={"name": "Bad Type", "stage_type": "INVALID", "sequence_order": 3},
            headers=officer_user["headers"],
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Gap 3: Drive status preconditions
# ---------------------------------------------------------------------------


class TestDriveStatusPreconditions:
    async def test_registration_open_without_deadline_fails(
        self, async_client: AsyncClient, officer_user, company_and_drive
    ):
        drive_id = str(company_and_drive["drive"].id)
        # Advance to PUBLISHED first
        await async_client.post(
            f"/api/v1/drives/{drive_id}/status",
            json={"status": "PUBLISHED"},
            headers=officer_user["headers"],
        )
        # Try to open registration — no deadline set → should fail
        resp = await async_client.post(
            f"/api/v1/drives/{drive_id}/status",
            json={"status": "REGISTRATION_OPEN"},
            headers=officer_user["headers"],
        )
        assert resp.status_code == 422, resp.text
        assert "registration_deadline" in resp.json()["detail"].lower()

    async def test_registration_open_with_deadline_succeeds(
        self, async_client: AsyncClient, officer_user, db_session: AsyncSession, company_and_drive
    ):
        drive = company_and_drive["drive"]
        # Set a deadline on the drive
        from datetime import datetime, timezone, timedelta
        drive.registration_deadline = datetime.now(timezone.utc) + timedelta(days=7)
        db_session.add(drive)
        await db_session.commit()

        drive_id = str(drive.id)
        await async_client.post(
            f"/api/v1/drives/{drive_id}/status",
            json={"status": "PUBLISHED"},
            headers=officer_user["headers"],
        )
        resp = await async_client.post(
            f"/api/v1/drives/{drive_id}/status",
            json={"status": "REGISTRATION_OPEN"},
            headers=officer_user["headers"],
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "REGISTRATION_OPEN"

    async def test_assessment_without_stages_fails(
        self, async_client: AsyncClient, officer_user, db_session: AsyncSession, company_and_drive
    ):
        drive = company_and_drive["drive"]
        from datetime import datetime, timezone, timedelta
        drive.registration_deadline = datetime.now(timezone.utc) + timedelta(days=7)
        db_session.add(drive)
        await db_session.commit()

        drive_id = str(drive.id)
        headers = officer_user["headers"]
        for status in ["PUBLISHED", "REGISTRATION_OPEN", "REGISTRATION_CLOSED", "SHORTLISTING"]:
            r = await async_client.post(
                f"/api/v1/drives/{drive_id}/status",
                json={"status": status},
                headers=headers,
            )
            assert r.status_code == 200, f"Failed on {status}: {r.text}"

        # Now try to advance to ASSESSMENT — no stages created → should fail
        resp = await async_client.post(
            f"/api/v1/drives/{drive_id}/status",
            json={"status": "ASSESSMENT"},
            headers=headers,
        )
        assert resp.status_code == 422, resp.text
        assert "stage" in resp.json()["detail"].lower()

    async def test_assessment_with_stages_succeeds(
        self, async_client: AsyncClient, officer_user, db_session: AsyncSession, company_and_drive
    ):
        drive = company_and_drive["drive"]
        from datetime import datetime, timezone, timedelta
        drive.registration_deadline = datetime.now(timezone.utc) + timedelta(days=7)
        db_session.add(drive)
        await db_session.commit()

        drive_id = str(drive.id)
        headers = officer_user["headers"]

        # Create a stage first
        stage_resp = await async_client.post(
            f"/api/v1/drives/{drive_id}/stages",
            json={"name": "Aptitude", "stage_type": "APTITUDE", "sequence_order": 1},
            headers=headers,
        )
        assert stage_resp.status_code == 201, stage_resp.text

        # Advance through statuses
        for status in ["PUBLISHED", "REGISTRATION_OPEN", "REGISTRATION_CLOSED", "SHORTLISTING"]:
            r = await async_client.post(
                f"/api/v1/drives/{drive_id}/status",
                json={"status": status},
                headers=headers,
            )
            assert r.status_code == 200, f"Failed on {status}: {r.text}"

        # Now ASSESSMENT should succeed
        resp = await async_client.post(
            f"/api/v1/drives/{drive_id}/status",
            json={"status": "ASSESSMENT"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "ASSESSMENT"
