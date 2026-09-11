"""
Push Sender Service abstraction.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from app.core.config import get_settings
from app.models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)


@dataclass
class PushDeliveryResult:
    status: Literal["success", "expired", "failed"]
    status_code: int | None = None
    error_message: str | None = None


class PushSenderService(Protocol):
    """Protocol for Web Push delivery."""

    async def send_notification(
        self,
        subscription: PushSubscription,
        payload: dict[str, Any],
    ) -> PushDeliveryResult:
        ...


class MockPushSenderService:
    """Mock push service for development and testing."""

    def __init__(self) -> None:
        self._sent_pushes: list[dict[str, Any]] = []
        self._simulated_statuses: dict[str, int | Exception] = {}

    def set_simulated_status(self, endpoint: str, status_or_exc: int | Exception) -> None:
        """Simulate a specific HTTP status code or exception for an endpoint."""
        self._simulated_statuses[endpoint] = status_or_exc

    def clear(self) -> None:
        self._sent_pushes.clear()
        self._simulated_statuses.clear()

    def get_sent_pushes(self) -> list[dict[str, Any]]:
        return list(self._sent_pushes)

    async def send_notification(
        self,
        subscription: PushSubscription,
        payload: dict[str, Any],
    ) -> PushDeliveryResult:
        endpoint = subscription.endpoint

        # Check for simulated failures/exceptions
        if endpoint in self._simulated_statuses:
            sim = self._simulated_statuses[endpoint]
            if isinstance(sim, Exception):
                logger.warning("Simulating push exception for endpoint %s: %s", endpoint, sim)
                return PushDeliveryResult(
                    status="failed",
                    error_message=str(sim),
                )
            if sim in (404, 410):
                logger.info("Simulating HTTP %d (expired) for endpoint %s", sim, endpoint)
                return PushDeliveryResult(
                    status="expired",
                    status_code=sim,
                    error_message="Subscription expired or not found",
                )
            elif sim >= 400:
                logger.warning("Simulating HTTP %d failure for endpoint %s", sim, endpoint)
                return PushDeliveryResult(
                    status="failed",
                    status_code=sim,
                    error_message=f"HTTP {sim} error",
                )

        record = {
            "subscription_id": str(subscription.id),
            "user_id": str(subscription.user_id),
            "endpoint": subscription.endpoint,
            "payload": payload,
        }
        self._sent_pushes.append(record)
        logger.info("Mock push delivered to endpoint: %s (user: %s)", endpoint, subscription.user_id)
        return PushDeliveryResult(status="success", status_code=201)


class PyWebPushSenderService:
    """Production Web Push sender using pywebpush."""

    def __init__(self, vapid_private_key: str, vapid_claims: dict[str, str]) -> None:
        self.vapid_private_key = vapid_private_key
        self.vapid_claims = vapid_claims

    async def send_notification(
        self,
        subscription: PushSubscription,
        payload: dict[str, Any],
    ) -> PushDeliveryResult:
        try:
            from pywebpush import webpush, WebPushException  # type: ignore[import-not-found]
        except ImportError:
            logger.error("pywebpush package is not installed.")
            return PushDeliveryResult(
                status="failed",
                error_message="pywebpush package not installed",
            )

        subscription_info = {
            "endpoint": subscription.endpoint,
            "keys": {
                "p256dh": subscription.p256dh_key,
                "auth": subscription.auth_key,
            },
        }

        try:
            response = webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=self.vapid_private_key,
                vapid_claims=self.vapid_claims,
            )
            return PushDeliveryResult(
                status="success",
                status_code=response.status_code if response else 200,
            )
        except WebPushException as e:
            status_code = getattr(e.response, "status_code", None) if hasattr(e, "response") else None
            if status_code in (404, 410):
                logger.info("Subscription %s expired (HTTP %s)", subscription.id, status_code)
                return PushDeliveryResult(
                    status="expired",
                    status_code=status_code,
                    error_message=str(e),
                )
            logger.error("WebPush failed for subscription %s: %s", subscription.id, str(e))
            return PushDeliveryResult(
                status="failed",
                status_code=status_code,
                error_message=str(e),
            )
        except Exception as e:
            logger.error("Unexpected push delivery error: %s", str(e))
            return PushDeliveryResult(
                status="failed",
                error_message=str(e),
            )


_global_mock_push_sender: MockPushSenderService | None = None


def get_push_sender_service() -> PushSenderService:
    global _global_mock_push_sender
    settings = get_settings()

    if settings.push_provider == "webpush" and settings.app_env in ("production", "staging"):
        return PyWebPushSenderService(
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={"sub": settings.vapid_subject},
        )

    if _global_mock_push_sender is None:
        _global_mock_push_sender = MockPushSenderService()
    return _global_mock_push_sender
