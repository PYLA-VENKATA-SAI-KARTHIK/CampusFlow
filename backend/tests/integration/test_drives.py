"""
Tests for Placement Drive Backend.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.models.audit_log import AuditLog


@pytest_asyncio.fixture
async def auth_users(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> dict:
    """Create a student and an officer, returning their auth headers."""

    student = User(
        email="drive_student@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Drive Student",
        is_active=True,
    )

    officer = User(
        email="drive_officer@campusflow.com",
        password_hash=hash_password("password123"),
        role="OFFICER",
        full_name="Drive Officer",
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
async def test_company(
    async_client: AsyncClient,
    auth_users: dict,
) -> str:
    """Create a company for placement-drive tests."""

    response = await async_client.post(
        "/api/v1/companies",
        json={
            "name": "Test Company",
            "industry": "Tech",
        },
        headers=auth_users["officer"],
    )

    assert response.status_code == 201, response.text

    return response.json()["id"]


@pytest.mark.asyncio
async def test_student_cannot_create_drive(
    async_client: AsyncClient,
    auth_users: dict,
    test_company: str,
):
    """Students must not be allowed to create placement drives."""

    response = await async_client.post(
        "/api/v1/drives",
        json={
            "company_id": test_company,
            "title": "SDE Intern",
            "job_role": "SDE",
            "eligibility_criteria": {
                "min_cgpa": 7.0
            },
        },
        headers=auth_users["student"],
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_officer_can_create_drive(
    async_client: AsyncClient,
    auth_users: dict,
    test_company: str,
    db_session: AsyncSession,
):
    """Officer should be able to create a placement drive."""

    response = await async_client.post(
        "/api/v1/drives",
        json={
            "company_id": test_company,
            "title": "SDE Intern",
            "job_role": "SDE",
            "ctc_lpa": 12.5,
            "eligibility_criteria": {
                "min_cgpa": 7.0
            },
        },
        headers=auth_users["officer"],
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["title"] == "SDE Intern"
    assert data["status"] == "DRAFT"

    # Security check:
    # created_by_user_id must come from the authenticated officer,
    # not from client-provided data.
    assert data["created_by_user_id"] == str(
        auth_users["officer_id"]
    )

    # Verify audit log
    stmt = select(AuditLog).where(
        AuditLog.entity_id == data["id"]
    )

    result = await db_session.execute(stmt)
    logs = result.scalars().all()

    assert len(logs) == 1
    assert logs[0].action == "DRIVE_CREATED"


@pytest.mark.asyncio
async def test_update_drive_status_lifecycle(
    async_client: AsyncClient,
    auth_users: dict,
    test_company: str,
):
    """Verify placement-drive lifecycle and authorization."""

    # ---------------------------------------------------------
    # 1. Officer creates a drive
    # ---------------------------------------------------------

    create_response = await async_client.post(
        "/api/v1/drives",
        json={
            "company_id": test_company,
            "title": "SDE",
            "job_role": "SDE",
            "eligibility_criteria": {},
        },
        headers=auth_users["officer"],
    )

    assert create_response.status_code == 201, create_response.text

    drive_id = create_response.json()["id"]

    # ---------------------------------------------------------
    # 2. Student cannot publish the drive
    # ---------------------------------------------------------

    student_publish = await async_client.post(
        f"/api/v1/drives/{drive_id}/status",
        json={
            "status": "PUBLISHED"
        },
        headers=auth_users["student"],
    )

    assert student_publish.status_code == 403

    # ---------------------------------------------------------
    # 3. Officer publishes the drive
    # ---------------------------------------------------------

    officer_publish = await async_client.post(
        f"/api/v1/drives/{drive_id}/status",
        json={
            "status": "PUBLISHED"
        },
        headers=auth_users["officer"],
    )

    assert officer_publish.status_code == 200, officer_publish.text
    assert officer_publish.json()["status"] == "PUBLISHED"

    # ---------------------------------------------------------
    # 4. Invalid transition:
    #    PUBLISHED -> COMPLETED
    # ---------------------------------------------------------

    invalid_transition = await async_client.post(
        f"/api/v1/drives/{drive_id}/status",
        json={
            "status": "COMPLETED"
        },
        headers=auth_users["officer"],
    )

    assert invalid_transition.status_code == 409

    # ---------------------------------------------------------
    # 5. Core drive details cannot be modified after publishing
    # ---------------------------------------------------------

    update_response = await async_client.patch(
        f"/api/v1/drives/{drive_id}",
        json={
            "title": "Hacked Title"
        },
        headers=auth_users["officer"],
    )

    assert update_response.status_code == 403


@pytest.mark.asyncio
async def test_get_drive_not_found(
    async_client: AsyncClient,
    auth_users: dict,
):
    """Requesting an unknown drive ID should return 404."""

    from uuid import uuid4

    response = await async_client.get(
        f"/api/v1/drives/{uuid4()}",
        headers=auth_users["student"],
    )

    assert response.status_code == 404