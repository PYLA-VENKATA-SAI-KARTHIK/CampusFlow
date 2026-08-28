"""
Tests for Student Profile Backend.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.branch import Branch
from app.models.student_profile import StudentProfile


@pytest_asyncio.fixture
async def auth_users(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> dict:
    """Create a student and an officer, returning their auth headers."""

    student = User(
        email="profile_student@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Profile Student",
        is_active=True,
    )

    officer = User(
        email="profile_officer@campusflow.com",
        password_hash=hash_password("password123"),
        role="OFFICER",
        full_name="Profile Officer",
        is_active=True,
    )

    db_session.add_all([student, officer])
    await db_session.commit()

    # Refresh to obtain generated IDs
    await db_session.refresh(student)
    await db_session.refresh(officer)

    # Login student
    r_student = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": student.email,
            "password": "password123",
        },
    )

    # Login officer
    r_officer = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": officer.email,
            "password": "password123",
        },
    )

    assert r_student.status_code == 200, r_student.text
    assert r_officer.status_code == 200, r_officer.text

    return {
        "student": {
            "Authorization": f"Bearer {r_student.json()['access_token']}"
        },
        "officer": {
            "Authorization": f"Bearer {r_officer.json()['access_token']}"
        },
        "student_id": student.id,
        "officer_id": officer.id,
    }


@pytest_asyncio.fixture
async def test_branch(db_session: AsyncSession) -> str:
    branch = Branch(code="CSE_TST", name="Computer Science Test")
    db_session.add(branch)
    await db_session.commit()
    return branch.code


@pytest_asyncio.fixture
async def test_profile(db_session: AsyncSession, auth_users: dict, test_branch: str) -> str:
    profile = StudentProfile(
        user_id=auth_users["student_id"],
        roll_number="12345678",
        branch_code=test_branch,
        batch_year=2024,
        cgpa=8.5,
        active_backlogs=0,
        phone_number="1234567890",
        gender="MALE",
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    return str(profile.id)


@pytest.mark.asyncio
async def test_student_can_get_my_profile(
    async_client: AsyncClient,
    auth_users: dict,
    test_profile: str,
):
    response = await async_client.get(
        "/api/v1/students/me",
        headers=auth_users["student"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["roll_number"] == "12345678"
    assert data["cgpa"] == 8.5
    assert data["user"]["email"] == "profile_student@campusflow.com"


@pytest.mark.asyncio
async def test_student_can_update_my_profile(
    async_client: AsyncClient,
    auth_users: dict,
    test_profile: str,
    db_session: AsyncSession,
):
    response = await async_client.patch(
        "/api/v1/students/me",
        headers=auth_users["student"],
        json={"cgpa": 9.2}
    )
    assert response.status_code == 200
    assert response.json()["cgpa"] == 9.2

    # Check audit log
    stmt = select(AuditLog).where(
        AuditLog.entity_id == test_profile
    )
    result = await db_session.execute(stmt)
    logs = result.scalars().all()
    assert len(logs) == 1
    assert logs[0].action == "PROFILE_UPDATED"
    assert logs[0].new_state["cgpa"] == 9.2


@pytest.mark.asyncio
async def test_unauthenticated_cannot_access_me(
    async_client: AsyncClient,
):
    response = await async_client.get("/api/v1/students/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_officer_can_list_students(
    async_client: AsyncClient,
    auth_users: dict,
    test_profile: str,
):
    response = await async_client.get(
        "/api/v1/officers/students",
        headers=auth_users["officer"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(s["id"] == test_profile for s in data["items"])


@pytest.mark.asyncio
async def test_officer_can_get_student(
    async_client: AsyncClient,
    auth_users: dict,
    test_profile: str,
):
    response = await async_client.get(
        f"/api/v1/officers/students/{test_profile}",
        headers=auth_users["officer"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_profile
    assert data["roll_number"] == "12345678"


@pytest.mark.asyncio
async def test_student_cannot_access_officer_endpoints(
    async_client: AsyncClient,
    auth_users: dict,
):
    response = await async_client.get(
        "/api/v1/officers/students",
        headers=auth_users["student"],
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_invalid_profile_data_rejected(
    async_client: AsyncClient,
    auth_users: dict,
    test_profile: str,
):
    # cgpa > 10.0 should be rejected
    response = await async_client.patch(
        "/api/v1/students/me",
        headers=auth_users["student"],
        json={"cgpa": 11.5}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_nonexistent_student_returns_404(
    async_client: AsyncClient,
    auth_users: dict,
):
    from uuid import uuid4
    response = await async_client.get(
        f"/api/v1/officers/students/{uuid4()}",
        headers=auth_users["officer"],
    )
    assert response.status_code == 404
