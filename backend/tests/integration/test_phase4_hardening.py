"""
Phase 4.1 — Local Hardening & Code Gaps Integration & Unit Tests.

Covers:
1. Rate limiting on /auth/login and /auth/activate (within limit vs exceeding limit 429)
2. Security headers and CSP validation (environment-aware HSTS, CSP directives, nosniff, DENY)
3. Database-level audit_logs immutability (INSERT succeeds, UPDATE rejected, DELETE rejected)
4. GoogleCloudStorageService unit tests with mocks (signed upload/download URLs, object verification)
"""
import pytest
from datetime import timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.config import get_settings
from app.core.security import hash_password
from app.core.security_headers import DEFAULT_CSP, SecurityHeadersMiddleware
from app.models.audit_log import AuditLog
from app.models.user import User
from app.services.storage_service import (
    GoogleCloudStorageService,
    MockStorageService,
    create_storage_service,
)


# ===========================================================================
# 1. Rate Limiting Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_01_login_rate_limiting_exceeded(async_client: AsyncClient):
    """
    Test that rapid repeated POST /api/v1/auth/login requests exceed the configured
    rate limit (10/minute) and return HTTP 429 Too Many Requests.
    """
    url = "/api/v1/auth/login"
    payload = {"email": "ratelimit_test@campus.edu", "password": "wrongpassword123"}

    # Send requests up to limit
    responses = []
    for _ in range(15):
        resp = await async_client.post(url, json=payload)
        responses.append(resp.status_code)

    # At least one request should have triggered 429 Too Many Requests
    assert 429 in responses, f"Expected 429 in responses, but got: {responses}"


@pytest.mark.asyncio
async def test_02_activate_rate_limiting_exceeded(async_client: AsyncClient):
    """
    Test that rapid repeated POST /api/v1/auth/activate requests exceed the configured
    rate limit (5/15minutes) and return HTTP 429 Too Many Requests.
    """
    url = "/api/v1/auth/activate"
    payload = {"activation_token": "dummytoken", "new_password": "newsecurepassword123"}

    responses = []
    for _ in range(10):
        resp = await async_client.post(url, json=payload)
        responses.append(resp.status_code)

    assert 429 in responses, f"Expected 429 in activate responses, but got: {responses}"


# ===========================================================================
# 2. Security Headers & CSP Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_03_security_headers_present_on_endpoints(async_client: AsyncClient):
    """
    Verify all standard defensive security headers and strict minimum CSP are returned on responses.
    """
    resp = await async_client.get("/api/v1/health")
    assert resp.status_code == 200

    headers = resp.headers

    # CSP verification
    assert "Content-Security-Policy" in headers
    csp = headers["Content-Security-Policy"]

    # Approved baseline directives
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    # Critical security check: unsafe-inline MUST NOT be allowed for script-src
    assert "script-src 'self' 'unsafe-inline'" not in csp
    assert "style-src 'self' 'unsafe-inline'" in csp
    # External fonts must NOT be allowed since app uses system fonts
    assert "fonts.googleapis.com" not in csp
    assert "fonts.gstatic.com" not in csp
    assert "font-src 'self' data:" in csp
    # img-src must only permit self, data, blob, and storage.googleapis.com (no arbitrary https:)
    assert "img-src 'self' data: blob: https://storage.googleapis.com" in csp
    assert "https: " not in csp.replace("https://storage.googleapis.com", "").replace("https://*.run.app", "")
    assert "connect-src 'self' http://localhost:8000 https://storage.googleapis.com https://*.run.app" in csp
    assert "worker-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "object-src 'none'" in csp
    assert "base-uri 'self'" in csp
    assert "form-action 'self'" in csp

    # Defensive headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Permissions-Policy" in headers

    # Environment-aware HSTS: In testing mode, HSTS must NOT be enforced
    assert "Strict-Transport-Security" not in headers


@pytest.mark.asyncio
async def test_04_hsts_enforced_in_production_mode():
    """
    Verify that when SecurityHeadersMiddleware is initialized with is_production=True,
    Strict-Transport-Security is injected.
    """
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route
    from httpx import ASGITransport

    async def dummy_endpoint(request):
        return PlainTextResponse("OK")

    test_app = Starlette(routes=[Route("/", dummy_endpoint)])
    test_app.add_middleware(SecurityHeadersMiddleware, is_production=True)

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="https://testserver") as test_client:
        resp = await test_client.get("/")
        assert resp.status_code == 200
        assert "Strict-Transport-Security" in resp.headers
        assert "max-age=31536000" in resp.headers["Strict-Transport-Security"]


