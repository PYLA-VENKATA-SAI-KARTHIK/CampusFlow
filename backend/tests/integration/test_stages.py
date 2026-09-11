"""
Tests for Placement Stages API.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.branch import Branch
from app.models.student_profile import StudentProfile
from app.models.placement_drive import PlacementDrive
from app.models.placement_stage import PlacementStage
from app.models.stage_assignment import StageAssignment
from app.models.drive_registration import DriveRegistration
from app.models.user import User
from app.core.security import hash_password


@pytest_asyncio.fixture
async def auth_users(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> dict:
    """Create a student and an officer, returning their auth headers."""
    student = User(
        email="stage_student@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Stage Student",
        is_active=True,
    )

    officer = User(
        email="stage_officer@campusflow.com",
        password_hash=hash_password("password123"),
        role="OFFICER",
        full_name="Stage Officer",
        is_active=True,
    )

    db_session.add_all([student, officer])
    await db_session.commit()
    await db_session.refresh(student)
    await db_session.refresh(officer)

    r_student = await async_client.post(
        "/api/v1/auth/login",
        json={"email": student.email, "password": "password123"},
    )
    r_officer = await async_client.post(
        "/api/v1/auth/login",
        json={"email": officer.email, "password": "password123"},
    )

    return {
        "student": {"Authorization": f"Bearer {r_student.json()['access_token']}"},
        "officer": {"Authorization": f"Bearer {r_officer.json()['access_token']}"},
        "student_id": student.id,
        "officer_id": officer.id,
    }


@pytest_asyncio.fixture
async def test_company(async_client: AsyncClient, auth_users: dict) -> str:
    response = await async_client.post(
        "/api/v1/companies",
        json={"name": "Stage Company", "industry": "Tech"},
        headers=auth_users["officer"],
    )
    return response.json()["id"]


@pytest_asyncio.fixture
async def test_drive(async_client: AsyncClient, auth_users: dict, test_company: str) -> str:
    response = await async_client.post(
        "/api/v1/drives",
        json={
            "company_id": test_company,
            "title": "Stage Test Drive",
            "job_role": "SDE",
            "eligibility_criteria": {},
        },
        headers=auth_users["officer"],
    )
    drive_id = response.json()["id"]
    await async_client.post(
        f"/api/v1/drives/{drive_id}/status",
        json={"status": "REGISTRATION_OPEN"},
        headers=auth_users["officer"],
    )
    return drive_id


@pytest_asyncio.fixture
async def student_setup(db_session: AsyncSession, auth_users: dict, test_drive: str) -> dict:
    branch = Branch(code="STG", name="Stage Branch")
    db_session.add(branch)
    await db_session.commit()

    profile = StudentProfile(
        user_id=auth_users["student_id"],
        roll_number="STG123",
        branch_code="STG",
        batch_year=2024,
        cgpa=8.0,
        active_backlogs=0,
        resume_gcs_path="gs://bucket/resume.pdf",
    )
    db_session.add(profile)
    await db_session.commit()

    reg = DriveRegistration(
        drive_id=test_drive,
        student_user_id=auth_users["student_id"],
        resume_gcs_path_at_registration="gs://bucket/resume.pdf",
        status="REGISTERED"
    )
    db_session.add(reg)
    await db_session.commit()
    
    return {"drive_id": test_drive, "student_id": auth_users["student_id"]}


@pytest.mark.asyncio
async def test_create_stage_officer_success(async_client: AsyncClient, auth_users: dict, test_drive: str):
    response = await async_client.post(
        f"/api/v1/drives/{test_drive}/stages",
        json={
            "name": "Aptitude Test",
            "stage_type": "APTITUDE",
            "sequence_order": 1
        },
        headers=auth_users["officer"]
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Aptitude Test"
    assert response.json()["is_published"] is False


@pytest.mark.asyncio
async def test_create_stage_student_fail(async_client: AsyncClient, auth_users: dict, test_drive: str):
    response = await async_client.post(
        f"/api/v1/drives/{test_drive}/stages",
        json={
            "name": "Aptitude Test",
            "stage_type": "APTITUDE",
            "sequence_order": 1
        },
        headers=auth_users["student"]
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_stage_invalid_type(async_client: AsyncClient, auth_users: dict, test_drive: str):
    response = await async_client.post(
        f"/api/v1/drives/{test_drive}/stages",
        json={
            "name": "Invalid Stage",
            "stage_type": "INVALID_TYPE",
            "sequence_order": 1
        },
        headers=auth_users["officer"]
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_duplicate_sequence_order(async_client: AsyncClient, auth_users: dict, test_drive: str):
    await async_client.post(
        f"/api/v1/drives/{test_drive}/stages",
        json={"name": "Aptitude Test", "stage_type": "APTITUDE", "sequence_order": 1},
        headers=auth_users["officer"]
    )
    response = await async_client.post(
        f"/api/v1/drives/{test_drive}/stages",
        json={"name": "Technical Test", "stage_type": "TECHNICAL", "sequence_order": 1},
        headers=auth_users["officer"]
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_and_publish_stage(async_client: AsyncClient, auth_users: dict, test_drive: str):
    create_resp = await async_client.post(
        f"/api/v1/drives/{test_drive}/stages",
        json={"name": "Aptitude Test", "stage_type": "APTITUDE", "sequence_order": 1},
        headers=auth_users["officer"]
    )
    stage_id = create_resp.json()["id"]

    update_resp = await async_client.patch(
        f"/api/v1/drives/{test_drive}/stages/{stage_id}",
        json={"name": "Updated Aptitude"},
        headers=auth_users["officer"]
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Updated Aptitude"

    pub_resp = await async_client.post(
        f"/api/v1/drives/{test_drive}/stages/{stage_id}/publish",
        headers=auth_users["officer"]
    )
    assert pub_resp.status_code == 200

    get_resp = await async_client.get(
        f"/api/v1/drives/{test_drive}/stages",
        headers=auth_users["officer"]
    )
    assert get_resp.json()[0]["is_published"] is True


@pytest.mark.asyncio
async def test_stage_idor(async_client: AsyncClient, auth_users: dict, test_company: str, test_drive: str):
    # Create a second drive
    response = await async_client.post(
        "/api/v1/drives",
        json={
            "company_id": test_company,
            "title": "Another Drive",
            "job_role": "SDE",
            "eligibility_criteria": {},
        },
        headers=auth_users["officer"],
    )
    drive2_id = response.json()["id"]

    create_resp = await async_client.post(
        f"/api/v1/drives/{test_drive}/stages",
        json={"name": "Aptitude Test", "stage_type": "APTITUDE", "sequence_order": 1},
        headers=auth_users["officer"]
    )
    stage_id = create_resp.json()["id"]

    # Try to update stage 1 using drive 2
    update_resp = await async_client.patch(
        f"/api/v1/drives/{drive2_id}/stages/{stage_id}",
        json={"name": "Hacked"},
        headers=auth_users["officer"]
    )
    assert update_resp.status_code == 404


@pytest.mark.asyncio
async def test_student_visibility_and_current_stage(async_client: AsyncClient, auth_users: dict, student_setup: dict, db_session: AsyncSession):
    drive_id = student_setup["drive_id"]
    student_id = student_setup["student_id"]

    # 1. Create Stage (Unpublished)
    create_resp = await async_client.post(
        f"/api/v1/drives/{drive_id}/stages",
        json={"name": "Aptitude Test", "stage_type": "APTITUDE", "sequence_order": 1},
        headers=auth_users["officer"]
    )
    stage_id = create_resp.json()["id"]

    # Student shouldn't see unpublished stage
    list_resp = await async_client.get(f"/api/v1/drives/{drive_id}/stages", headers=auth_users["student"])
    assert len(list_resp.json()) == 0

    # 2. Publish Stage, but no assignment
    await async_client.post(f"/api/v1/drives/{drive_id}/stages/{stage_id}/publish", headers=auth_users["officer"])
    
    list_resp = await async_client.get(f"/api/v1/drives/{drive_id}/stages", headers=auth_users["student"])
    assert len(list_resp.json()) == 0

    # 3. Create mock assignment
    assignment = StageAssignment(
        stage_id=stage_id,
        student_user_id=student_id,
        drive_id=drive_id,
        status="SHORTLISTED"
    )
    db_session.add(assignment)
    await db_session.commit()

    # Now student should see it
    list_resp = await async_client.get(f"/api/v1/drives/{drive_id}/stages", headers=auth_users["student"])
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["id"] == stage_id

    # 4. Check applications endpoint my_current_stage
    apps_resp = await async_client.get("/api/v1/students/me/applications", headers=auth_users["student"])
    assert apps_resp.status_code == 200
    apps = apps_resp.json()["items"]
    assert len(apps) == 1
    
    current_stage = apps[0]["my_current_stage"]
    assert current_stage is not None
    assert current_stage["stage_name"] == "Aptitude Test"
    assert current_stage["stage_status"] == "SHORTLISTED"
