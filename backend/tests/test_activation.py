"""
Tests for account activation.
"""
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_secure_token, hash_password, hash_token
from app.models.account_activation import AccountActivation
from app.models.user import User


@pytest.fixture
async def unactivated_user(db_session: AsyncSession) -> tuple[User, str]:
    user = User(
        email="unactivated@campusflow.test",
        password_hash=hash_password("dummy"),
        role="STUDENT",
        full_name="Unactivated Student",
        is_active=False,
        must_change_password=True,
    )
    db_session.add(user)
    await db_session.commit()

    raw_token = generate_secure_token()
    activation = AccountActivation(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    db_session.add(activation)
    await db_session.commit()

    return user, raw_token


@pytest.fixture
async def expired_activation_user(db_session: AsyncSession) -> tuple[User, str]:
    user = User(
        email="expired@campusflow.test",
        password_hash=hash_password("dummy"),
        role="STUDENT",
        full_name="Expired Student",
        is_active=False,
        must_change_password=True,
    )
    db_session.add(user)
    await db_session.commit()

    raw_token = generate_secure_token()
    activation = AccountActivation(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
    )
    db_session.add(activation)
    await db_session.commit()

    return user, raw_token


@pytest.mark.asyncio
async def test_activate_success(
    async_client: AsyncClient, unactivated_user: tuple[User, str], db_session: AsyncSession
):
    user, raw_token = unactivated_user
    response = await async_client.post(
        "/api/v1/auth/activate",
        json={"activation_token": raw_token, "new_password": "NewSecurePassword123!"},
    )
    assert response.status_code == 204

    # Verify DB state
    await db_session.refresh(user)
    assert user.is_active is True
    assert user.must_change_password is False


@pytest.mark.asyncio
async def test_activate_expired_token(
    async_client: AsyncClient, expired_activation_user: tuple[User, str]
):
    _, raw_token = expired_activation_user
    response = await async_client.post(
        "/api/v1/auth/activate",
        json={"activation_token": raw_token, "new_password": "NewSecurePassword123!"},
    )
    assert response.status_code == 400
    assert response.json()["title"] == "Activation Token Expired"


@pytest.mark.asyncio
async def test_activate_invalid_token(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/activate",
        json={"activation_token": "invalid_random_token_string", "new_password": "NewSecurePassword123!"},
    )
    assert response.status_code == 400
    assert response.json()["title"] == "Activation Token Invalid"
