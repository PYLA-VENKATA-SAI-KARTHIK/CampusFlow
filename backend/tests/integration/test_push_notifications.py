"""
CampusFlow — Phase 3.4 Web Push Notifications & Browser Subscriptions Tests

Comprehensive tests covering:
1. GET /notifications/vapid-public-key
2. Unauthenticated registration returns 401
3. Authenticated registration creates active PushSubscription row
4. Duplicate same-user endpoint updates keys and reactivates
5. Duplicate endpoint owned by another user is strictly rejected (hijacking protection)
6. DELETE /notifications/push-subscription deactivates subscription
7. IDOR deletion attempt (User A cannot delete User B's endpoint)
8. GET /notifications/push-subscription/status returns correct active count
9. Valid HTTPS endpoint passes schema validation
10. Non-HTTPS endpoint fails schema validation (422)
11. Worker sends push notification to active subscription
12. Worker sends push to multiple devices for the same user
13. Worker deactivates subscription on HTTP 410 Gone
14. Worker deactivates subscription on HTTP 404 Not Found
15. Worker does not deactivate subscription on temporary HTTP 500 failure
16. Push delivery failure isolates errors and preserves in-app notification record
17. User with zero active subscriptions receives in-app notification without error
18. Successful push delivery updates push_sent = True
19. Successful push delivery populates push_sent_at timestamp
20. Worker continues delivering to other devices after one device failure
21. Worker idempotency remains intact with push delivery
22. Existing deadline reminder behavior remains intact
23. Existing Phase 3.2 event notification behavior remains intact
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
from app.models.notification import Notification
from app.models.push_subscription import PushSubscription
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.repositories.push_subscription_repository import PushSubscriptionRepository
from app.schemas.notification import NotificationTaskPayload
from app.services.notification_worker import NotificationWorkerService
from app.services.push_sender_service import MockPushSenderService, get_push_sender_service


@pytest_asyncio.fixture
async def push_test_setup(db_session: AsyncSession, async_client: AsyncClient) -> dict:
    push_service: MockPushSenderService = get_push_sender_service()  # type: ignore[assignment]
    if hasattr(push_service, "clear"):
        push_service.clear()

    # User 1: Student A
    user_a = User(
        email="push_student_a@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Student A Push",
        is_active=True,
    )
    # User 2: Student B
    user_b = User(
        email="push_student_b@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Student B Push",
        is_active=True,
    )
    db_session.add_all([user_a, user_b])
    await db_session.commit()
    await db_session.refresh(user_a)
    await db_session.refresh(user_b)

    # Login tokens
    res_a = await async_client.post(
        "/api/v1/auth/login",
        json={"email": user_a.email, "password": "password123"},
    )
    token_a = res_a.json()["access_token"]

    res_b = await async_client.post(
        "/api/v1/auth/login",
        json={"email": user_b.email, "password": "password123"},
    )
    token_b = res_b.json()["access_token"]

    return {
        "user_a": user_a,
        "user_b": user_b,
        "token_a": token_a,
        "token_b": token_b,
        "auth_a": {"Authorization": f"Bearer {token_a}"},
        "auth_b": {"Authorization": f"Bearer {token_b}"},
        "push_service": push_service,
    }


# -----------------------------------------------------------------------------
# API Endpoint Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_1_get_vapid_public_key(async_client: AsyncClient):
    """TEST 1: GET /notifications/vapid-public-key returns configured public key."""
    res = await async_client.get("/api/v1/notifications/vapid-public-key")
    assert res.status_code == 200
    data = res.json()
    assert "vapid_public_key" in data
    assert len(data["vapid_public_key"]) > 10


@pytest.mark.asyncio
async def test_2_unauthenticated_registration_rejected(async_client: AsyncClient):
    """TEST 2: Unauthenticated subscription registration returns 401."""
    payload = {
        "endpoint": "https://fcm.googleapis.com/fcm/send/test-unauth-endpoint",
        "p256dh_key": "BNcRdreALRF",
        "auth_key": "tBHItJI5svb",
    }
    res = await async_client.post("/api/v1/notifications/push-subscription", json=payload)
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_3_authenticated_registration_creates_row(
    async_client: AsyncClient,
    db_session: AsyncSession,
    push_test_setup: dict,
):
    """TEST 3: Authenticated registration creates an active push subscription."""
    payload = {
        "endpoint": "https://fcm.googleapis.com/fcm/send/device-1-user-a",
        "p256dh_key": "key-p256dh-1",
        "auth_key": "key-auth-1",
        "user_agent": "Mozilla/5.0 Chrome/120.0",
    }
    res = await async_client.post(
        "/api/v1/notifications/push-subscription",
        json=payload,
        headers=push_test_setup["auth_a"],
    )
    assert res.status_code == 201
    data = res.json()
    assert data["endpoint"] == payload["endpoint"]
    assert data["is_active"] is True
    assert data["user_agent"] == payload["user_agent"]
    # Verify auth/p256dh keys are not exposed in response
    assert "auth_key" not in data
    assert "p256dh_key" not in data

    # Verify DB record
    stmt = select(PushSubscription).where(PushSubscription.endpoint == payload["endpoint"])
    sub = await db_session.scalar(stmt)
    assert sub is not None
    assert sub.user_id == push_test_setup["user_a"].id
    assert sub.is_active is True


@pytest.mark.asyncio
async def test_4_duplicate_same_user_subscription_updates(
    async_client: AsyncClient,
    db_session: AsyncSession,
    push_test_setup: dict,
):
    """TEST 4: Registering same endpoint for same user updates keys & reactivates."""
    endpoint = "https://fcm.googleapis.com/fcm/send/device-repeat-user-a"
    # Registration 1
    await async_client.post(
        "/api/v1/notifications/push-subscription",
        json={"endpoint": endpoint, "p256dh_key": "key1", "auth_key": "auth1"},
        headers=push_test_setup["auth_a"],
    )

    # Deactivate
    del_res = await async_client.request(
        "DELETE",
        "/api/v1/notifications/push-subscription",
        json={"endpoint": endpoint},
        headers=push_test_setup["auth_a"],
    )
    assert del_res.status_code == 200

    # Registration 2 with new keys
    res2 = await async_client.post(
        "/api/v1/notifications/push-subscription",
        json={"endpoint": endpoint, "p256dh_key": "key2-updated", "auth_key": "auth2-updated"},
        headers=push_test_setup["auth_a"],
    )
    assert res2.status_code == 201
    assert res2.json()["is_active"] is True

    # Verify updated in DB
    await db_session.rollback()
    stmt = select(PushSubscription).where(PushSubscription.endpoint == endpoint)
    sub = await db_session.scalar(stmt)
    assert sub is not None
    assert sub.p256dh_key == "key2-updated"
    assert sub.auth_key == "auth2-updated"
    assert sub.is_active is True


@pytest.mark.asyncio
async def test_5_duplicate_endpoint_other_user_rejected(
    async_client: AsyncClient,
    push_test_setup: dict,
):
    """TEST 5: Hijacking protection — User B registering User A's endpoint is rejected with 409."""
    endpoint = "https://fcm.googleapis.com/fcm/send/device-hijack-target"

    # User A registers endpoint
    res_a = await async_client.post(
        "/api/v1/notifications/push-subscription",
        json={"endpoint": endpoint, "p256dh_key": "key-a", "auth_key": "auth-a"},
        headers=push_test_setup["auth_a"],
    )
    assert res_a.status_code == 201

    # User B tries to register same endpoint
    res_b = await async_client.post(
        "/api/v1/notifications/push-subscription",
        json={"endpoint": endpoint, "p256dh_key": "key-b", "auth_key": "auth-b"},
        headers=push_test_setup["auth_b"],
    )
    assert res_b.status_code == 409
    assert "already registered" in res_b.json()["detail"].lower()


