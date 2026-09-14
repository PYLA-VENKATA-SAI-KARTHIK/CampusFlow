"""
Comprehensive backend tests for the Student Registration Number flow.

Covers:
1. Valid registration number can register an eligible student.
2. Unknown registration number is rejected.
3. Already activated student cannot register again.
4. Duplicate user is not created.
5. Student can log in after registration.
6. One student cannot register/activate another student's account.
7. Password is never returned in API responses.
8. Existing authorization/RBAC behavior remains intact.
"""
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.branch import Branch
from app.models.student_profile import StudentProfile
from app.models.user import User


@pytest.fixture
async def ensure_branch(db_session: AsyncSession) -> Branch:
    """Ensure CSE branch exists in the test database."""
    res = await db_session.execute(select(Branch).where(Branch.code == "CSE"))
    branch = res.scalar_one_or_none()
    if not branch:
        branch = Branch(code="CSE", name="Computer Science and Engineering")
        db_session.add(branch)
        await db_session.commit()
    return branch



@pytest.fixture
async def eligible_student(
    db_session: AsyncSession, ensure_branch: Branch
) -> tuple[User, StudentProfile]:
    """Pre-provision an unactivated student with a known registration number."""
    user = User(
        id=uuid4(),
        email="unregistered.student@campusflow.edu",
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
        roll_number="99230041249",
        branch_code=ensure_branch.code,
        batch_year=2026,
        cgpa=8.50,
        active_backlogs=0,
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(profile)
    return user, profile


@pytest.mark.asyncio
async def test_register_success(
    async_client: AsyncClient,
    eligible_student: tuple[User, StudentProfile],
    db_session: AsyncSession,
):
    """1. Valid registration number can register an eligible student."""
    user, profile = eligible_student
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "registration_number": "99230041249",
            "password": "NewSecurePassword123!",
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Registration completed successfully. You can now sign in."
    assert data["registration_number"] == "99230041249"
    assert data["email"] == "99230041249@klu.ac.in"

    # Verify DB state
    await db_session.refresh(user)
    assert user.email == "99230041249@klu.ac.in"
    assert user.is_active is True
    assert user.must_change_password is False
    assert verify_password("NewSecurePassword123!", user.password_hash)


@pytest.mark.asyncio
async def test_register_unknown_registration_number(async_client: AsyncClient):
    """2. Unknown registration number is rejected with 404."""
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "registration_number": "NON_EXISTENT_99999",
            "password": "NewSecurePassword123!",
        },
    )
    assert response.status_code == 404
    data = response.json()
    assert "Registration number not found. Please contact your placement office." in data["detail"]


@pytest.mark.asyncio
async def test_register_already_activated_rejected(
    async_client: AsyncClient,
    eligible_student: tuple[User, StudentProfile],
):
    """3. Already activated student cannot register again (returns 409)."""
    # First registration
    res1 = await async_client.post(
        "/api/v1/auth/register",
        json={
            "registration_number": "99230041249",
            "password": "NewSecurePassword123!",
        },
    )
    assert res1.status_code == 200

    # Second registration attempt
    res2 = await async_client.post(
        "/api/v1/auth/register",
        json={
            "registration_number": "99230041249",
            "password": "AnotherPassword456!",
        },
    )
    assert res2.status_code == 409
    data = res2.json()
    assert "This student account is already registered. Please sign in." in data["detail"]


@pytest.mark.asyncio
async def test_duplicate_user_not_created(
    async_client: AsyncClient,
    eligible_student: tuple[User, StudentProfile],
    db_session: AsyncSession,
):
    """4. Duplicate user is not created during registration."""
    users_before = await db_session.scalar(select(func.count(User.id)))
    profiles_before = await db_session.scalar(select(func.count(StudentProfile.id)))

    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "registration_number": "99230041249",
            "password": "NewSecurePassword123!",
        },
    )
    assert response.status_code == 200

    users_after = await db_session.scalar(select(func.count(User.id)))
    profiles_after = await db_session.scalar(select(func.count(StudentProfile.id)))

    assert users_after == users_before
    assert profiles_after == profiles_before


@pytest.mark.asyncio
async def test_student_can_login_after_registration(
    async_client: AsyncClient,
    eligible_student: tuple[User, StudentProfile],
):
    """5. Student can log in after registration using newly set password."""
    user, profile = eligible_student
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={
            "registration_number": profile.roll_number,
            "password": "NewSecurePassword123!",
        },
    )
    assert reg_res.status_code == 200

    # Login with university email
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": f"{profile.roll_number}@klu.ac.in",
            "password": "NewSecurePassword123!",
        },
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # Login with registration number (dual login support)
    login_reg_res = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": profile.roll_number,
            "password": "NewSecurePassword123!",
        },
    )
    assert login_reg_res.status_code == 200
    assert "access_token" in login_reg_res.json()


