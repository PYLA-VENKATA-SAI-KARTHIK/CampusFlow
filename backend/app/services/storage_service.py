"""
CampusFlow — Storage Service Abstraction.

Provides interfaces and implementations for object storage:
- MockStorageService: In-memory simulation for local development and test suites.
- GoogleCloudStorageService: Production implementation utilizing google-cloud-storage
  for V4 signed URLs and blob metadata verification.
"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class StorageService(Protocol):
    async def generate_upload_url(
        self,
        object_path: str,
        content_type: str,
        max_size_bytes: int,
        expires_in_seconds: int,
    ) -> str:
        """Generate a signed URL for uploading an object."""
        ...

    async def generate_download_url(
        self, object_path: str, expires_in_seconds: int
    ) -> str:
        """Generate a signed URL for downloading an object."""
        ...

    async def verify_object(self, object_path: str) -> dict | None:
        """
        Verify an object exists and return metadata.
        Returns a dictionary with 'size' (in bytes) and 'content_type',
        or None if the object does not exist.
        """
        ...


class MockStorageService:
    """Mock storage service for testing and local development without GCS."""

    def __init__(self, bucket_name: str) -> None:
        self.bucket_name = bucket_name
        # Keep realistic mock state for tests to simulate uploads
        self.mock_objects: dict[str, dict] = {}

    async def generate_upload_url(
        self,
        object_path: str,
        content_type: str,
        max_size_bytes: int,
        expires_in_seconds: int,
    ) -> str:
        return f"https://storage.googleapis.com/{self.bucket_name}/{object_path}?sig=mockPUT"

    async def generate_download_url(
        self, object_path: str, expires_in_seconds: int
    ) -> str:
        return f"https://storage.googleapis.com/{self.bucket_name}/{object_path}?sig=mockGET"

    async def verify_object(self, object_path: str) -> dict | None:
        return self.mock_objects.get(object_path)


class GoogleCloudStorageService:
    """
    Production Google Cloud Storage service implementation.
    Generates V4 signed URLs for uploads and downloads, and checks object metadata.
    """

    def __init__(self, bucket_name: str, client: Any = None) -> None:
        if not bucket_name or not bucket_name.strip():
            raise ValueError("GCS bucket_name must be configured.")
        self.bucket_name = bucket_name.strip()
        self._client = client

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from google.cloud import storage  # type: ignore[import-not-found]

                self._client = storage.Client()
            except Exception as e:
                logger.error("Failed to initialize Google Cloud Storage client: %s", type(e).__name__)
                raise RuntimeError(
                    "Google Cloud Storage client could not be initialized. "
                    "Ensure google-cloud-storage is installed and GCP credentials are configured."
                ) from e
        return self._client

    async def generate_upload_url(
        self,
        object_path: str,
        content_type: str,
        max_size_bytes: int,
        expires_in_seconds: int,
    ) -> str:
        client = self._get_client()
        bucket = client.bucket(self.bucket_name)
        blob = bucket.blob(object_path)

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expires_in_seconds),
            method="PUT",
            content_type=content_type,
        )
        return url

    async def generate_download_url(
        self, object_path: str, expires_in_seconds: int
    ) -> str:
        client = self._get_client()
        bucket = client.bucket(self.bucket_name)
        blob = bucket.blob(object_path)

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expires_in_seconds),
            method="GET",
        )
        return url

    async def verify_object(self, object_path: str) -> dict | None:
        client = self._get_client()
        bucket = client.bucket(self.bucket_name)
        try:
            blob = bucket.get_blob(object_path)
        except Exception as e:
            logger.warning("Error fetching blob %s: %s", object_path, type(e).__name__)
            return None

        if blob is None:
            return None

        # If blob.exists() exists as method on SDK blob, verify it
        if hasattr(blob, "exists") and not blob.exists():
            return None

        size = getattr(blob, "size", None)
        content_type = getattr(blob, "content_type", None)
        return {
            "size": size,
            "content_type": content_type,
        }


def create_storage_service(
    provider: str, bucket_name: str, client: Any = None
) -> StorageService:
    if provider == "mock":
        return MockStorageService(bucket_name=bucket_name)
    elif provider == "gcs":
        return GoogleCloudStorageService(bucket_name=bucket_name, client=client)
    raise ValueError(f"Unknown storage provider: {provider}")