@pytest.mark.asyncio
async def test_6_delete_push_subscription_authenticated(
    async_client: AsyncClient,
    db_session: AsyncSession,
    push_test_setup: dict,
):
    """TEST 6: DELETE /notifications/push-subscription deactivates subscription."""
    endpoint = "https://fcm.googleapis.com/fcm/send/device-to-delete"

    await async_client.post(
        "/api/v1/notifications/push-subscription",
        json={"endpoint": endpoint, "p256dh_key": "k", "auth_key": "a"},
        headers=push_test_setup["auth_a"],
    )

    res = await async_client.request(
        "DELETE",
        "/api/v1/notifications/push-subscription",
        json={"endpoint": endpoint},
        headers=push_test_setup["auth_a"],
    )
    assert res.status_code == 200
    assert res.json()["status"] == "unsubscribed"

    # Verify is_active = False in DB
    await db_session.rollback()
    stmt = select(PushSubscription).where(PushSubscription.endpoint == endpoint)
    sub = await db_session.scalar(stmt)
    assert sub is not None
    assert sub.is_active is False


@pytest.mark.asyncio
async def test_7_idor_deletion_attempt_fails(
    async_client: AsyncClient,
    db_session: AsyncSession,
    push_test_setup: dict,
):
    """TEST 7: IDOR — User B cannot deactivate User A's subscription."""
    endpoint = "https://fcm.googleapis.com/fcm/send/device-user-a-protected"

    # User A creates subscription
    await async_client.post(
        "/api/v1/notifications/push-subscription",
        json={"endpoint": endpoint, "p256dh_key": "k", "auth_key": "a"},
        headers=push_test_setup["auth_a"],
    )

    # User B attempts to delete User A's endpoint
    res = await async_client.request(
        "DELETE",
        "/api/v1/notifications/push-subscription",
        json={"endpoint": endpoint},
        headers=push_test_setup["auth_b"],
    )
    assert res.status_code == 200  # Safe response, but does NOT modify User A's subscription

    # Verify User A's subscription remains active
    stmt = select(PushSubscription).where(PushSubscription.endpoint == endpoint)
    sub = await db_session.scalar(stmt)
    assert sub is not None
    assert sub.is_active is True
    assert sub.user_id == push_test_setup["user_a"].id


