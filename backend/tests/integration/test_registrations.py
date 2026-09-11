import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.core.security import hash_password
from app.models.user import User
from app.models.branch import Branch
from app.models.company import Company
from app.models.student_profile import StudentProfile
from sqlalchemy import select

@pytest_asyncio.fixture
async def auth_users(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> dict:
    student = User(
        email="reg_student@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Reg Student",
        is_active=True,
    )
    student_ineligible = User(
        email="reg_student_in@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Reg Ineligible",
        is_active=True,
    )
    officer = User(
        email="reg_officer@campusflow.com",
        password_hash=hash_password("password123"),
        role="OFFICER",
        full_name="Reg Officer",
        is_active=True,
    )

    db_session.add_all([student, student_ineligible, officer])
    await db_session.commit()

    await db_session.refresh(student)
    await db_session.refresh(student_ineligible)
    await db_session.refresh(officer)

    # Add branch
    branch = Branch(code="CSE", name="Computer Science")
    db_session.add(branch)
    await db_session.commit()

    # Add profiles
    prof1 = StudentProfile(
        user_id=student.id,
        roll_number="REG123",
        branch_code="CSE",
        batch_year=2024,
        cgpa=8.0,
        active_backlogs=0,
        gender="MALE",
        resume_gcs_path=f"resumes/{student.id}/test_resume.pdf",
    )
    prof2 = StudentProfile(
        user_id=student_ineligible.id,
        roll_number="REG456",
        branch_code="CSE",
        batch_year=2024,
        cgpa=5.0,
        active_backlogs=2,
        gender="FEMALE",
        resume_gcs_path=None,
    )
    db_session.add_all([prof1, prof2])
    await db_session.commit()

    r_student = await async_client.post("/api/v1/auth/login", json={"email": student.email, "password": "password123"})
    r_student_in = await async_client.post("/api/v1/auth/login", json={"email": student_ineligible.email, "password": "password123"})
    r_officer = await async_client.post("/api/v1/auth/login", json={"email": officer.email, "password": "password123"})

    return {
        "student": {"Authorization": f"Bearer {r_student.json()['access_token']}"},
        "student_ineligible": {"Authorization": f"Bearer {r_student_in.json()['access_token']}"},
        "officer": {"Authorization": f"Bearer {r_officer.json()['access_token']}"},
        "student_id": student.id,
        "student_ineligible_id": student_ineligible.id,
        "officer_id": officer.id,
    }

@pytest_asyncio.fixture
async def test_company(
    async_client: AsyncClient,
    auth_users: dict,
) -> str:
    r = await async_client.post(
        "/api/v1/companies",
        json={
            "name": "Reg Company",
            "website": "https://reg.example.com",
            "industry": "Technology",
            "description": "Tech comp",
        },
        headers=auth_users["officer"],
    )
    return r.json()["id"]


@pytest.mark.asyncio
async def test_student_register_success(
    async_client: AsyncClient,
    auth_users: dict,
    test_company: str,
    db_session: AsyncSession,
):
    student_headers = auth_users["student"]
    
    officer_headers = auth_users["officer"]
    
    drive_data = {
        "company_id": test_company,
        "title": "SDE Intern Reg Test",
        "job_role": "SDE Intern",
        "registration_deadline": "2026-12-31T23:59:59Z",
        "eligibility_criteria": {
            "min_cgpa": 7.0,
            "max_active_backlogs": 0,
            "eligible_branches": ["CSE"],
        }
    }
    r = await async_client.post("/api/v1/drives", json=drive_data, headers=officer_headers)
    assert r.status_code == 201
    drive_id = r.json()["id"]

    # Open Registration
    r = await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "PUBLISHED"}, headers=officer_headers)
    r = await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "REGISTRATION_OPEN"}, headers=officer_headers)
    assert r.status_code == 200

    # 3. Register Student
    r = await async_client.post(f"/api/v1/drives/{drive_id}/register", headers=student_headers)
    assert r.status_code == 201
    reg_id = r.json()["id"]
    assert r.json()["resume_gcs_path_at_registration"] == f"resumes/{auth_users['student_id']}/test_resume.pdf"
    assert r.json()["status"] == "REGISTERED"

    # 4. Duplicate Registration
    r_dup = await async_client.post(f"/api/v1/drives/{drive_id}/register", headers=student_headers)
    assert r_dup.status_code == 409


