"""
Tests for Role-Based Access Control (RBAC).
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User


@pytest_asyncio.fixture
async def auth_headers(async_client: AsyncClient, db_session: AsyncSession) -> dict[str, dict[str, str]]:
    """Returns auth headers for both a STUDENT and an OFFICER."""
    # Create Student
    student = User(
        email="rbac_student@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="RBAC Student",
        is_active=True,
    )
    # Create Officer
    officer = User(
        email="rbac_officer@campusflow.com",
        password_hash=hash_password("password123"),
        role="OFFICER",
        full_name="RBAC Officer",
        is_active=True,
    )
    db_session.add_all([student, officer])
    await db_session.commit()

    # Login both
    r_student = await async_client.post(
        "/api/v1/auth/login", json={"email": student.email, "password": "password123"}
    )
    r_officer = await async_client.post(
        "/api/v1/auth/login", json={"email": officer.email, "password": "password123"}
    )

    return {
        "student": {"Authorization": f"Bearer {r_student.json()['access_token']}"},
        "officer": {"Authorization": f"Bearer {r_officer.json()['access_token']}"},
    }


@pytest.mark.asyncio
async def test_rbac_officer_access(async_client: AsyncClient, auth_headers: dict):
    response = await async_client.get(
        "/api/v1/branches/protected", headers=auth_headers["officer"]
    )
    assert response.status_code == 200
    assert "access" in response.json()["message"]


@pytest.mark.asyncio
async def test_rbac_student_denied(async_client: AsyncClient, auth_headers: dict):
    response = await async_client.get(
        "/api/v1/branches/protected", headers=auth_headers["student"]
    )
    assert response.status_code == 403
    assert response.json()["title"] == "Permission Denied"