# ===========================================================================
# 3. Database Audit Log Immutability Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_05_audit_log_insert_succeeds(db_session):
    """
    Verify that standard INSERT into audit_logs table succeeds without issue.
    """
    # Create test user
    user = User(
        id=uuid4(),
        email=f"audit_user_{uuid4().hex[:6]}@campus.edu",
        full_name="Audit Test User",
        role="ADMIN",
        password_hash=hash_password("password123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    audit_entry = AuditLog(
        id=uuid4(),
        performed_by_user_id=user.id,
        action="TEST_MUTATION",
        entity_type="TEST",
        entity_id=user.id,
        new_state={"key": "initial_value"},
    )
    db_session.add(audit_entry)
    await db_session.commit()

    # Re-fetch to ensure entry was stored
    result = await db_session.execute(
        text(f"SELECT action FROM campusflow.audit_logs WHERE id = '{audit_entry.id}'")
    )
    row = result.fetchone()
    assert row is not None
    assert row[0] == "TEST_MUTATION"


@pytest.mark.asyncio
async def test_06_audit_log_update_fails_due_to_trigger(db_session):
    """
    Verify that attempting to UPDATE an existing row in audit_logs raises an exception
    from the PostgreSQL trigger function.
    """
    log_id = uuid4()
    audit_entry = AuditLog(
        id=log_id,
        action="ORIGINAL_ACTION",
        entity_type="SYSTEM",
        new_state={"status": "ok"},
    )
    db_session.add(audit_entry)
    await db_session.commit()

    # Attempt to UPDATE audit_logs
    with pytest.raises(DBAPIError) as exc_info:
        await db_session.execute(
            text(f"UPDATE campusflow.audit_logs SET action = 'ALTERED_ACTION' WHERE id = '{log_id}'")
        )
        await db_session.commit()

    assert "audit_logs table is immutable" in str(exc_info.value)
    await db_session.rollback()


@pytest.mark.asyncio
async def test_07_audit_log_delete_fails_due_to_trigger(db_session):
    """
    Verify that attempting to DELETE an existing row in audit_logs raises an exception
    from the PostgreSQL trigger function.
    """
    log_id = uuid4()
    audit_entry = AuditLog(
        id=log_id,
        action="TO_BE_DELETED",
        entity_type="SYSTEM",
        new_state={"status": "ok"},
    )
    db_session.add(audit_entry)
    await db_session.commit()

    # Attempt to DELETE from audit_logs
    with pytest.raises(DBAPIError) as exc_info:
        await db_session.execute(
            text(f"DELETE FROM campusflow.audit_logs WHERE id = '{log_id}'")
        )
        await db_session.commit()

    assert "audit_logs table is immutable" in str(exc_info.value)
    await db_session.rollback()


# ===========================================================================
# 4. GoogleCloudStorageService Unit Tests (Mocked)
# ===========================================================================

@pytest.mark.asyncio
async def test_08_gcs_service_generate_upload_url():
    """
    Verify GoogleCloudStorageService generate_upload_url delegates correctly to blob.generate_signed_url.
    """
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_blob = MagicMock()

    mock_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob
    mock_blob.generate_signed_url.return_value = "https://storage.googleapis.com/test-bucket/resumes/user1.pdf?sig=v4PUT"

    service = GoogleCloudStorageService(bucket_name="test-bucket", client=mock_client)
    url = await service.generate_upload_url(
        object_path="resumes/user1.pdf",
        content_type="application/pdf",
        max_size_bytes=5 * 1024 * 1024,
        expires_in_seconds=900,
    )

    assert "sig=v4PUT" in url
    mock_client.bucket.assert_called_once_with("test-bucket")
    mock_bucket.blob.assert_called_once_with("resumes/user1.pdf")
    mock_blob.generate_signed_url.assert_called_once_with(
        version="v4",
        expiration=timedelta(seconds=900),
        method="PUT",
        content_type="application/pdf",
    )


@pytest.mark.asyncio
async def test_09_gcs_service_generate_download_url():
    """
    Verify GoogleCloudStorageService generate_download_url delegates correctly to blob.generate_signed_url.
    """
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_blob = MagicMock()

    mock_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob
    mock_blob.generate_signed_url.return_value = "https://storage.googleapis.com/test-bucket/resumes/user1.pdf?sig=v4GET"

    service = GoogleCloudStorageService(bucket_name="test-bucket", client=mock_client)
    url = await service.generate_download_url(
        object_path="resumes/user1.pdf",
        expires_in_seconds=900,
    )

    assert "sig=v4GET" in url
    mock_blob.generate_signed_url.assert_called_once_with(
        version="v4",
        expiration=timedelta(seconds=900),
        method="GET",
    )


@pytest.mark.asyncio
async def test_10_gcs_service_verify_object_found():
    """
    Verify GoogleCloudStorageService verify_object returns size and content_type when blob exists.
    """
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_blob = MagicMock()

    mock_blob.exists.return_value = True
    mock_blob.size = 1048576
    mock_blob.content_type = "application/pdf"

    mock_client.bucket.return_value = mock_bucket
    mock_bucket.get_blob.return_value = mock_blob

    service = GoogleCloudStorageService(bucket_name="test-bucket", client=mock_client)
    meta = await service.verify_object("resumes/user1.pdf")

    assert meta is not None
    assert meta["size"] == 1048576
    assert meta["content_type"] == "application/pdf"


@pytest.mark.asyncio
async def test_11_gcs_service_verify_object_not_found():
    """
    Verify GoogleCloudStorageService verify_object returns None when blob is not found.
    """
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_client.bucket.return_value = mock_bucket
    mock_bucket.get_blob.return_value = None

    service = GoogleCloudStorageService(bucket_name="test-bucket", client=mock_client)
    meta = await service.verify_object("resumes/nonexistent.pdf")

    assert meta is None


@pytest.mark.asyncio
async def test_12_storage_factory_providers():
    """
    Verify create_storage_service factory returns appropriate implementations.
    """
    mock_svc = create_storage_service(provider="mock", bucket_name="test-bkt")
    assert isinstance(mock_svc, MockStorageService)

    gcs_svc = create_storage_service(provider="gcs", bucket_name="test-bkt", client=MagicMock())
    assert isinstance(gcs_svc, GoogleCloudStorageService)

    with pytest.raises(ValueError):
        create_storage_service(provider="s3_unsupported", bucket_name="test-bkt")


@pytest.mark.asyncio
async def test_13_gcs_service_validation_and_safe_failure():
    """
    Verify GoogleCloudStorageService requires non-empty bucket_name and fails safely
    without exposing credentials or secrets if GCS initialization fails.
    """
    # Empty bucket_name must raise ValueError
    with pytest.raises(ValueError) as exc_info:
        GoogleCloudStorageService(bucket_name="")
    assert "bucket_name must be configured" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info2:
        GoogleCloudStorageService(bucket_name="   ")
    assert "bucket_name must be configured" in str(exc_info2.value)

    # Missing client initialization fails safely with RuntimeError
    service = GoogleCloudStorageService(bucket_name="valid-bucket")
    # Simulate client creation failure (e.g. no GCP credentials in test environment)
    with patch("google.cloud.storage.Client", side_effect=Exception("Private Key Error")):
        with pytest.raises(RuntimeError) as exc_info3:
            service._get_client()
        # Ensure error message does not expose underlying key or internal details
        assert "Google Cloud Storage client could not be initialized" in str(exc_info3.value)
        assert "Private Key Error" not in str(exc_info3.value)


@pytest.mark.asyncio
async def test_14_mock_storage_service_full_lifecycle():
    """
    Verify MockStorageService full lifecycle: upload URL generation, simulated upload,
    object verification, and download URL generation.
    """
    mock_storage = MockStorageService(bucket_name="campusflow-resumes")
    path = "resumes/student-123/resume.pdf"

    # Upload URL
    up_url = await mock_storage.generate_upload_url(
        object_path=path,
        content_type="application/pdf",
        max_size_bytes=5242880,
        expires_in_seconds=900,
    )
    assert path in up_url
    assert "sig=mockPUT" in up_url

    # Object not yet in storage
    meta_before = await mock_storage.verify_object(path)
    assert meta_before is None

    # Simulate upload
    mock_storage.mock_objects[path] = {"size": 2048, "content_type": "application/pdf"}
    meta_after = await mock_storage.verify_object(path)
    assert meta_after == {"size": 2048, "content_type": "application/pdf"}

    # Download URL
    down_url = await mock_storage.generate_download_url(
        object_path=path,
        expires_in_seconds=900,
    )
    assert path in down_url
    assert "sig=mockGET" in down_url


@pytest.mark.asyncio
async def test_15_gcs_verify_object_handles_unexpected_exception():
    """
    Verify GoogleCloudStorageService verify_object gracefully returns None if an unexpected
    exception occurs during get_blob (e.g. network error, API quota error).
    """
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_client.bucket.return_value = mock_bucket
    mock_bucket.get_blob.side_effect = Exception("Transient GCS API Error")

    service = GoogleCloudStorageService(bucket_name="test-bucket", client=mock_client)
    meta = await service.verify_object("resumes/any.pdf")
    assert meta is None


@pytest.mark.asyncio
async def test_16_resume_confirm_blocks_path_traversal(async_client: AsyncClient, db_session):
    """
    Verify that confirm_resume_upload strictly blocks path traversal sequences (..)
    even if the object path begins with the user's expected prefix.
    """
    # Create and authenticate a student
    student_id = uuid4()
    student_user = User(
        id=student_id,
        email="traversal.student@campus.edu",
        full_name="Traversal Student",
        role="STUDENT",
        password_hash=hash_password("password123"),
        is_active=True,
    )
    db_session.add(student_user)
    await db_session.commit()

    # Login
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "traversal.student@campus.edu", "password": "password123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    auth_header = {"Authorization": f"Bearer {token}"}

    # Attempt path traversal
    traversal_path = f"resumes/{student_id}/../../etc/passwd.pdf"
    resp = await async_client.post(
        "/api/v1/students/me/resume-confirm",
        headers=auth_header,
        json={"object_path": traversal_path},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == "Invalid object path."
