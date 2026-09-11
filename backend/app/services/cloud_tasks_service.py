"""
CampusFlow — Cloud Tasks Service Abstraction

Provides a clean interface for enqueueing asynchronous background tasks.
- MockCloudTasksService: In-memory task queue for testing and local development.
- GoogleCloudTasksService: Production Cloud Tasks implementation.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Protocol
from uuid import uuid4

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class CloudTasksService(Protocol):
    """Protocol defining the interface for task enqueueing."""

    async def enqueue_notification_task(
        self,
        payload: dict[str, Any],
        task_name: str | None = None,
        schedule_time_seconds: int | None = None,
    ) -> str:
        """
        Enqueue a notification task.
        Returns the unique task identifier / path.
        """
        ...


class MockCloudTasksService:
    """
    In-memory mock Cloud Tasks service for development and testing.
    Records all enqueued tasks in-memory for assertion and inspectability.
    """

    def __init__(
        self,
        queue_name: str = "campusflow-notifications",
        location: str = "asia-south1",
        project_id: str = "mock-project",
    ) -> None:
        self.queue_name = queue_name
        self.location = location
        self.project_id = project_id
        self.enqueued_tasks: list[dict[str, Any]] = []

    async def enqueue_notification_task(
        self,
        payload: dict[str, Any],
        task_name: str | None = None,
        schedule_time_seconds: int | None = None,
    ) -> str:
        task_id = task_name or str(uuid4())
        task_path = (
            f"projects/{self.project_id}/locations/{self.location}"
            f"/queues/{self.queue_name}/tasks/{task_id}"
        )
        task_record = {
            "task_id": task_id,
            "task_path": task_path,
            "queue": self.queue_name,
            "payload": payload,
            "schedule_time_seconds": schedule_time_seconds,
        }
        self.enqueued_tasks.append(task_record)
        logger.debug("MockCloudTasksService enqueued task: %s", task_path)
        return task_path

    def get_tasks(self) -> list[dict[str, Any]]:
        """Return a copy of all enqueued tasks."""
        return list(self.enqueued_tasks)

    def clear(self) -> None:
        """Clear all recorded tasks."""
        self.enqueued_tasks.clear()


class GoogleCloudTasksService:
    """
    Production Google Cloud Tasks implementation.
    Enqueues HTTP tasks targeted at the internal worker endpoint.
    """

    def __init__(
        self,
        project_id: str,
        location: str,
        queue_name: str,
        service_account_email: str,
        target_url: str,
    ) -> None:
        self.project_id = project_id
        self.location = location
        self.queue_name = queue_name
        self.service_account_email = service_account_email
        self.target_url = target_url

        try:
            from google.cloud import tasks_v2  # type: ignore[import-not-found]
            self.client = tasks_v2.CloudTasksClient()
            self.parent = self.client.queue_path(project_id, location, queue_name)
        except (ImportError, Exception):
            self.client = None
            self.parent = None
            logger.warning(
                "google-cloud-tasks is not installed or initialized. GoogleCloudTasksService cannot initialize client."
            )

    async def enqueue_notification_task(
        self,
        payload: dict[str, Any],
        task_name: str | None = None,
        schedule_time_seconds: int | None = None,
    ) -> str:
        if self.client is None:
            raise NotImplementedError(
                "Google Cloud Tasks client library is not installed or configured."
            )

        from google.cloud import tasks_v2  # type: ignore[import-not-found]

        task: dict[str, Any] = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{self.target_url.rstrip('/')}/internal/tasks/send-notification",
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(payload).encode("utf-8"),
                "oidc_token": {
                    "service_account_email": self.service_account_email,
                    "audience": self.target_url,
                },
            }
        }

        if task_name:
            task["name"] = self.client.task_path(
                self.project_id, self.location, self.queue_name, task_name
            )

        response = self.client.create_task(
            request={"parent": self.parent, "task": task}
        )
        return response.name


def create_cloud_tasks_service(
    provider: str,
    settings: Settings | None = None,
) -> CloudTasksService:
    """Factory creating the appropriate Cloud Tasks provider."""
    cfg = settings or get_settings()
    if provider == "mock":
        return MockCloudTasksService(
            queue_name=cfg.cloud_tasks_queue_name,
            location=cfg.cloud_tasks_location,
            project_id=cfg.cloud_tasks_project_id or "mock-project",
        )
    elif provider == "cloud_tasks":
        return GoogleCloudTasksService(
            project_id=cfg.cloud_tasks_project_id,
            location=cfg.cloud_tasks_location,
            queue_name=cfg.cloud_tasks_queue_name,
            service_account_email=cfg.cloud_tasks_service_account_email,
            target_url=cfg.internal_service_url,
        )
    raise ValueError(f"Unknown notification task provider: {provider}")


_cloud_tasks_service_instance: CloudTasksService | None = None


def get_cloud_tasks_service() -> CloudTasksService:
    """Returns the configured Cloud Tasks service singleton."""
    global _cloud_tasks_service_instance
    if _cloud_tasks_service_instance is None:
        settings = get_settings()
        _cloud_tasks_service_instance = create_cloud_tasks_service(
            provider=settings.notification_task_provider,
            settings=settings,
        )
    return _cloud_tasks_service_instance
