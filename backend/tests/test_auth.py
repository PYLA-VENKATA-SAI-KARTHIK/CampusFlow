"""
Tests for authentication logic.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User


@pytest.fixture
async def active_user(db_session: AsyncSession) -> User:
    user = User(
        email="student@campusflow.test",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Test Student",
        is_active=True,
        must_change_password=False,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
async def inactive_user(db_session: AsyncSession) -> User:
    user = User(
        email="inactive@campusflow.test",
        password_hash=hash_password("dummy"),
        role="STUDENT",
        full_name="Inactive Student",
        is_active=False,
        must_change_password=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, active_user: User):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": active_user.email, "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == active_user.email


@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient, active_user: User):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": active_user.email, "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["title"] == "Authentication Failed"


@pytest.mark.asyncio
async def test_login_inactive_user(async_client: AsyncClient, inactive_user: User):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": inactive_user.email, "password": "dummy"},
    )
    assert response.status_code == 401
    assert response.json()["title"] == "Account Not Active"


@pytest.mark.asyncio
async def test_get_me_unauthorized(async_client: AsyncClient):
    response = await async_client.get("/api/v1/auth/me")
    assert response.status_code == 401
