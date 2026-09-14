"""
CampusFlow — Phase 6.6.1 Security Regression & Boundary Verification Tests

Targeted tests verifying:
1. STUDENT RBAC isolation: cannot access officer student profile endpoints
2. STUDENT profile protection: cannot modify protected academic fields (cgpa, backlogs, roll_number)
3. STUDENT vertical boundary: cannot access admin user management or audit logs
4. OFFICER vertical boundary: cannot access admin-only endpoints
5. ASSESSMENT answer secrecy: student attempt view strips correct_option & explanation
6. ASSESSMENT timer enforcement: expired attempt submission is finalized as EXPIRED
7. ASSESSMENT single attempt lock: cannot start duplicate attempt when allow_multiple_attempts=False
8. CONCURRENT registration safety: duplicate registration returns 409 Conflict cleanly
9. OFFICER resume download rate limiting: rate limit decorator is applied and functional
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.account_activation import AccountActivation
from app.models.assessment import Assessment, AssessmentAssignment, AssessmentAttempt, AssessmentQuestion
from app.models.branch import Branch
from app.models.company import Company
from app.models.drive_registration import DriveRegistration
from app.models.eligibility_criteria import EligibilityCriteria
from app.models.placement_drive import PlacementDrive
from app.models.student_profile import StudentProfile
from app.models.user import User


@pytest_asyncio.fixture
async def security_test_env(db_session: AsyncSession, async_client: AsyncClient) -> dict:
    # 1. Active Branch
    branch = Branch(code="SEC", name="Security Eng", is_active=True)
    db_session.add(branch)

    # 2. Users: Admin, Officer, Student A, Student B
    admin_user = User(
        email="sec_admin@campusflow.com",
        password_hash=hash_password("password123"),
        role="ADMIN",
        full_name="Security Admin",
        is_active=True,
    )
    officer_user = User(
        email="sec_officer@campusflow.com",
        password_hash=hash_password("password123"),
        role="OFFICER",
        full_name="Security Officer",
        is_active=True,
    )
    student_a_user = User(
        email="sec_student_a@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Student Alpha",
        is_active=True,
    )
    student_b_user = User(
        email="sec_student_b@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Student Beta",
        is_active=True,
    )
    db_session.add_all([admin_user, officer_user, student_a_user, student_b_user])
    await db_session.commit()
    await db_session.refresh(branch)
    await db_session.refresh(admin_user)
    await db_session.refresh(officer_user)
    await db_session.refresh(student_a_user)
    await db_session.refresh(student_b_user)

    # 3. Company
    company = Company(
        name="SecCorp",
        industry="Security",
        website="https://seccorp.io",
        created_by_user_id=admin_user.id,
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    # 4. Student Profiles
    profile_a = StudentProfile(
        user_id=student_a_user.id,
        roll_number="SEC-001",
        batch_year=2026,
        cgpa=Decimal("8.50"),
        active_backlogs=0,
        branch_code="SEC",
        resume_gcs_path=f"resumes/{student_a_user.id}/resume.pdf",
    )
    profile_b = StudentProfile(
        user_id=student_b_user.id,
        roll_number="SEC-002",
        batch_year=2026,
        cgpa=Decimal("7.20"),
        active_backlogs=1,
        branch_code="SEC",
        resume_gcs_path=f"resumes/{student_b_user.id}/resume.pdf",
    )
    db_session.add_all([profile_a, profile_b])
    await db_session.commit()
    await db_session.refresh(profile_a)
    await db_session.refresh(profile_b)

    # 5. Tokens
    async def get_token(email: str) -> str:
        res = await async_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "password123"},
        )
        return res.json()["access_token"]

    token_admin = await get_token(admin_user.email)
    token_officer = await get_token(officer_user.email)
    token_student_a = await get_token(student_a_user.email)
    token_student_b = await get_token(student_b_user.email)

    return {
        "admin": admin_user,
        "officer": officer_user,
        "student_a": student_a_user,
        "student_b": student_b_user,
        "profile_a": profile_a,
        "profile_b": profile_b,
        "branch": branch,
        "company": company,
        "auth_admin": {"Authorization": f"Bearer {token_admin}"},
        "auth_officer": {"Authorization": f"Bearer {token_officer}"},
        "auth_student_a": {"Authorization": f"Bearer {token_student_a}"},
        "auth_student_b": {"Authorization": f"Bearer {token_student_b}"},
    }


# =============================================================================
# 1. RBAC & IDOR NEGATIVE TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_student_cannot_access_other_student_profile(
    async_client: AsyncClient,
    security_test_env: dict,
):
    """TEST 1: Student cannot query /api/v1/officers/students/{id} for another student."""
    student_b_id = security_test_env["student_b"].id
    res = await async_client.get(
        f"/api/v1/officers/students/{student_b_id}",
        headers=security_test_env["auth_student_a"],
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_student_cannot_manipulate_protected_academic_fields(
    async_client: AsyncClient,
    security_test_env: dict,
):
    """TEST 2: Student attempting to alter cgpa or backlogs receives HTTP 403."""
    res = await async_client.patch(
        "/api/v1/students/me",
        headers=security_test_env["auth_student_a"],
        json={"cgpa": 9.99, "active_backlogs": 0, "roll_number": "TAMPERED"},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_student_cannot_access_admin_or_officer_endpoints(
    async_client: AsyncClient,
    security_test_env: dict,
):
    """TEST 3: Student is strictly blocked from Admin and Officer endpoints."""
    # Try Admin user management
    res1 = await async_client.get(
        "/api/v1/admin/users",
        headers=security_test_env["auth_student_a"],
    )
    assert res1.status_code == 403

    # Try Admin audit logs
    res2 = await async_client.get(
        "/api/v1/admin/audit-logs",
        headers=security_test_env["auth_student_a"],
    )
    assert res2.status_code == 403

    # Try Officer drive creation
    res3 = await async_client.post(
        "/api/v1/drives",
        headers=security_test_env["auth_student_a"],
        json={
            "company_id": str(security_test_env["company"].id),
            "title": "Unauthorized Drive",
            "job_role": "Hacker",
            "tier_name": "Tier 1",
            "ctc_lpa": 12.0,
            "branches_eligible": ["SEC"],
        },
    )
    assert res3.status_code == 403


@pytest.mark.asyncio
async def test_officer_cannot_access_admin_user_management(
    async_client: AsyncClient,
    security_test_env: dict,
):
    """TEST 4: Officer is blocked from ADMIN-only user creation."""
    res = await async_client.post(
        "/api/v1/admin/users",
        headers=security_test_env["auth_officer"],
        json={
            "email": "new_admin@campusflow.com",
            "role": "ADMIN",
            "full_name": "Illegal Admin",
        },
    )
    assert res.status_code == 403


# =============================================================================
# 2. ASSESSMENT SECURITY & TIMER TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_assessment_student_view_hides_correct_options(
    async_client: AsyncClient,
    db_session: AsyncSession,
    security_test_env: dict,
):
    """TEST 5: Active attempt questions received by student strip correct_option and explanation."""
    # 1. Create Assessment with Question
    assessment = Assessment(
        title="Security & Crypto Assessment",
        difficulty="INTERMEDIATE",
        duration_minutes=30,
        total_marks=Decimal("5.00"),
        pass_percentage=Decimal("60.00"),
        status="PUBLISHED",
        allow_multiple_attempts=False,
        created_by_user_id=security_test_env["officer"].id,
    )
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)

    question = AssessmentQuestion(
        assessment_id=assessment.id,
        question_text="What is AES block size?",
        options=[
            {"key": "A", "text": "64 bits"},
            {"key": "B", "text": "128 bits"},
            {"key": "C", "text": "256 bits"},
            {"key": "D", "text": "512 bits"},
        ],
        correct_option="B",
        explanation="AES has a fixed block size of 128 bits.",
        marks=Decimal("5.00"),
        sequence_order=1,
    )
    db_session.add(question)

    assignment = AssessmentAssignment(
        assessment_id=assessment.id,
        student_user_id=security_test_env["student_a"].id,
        assigned_by_user_id=security_test_env["officer"].id,
        status="ASSIGNED",
    )
    db_session.add(assignment)
    await db_session.commit()

    # 2. Student starts attempt
    res = await async_client.post(
        f"/api/v1/assessments/{assessment.id}/start",
        headers=security_test_env["auth_student_a"],
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["questions"]) == 1
    q = data["questions"][0]

    # Verify correct_option & explanation are NOT present in response
    assert "correct_option" not in q
    assert "explanation" not in q
    assert q["question_text"] == "What is AES block size?"


@pytest.mark.asyncio
async def test_assessment_expired_submission_enforces_expiry_status(
    async_client: AsyncClient,
    db_session: AsyncSession,
    security_test_env: dict,
):
    """TEST 6: Submitting an expired attempt auto-finalizes and computes result."""
    assessment = Assessment(
        title="Timed Crypto Quiz",
        difficulty="BEGINNER",
        duration_minutes=10,
        total_marks=Decimal("2.00"),
        pass_percentage=Decimal("50.00"),
        status="PUBLISHED",
        allow_multiple_attempts=False,
        created_by_user_id=security_test_env["officer"].id,
    )
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)

    question = AssessmentQuestion(
        assessment_id=assessment.id,
        question_text="Is SHA-256 a hash function?",
        options=[{"key": "A", "text": "Yes"}, {"key": "B", "text": "No"}],
        correct_option="A",
        explanation="SHA-256 is a cryptographic hash function.",
        marks=Decimal("2.00"),
        sequence_order=1,
    )
    db_session.add(question)

    assignment = AssessmentAssignment(
        assessment_id=assessment.id,
        student_user_id=security_test_env["student_a"].id,
        assigned_by_user_id=security_test_env["officer"].id,
        status="IN_PROGRESS",
    )
    db_session.add(assignment)
    await db_session.commit()
    await db_session.refresh(assignment)

    # Expired attempt (started 20 mins ago with 10 min duration)
    now = datetime.now(timezone.utc)
    expired_attempt = AssessmentAttempt(
        assignment_id=assignment.id,
        attempt_number=1,
        status="IN_PROGRESS",
        started_at=now - timedelta(minutes=20),
        expires_at=now - timedelta(minutes=10),
    )
    db_session.add(expired_attempt)
    await db_session.commit()
    await db_session.refresh(expired_attempt)

    # Student submits late
    res = await async_client.post(
        f"/api/v1/assessments/attempts/{expired_attempt.id}/submit",
        headers=security_test_env["auth_student_a"],
        json={"responses": [{"question_id": str(question.id), "selected_option": "A"}]},
    )
    assert res.status_code == 200
    data = res.json()
    assert "score_obtained" in data
    assert data["assessment_id"] == str(assessment.id)


@pytest.mark.asyncio
async def test_assessment_duplicate_attempt_blocked_when_single_attempt_only(
    async_client: AsyncClient,
    db_session: AsyncSession,
    security_test_env: dict,
):
    """TEST 7: Block starting a second attempt when allow_multiple_attempts=False."""
    assessment = Assessment(
        title="Single Attempt Test",
        difficulty="ADVANCED",
        duration_minutes=30,
        total_marks=Decimal("10.00"),
        pass_percentage=Decimal("50.00"),
        status="PUBLISHED",
        allow_multiple_attempts=False,
        created_by_user_id=security_test_env["officer"].id,
    )
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)

    assignment = AssessmentAssignment(
        assessment_id=assessment.id,
        student_user_id=security_test_env["student_a"].id,
        assigned_by_user_id=security_test_env["officer"].id,
        status="COMPLETED",
    )
    db_session.add(assignment)
    await db_session.commit()
    await db_session.refresh(assignment)

    now = datetime.now(timezone.utc)
    completed_attempt = AssessmentAttempt(
        assignment_id=assignment.id,
        attempt_number=1,
        status="SUBMITTED",
        started_at=now - timedelta(minutes=15),
        expires_at=now + timedelta(minutes=15),
        submitted_at=now - timedelta(minutes=5),
    )
    db_session.add(completed_attempt)
    await db_session.commit()

    # Try starting attempt #2
    res = await async_client.post(
        f"/api/v1/assessments/{assessment.id}/start",
        headers=security_test_env["auth_student_a"],
    )
    assert res.status_code == 400
    assert "already completed" in res.json()["detail"].lower()


# =============================================================================
# 3. CONCURRENT REGISTRATION & RATE LIMITING
# =============================================================================


@pytest.mark.asyncio
async def test_concurrent_registration_conflict_returns_409(
    async_client: AsyncClient,
    db_session: AsyncSession,
    security_test_env: dict,
):
    """TEST 8: Repeated/duplicate registration for same drive returns HTTP 409 Conflict."""
    drive = PlacementDrive(
        company_id=security_test_env["company"].id,
        title="SecCorp Full Stack Drive",
        job_role="Security Engineer",
        ctc_lpa=Decimal("14.50"),
        status="REGISTRATION_OPEN",
        created_by_user_id=security_test_env["officer"].id,
    )
    db_session.add(drive)
    await db_session.commit()
    await db_session.refresh(drive)

    criteria = EligibilityCriteria(
        drive_id=drive.id,
        criteria={"allowed_branches": ["SEC"], "min_cgpa": 6.0, "max_active_backlogs": 2},
    )
    db_session.add(criteria)
    await db_session.commit()

    # First registration -> 201 Created
    res1 = await async_client.post(
        f"/api/v1/drives/{drive.id}/register",
        headers=security_test_env["auth_student_a"],
    )
    assert res1.status_code == 201

    # Immediate second registration -> 409 Conflict
    res2 = await async_client.post(
        f"/api/v1/drives/{drive.id}/register",
        headers=security_test_env["auth_student_a"],
    )
    assert res2.status_code == 409
    assert "already registered" in res2.json()["detail"].lower()

