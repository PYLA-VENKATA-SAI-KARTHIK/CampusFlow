from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.dependencies import UserContext, get_current_user, get_db
from app.repositories.notification_repository import NotificationRepository
from app.repositories.push_subscription_repository import PushSubscriptionRepository
from app.schemas.common import PaginatedResponse
from app.schemas.notification import NotificationResponse
from app.schemas.push_subscription import (
    PushStatusResponse,
    PushSubscriptionCreate,
    PushSubscriptionDelete,
    PushSubscriptionResponse,
    PushUnsubscribeResponse,
    VapidPublicKeyResponse,
)

router = APIRouter()


def get_notif_repo(session: AsyncSession = Depends(get_db)) -> NotificationRepository:
    return NotificationRepository(session)


def get_push_repo(session: AsyncSession = Depends(get_db)) -> PushSubscriptionRepository:
    return PushSubscriptionRepository(session)


@router.get("/vapid-public-key", response_model=VapidPublicKeyResponse)
async def get_vapid_public_key() -> VapidPublicKeyResponse:
    """Return the VAPID public key required for frontend pushManager subscription."""
    settings = get_settings()
    return VapidPublicKeyResponse(vapid_public_key=settings.vapid_public_key)


@router.post(
    "/push-subscription",
    response_model=PushSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register browser push subscription",
)
async def register_push_subscription(
    payload: PushSubscriptionCreate,
    current_user: Annotated[UserContext, Depends(get_current_user)],
    repo: Annotated[PushSubscriptionRepository, Depends(get_push_repo)],
) -> PushSubscriptionResponse:
    """Store or reactivate a browser push subscription for the authenticated user."""
    subscription = await repo.upsert_subscription(
        user_id=current_user.user_id,
        endpoint=payload.endpoint,
        p256dh_key=payload.p256dh_key,
        auth_key=payload.auth_key,
        user_agent=payload.user_agent,
    )
    await repo.session.commit()
    return subscription


@router.delete(
    "/push-subscription",
    response_model=PushUnsubscribeResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove browser push subscription",
)
async def remove_push_subscription(
    payload: PushSubscriptionDelete,
    current_user: Annotated[UserContext, Depends(get_current_user)],
    repo: Annotated[PushSubscriptionRepository, Depends(get_push_repo)],
) -> PushUnsubscribeResponse:
    """Deactivate a browser push subscription owned by the authenticated user."""
    await repo.deactivate_by_endpoint(
        user_id=current_user.user_id,
        endpoint=payload.endpoint,
    )
    await repo.session.commit()
    return PushUnsubscribeResponse(status="unsubscribed")


@router.get(
    "/push-subscription/status",
    response_model=PushStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Check active push subscriptions status",
)
async def get_push_subscription_status(
    current_user: Annotated[UserContext, Depends(get_current_user)],
    repo: Annotated[PushSubscriptionRepository, Depends(get_push_repo)],
) -> PushStatusResponse:
    """Check if the authenticated user has active push subscriptions."""
    count = await repo.count_active_for_user(user_id=current_user.user_id)
    return PushStatusResponse(
        has_active_subscription=count > 0,
        active_count=count,
    )


@router.get("", response_model=PaginatedResponse[NotificationResponse])
async def list_notifications(
    current_user: Annotated[UserContext, Depends(get_current_user)],
    repo: Annotated[NotificationRepository, Depends(get_notif_repo)],
    is_read: bool | None = Query(None, description="Filter by read status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[NotificationResponse]:
    """List the authenticated user's in-app notifications."""
    skip = (page - 1) * page_size
    notifications, total = await repo.list_for_user(
        user_id=current_user.user_id,
        is_read=is_read,
        skip=skip,
        limit=page_size,
    )
    return PaginatedResponse(
        items=list(notifications),
        total=total,
        page=page,
        page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.post("/read-all", response_model=dict)
async def mark_all_read(
    current_user: Annotated[UserContext, Depends(get_current_user)],
    repo: Annotated[NotificationRepository, Depends(get_notif_repo)],
) -> dict:
    """Mark all of the authenticated user's notifications as read."""
    count = await repo.mark_all_read(user_id=current_user.user_id)
    await repo.session.commit()
    return {"marked_read": count}


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    current_user: Annotated[UserContext, Depends(get_current_user)],
    repo: Annotated[NotificationRepository, Depends(get_notif_repo)],
) -> NotificationResponse:
    """Mark a single notification as read. Idempotent. IDOR-protected."""
    notification = await repo.get_by_id(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found.")

    # IDOR: notification must belong to the authenticated user
    if str(notification.user_id) != str(current_user.user_id):
        raise HTTPException(status_code=403, detail="Access forbidden.")

    notification = await repo.mark_read(notification)
    await repo.session.commit()
    await repo.session.refresh(notification)
    return notification