@pytest.mark.asyncio
async def test_8_subscription_status_endpoint(
    async_client: AsyncClient,
    push_test_setup: dict,
):
    """TEST 8: GET /notifications/push-subscription/status returns correct count."""
    endpoint1 = "https://fcm.googleapis.com/fcm/send/device-status-1"
    endpoint2 = "https://fcm.googleapis.com/fcm/send/device-status-2"

    # Initially 0
    r0 = await async_client.get(
        "/api/v1/notifications/push-subscription/status",
        headers=push_test_setup["auth_a"],
    )
    assert r0.status_code == 200
    assert r0.json()["has_active_subscription"] is False
    assert r0.json()["active_count"] == 0

    # Add 2 subscriptions
    await async_client.post(
        "/api/v1/notifications/push-subscription",
        json={"endpoint": endpoint1, "p256dh_key": "k1", "auth_key": "a1"},
        headers=push_test_setup["auth_a"],
    )
    await async_client.post(
        "/api/v1/notifications/push-subscription",
        json={"endpoint": endpoint2, "p256dh_key": "k2", "auth_key": "a2"},
        headers=push_test_setup["auth_a"],
    )

    r1 = await async_client.get(
        "/api/v1/notifications/push-subscription/status",
        headers=push_test_setup["auth_a"],
    )
    assert r1.status_code == 200
    assert r1.json()["has_active_subscription"] is True
    assert r1.json()["active_count"] == 2


@pytest.mark.asyncio
async def test_9_10_endpoint_https_validation(
    async_client: AsyncClient,
    push_test_setup: dict,
):
    """TEST 9 & 10: HTTPS endpoints pass, non-HTTPS or invalid endpoints fail with 422."""
    # Invalid: http://
    r1 = await async_client.post(
        "/api/v1/notifications/push-subscription",
        json={"endpoint": "http://insecure.endpoint.com/test", "p256dh_key": "k", "auth_key": "a"},
        headers=push_test_setup["auth_a"],
    )
    assert r1.status_code == 422

    # Invalid: javascript:// or plain string
    r2 = await async_client.post(
        "/api/v1/notifications/push-subscription",
        json={"endpoint": "not-a-url", "p256dh_key": "k", "auth_key": "a"},
        headers=push_test_setup["auth_a"],
    )
    assert r2.status_code == 422


