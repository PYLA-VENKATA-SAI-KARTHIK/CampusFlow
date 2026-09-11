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
from app.models.branch import Branch
from app.models.student_profile import StudentProfile


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
async def test_branch(db_session: AsyncSession) -> str:
    branch = Branch(code="CSE", name="Computer Science")
    db_session.add(branch)
    await db_session.commit()
    return branch.code


@pytest_asyncio.fixture
async def student_profile(
    db_session: AsyncSession, auth_users: dict, test_branch: str
) -> StudentProfile:
    profile = StudentProfile(
        user_id=auth_users["student_id"],
        roll_number="ELG12345",
        branch_code=test_branch,
        batch_year=2024,
        cgpa=8.0,
        active_backlogs=0,
        gender="MALE",
    )
    db_session.add(profile)
    await db_session.commit()
    return profile


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

# --- ELIGIBILITY TESTS ---

@pytest.mark.asyncio
async def test_eligibility_all_pass(
    async_client: AsyncClient,
    auth_users: dict,
    test_company: str,
    student_profile: StudentProfile,
):
    """Test when a student satisfies all criteria."""
    
    # Create drive
    create_resp = await async_client.post(
        "/api/v1/drives",
        json={
            "company_id": test_company,
            "title": "SDE",
            "job_role": "SDE",
            "eligibility_criteria": {
                "min_cgpa": 7.5,
                "max_active_backlogs": 1,
                "eligible_branches": ["CSE", "IT"],
                "eligible_batch_years": [2024],
                "gender": "MALE"
            },
        },
        headers=auth_users["officer"],
    )
    drive_id = create_resp.json()["id"]

    # Student checks eligibility
    resp = await async_client.get(
        f"/api/v1/drives/{drive_id}/eligibility-check",
        headers=auth_users["student"],
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_eligible"] is True
    assert len(data["reasons"]) == 0
    assert data["drive_id"] == drive_id

    # Test automatic my_eligibility population
    get_resp = await async_client.get(
        f"/api/v1/drives/{drive_id}",
        headers=auth_users["student"],
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["my_eligibility"]["is_eligible"] is True


@pytest.mark.asyncio
async def test_eligibility_cgpa_failure(
    async_client: AsyncClient,
    auth_users: dict,
    test_company: str,
    student_profile: StudentProfile,
):
    create_resp = await async_client.post(
        "/api/v1/drives",
        json={
            "company_id": test_company,
            "title": "SDE",
            "job_role": "SDE",
            "eligibility_criteria": {
                "min_cgpa": 8.5
            },
        },
        headers=auth_users["officer"],
    )
    drive_id = create_resp.json()["id"]

    resp = await async_client.get(
        f"/api/v1/drives/{drive_id}/eligibility-check",
        headers=auth_users["student"],
    )
    
    data = resp.json()
    assert data["is_eligible"] is False
    assert len(data["reasons"]) == 1
    assert "below the minimum required CGPA (8.5)" in data["reasons"][0]


from app.core.security import hash_password

@pytest.mark.asyncio
async def test_eligibility_backlog_failure(
    async_client: AsyncClient,
    auth_users: dict,
    test_company: str,
    test_branch: str,
    db_session: AsyncSession,
):
    # Create student with backlogs
    user_bl = User(
        email="backlog@campusflow.com",
        password_hash=hash_password("pw"),
        role="STUDENT",
        full_name="Backlog Student",
        is_active=True,
    )
    db_session.add(user_bl)
    await db_session.commit()
    await db_session.refresh(user_bl)
    
    prof_bl = StudentProfile(
        user_id=user_bl.id,
        roll_number="BL123",
        branch_code=test_branch,
        batch_year=2024,
        cgpa=8.0,
        active_backlogs=2,
    )
    db_session.add(prof_bl)
    await db_session.commit()

    # Login student
    r_student = await async_client.post("/api/v1/auth/login", json={"email": "backlog@campusflow.com", "password": "pw"})
    token = r_student.json()["access_token"]
    
    create_resp = await async_client.post(
        "/api/v1/drives",
        json={
            "company_id": test_company,
            "title": "SDE",
            "job_role": "SDE",
            "eligibility_criteria": {
                "max_active_backlogs": 1
            },
        },
        headers=auth_users["officer"],
    )
    drive_id = create_resp.json()["id"]

    resp = await async_client.get(
        f"/api/v1/drives/{drive_id}/eligibility-check",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    data = resp.json()
    assert data["is_eligible"] is False
    assert len(data["reasons"]) == 1
    assert "exceed the maximum allowed (1)" in data["reasons"][0]


@pytest.mark.asyncio
async def test_eligibility_multiple_failures(
    async_client: AsyncClient,
    auth_users: dict,
    test_company: str,
    student_profile: StudentProfile,
):
    create_resp = await async_client.post(
        "/api/v1/drives",
        json={
            "company_id": test_company,
            "title": "SDE",
            "job_role": "SDE",
            "eligibility_criteria": {
                "min_cgpa": 8.5, # FAIL (8.0 < 8.5)
                "eligible_branches": ["ECE"], # FAIL (CSE not in ECE)
                "eligible_batch_years": [2023], # FAIL (2024 != 2023)
                "gender": "FEMALE" # FAIL (MALE != FEMALE)
            },
        },
        headers=auth_users["officer"],
    )
    drive_id = create_resp.json()["id"]

    resp = await async_client.get(
        f"/api/v1/drives/{drive_id}/eligibility-check",
        headers=auth_users["student"],
    )
    
    data = resp.json()
    assert data["is_eligible"] is False
    assert len(data["reasons"]) == 4


@pytest.mark.asyncio
async def test_eligibility_unspecified_criteria(
    async_client: AsyncClient,
    auth_users: dict,
    test_company: str,
    student_profile: StudentProfile,
):
    create_resp = await async_client.post(
        "/api/v1/drives",
        json={
            "company_id": test_company,
            "title": "SDE",
            "job_role": "SDE",
            "eligibility_criteria": {}, # No criteria
        },
        headers=auth_users["officer"],
    )
    drive_id = create_resp.json()["id"]

    resp = await async_client.get(
        f"/api/v1/drives/{drive_id}/eligibility-check",
        headers=auth_users["student"],
    )
    
    data = resp.json()
    assert data["is_eligible"] is True


@pytest.mark.asyncio
async def test_eligibility_case_insensitive_branch(
    async_client: AsyncClient,
    auth_users: dict,
    test_company: str,
    student_profile: StudentProfile,
):
    create_resp = await async_client.post(
        "/api/v1/drives",
        json={
            "company_id": test_company,
            "title": "SDE",
            "job_role": "SDE",
            "eligibility_criteria": {
                "eligible_branches": ["cse", "iT"] # lowercase 'cse' vs profile 'CSE'
            },
        },
        headers=auth_users["officer"],
    )
    drive_id = create_resp.json()["id"]

    resp = await async_client.get(
        f"/api/v1/drives/{drive_id}/eligibility-check",
        headers=auth_users["student"],
    )
    
    data = resp.json()
    assert data["is_eligible"] is True


@pytest.mark.asyncio
async def test_officer_eligible_students(
    async_client: AsyncClient,
    auth_users: dict,
    test_company: str,
    student_profile: StudentProfile,
    db_session: AsyncSession
):
    # Add a second student who is NOT eligible
    user2 = User(
        email="drive_student2@campusflow.com",
        password_hash="pw",
        role="STUDENT",
        full_name="Not Eligible",
        is_active=True,
    )
    db_session.add(user2)
    await db_session.commit()
    await db_session.refresh(user2)
    
    prof2 = StudentProfile(
        user_id=user2.id,
        roll_number="ELG12346",
        branch_code=student_profile.branch_code,
        batch_year=2024,
        cgpa=6.0, # Below min CGPA
        active_backlogs=0,
    )
    db_session.add(prof2)
    await db_session.commit()
    
    create_resp = await async_client.post(
        "/api/v1/drives",
        json={
            "company_id": test_company,
            "title": "SDE",
            "job_role": "SDE",
            "eligibility_criteria": {
                "min_cgpa": 7.0
            },
        },
        headers=auth_users["officer"],
    )
    drive_id = create_resp.json()["id"]

    # Officer lists eligible students
    resp = await async_client.get(
        f"/api/v1/drives/{drive_id}/eligible-students?page=1&page_size=10",
        headers=auth_users["officer"],
    )
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["user_id"] == str(student_profile.user_id)


@pytest.mark.asyncio
async def test_student_forbidden_eligible_students(
    async_client: AsyncClient,
    auth_users: dict,
    test_company: str,
):
    resp = await async_client.get(
        f"/api/v1/drives/123e4567-e89b-12d3-a456-426614174000/eligible-students",
        headers=auth_users["student"],
    )
    assert resp.status_code == 403