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
        email="student@campusflow.com",
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
        email="inactive@campusflow.com",
        password_hash=hash_password("dummy"),
        role="STUDENT",
        full_name="Inactive Student",
        is_active=False,
        must_change_password=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user


from uuid import uuid4
from app.models.student_profile import StudentProfile
from app.models.branch import Branch


@pytest.fixture
async def branch(db_session: AsyncSession) -> Branch:
    b = Branch(code="CSE", name="Computer Science and Engineering", is_active=True)
    db_session.add(b)
    await db_session.commit()
    return b


@pytest.fixture
async def active_student(db_session: AsyncSession, branch: Branch) -> tuple[User, StudentProfile]:
    user = User(
        id=uuid4(),
        email="student99@campusflow.com",
        password_hash=hash_password("Password@123"),
        role="STUDENT",
        full_name="Numeric Roll Student",
        is_active=True,
        must_change_password=False,
    )
    db_session.add(user)
    await db_session.flush()

    profile = StudentProfile(
        id=uuid4(),
        user_id=user.id,
        roll_number="99230041249",
        branch_code=branch.code,
        batch_year=2026,
        cgpa=8.95,
        active_backlogs=0,
    )
    db_session.add(profile)
    await db_session.commit()
    return user, profile


@pytest.fixture
async def active_student_leading_zero(db_session: AsyncSession, branch: Branch) -> tuple[User, StudentProfile]:
    user = User(
        id=uuid4(),
        email="student00123@campusflow.com",
        password_hash=hash_password("Password@123"),
        role="STUDENT",
        full_name="Leading Zero Student",
        is_active=True,
        must_change_password=False,
    )
    db_session.add(user)
    await db_session.flush()

    profile = StudentProfile(
        id=uuid4(),
        user_id=user.id,
        roll_number="00123456789",
        branch_code=branch.code,
        batch_year=2026,
        cgpa=9.1,
        active_backlogs=0,
    )
    db_session.add(profile)
    await db_session.commit()
    return user, profile


@pytest.fixture
async def inactive_student(db_session: AsyncSession, branch: Branch) -> tuple[User, StudentProfile]:
    user = User(
        id=uuid4(),
        email="unregistered.student@campusflow.com",
        password_hash=hash_password("temporary-placeholder"),
        role="STUDENT",
        full_name="Unregistered Student",
        is_active=False,
        must_change_password=True,
    )
    db_session.add(user)
    await db_session.flush()

    profile = StudentProfile(
        id=uuid4(),
        user_id=user.id,
        roll_number="99230099999",
        branch_code=branch.code,
        batch_year=2026,
        cgpa=7.5,
        active_backlogs=0,
    )
    db_session.add(profile)
    await db_session.commit()
    return user, profile


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, active_user: User):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": active_user.email, "password": "password123"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == active_user.email


@pytest.mark.asyncio
async def test_login_success_with_registration_number(
    async_client: AsyncClient, active_student: tuple[User, StudentProfile]
):
    user, profile = active_student
    # Login using identifier = "99230041249"
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "99230041249", "password": "Password@123"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == user.email

    # Login using email field filled with registration number
    response2 = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "99230041249", "password": "Password@123"},
    )
    assert response2.status_code == 200, response2.text


@pytest.mark.asyncio
async def test_login_success_with_leading_zero_registration_number(
    async_client: AsyncClient, active_student_leading_zero: tuple[User, StudentProfile]
):
    user, profile = active_student_leading_zero
    # Must preserve leading zeros as a string
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "00123456789", "password": "Password@123"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["user"]["email"] == user.email


@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient, active_user: User):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": active_user.email, "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["title"] == "Authentication Failed"


@pytest.mark.asyncio
async def test_login_wrong_password_with_registration_number(
    async_client: AsyncClient, active_student: tuple[User, StudentProfile]
):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "99230041249", "password": "WrongPassword@123"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["title"] == "Authentication Failed"
    assert isinstance(data["detail"], str)


@pytest.mark.asyncio
async def test_login_unknown_registration_number(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "UNKNOWN999", "password": "Password@123"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["title"] == "Authentication Failed"
    assert isinstance(data["detail"], str)


@pytest.mark.asyncio
async def test_login_inactive_student_registration_number(
    async_client: AsyncClient, inactive_student: tuple[User, StudentProfile]
):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "99230099999", "password": "temporary-placeholder"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["title"] == "Account Not Active"
    assert isinstance(data["detail"], str)


@pytest.mark.asyncio
async def test_login_empty_identifier_validation_error(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "", "password": "Password@123"},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["title"] == "Validation Error"
    assert isinstance(data["detail"], str)
    assert "required" in data["detail"].lower()


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