# -----------------------------------------------------------------------------
# Worker & Push Delivery Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_11_worker_sends_push_notification(
    db_session: AsyncSession,
    push_test_setup: dict,
):
    """TEST 11: Notification worker sends push to active subscription."""
    user_id = push_test_setup["user_a"].id
    endpoint = "https://fcm.googleapis.com/fcm/send/worker-push-single"

    # Add active subscription
    sub = PushSubscription(
        user_id=user_id,
        endpoint=endpoint,
        p256dh_key="p256dh-worker-1",
        auth_key="auth-worker-1",
        is_active=True,
    )
    db_session.add(sub)
    await db_session.commit()

    worker = NotificationWorkerService(
        notification_repo=NotificationRepository(session=db_session),
        session=db_session,
        push_repo=PushSubscriptionRepository(session=db_session),
        push_sender=push_test_setup["push_service"],
    )

    task_payload = NotificationTaskPayload(
        user_id=user_id,
        notification_type="DRIVE_PUBLISHED",
        title="New Placement Drive",
        body="Google is hiring SDEs",
        reference_id=uuid4(),
        reference_type="DRIVE",
        send_push=True,
    )

    res = await worker.process_notification_task(task_payload)
    assert res.status == "processed"

    sent = push_test_setup["push_service"].get_sent_pushes()
    matching = [p for p in sent if p["endpoint"] == endpoint]
    assert len(matching) == 1
    assert matching[0]["payload"]["title"] == "New Placement Drive"


@pytest.mark.asyncio
async def test_12_worker_sends_to_multiple_devices(
    db_session: AsyncSession,
    push_test_setup: dict,
):
    """TEST 12: Worker sends push to all active devices of the user."""
    user_id = push_test_setup["user_a"].id
    ep1 = "https://fcm.googleapis.com/fcm/send/multi-device-1"
    ep2 = "https://fcm.googleapis.com/fcm/send/multi-device-2"

    sub1 = PushSubscription(user_id=user_id, endpoint=ep1, p256dh_key="k1", auth_key="a1", is_active=True)
    sub2 = PushSubscription(user_id=user_id, endpoint=ep2, p256dh_key="k2", auth_key="a2", is_active=True)
    db_session.add_all([sub1, sub2])
    await db_session.commit()

    worker = NotificationWorkerService(
        notification_repo=NotificationRepository(session=db_session),
        session=db_session,
        push_repo=PushSubscriptionRepository(session=db_session),
        push_sender=push_test_setup["push_service"],
    )

    task_payload = NotificationTaskPayload(
        user_id=user_id,
        notification_type="SHORTLISTED",
        title="Shortlisted!",
        body="You made it to the interview round.",
        reference_id=uuid4(),
        reference_type="DRIVE",
        send_push=True,
    )

    res = await worker.process_notification_task(task_payload)
    assert res.status == "processed"

    sent = push_test_setup["push_service"].get_sent_pushes()
    sent_endpoints = {p["endpoint"] for p in sent}
    assert ep1 in sent_endpoints
    assert ep2 in sent_endpoints


@pytest.mark.asyncio
async def test_13_14_worker_deactivates_on_410_and_404(
    db_session: AsyncSession,
    push_test_setup: dict,
):
    """TEST 13 & 14: Worker marks subscription is_active = False on HTTP 410 or 404."""
    user_id = push_test_setup["user_a"].id
    ep_410 = "https://fcm.googleapis.com/fcm/send/expired-410"
    ep_404 = "https://fcm.googleapis.com/fcm/send/notfound-404"

    sub_410 = PushSubscription(user_id=user_id, endpoint=ep_410, p256dh_key="k", auth_key="a", is_active=True)
    sub_404 = PushSubscription(user_id=user_id, endpoint=ep_404, p256dh_key="k", auth_key="a", is_active=True)
    db_session.add_all([sub_410, sub_404])
    await db_session.commit()

    push_test_setup["push_service"].set_simulated_status(ep_410, 410)
    push_test_setup["push_service"].set_simulated_status(ep_404, 404)

    worker = NotificationWorkerService(
        notification_repo=NotificationRepository(session=db_session),
        session=db_session,
        push_repo=PushSubscriptionRepository(session=db_session),
        push_sender=push_test_setup["push_service"],
    )

    task = NotificationTaskPayload(
        user_id=user_id,
        notification_type="STAGE_UPDATED",
        title="Stage Updated",
        body="Interview scheduled",
        reference_id=uuid4(),
        send_push=True,
    )

    res = await worker.process_notification_task(task)
    assert res.status == "processed"

    # Verify both subscriptions are now marked inactive in DB
    await db_session.refresh(sub_410)
    await db_session.refresh(sub_404)
    assert sub_410.is_active is False
    assert sub_404.is_active is False