@pytest.mark.asyncio
async def test_student_register_fails_without_resume(
    async_client: AsyncClient,
    auth_users: dict,
    test_company: str,
):
    student_headers = auth_users["student_ineligible"] # using as a student without resume
    officer_headers = auth_users["officer"]
    
    drive_data = {
        "company_id": test_company,
        "title": "SDE Intern No Resume",
        "job_role": "SDE Intern",
        "registration_deadline": "2026-12-31T23:59:59Z",
        "eligibility_criteria": {}
    }
    r = await async_client.post("/api/v1/drives", json=drive_data, headers=officer_headers)
    drive_id = r.json()["id"]
    await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "PUBLISHED"}, headers=officer_headers)
    await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "REGISTRATION_OPEN"}, headers=officer_headers)

    r = await async_client.post(f"/api/v1/drives/{drive_id}/register", headers=student_headers)
    assert r.status_code == 400
    assert "resume" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_student_register_fails_ineligible(
    async_client: AsyncClient,
    auth_users: dict,
    test_company: str,
    db_session: AsyncSession,
):
    student_headers = auth_users["student_ineligible"]
    
    # Update prof2 to have a resume for this test
    stmt = select(StudentProfile).where(StudentProfile.user_id == auth_users["student_ineligible_id"])
    result = await db_session.execute(stmt)
    prof2 = result.scalar_one()

    prof2.resume_gcs_path = "resumes/some/test.pdf"
    await db_session.commit()
    
    officer_headers = auth_users["officer"]
    
    drive_data = {
        "company_id": test_company,
        "title": "SDE Intern High Bar",
        "job_role": "SDE Intern",
        "registration_deadline": "2026-12-31T23:59:59Z",
        "eligibility_criteria": {
            "min_cgpa": 9.9
        }
    }
    r = await async_client.post("/api/v1/drives", json=drive_data, headers=officer_headers)
    drive_id = r.json()["id"]
    await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "PUBLISHED"}, headers=officer_headers)
    await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "REGISTRATION_OPEN"}, headers=officer_headers)

    r = await async_client.post(f"/api/v1/drives/{drive_id}/register", headers=student_headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_student_register_fails_draft(
    async_client: AsyncClient,
    auth_users: dict,
    test_company: str,
):
    student_headers = auth_users["student"]
    officer_headers = auth_users["officer"]
    
    drive_data = {
        "company_id": test_company,
        "title": "SDE Intern Draft",
        "job_role": "SDE Intern",
        "eligibility_criteria": {}
    }
    r = await async_client.post("/api/v1/drives", json=drive_data, headers=officer_headers)
    drive_id = r.json()["id"]

    r = await async_client.post(f"/api/v1/drives/{drive_id}/register", headers=student_headers)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_officer_list_registrations(
    async_client: AsyncClient,
    auth_users: dict,
    test_company: str,
):
    officer_headers = auth_users["officer"]
    student_headers = auth_users["student"]

    # Create drive
    drive_data = {
        "company_id": test_company,
        "title": "SDE Intern List Regs",
        "job_role": "SDE",
        "registration_deadline": "2026-12-31T23:59:59Z",
        "eligibility_criteria": {}
    }
    r = await async_client.post("/api/v1/drives", json=drive_data, headers=officer_headers)
    drive_id = r.json()["id"]
    await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "PUBLISHED"}, headers=officer_headers)
    await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "REGISTRATION_OPEN"}, headers=officer_headers)

    # Register
    await async_client.post(f"/api/v1/drives/{drive_id}/register", headers=student_headers)

    # List
    r_list = await async_client.get(f"/api/v1/drives/{drive_id}/registrations", headers=officer_headers)
    assert r_list.status_code == 200
    data = r_list.json()
    assert data["total"] == 1
    assert data["items"][0]["student"]["roll_number"] is not None


@pytest.mark.asyncio
async def test_student_list_applications(
    async_client: AsyncClient,
    auth_users: dict,
    test_company: str,
):
    student_headers = auth_users["student"]
    officer_headers = auth_users["officer"]

    # Create drive
    drive_data = {
        "company_id": test_company,
        "title": "SDE Intern App List",
        "job_role": "SDE",
        "registration_deadline": "2026-12-31T23:59:59Z",
        "eligibility_criteria": {}
    }
    r = await async_client.post("/api/v1/drives", json=drive_data, headers=officer_headers)
    drive_id = r.json()["id"]
    await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "PUBLISHED"}, headers=officer_headers)
    await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "REGISTRATION_OPEN"}, headers=officer_headers)

    # Register
    await async_client.post(f"/api/v1/drives/{drive_id}/register", headers=student_headers)

    # List apps
    r_apps = await async_client.get("/api/v1/students/me/applications", headers=student_headers)
    assert r_apps.status_code == 200
    data = r_apps.json()
    assert data["total"] >= 1
    item = [x for x in data["items"] if x["drive_id"] == drive_id][0]
    assert item["drive_title"] == "SDE Intern App List"
    assert item["my_current_stage"] is None


@pytest.mark.asyncio
async def test_rbac_registration(
    async_client: AsyncClient,
    auth_users: dict,
    test_company: str,
):
    officer_headers = auth_users["officer"]
    student_headers = auth_users["student"]

    # Create drive
    drive_data = {
        "company_id": test_company,
        "title": "SDE Intern RBAC",
        "job_role": "SDE",
        "registration_deadline": "2026-12-31T23:59:59Z",
        "eligibility_criteria": {}
    }
    r = await async_client.post("/api/v1/drives", json=drive_data, headers=officer_headers)
    drive_id = r.json()["id"]
    await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "PUBLISHED"}, headers=officer_headers)
    await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "REGISTRATION_OPEN"}, headers=officer_headers)

    # Officer cannot register
    r_reg = await async_client.post(f"/api/v1/drives/{drive_id}/register", headers=officer_headers)
    assert r_reg.status_code == 403

    # Student cannot list registrations
    r_list = await async_client.get(f"/api/v1/drives/{drive_id}/registrations", headers=student_headers)
    assert r_list.status_code == 403
