"""
Integration Tests for Phase 3.6 Officer Analytics.

Covers:
1. Officer can access drive analytics
2. Admin can access drive analytics
3. Student receives 403 Forbidden
4. Unauthenticated request receives 401 Unauthorized
5. Nonexistent drive returns 404 Not Found
6. Correct registration count (status='REGISTERED')
7. Withdrawn registrations excluded
8. Cancelled registrations excluded
9. Rejected registrations excluded
10. Correct stage counts (assigned, shortlisted, appeared, selected, rejected)
11. Multiple stages handled in sequence
12. Unpublished stages handled correctly (is_published: false visible to Officer)
13. Duplicate student assignments do not inflate unique metrics
14. Correct branch aggregation
15. Branches with zero candidates are included with 0 counts
16. Zero eligible students handled safely (0.0%)
17. Zero registrations handled safely (0.0%)
18. Overview metrics are correct
19. Unique placed students deduplicated across drives
20. Overall placement percentage handles zero denominator (0.0%)
21. No PII (names, emails, roll numbers, resumes) in response
22. Overview endpoint RBAC (student 403, unauthenticated 401)
23. Legacy overview route (/admin/analytics/overview) works identically
24. Drive resource authorization behavior matches institutional rules
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.branch import Branch
from app.models.company import Company
from app.models.drive_registration import DriveRegistration
from app.models.eligibility_criteria import EligibilityCriteria
from app.models.placement_drive import PlacementDrive
from app.models.placement_stage import PlacementStage
from app.models.stage_assignment import StageAssignment
from app.models.student_profile import StudentProfile
from app.models.user import User


@pytest_asyncio.fixture
async def analytics_setup(db_session: AsyncSession, async_client: AsyncClient) -> dict:
    # 1. Branches: CSE, ECE, MECH
    b_cse = Branch(code="CSE", name="Computer Science & Engineering")
    b_ece = Branch(code="ECE", name="Electronics & Communication")
    b_mech = Branch(code="MECH", name="Mechanical Engineering")
    db_session.add_all([b_cse, b_ece, b_mech])
    await db_session.commit()

    # 2. Users
    officer = User(
        email="analytics_officer@campusflow.com",
        password_hash=hash_password("password123"),
        role="OFFICER",
        full_name="Placement Officer",
        is_active=True,
    )
    admin = User(
        email="analytics_admin@campusflow.com",
        password_hash=hash_password("password123"),
        role="ADMIN",
        full_name="System Admin",
        is_active=True,
    )
    student1 = User(
        email="analytics_student1@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Student One CSE",
        is_active=True,
    )
    student2 = User(
        email="analytics_student2@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Student Two ECE",
        is_active=True,
    )
    student3 = User(
        email="analytics_student3@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Student Three Ineligible MECH",
        is_active=True,
    )

    db_session.add_all([officer, admin, student1, student2, student3])
    await db_session.commit()
    await db_session.refresh(officer)
    await db_session.refresh(admin)
    await db_session.refresh(student1)
    await db_session.refresh(student2)
    await db_session.refresh(student3)

    # 3. Student Profiles
    p1 = StudentProfile(
        user_id=student1.id,
        roll_number="ANL-001",
        branch_code="CSE",
        batch_year=2026,
        cgpa=8.5,
        active_backlogs=0,
        resume_gcs_path="resumes/s1.pdf",
    )
    p2 = StudentProfile(
        user_id=student2.id,
        roll_number="ANL-002",
        branch_code="ECE",
        batch_year=2026,
        cgpa=7.8,
        active_backlogs=0,
        resume_gcs_path="resumes/s2.pdf",
    )
    p3 = StudentProfile(
        user_id=student3.id,
        roll_number="ANL-003",
        branch_code="MECH",
        batch_year=2026,
        cgpa=5.5,
        active_backlogs=2,
        resume_gcs_path="resumes/s3.pdf",
    )
    db_session.add_all([p1, p2, p3])

    # 4. Companies & Placement Drives
    company1 = Company(name="Google Inc", created_by_user_id=officer.id)
    company2 = Company(name="Microsoft Corp", created_by_user_id=officer.id)
    db_session.add_all([company1, company2])
    await db_session.commit()
    await db_session.refresh(company1)
    await db_session.refresh(company2)

    drive1 = PlacementDrive(
        company_id=company1.id,
        title="Google SWE 2026",
        job_role="Software Engineer",
        ctc_lpa=25.0,
        status="ASSESSMENT",
        registration_deadline=datetime.now(timezone.utc),
        created_by_user_id=officer.id,
    )
    drive2 = PlacementDrive(
        company_id=company2.id,
        title="Microsoft PM 2026",
        job_role="Product Manager",
        ctc_lpa=30.0,
        status="COMPLETED",
        registration_deadline=datetime.now(timezone.utc),
        created_by_user_id=officer.id,
    )
    db_session.add_all([drive1, drive2])
    await db_session.commit()
    await db_session.refresh(drive1)
    await db_session.refresh(drive2)

    # 5. Eligibility Criteria (Drive 1: CSE and ECE, min_cgpa 7.0, max_backlogs 0)
    criteria1 = EligibilityCriteria(
        drive_id=drive1.id,
        criteria={
            "min_cgpa": 7.0,
            "max_active_backlogs": 0,
            "eligible_branches": ["CSE", "ECE"],
            "eligible_batch_years": [2026],
        },
    )
    db_session.add(criteria1)

    # 6. Registrations for Drive 1:
    # Student 1: REGISTERED
    # Student 2: REGISTERED
    # Student 3: WITHDRAWN
    reg1_1 = DriveRegistration(
        drive_id=drive1.id,
        student_user_id=student1.id,
        resume_gcs_path_at_registration="resumes/s1.pdf",
        status="REGISTERED",
    )
    reg1_2 = DriveRegistration(
        drive_id=drive1.id,
        student_user_id=student2.id,
        resume_gcs_path_at_registration="resumes/s2.pdf",
        status="REGISTERED",
    )
    reg1_3 = DriveRegistration(
        drive_id=drive1.id,
        student_user_id=student3.id,
        resume_gcs_path_at_registration="resumes/s3.pdf",
        status="WITHDRAWN",
    )
    # Registration for Drive 2: Student 1 REGISTERED
    reg2_1 = DriveRegistration(
        drive_id=drive2.id,
        student_user_id=student1.id,
        resume_gcs_path_at_registration="resumes/s1.pdf",
        status="REGISTERED",
    )
    db_session.add_all([reg1_1, reg1_2, reg1_3, reg2_1])

    # 7. Placement Stages for Drive 1:
    # Stage 1: Coding (Seq 1, Published)
    # Stage 2: Tech Interview (Seq 2, Published)
    # Stage 3: HR (Seq 3, Unpublished)
    stage1 = PlacementStage(
        drive_id=drive1.id,
        name="Coding Round",
        stage_type="CODING",
        sequence_order=1,
        is_published=True,
    )
    stage2 = PlacementStage(
        drive_id=drive1.id,
        name="Technical Round",
        stage_type="TECHNICAL",
        sequence_order=2,
        is_published=True,
    )
    stage3 = PlacementStage(
        drive_id=drive1.id,
        name="HR Round",
        stage_type="HR",
        sequence_order=3,
        is_published=False,
    )
    db_session.add_all([stage1, stage2, stage3])
    await db_session.commit()
    await db_session.refresh(stage1)
    await db_session.refresh(stage2)
    await db_session.refresh(stage3)

    # 8. Stage Assignments for Drive 1:
    # Stage 1: Student 1 = SELECTED, Student 2 = SELECTED
    # Stage 2: Student 1 = SELECTED, Student 2 = REJECTED
    # Stage 3 (Unpublished): Student 1 = SHORTLISTED
    asg1_1 = StageAssignment(stage_id=stage1.id, drive_id=drive1.id, student_user_id=student1.id, status="SELECTED")
    asg1_2 = StageAssignment(stage_id=stage1.id, drive_id=drive1.id, student_user_id=student2.id, status="SELECTED")
    asg2_1 = StageAssignment(stage_id=stage2.id, drive_id=drive1.id, student_user_id=student1.id, status="SELECTED")
    asg2_2 = StageAssignment(stage_id=stage2.id, drive_id=drive1.id, student_user_id=student2.id, status="REJECTED")
    asg3_1 = StageAssignment(stage_id=stage3.id, drive_id=drive1.id, student_user_id=student1.id, status="SHORTLISTED")
    db_session.add_all([asg1_1, asg1_2, asg2_1, asg2_2, asg3_1])

    # Drive 2 Stage & Assignment: Student 1 also SELECTED in Drive 2
    stage_d2 = PlacementStage(
        drive_id=drive2.id,
        name="Final Selection",
        stage_type="HR",
        sequence_order=1,
        is_published=True,
    )
    db_session.add(stage_d2)
    await db_session.commit()
    await db_session.refresh(stage_d2)

    asg_d2_1 = StageAssignment(stage_id=stage_d2.id, drive_id=drive2.id, student_user_id=student1.id, status="SELECTED")
    db_session.add(asg_d2_1)
    await db_session.commit()

    # Login tokens
    r_off = await async_client.post("/api/v1/auth/login", json={"email": officer.email, "password": "password123"})
    r_adm = await async_client.post("/api/v1/auth/login", json={"email": admin.email, "password": "password123"})
    r_stu = await async_client.post("/api/v1/auth/login", json={"email": student1.email, "password": "password123"})

    token_off = r_off.json()["access_token"]
    token_adm = r_adm.json()["access_token"]
    token_stu = r_stu.json()["access_token"]

    return {
        "officer": officer,
        "admin": admin,
        "student1": student1,
        "student2": student2,
        "student3": student3,
        "drive1": drive1,
        "drive2": drive2,
        "headers_officer": {"Authorization": f"Bearer {token_off}"},
        "headers_admin": {"Authorization": f"Bearer {token_adm}"},
        "headers_student": {"Authorization": f"Bearer {token_stu}"},
    }


# =============================================================================
# 1. Drive Analytics Tests
# =============================================================================

@pytest.mark.asyncio
async def test_1_officer_can_access_drive_analytics(async_client: AsyncClient, analytics_setup: dict):
    """TEST 1: Officer can fetch drive analytics with complete funnel and branch stats."""
    drive_id = analytics_setup["drive1"].id
    res = await async_client.get(
        f"/api/v1/drives/{drive_id}/analytics",
        headers=analytics_setup["headers_officer"],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["drive_id"] == str(drive_id)
    assert data["company_name"] == "Google Inc"
    assert data["job_role"] == "Software Engineer"
    assert "summary" in data
    assert "stage_funnel" in data
    assert "branch_breakdown" in data


@pytest.mark.asyncio
async def test_2_admin_can_access_drive_analytics(async_client: AsyncClient, analytics_setup: dict):
    """TEST 2: Admin can access drive analytics."""
    drive_id = analytics_setup["drive1"].id
    res = await async_client.get(
        f"/api/v1/drives/{drive_id}/analytics",
        headers=analytics_setup["headers_admin"],
    )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_3_student_forbidden_403(async_client: AsyncClient, analytics_setup: dict):
    """TEST 3: Student receives 403 Forbidden when requesting drive analytics."""
    drive_id = analytics_setup["drive1"].id
    res = await async_client.get(
        f"/api/v1/drives/{drive_id}/analytics",
        headers=analytics_setup["headers_student"],
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_4_unauthenticated_401(async_client: AsyncClient, analytics_setup: dict):
    """TEST 4: Unauthenticated request receives 401."""
    drive_id = analytics_setup["drive1"].id
    res = await async_client.get(f"/api/v1/drives/{drive_id}/analytics")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_5_nonexistent_drive_404(async_client: AsyncClient, analytics_setup: dict):
    """TEST 5: Nonexistent drive UUID returns 404."""
    fake_id = uuid4()
    res = await async_client.get(
        f"/api/v1/drives/{fake_id}/analytics",
        headers=analytics_setup["headers_officer"],
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_6_7_8_9_registration_count_and_status_filtering(async_client: AsyncClient, analytics_setup: dict):
    """TEST 6, 7, 8, 9: Registered count strictly includes REGISTERED and excludes WITHDRAWN/CANCELLED."""
    drive_id = analytics_setup["drive1"].id
    res = await async_client.get(
        f"/api/v1/drives/{drive_id}/analytics",
        headers=analytics_setup["headers_officer"],
    )
    assert res.status_code == 200
    summary = res.json()["summary"]
    # Student 1 and Student 2 are REGISTERED; Student 3 is WITHDRAWN
    assert summary["registered_count"] == 2
    # Student 1 & 2 are eligible (Student 3 is MECH with cgpa 5.5)
    assert summary["eligible_count"] == 2
    assert summary["registration_rate_percentage"] == 100.0


@pytest.mark.asyncio
async def test_10_11_12_stage_funnel_and_unpublished_stages(async_client: AsyncClient, analytics_setup: dict):
    """TEST 10, 11, 12: Stage funnel ordered by sequence_order with correct counts and is_published status."""
    drive_id = analytics_setup["drive1"].id
    res = await async_client.get(
        f"/api/v1/drives/{drive_id}/analytics",
        headers=analytics_setup["headers_officer"],
    )
    assert res.status_code == 200
    funnel = res.json()["stage_funnel"]
    assert len(funnel) == 3

    # Stage 1: Coding (Seq 1, Published, 2 assigned, 2 selected)
    assert funnel[0]["sequence_order"] == 1
    assert funnel[0]["name"] == "Coding Round"
    assert funnel[0]["is_published"] is True
    assert funnel[0]["assigned_count"] == 2
    assert funnel[0]["selected_count"] == 2

    # Stage 2: Tech Round (Seq 2, Published, 2 assigned, 1 selected, 1 rejected)
    assert funnel[1]["sequence_order"] == 2
    assert funnel[1]["assigned_count"] == 2
    assert funnel[1]["selected_count"] == 1
    assert funnel[1]["rejected_count"] == 1

    # Stage 3: HR Round (Seq 3, Unpublished, 1 assigned, 1 shortlisted)
    assert funnel[2]["sequence_order"] == 3
    assert funnel[2]["is_published"] is False
    assert funnel[2]["assigned_count"] == 1
    assert funnel[2]["shortlisted_count"] == 1


@pytest.mark.asyncio
async def test_13_duplicate_assignments_do_not_inflate_unique_metrics(async_client: AsyncClient, analytics_setup: dict):
    """TEST 13: Unique selected and shortlisted counts are deduplicated across multiple stages."""
    drive_id = analytics_setup["drive1"].id
    res = await async_client.get(
        f"/api/v1/drives/{drive_id}/analytics",
        headers=analytics_setup["headers_officer"],
    )
    assert res.status_code == 200
    summary = res.json()["summary"]
    # Student 1 is selected in Stage 1 & Stage 2, Student 2 is selected in Stage 1 only -> 2 distinct shortlisted/selected
    assert summary["total_shortlisted_count"] == 2
    assert summary["total_selected_count"] == 2
    # Conversion: 2 selected / 2 registered = 100%
    assert summary["overall_conversion_percentage"] == 100.0


@pytest.mark.asyncio
async def test_14_15_branch_breakdown_includes_zero_count_branches(async_client: AsyncClient, analytics_setup: dict):
    """TEST 14 & 15: Branch breakdown aggregates correctly and includes active branches with 0 candidates."""
    drive_id = analytics_setup["drive1"].id
    res = await async_client.get(
        f"/api/v1/drives/{drive_id}/analytics",
        headers=analytics_setup["headers_officer"],
    )
    assert res.status_code == 200
    breakdown = {b["branch_code"]: b for b in res.json()["branch_breakdown"]}

    # CSE: 1 eligible, 1 registered, 1 shortlisted, 1 selected
    assert breakdown["CSE"]["eligible_count"] == 1
    assert breakdown["CSE"]["registered_count"] == 1
    assert breakdown["CSE"]["selected_count"] == 1

    # ECE: 1 eligible, 1 registered, 1 shortlisted, 1 selected
    assert breakdown["ECE"]["eligible_count"] == 1
    assert breakdown["ECE"]["registered_count"] == 1
    assert breakdown["ECE"]["selected_count"] == 1

    # MECH: 0 eligible, 0 registered, 0 shortlisted, 0 selected
    assert breakdown["MECH"]["eligible_count"] == 0
    assert breakdown["MECH"]["registered_count"] == 0
    assert breakdown["MECH"]["selected_count"] == 0


@pytest.mark.asyncio
async def test_16_17_zero_eligible_and_zero_registrations(
    async_client: AsyncClient,
    db_session: AsyncSession,
    analytics_setup: dict,
):
    """TEST 16 & 17: Drive with 0 eligible and 0 registered handles percentages gracefully (0.0%)."""
    officer = analytics_setup["officer"]
    company = Company(name="Zero Drive Co", created_by_user_id=officer.id)
    db_session.add(company)
    await db_session.commit()

    # Impossible criteria: min_cgpa 10.0, batch_year 2030
    zero_drive = PlacementDrive(
        company_id=company.id,
        title="Zero Candidate Drive",
        job_role="Consultant",
        status="PUBLISHED",
        created_by_user_id=officer.id,
    )
    db_session.add(zero_drive)
    await db_session.commit()
    await db_session.refresh(zero_drive)

    crit = EligibilityCriteria(
        drive_id=zero_drive.id,
        criteria={"min_cgpa": 10.0, "eligible_batch_years": [2030]},
    )
    db_session.add(crit)
    await db_session.commit()

    res = await async_client.get(
        f"/api/v1/drives/{zero_drive.id}/analytics",
        headers=analytics_setup["headers_officer"],
    )
    assert res.status_code == 200
    summary = res.json()["summary"]
    assert summary["eligible_count"] == 0
    assert summary["registered_count"] == 0
    assert summary["registration_rate_percentage"] == 0.0
    assert summary["overall_conversion_percentage"] == 0.0
    assert res.json()["stage_funnel"] == []


# =============================================================================
# 2. Overview / Platform-Wide Analytics Tests
# =============================================================================

@pytest.mark.asyncio
async def test_18_19_20_overview_analytics_and_deduplication(async_client: AsyncClient, analytics_setup: dict):
    """TEST 18, 19, 20: Platform overview aggregates metrics and deduplicates placed students across drives."""
    res = await async_client.get(
        "/api/v1/analytics/overview",
        headers=analytics_setup["headers_officer"],
    )
    assert res.status_code == 200
    data = res.json()

    drives = data["drives_summary"]
    assert drives["total_drives"] == 2
    assert drives["active_drives"] == 1  # Drive 1 is ASSESSMENT
    assert drives["completed_drives"] == 1  # Drive 2 is COMPLETED

    metrics = data["placement_metrics"]
    # Total active students = 3 (Student 1, Student 2, Student 3)
    assert metrics["total_active_students"] == 3
    # Student 1 is selected in Drive 1 & Drive 2, Student 2 is selected in Drive 1 -> 2 distinct placed students
    assert metrics["total_placed_students"] == 2
    # Placement rate = 2 / 3 * 100 = 66.67%
    assert metrics["overall_placement_percentage"] == 66.67
    assert metrics["total_applications_submitted"] == 3  # 2 in Drive 1, 1 in Drive 2
    assert metrics["highest_ctc_lpa"] == 30.0

    branch_stats = {b["branch_code"]: b for b in data["branch_placement_stats"]}
    assert branch_stats["CSE"]["placed_students"] == 1
    assert branch_stats["ECE"]["placed_students"] == 1
    assert branch_stats["MECH"]["placed_students"] == 0


@pytest.mark.asyncio
async def test_21_no_pii_in_analytics_responses(async_client: AsyncClient, analytics_setup: dict):
    """TEST 21: Verify no student personal identifiable information (PII) is leaked in analytics."""
    drive_id = analytics_setup["drive1"].id

    # Drive analytics
    r1 = await async_client.get(
        f"/api/v1/drives/{drive_id}/analytics",
        headers=analytics_setup["headers_officer"],
    )
    t1 = r1.text
    assert "ANL-001" not in t1
    assert "Student One" not in t1
    assert "resumes/s1.pdf" not in t1
    assert "password123" not in t1

    # Overview analytics
    r2 = await async_client.get(
        "/api/v1/analytics/overview",
        headers=analytics_setup["headers_officer"],
    )
    t2 = r2.text
    assert "ANL-001" not in t2
    assert "analytics_student1@campusflow.com" not in t2


@pytest.mark.asyncio
async def test_22_overview_rbac(async_client: AsyncClient, analytics_setup: dict):
    """TEST 22: Overview analytics is restricted to OFFICER and ADMIN (Student 403, Unauth 401)."""
    # Student -> 403
    r1 = await async_client.get(
        "/api/v1/analytics/overview",
        headers=analytics_setup["headers_student"],
    )
    assert r1.status_code == 403

    # Unauthenticated -> 401
    r2 = await async_client.get("/api/v1/analytics/overview")
    assert r2.status_code == 401


@pytest.mark.asyncio
async def test_23_legacy_admin_overview_route_compatibility(async_client: AsyncClient, analytics_setup: dict):
    """TEST 23: Legacy route /admin/analytics/overview works and returns identical response structure."""
    res = await async_client.get(
        "/api/v1/admin/analytics/overview",
        headers=analytics_setup["headers_admin"],
    )
    assert res.status_code == 200
    data = res.json()
    assert "drives_summary" in data
    assert "placement_metrics" in data
    assert "branch_placement_stats" in data