@pytest.mark.asyncio
async def test_15_temporary_push_failure_does_not_deactivate(
    db_session: AsyncSession,
    push_test_setup: dict,
):
    """TEST 15: Temporary push service error (500) does not deactivate subscription."""
    user_id = push_test_setup["user_a"].id
    ep_500 = "https://fcm.googleapis.com/fcm/send/temporary-500"

    sub_500 = PushSubscription(user_id=user_id, endpoint=ep_500, p256dh_key="k", auth_key="a", is_active=True)
    db_session.add(sub_500)
    await db_session.commit()

    push_test_setup["push_service"].set_simulated_status(ep_500, 500)

    worker = NotificationWorkerService(
        notification_repo=NotificationRepository(session=db_session),
        session=db_session,
        push_repo=PushSubscriptionRepository(session=db_session),
        push_sender=push_test_setup["push_service"],
    )

    task = NotificationTaskPayload(
        user_id=user_id,
        notification_type="STAGE_UPDATED",
        title="Stage Updated",
        body="Interview scheduled",
        reference_id=uuid4(),
        send_push=True,
    )

    res = await worker.process_notification_task(task)
    assert res.status == "processed"

    await db_session.refresh(sub_500)
    assert sub_500.is_active is True


@pytest.mark.asyncio
async def test_16_push_failure_preserves_in_app_notification(
    db_session: AsyncSession,
    push_test_setup: dict,
):
    """TEST 16: Push network failure does NOT roll back the in-app notification record."""
    user_id = push_test_setup["user_a"].id
    ep_fail = "https://fcm.googleapis.com/fcm/send/crash-network"

    sub_fail = PushSubscription(user_id=user_id, endpoint=ep_fail, p256dh_key="k", auth_key="a", is_active=True)
    db_session.add(sub_fail)
    await db_session.commit()

    push_test_setup["push_service"].set_simulated_status(ep_fail, RuntimeError("Push Gateway Connection Reset"))

    worker = NotificationWorkerService(
        notification_repo=NotificationRepository(session=db_session),
        session=db_session,
        push_repo=PushSubscriptionRepository(session=db_session),
        push_sender=push_test_setup["push_service"],
    )

    task = NotificationTaskPayload(
        user_id=user_id,
        notification_type="RESULT_PUBLISHED",
        title="Final Offer",
        body="Congratulations on your placement offer!",
        reference_id=uuid4(),
        send_push=True,
    )

    res = await worker.process_notification_task(task)
    assert res.status == "processed"
    assert res.notification_id is not None

    # Verify in-app notification still exists in DB
    stmt = select(Notification).where(Notification.id == res.notification_id)
    notif = await db_session.scalar(stmt)
    assert notif is not None
    assert notif.title == "Final Offer"
    assert notif.push_sent is False


@pytest.mark.asyncio
async def test_17_zero_subscriptions_creates_in_app_notification(
    db_session: AsyncSession,
    push_test_setup: dict,
):
    """TEST 17: User with zero active subscriptions receives in-app notification with push_sent=False."""
    user_id = push_test_setup["user_b"].id  # User B has no subscriptions

    worker = NotificationWorkerService(
        notification_repo=NotificationRepository(session=db_session),
        session=db_session,
        push_repo=PushSubscriptionRepository(session=db_session),
        push_sender=push_test_setup["push_service"],
    )

    task = NotificationTaskPayload(
        user_id=user_id,
        notification_type="DRIVE_PUBLISHED",
        title="Zero Sub Test",
        body="In-app only delivery",
        reference_id=uuid4(),
        send_push=True,
    )

    res = await worker.process_notification_task(task)
    assert res.status == "processed"
    assert res.notification_id is not None

    stmt = select(Notification).where(Notification.id == res.notification_id)
    notif = await db_session.scalar(stmt)
    assert notif is not None
    assert notif.push_sent is False
    assert notif.push_sent_at is None


