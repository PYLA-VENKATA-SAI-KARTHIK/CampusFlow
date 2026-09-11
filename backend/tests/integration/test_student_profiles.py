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
from uuid import uuid4

@pytest_asyncio.fixture
async def auth_users(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> dict:
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
    admin = User(
        email="profile_admin@campusflow.com",
        password_hash=hash_password("password123"),
        role="ADMIN",
        full_name="Profile Admin",
        is_active=True,
    )

    db_session.add_all([student, officer, admin])
    await db_session.commit()

    await db_session.refresh(student)
    await db_session.refresh(officer)
    await db_session.refresh(admin)

    r_student = await async_client.post("/api/v1/auth/login", json={"email": student.email, "password": "password123"})
    r_officer = await async_client.post("/api/v1/auth/login", json={"email": officer.email, "password": "password123"})
    r_admin = await async_client.post("/api/v1/auth/login", json={"email": admin.email, "password": "password123"})

    return {
        "student": {"Authorization": f"Bearer {r_student.json()['access_token']}"},
        "officer": {"Authorization": f"Bearer {r_officer.json()['access_token']}"},
        "admin": {"Authorization": f"Bearer {r_admin.json()['access_token']}"},
        "student_id": student.id,
        "officer_id": officer.id,
        "admin_id": admin.id,
    }


@pytest_asyncio.fixture
async def test_branch(db_session: AsyncSession) -> str:
    branch = Branch(code="CSE_TST", name="Computer Science Test")
    branch2 = Branch(code="ECE_TST", name="Electronics Test")
    db_session.add_all([branch, branch2])
    await db_session.commit()
    return branch.code


@pytest_asyncio.fixture
async def test_profiles(db_session: AsyncSession, auth_users: dict, test_branch: str) -> dict:
    profile1 = StudentProfile(
        user_id=auth_users["student_id"],
        roll_number="12345678",
        branch_code=test_branch,
        batch_year=2024,
        cgpa=8.5,
        active_backlogs=0,
        phone_number="1234567890",
        gender="MALE",
        resume_gcs_path="resumes/test.pdf"
    )
    
    # Another student for list testing
    other_student = User(
        email="other@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Other Student",
        is_active=True,
    )
    db_session.add(other_student)
    await db_session.commit()
    await db_session.refresh(other_student)
    
    profile2 = StudentProfile(
        user_id=other_student.id,
        roll_number="87654321",
        branch_code="ECE_TST",
        batch_year=2025,
        cgpa=9.1,
        active_backlogs=1,
    )
    
    db_session.add_all([profile1, profile2])
    await db_session.commit()
    await db_session.refresh(profile1)
    await db_session.refresh(profile2)
    return {"profile1": str(profile1.id), "profile2": str(profile2.id)}


# 1. Student can GET /api/v1/students/me
@pytest.mark.asyncio
async def test_student_can_get_my_profile(async_client: AsyncClient, auth_users: dict, test_profiles: dict):
    response = await async_client.get("/api/v1/students/me", headers=auth_users["student"])
    assert response.status_code == 200
    data = response.json()
    assert data["roll_number"] == "12345678"
    assert data["cgpa"] == 8.5
    assert data["user"]["email"] == "profile_student@campusflow.com"


# 2. Non-student cannot access /api/v1/students/me
@pytest.mark.asyncio
async def test_unauthenticated_cannot_access_me(async_client: AsyncClient):
    response = await async_client.get("/api/v1/students/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_officer_cannot_access_me(async_client: AsyncClient, auth_users: dict):
    response = await async_client.get("/api/v1/students/me", headers=auth_users["officer"])
    assert response.status_code == 403


# 3. Student can update phone_number
@pytest.mark.asyncio
async def test_student_can_update_phone_number(async_client: AsyncClient, auth_users: dict, test_profiles: dict):
    response = await async_client.patch(
        "/api/v1/students/me",
        headers=auth_users["student"],
        json={"phone_number": "9999999999"}
    )
    assert response.status_code == 200
    assert response.json()["phone_number"] == "9999999999"

# 4. Student can update gender
@pytest.mark.asyncio
async def test_student_can_update_gender(async_client: AsyncClient, auth_users: dict, test_profiles: dict):
    response = await async_client.patch("/api/v1/students/me", headers=auth_users["student"], json={"gender": "FEMALE"})
    assert response.status_code == 200
    assert response.json()["gender"] == "FEMALE"

# 5. Student can update avatar using the intended field
@pytest.mark.asyncio
async def test_student_can_update_avatar(async_client: AsyncClient, auth_users: dict, test_profiles: dict):
    response = await async_client.patch("/api/v1/students/me", headers=auth_users["student"], json={"avatar_gcs_path": "avatars/new.png"})
    assert response.status_code == 200
    assert response.json()["avatar_gcs_path"] == "avatars/new.png"

# 6-11. Student cannot modify academic fields
@pytest.mark.parametrize("field,value", [
    ("cgpa", 9.9),
    ("active_backlogs", 5),
    ("branch_code", "ECE_TST"),
    ("batch_year", 2026),
    ("roll_number", "HACKER"),
    ("resume_gcs_path", "hack/resume.pdf")
])
@pytest.mark.asyncio
async def test_student_cannot_modify_protected_fields(async_client: AsyncClient, auth_users: dict, test_profiles: dict, field: str, value):
    response = await async_client.patch(
        "/api/v1/students/me",
        headers=auth_users["student"],
        json={field: value}
    )
    assert response.status_code == 403


# 12. Officer can list students
@pytest.mark.asyncio
async def test_officer_can_list_students(async_client: AsyncClient, auth_users: dict, test_profiles: dict):
    response = await async_client.get("/api/v1/officers/students", headers=auth_users["officer"])
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2

# 13. Admin can list students
@pytest.mark.asyncio
async def test_admin_can_list_students(async_client: AsyncClient, auth_users: dict, test_profiles: dict):
    response = await async_client.get("/api/v1/officers/students", headers=auth_users["admin"])
    assert response.status_code == 200
    assert response.json()["total"] >= 2


# 14. Student cannot access officer student endpoints
@pytest.mark.asyncio
async def test_student_cannot_access_officer_endpoints(async_client: AsyncClient, auth_users: dict):
    response = await async_client.get("/api/v1/officers/students", headers=auth_users["student"])
    assert response.status_code == 403


# 15. Officer can get a student profile
@pytest.mark.asyncio
async def test_officer_can_get_student(async_client: AsyncClient, auth_users: dict, test_profiles: dict):
    response = await async_client.get(f"/api/v1/officers/students/{test_profiles['profile1']}", headers=auth_users["officer"])
    assert response.status_code == 200
    assert response.json()["id"] == test_profiles['profile1']


# 16. Officer cannot get another student's data through /students/me
@pytest.mark.asyncio
async def test_officer_cannot_use_student_me(async_client: AsyncClient, auth_users: dict, test_profiles: dict):
    # Officer role is not STUDENT, so they should be 403'd from /students/me entirely.
    response = await async_client.get("/api/v1/students/me", headers=auth_users["officer"])
    assert response.status_code == 403


# 17. Pagination works correctly
@pytest.mark.asyncio
async def test_pagination(async_client: AsyncClient, auth_users: dict, test_profiles: dict):
    response = await async_client.get("/api/v1/officers/students?page=1&page_size=1", headers=auth_users["officer"])
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] >= 2
    
    response2 = await async_client.get("/api/v1/officers/students?page=2&page_size=1", headers=auth_users["officer"])
    assert response2.status_code == 200
    assert len(response2.json()["items"]) == 1
    assert response2.json()["items"][0]["id"] != data["items"][0]["id"]


# 18. Branch filter works
@pytest.mark.asyncio
async def test_branch_filter(async_client: AsyncClient, auth_users: dict, test_profiles: dict):
    response = await async_client.get("/api/v1/officers/students?branch_code=ECE_TST", headers=auth_users["officer"])
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["branch_code"] == "ECE_TST"


# 19. Batch year filter works
@pytest.mark.asyncio
async def test_batch_year_filter(async_client: AsyncClient, auth_users: dict, test_profiles: dict):
    response = await async_client.get("/api/v1/officers/students?batch_year=2024", headers=auth_users["officer"])
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["batch_year"] == 2024


# 20. Minimum CGPA filter works
@pytest.mark.asyncio
async def test_min_cgpa_filter(async_client: AsyncClient, auth_users: dict, test_profiles: dict):
    response = await async_client.get("/api/v1/officers/students?min_cgpa=9.0", headers=auth_users["officer"])
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["cgpa"] >= 9.0


# 21. Search filter works
@pytest.mark.asyncio
async def test_search_filter(async_client: AsyncClient, auth_users: dict, test_profiles: dict):
    response = await async_client.get("/api/v1/officers/students?search=Other", headers=auth_users["officer"])
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["roll_number"] == "87654321"


# 22. Officer resume download endpoint requires proper role
@pytest.mark.asyncio
async def test_resume_download_requires_officer(async_client: AsyncClient, auth_users: dict, test_profiles: dict):
    response = await async_client.get(f"/api/v1/officers/students/{test_profiles['profile1']}/resume-download-url", headers=auth_users["student"])
    assert response.status_code == 403


# 23. Resume download creates the required audit log
@pytest.mark.asyncio
async def test_resume_download_creates_audit_log(async_client: AsyncClient, auth_users: dict, test_profiles: dict, db_session: AsyncSession):
    response = await async_client.get(f"/api/v1/officers/students/{test_profiles['profile1']}/resume-download-url", headers=auth_users["officer"])
    assert response.status_code == 200
    assert "url" in response.json()
    assert "mock" in response.json()["url"]

    # Verify audit log
    stmt = select(AuditLog).where(AuditLog.entity_id == test_profiles["profile1"], AuditLog.action == "RESUME_DOWNLOADED")
    result = await db_session.execute(stmt)
    logs = result.scalars().all()
    assert len(logs) == 1
    assert logs[0].performed_by_user_id == auth_users["officer_id"]
    assert logs[0].new_state["resume_path"] == "resumes/test.pdf"


# --- Resume Flow Tests ---

@pytest.mark.asyncio
async def test_resume_upload_url(async_client: AsyncClient, auth_users: dict, test_profiles: dict):
    # 1. Student can request resume upload URL
    response = await async_client.get("/api/v1/students/me/resume-upload-url", headers=auth_users["student"])
    assert response.status_code == 200
    data = response.json()
    
    assert "upload_url" in data
    assert "object_path" in data
    
    # 3. Upload URL has expected expiration (15 mins = 900s)
    assert data["expires_in"] == 900
    
    # 4. Upload URL targets the authenticated student's namespace
    assert data["object_path"].startswith(f"resumes/{auth_users['student_id']}/")
    assert data["object_path"].endswith(".pdf")

@pytest.mark.asyncio
async def test_non_student_resume_upload_url(async_client: AsyncClient, auth_users: dict):
    # 2. Non-student cannot request resume upload URL
    response = await async_client.get("/api/v1/students/me/resume-upload-url", headers=auth_users["officer"])
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_resume_confirm_success(async_client: AsyncClient, auth_users: dict, test_profiles: dict):
    # 6. Student can confirm a valid PDF object
    # First get an upload URL to get a valid object path
    upload_res = await async_client.get("/api/v1/students/me/resume-upload-url", headers=auth_users["student"])
    object_path = upload_res.json()["object_path"]
    
    # Simulate GCS upload by placing the mock object in the storage service directly.
    # To do this safely in tests without importing the app's running instance, we can rely on the
    # storage service dependency caching or we can mock it here.
    # A simpler way: we'll override the storage service dependency for this test.
    from app.main import app
    from app.core.dependencies import get_storage_service
    from app.services.storage_service import MockStorageService
    
    mock_storage = MockStorageService(bucket_name="test-bucket")
    mock_storage.mock_objects[object_path] = {"size": 1024 * 1024, "content_type": "application/pdf"}
    
    app.dependency_overrides[get_storage_service] = lambda: mock_storage
    
    try:
        response = await async_client.post(
            "/api/v1/students/me/resume-confirm",
            headers=auth_users["student"],
            json={"object_path": object_path}
        )
        assert response.status_code == 200
        
        # 12. Successful confirmation updates resume_gcs_path
        data = response.json()
        assert data["resume_gcs_path"] == object_path
        
        # 13. Successful confirmation updates resume_uploaded_at
        assert data["resume_uploaded_at"] is not None
    finally:
        app.dependency_overrides.pop(get_storage_service, None)

@pytest.mark.asyncio
async def test_resume_confirm_idor(async_client: AsyncClient, auth_users: dict):
    # 7. Student cannot confirm another student's object
    # 8. Student cannot confirm an object outside their namespace
    response = await async_client.post(
        "/api/v1/students/me/resume-confirm",
        headers=auth_users["student"],
        json={"object_path": "resumes/some-other-uuid/hacked.pdf"}
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_resume_confirm_validation(async_client: AsyncClient, auth_users: dict, test_profiles: dict):
    upload_res = await async_client.get("/api/v1/students/me/resume-upload-url", headers=auth_users["student"])
    object_path = upload_res.json()["object_path"]
    
    from app.main import app
    from app.core.dependencies import get_storage_service
    from app.services.storage_service import MockStorageService
    
    mock_storage = MockStorageService(bucket_name="test-bucket")
    
    # 9. Non-PDF object is rejected
    mock_storage.mock_objects[object_path] = {"size": 1024, "content_type": "image/jpeg"}
    app.dependency_overrides[get_storage_service] = lambda: mock_storage
    
    try:
        response = await async_client.post(
            "/api/v1/students/me/resume-confirm",
            headers=auth_users["student"],
            json={"object_path": object_path}
        )
        assert response.status_code == 422
        
        # 10. File larger than 5 MB is rejected
        mock_storage.mock_objects[object_path] = {"size": 10 * 1024 * 1024, "content_type": "application/pdf"}
        response = await async_client.post(
            "/api/v1/students/me/resume-confirm",
            headers=auth_users["student"],
            json={"object_path": object_path}
        )
        assert response.status_code == 422
        
        # 11. Missing GCS object is rejected
        mock_storage.mock_objects.pop(object_path)
        response = await async_client.post(
            "/api/v1/students/me/resume-confirm",
            headers=auth_users["student"],
            json={"object_path": object_path}
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_storage_service, None)

@pytest.mark.asyncio
async def test_student_download_resume(async_client: AsyncClient, auth_users: dict, test_profiles: dict):
    # 14. Student can request own resume download URL
    response = await async_client.get("/api/v1/students/me/resume-download-url", headers=auth_users["student"])
    assert response.status_code == 200
    assert "url" in response.json()

@pytest.mark.asyncio
async def test_student_download_resume_not_found(async_client: AsyncClient, auth_users: dict, test_profiles: dict, db_session: AsyncSession):
    # Use profile2 which hasn't had a resume uploaded in the tests yet
    from app.models.student_profile import StudentProfile
    
    # Ensure it's clear
    stmt = select(StudentProfile).where(StudentProfile.id == test_profiles["profile2"])
    result = await db_session.execute(stmt)
    profile = result.scalar_one()
    profile.resume_gcs_path = None
    await db_session.commit()

    # Get student2's auth
    from app.models.user import User
    stmt = select(User).where(User.id == profile.user_id)
    result = await db_session.execute(stmt)
    student2 = result.scalar_one()
    
    r_login = await async_client.post("/api/v1/auth/login", json={"email": student2.email, "password": "password123"})
    token = r_login.json()["access_token"]
    
    # 15. Student without resume receives appropriate 404
    response = await async_client.get("/api/v1/students/me/resume-download-url", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
