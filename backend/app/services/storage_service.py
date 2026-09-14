"""
CampusFlow — Storage Service Abstraction.

Provides interfaces and implementations for object storage:
- MockStorageService: Local filesystem and in-memory simulation for local development and test suites.
- GoogleCloudStorageService: Production implementation utilizing google-cloud-storage
  for V4 signed URLs and blob metadata verification.
"""
from __future__ import annotations

import logging
import os
from datetime import timedelta
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger(__name__)

# Shared in-memory metadata store across MockStorageService instances
_GLOBAL_MOCK_OBJECTS: dict[str, dict] = {}
_DEFAULT_STORAGE_DIR = Path(__file__).resolve().parent.parent.parent / ".local_storage"


class StorageService(Protocol):
    async def generate_upload_url(
        self,
        object_path: str,
        content_type: str,
        max_size_bytes: int,
        expires_in_seconds: int,
    ) -> str:
        """Generate a signed/local URL for uploading an object."""
        ...

    async def generate_download_url(
        self, object_path: str, expires_in_seconds: int
    ) -> str:
        """Generate a signed/local URL for downloading an object."""
        ...

    async def verify_object(self, object_path: str) -> dict | None:
        """
        Verify an object exists and return metadata.
        Returns a dictionary with 'size' (in bytes) and 'content_type',
        or None if the object does not exist.
        """
        ...

    async def save_object(
        self, object_path: str, content: bytes, content_type: str = "application/pdf"
    ) -> dict:
        """Save an object directly to storage and record metadata."""
        ...

    async def get_object(self, object_path: str) -> tuple[bytes, str] | None:
        """Retrieve raw content bytes and content type for an object."""
        ...


class MockStorageService:
    """Mock/local storage service for testing and local development without GCS."""

    def __init__(
        self, bucket_name: str = "campusflow-resumes", base_url: str | None = None, storage_dir: Path | None = None
    ) -> None:
        self.bucket_name = bucket_name
        self.base_url = (base_url or os.getenv("INTERNAL_SERVICE_URL", "http://localhost:8000")).rstrip("/")
        self.storage_dir = storage_dir or _DEFAULT_STORAGE_DIR
        self.mock_objects: dict[str, dict] = _GLOBAL_MOCK_OBJECTS

    async def generate_upload_url(
        self,
        object_path: str,
        content_type: str,
        max_size_bytes: int,
        expires_in_seconds: int,
    ) -> str:
        clean_path = object_path.lstrip("/")
        return f"{self.base_url}/api/v1/storage/upload/{clean_path}?sig=mockPUT"

    async def generate_download_url(
        self, object_path: str, expires_in_seconds: int
    ) -> str:
        clean_path = object_path.lstrip("/")
        return f"{self.base_url}/api/v1/storage/download/{clean_path}?sig=mockGET"

    async def save_object(
        self, object_path: str, content: bytes, content_type: str = "application/pdf"
    ) -> dict:
        clean_path = object_path.lstrip("/")
        file_path = self.storage_dir / clean_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)

        meta = {"size": len(content), "content_type": content_type}
        self.mock_objects[clean_path] = meta
        _GLOBAL_MOCK_OBJECTS[clean_path] = meta
        return meta

    async def get_object(self, object_path: str) -> tuple[bytes, str] | None:
        clean_path = object_path.lstrip("/")
        file_path = self.storage_dir / clean_path
        if file_path.is_file():
            meta = self.mock_objects.get(clean_path, {})
            content_type = meta.get("content_type", "application/pdf")
            return file_path.read_bytes(), content_type

        # Fallback to in-memory content if stored during mock tests
        if clean_path in self.mock_objects and "content" in self.mock_objects[clean_path]:
            return self.mock_objects[clean_path]["content"], self.mock_objects[clean_path].get("content_type", "application/pdf")

        return None

    async def verify_object(self, object_path: str) -> dict | None:
        clean_path = object_path.lstrip("/")
        # Check in-memory store first
        if clean_path in self.mock_objects:
            return self.mock_objects[clean_path]
        if clean_path in _GLOBAL_MOCK_OBJECTS:
            return _GLOBAL_MOCK_OBJECTS[clean_path]

        # Check local filesystem
        file_path = self.storage_dir / clean_path
        if file_path.is_file():
            meta = {
                "size": file_path.stat().st_size,
                "content_type": "application/pdf",
            }
            self.mock_objects[clean_path] = meta
            _GLOBAL_MOCK_OBJECTS[clean_path] = meta
            return meta

        return None


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

    async def save_object(
        self, object_path: str, content: bytes, content_type: str = "application/pdf"
    ) -> dict:
        client = self._get_client()
        bucket = client.bucket(self.bucket_name)
        blob = bucket.blob(object_path)
        blob.upload_from_string(content, content_type=content_type)
        return {"size": len(content), "content_type": content_type}

    async def get_object(self, object_path: str) -> tuple[bytes, str] | None:
        client = self._get_client()
        bucket = client.bucket(self.bucket_name)
        blob = bucket.get_blob(object_path)
        if blob is None:
            return None
        if hasattr(blob, "exists") and not blob.exists():
            return None
        return blob.download_as_bytes(), blob.content_type or "application/pdf"

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


# Singleton instance for local mock storage
_mock_storage_singleton: MockStorageService | None = None


def create_storage_service(
    provider: str, bucket_name: str, client: Any = None
) -> StorageService:
    global _mock_storage_singleton
    if provider == "mock":
        if _mock_storage_singleton is None or _mock_storage_singleton.bucket_name != bucket_name:
            _mock_storage_singleton = MockStorageService(bucket_name=bucket_name)
        return _mock_storage_singleton
    elif provider == "gcs":
        return GoogleCloudStorageService(bucket_name=bucket_name, client=client)
    raise ValueError(f"Unknown storage provider: {provider}")