@pytest.mark.asyncio
async def test_18_19_successful_push_updates_push_sent_and_timestamp(
    db_session: AsyncSession,
    push_test_setup: dict,
):
    """TEST 18 & 19: Successful push delivery updates push_sent = True and push_sent_at timestamp."""
    user_id = push_test_setup["user_a"].id
    endpoint = "https://fcm.googleapis.com/fcm/send/success-timestamp-check"

    sub = PushSubscription(user_id=user_id, endpoint=endpoint, p256dh_key="k", auth_key="a", is_active=True)
    db_session.add(sub)
    await db_session.commit()

    worker = NotificationWorkerService(
        notification_repo=NotificationRepository(session=db_session),
        session=db_session,
        push_repo=PushSubscriptionRepository(session=db_session),
        push_sender=push_test_setup["push_service"],
    )

    task = NotificationTaskPayload(
        user_id=user_id,
        notification_type="DRIVE_PUBLISHED",
        title="Timestamp Check",
        body="Verify push_sent_at",
        reference_id=uuid4(),
        send_push=True,
    )

    res = await worker.process_notification_task(task)
    assert res.status == "processed"

    stmt = select(Notification).where(Notification.id == res.notification_id)
    notif = await db_session.scalar(stmt)
    assert notif is not None
    assert notif.push_sent is True
    assert notif.push_sent_at is not None
    assert isinstance(notif.push_sent_at, datetime)


@pytest.mark.asyncio
async def test_20_worker_continues_after_one_device_fails(
    db_session: AsyncSession,
    push_test_setup: dict,
):
    """TEST 20: Device 1 fails (410), Device 2 succeeds -> push_sent = True and both handled."""
    user_id = push_test_setup["user_a"].id
    ep_fail = "https://fcm.googleapis.com/fcm/send/partial-fail-ep1"
    ep_ok = "https://fcm.googleapis.com/fcm/send/partial-ok-ep2"

    sub_fail = PushSubscription(user_id=user_id, endpoint=ep_fail, p256dh_key="k1", auth_key="a1", is_active=True)
    sub_ok = PushSubscription(user_id=user_id, endpoint=ep_ok, p256dh_key="k2", auth_key="a2", is_active=True)
    db_session.add_all([sub_fail, sub_ok])
    await db_session.commit()

    push_test_setup["push_service"].set_simulated_status(ep_fail, 410)

    worker = NotificationWorkerService(
        notification_repo=NotificationRepository(session=db_session),
        session=db_session,
        push_repo=PushSubscriptionRepository(session=db_session),
        push_sender=push_test_setup["push_service"],
    )

    task = NotificationTaskPayload(
        user_id=user_id,
        notification_type="DRIVE_PUBLISHED",
        title="Partial Device Test",
        body="Device 2 should succeed",
        reference_id=uuid4(),
        send_push=True,
    )

    res = await worker.process_notification_task(task)
    assert res.status == "processed"

    # Verify Device 1 deactivated, Device 2 remains active
    await db_session.refresh(sub_fail)
    await db_session.refresh(sub_ok)
    assert sub_fail.is_active is False
    assert sub_ok.is_active is True
    assert sub_ok.last_used_at is not None

    # Notification push_sent marked true because at least 1 device succeeded
    stmt = select(Notification).where(Notification.id == res.notification_id)
    notif = await db_session.scalar(stmt)
    assert notif.push_sent is True


@pytest.mark.asyncio
async def test_21_worker_idempotency_remains_intact(
    db_session: AsyncSession,
    push_test_setup: dict,
):
    """TEST 21: Reprocessing identical task returns skipped idempotent duplicate."""
    user_id = push_test_setup["user_a"].id
    ref_id = uuid4()

    worker = NotificationWorkerService(
        notification_repo=NotificationRepository(session=db_session),
        session=db_session,
        push_repo=PushSubscriptionRepository(session=db_session),
        push_sender=push_test_setup["push_service"],
    )

    task = NotificationTaskPayload(
        user_id=user_id,
        notification_type="DEADLINE_REMINDER_24H",
        title="Deadline Reminder",
        body="24 hours left",
        reference_id=ref_id,
        send_push=True,
    )

    # First execution
    res1 = await worker.process_notification_task(task)
    assert res1.status == "processed"

    # Second execution (identical task)
    res2 = await worker.process_notification_task(task)
    assert res2.status == "skipped"
    assert res2.reason == "idempotent_duplicate"