@pytest.mark.asyncio
async def test_cannot_hijack_another_students_account(
    async_client: AsyncClient,
    eligible_student: tuple[User, StudentProfile],
    db_session: AsyncSession,
):
    """6. One student cannot hijack/re-register another student's account."""
    user, profile = eligible_student
    # Register legit student
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "registration_number": profile.roll_number,
            "password": "OriginalPassword123!",
        },
    )

    # Malicious actor tries to overwrite password with their own
    malicious_res = await async_client.post(
        "/api/v1/auth/register",
        json={
            "registration_number": profile.roll_number,
            "password": "HackerPassword999!",
        },
    )
    assert malicious_res.status_code == 409

    # Original password remains valid
    login_check = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": f"{profile.roll_number}@klu.ac.in",
            "password": "OriginalPassword123!",
        },
    )
    assert login_check.status_code == 200

    # Hacker password fails
    login_hacker = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": f"{profile.roll_number}@klu.ac.in",
            "password": "HackerPassword999!",
        },
    )
    assert login_hacker.status_code == 401


@pytest.mark.asyncio
async def test_password_never_returned_in_api_response(
    async_client: AsyncClient,
    eligible_student: tuple[User, StudentProfile],
):
    """7. Password and password hashes are NEVER returned in API responses."""
    user, profile = eligible_student
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "registration_number": profile.roll_number,
            "password": "NewSecurePassword123!",
        },
    )
    assert response.status_code == 200
    raw_text = response.text
    assert "NewSecurePassword123!" not in raw_text
    assert "password_hash" not in raw_text
    assert "$2b$" not in raw_text


@pytest.mark.asyncio
async def test_rbac_and_academic_integrity(
    async_client: AsyncClient,
    eligible_student: tuple[User, StudentProfile],
    db_session: AsyncSession,
):
    """8. Academic fields remain intact and RBAC guards are preserved."""
    user, profile = eligible_student
    original_cgpa = float(profile.cgpa)
    original_branch = profile.branch_code
    original_batch = profile.batch_year

    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={
            "registration_number": profile.roll_number,
            "password": "NewSecurePassword123!",
        },
    )
    assert reg_res.status_code == 200

    # Verify student profile fields are untouched
    await db_session.refresh(profile)
    assert float(profile.cgpa) == original_cgpa
    assert profile.branch_code == original_branch
    assert profile.batch_year == original_batch

    # Login to get JWT
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": f"{profile.roll_number}@klu.ac.in",
            "password": "NewSecurePassword123!",
        },
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Student can access own profile
    me_res = await async_client.get("/api/v1/students/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["roll_number"] == profile.roll_number

    # Student CANNOT access admin endpoints (RBAC 403)
    admin_res = await async_client.get("/api/v1/admin/users", headers=headers)
    assert admin_res.status_code == 403


@pytest.mark.asyncio
async def test_student_name_update_and_protected_academic_fields(
    async_client: AsyncClient,
    eligible_student: tuple[User, StudentProfile],
    db_session: AsyncSession,
):
    """9. Student can edit their display name, but academic fields remain strictly locked."""
    user, profile = eligible_student
    # Register first
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "registration_number": profile.roll_number,
            "password": "NewSecurePassword123!",
        },
    )

    # Login to get JWT
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "99230041249@klu.ac.in",
            "password": "NewSecurePassword123!",
        },
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Update full_name
    update_res = await async_client.patch(
        "/api/v1/students/me",
        json={"full_name": "Updated Student Name", "phone_number": "+91 9999988888"},
        headers=headers,
    )
    assert update_res.status_code == 200
    res_data = update_res.json()
    assert res_data["user"]["full_name"] == "Updated Student Name"
    assert res_data["phone_number"] == "+91 9999988888"

    # Verify DB state
    await db_session.refresh(user)
    assert user.full_name == "Updated Student Name"

    # 2. Attempting to modify protected academic fields is rejected with 403
    hack_res = await async_client.patch(
        "/api/v1/students/me",
        json={"cgpa": 10.0, "roll_number": "HACKED_ROLL", "batch_year": 2030},
        headers=headers,
    )
    assert hack_res.status_code == 403
    assert "Cannot modify protected academic or system fields." in hack_res.json()["detail"]

    # Verify academic fields did not change in DB
    await db_session.refresh(profile)
    assert profile.roll_number == "99230041249"
    assert float(profile.cgpa) == 8.50
    assert profile.batch_year == 2026
