"""
Integration tests for Master Student List Import and Multi-Round Stage Qualified List Upload.
"""
import io
import csv
from uuid import uuid4
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.branch import Branch
from app.models.drive_registration import DriveRegistration
from app.models.placement_drive import PlacementDrive
from app.models.placement_stage import PlacementStage
from app.models.stage_assignment import StageAssignment
from app.models.student_profile import StudentProfile
from app.models.user import User


@pytest_asyncio.fixture
async def seeded_test_env(async_client: AsyncClient, db_session: AsyncSession):
    """Seed test branches, officer, and students."""
    # 1. Branch
    branch = Branch(code="CSE", name="Computer Science and Engineering", is_active=True)
    db_session.add(branch)

    # 2. Officer
    officer = User(
        id=uuid4(),
        email="stage_officer_test@campusflow.com",
        password_hash=hash_password("officer123"),
        role="OFFICER",
        full_name="Placement Officer",
        is_active=True,
    )
    # 3. Admin
    admin = User(
        id=uuid4(),
        email="stage_admin_test@campusflow.com",
        password_hash=hash_password("admin123"),
        role="ADMIN",
        full_name="Admin Officer",
        is_active=True,
    )
    # 4. Students
    students = []
    profiles = []
    reg_nos = ["009923001", "009923002", "009923003", "009923004", "009923005"]
    for i, rno in enumerate(reg_nos, start=1):
        u = User(
            id=uuid4(),
            email=f"{rno}@klu.ac.in",
            password_hash=hash_password("student123"),
            role="STUDENT",
            full_name=f"Student {rno}",
            is_active=True,
        )
        p = StudentProfile(
            id=uuid4(),
            user_id=u.id,
            roll_number=rno,
            branch_code="CSE",
            batch_year=2026,
            cgpa=8.5 + (i * 0.1),
            active_backlogs=0,
            resume_gcs_path=f"resumes/{u.id}/resume.pdf",
        )
        students.append(u)
        profiles.append(p)

    db_session.add_all([officer, admin, *students, *profiles])
    await db_session.commit()

    # Login tokens
    r_off = await async_client.post("/api/v1/auth/login", json={"email": officer.email, "password": "officer123"})
    r_adm = await async_client.post("/api/v1/auth/login", json={"email": admin.email, "password": "admin123"})
    r_stu = await async_client.post("/api/v1/auth/login", json={"identifier": reg_nos[0], "password": "student123"})

    officer_token = r_off.json()["access_token"]
    admin_token = r_adm.json()["access_token"]
    student_token = r_stu.json()["access_token"]

    return {
        "officer_headers": {"Authorization": f"Bearer {officer_token}"},
        "admin_headers": {"Authorization": f"Bearer {admin_token}"},
        "student_headers": {"Authorization": f"Bearer {student_token}"},
        "students": students,
        "profiles": profiles,
        "reg_nos": reg_nos,
    }


@pytest.mark.asyncio
async def test_master_student_import_all_rows_without_row_limit(
    async_client: AsyncClient,
    seeded_test_env: dict,
    db_session: AsyncSession,
):
    """
    PART 1: Master student list import must import ALL valid rows without arbitrary limits.
    String registration numbers and leading zeroes must be preserved.
    """
    headers = seeded_test_env["officer_headers"]

    # Generate CSV with 150 student rows (well over 100 rows preview threshold)
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(["Registration Number", "Student Name", "Branch", "Batch Year", "CGPA", "Active Backlogs"])
    for i in range(1, 151):
        writer.writerow([f"000992300{i:03d}", f"Bulk Student {i}", "CSE", "2026", "8.2", "0"])

    file_bytes = csv_buffer.getvalue().encode("utf-8")

    # 1. Preview Import
    preview_res = await async_client.post(
        "/api/v1/admin/students/import/preview",
        files={"file": ("master_students_150.csv", file_bytes, "text/csv")},
        headers=headers,
    )
    assert preview_res.status_code == 200
    data = preview_res.json()
    assert data["total_rows"] == 150
    assert data["valid_count"] == 150
    assert len(data["valid_items"]) == 150
    assert len(data["preview_items"]) == 100  # UI preview table limited to 100

    # 2. Confirm Import of all 150 rows
    confirm_res = await async_client.post(
        "/api/v1/admin/students/import/confirm",
        json={"filename": "master_students_150.csv", "items": data["valid_items"]},
        headers=headers,
    )
    assert confirm_res.status_code == 200
    confirm_data = confirm_res.json()
    assert confirm_data["total_processed"] == 150
    assert confirm_data["created_count"] == 150

    # 3. Verify in Database that string registration numbers with leading zeros are preserved
    stmt = select(StudentProfile).where(StudentProfile.roll_number == "000992300001")
    profile = (await db_session.execute(stmt)).scalar_one_or_none()
    assert profile is not None
    assert profile.roll_number == "000992300001"
    assert profile.branch_code == "CSE"


@pytest.mark.asyncio
async def test_multi_round_qualified_list_upload_workflow(
    async_client: AsyncClient,
    seeded_test_env: dict,
    db_session: AsyncSession,
):
    """
    PART 2 to 14: Multi-round placement drive qualification upload:
    - Drive with multiple rounds (Round 1 Aptitude, Round 2 Tech, Round 3 HR).
    - Students apply to drive.
    - Officer uploads Round 1 qualified list with string registration numbers.
    - Matched students advance to Round 1 QUALIFIED.
    - Non-shortlisted students are NOT auto-rejected.
    - Unknown and not-applied registration numbers are reported.
    - Officer uploads Round 2 qualified list.
    - Student portal reflects confirmed round progression.
    - RBAC restricts upload to Officer/Admin.
    """
    officer_headers = seeded_test_env["officer_headers"]
    student_headers = seeded_test_env["student_headers"]
    students = seeded_test_env["students"]
    reg_nos = seeded_test_env["reg_nos"]

    # 1. Create Company
    r_co = await async_client.post(
        "/api/v1/companies",
        json={"name": "TCS Enterprise", "industry": "IT Services"},
        headers=officer_headers,
    )
    assert r_co.status_code == 201
    company_id = r_co.json()["id"]

    # 2. Create Drive
    r_dr = await async_client.post(
        "/api/v1/drives",
        json={
            "company_id": company_id,
            "title": "TCS Digital 2026",
            "job_role": "AI/ML Engineer",
            "ctc_lpa": 12.0,
            "eligibility_criteria": {
                "min_cgpa": 7.0,
                "max_active_backlogs": 0,
                "eligible_branches": ["CSE"],
                "eligible_batch_years": [2026],
            },
        },
        headers=officer_headers,
    )
    assert r_dr.status_code == 201
    drive_id = r_dr.json()["id"]

    # 3. Create 3 Rounds/Stages for this drive
    # Round 1: Aptitude
    r_s1 = await async_client.post(
        f"/api/v1/drives/{drive_id}/stages",
        json={"name": "Aptitude Assessment", "stage_type": "APTITUDE", "sequence_order": 1},
        headers=officer_headers,
    )
    assert r_s1.status_code == 201
    stage_1_id = r_s1.json()["id"]

    # Round 2: Technical Assessment
    r_s2 = await async_client.post(
        f"/api/v1/drives/{drive_id}/stages",
        json={"name": "Technical Assessment", "stage_type": "TECHNICAL", "sequence_order": 2},
        headers=officer_headers,
    )
    assert r_s2.status_code == 201
    stage_2_id = r_s2.json()["id"]

    # Round 3: HR Interview
    r_s3 = await async_client.post(
        f"/api/v1/drives/{drive_id}/stages",
        json={"name": "HR Interview", "stage_type": "HR", "sequence_order": 3},
        headers=officer_headers,
    )
    assert r_s3.status_code == 201
    stage_3_id = r_s3.json()["id"]

    # 4. Open Registration & Register 4 students (reg_nos[0], reg_nos[1], reg_nos[2], reg_nos[3])
    # Note: reg_nos[4] ("009923005") will intentionally NOT apply to test "Not Applied" category
    await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "PUBLISHED"}, headers=officer_headers)
    await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "REGISTRATION_OPEN"}, headers=officer_headers)

    for i in range(4):
        reg = DriveRegistration(
            id=uuid4(),
            drive_id=drive_id,
            student_user_id=students[i].id,
            resume_gcs_path_at_registration=f"resumes/{students[i].id}/resume.pdf",
            status="REGISTERED",
        )
        db_session.add(reg)
    await db_session.commit()

    # 5. Round 1 Qualified Upload: Company sends list with:
    # - reg_nos[0] ("009923001") -> Applied (Matched)
    # - reg_nos[1] ("009923002") -> Applied (Matched)
    # - reg_nos[2] ("009923003") -> Applied (Matched)
    # - reg_nos[4] ("009923005") -> Master student who DID NOT APPLY (Not Applied)
    # - "009999999" -> Does not exist in master list (Unknown Reg No)
    # - reg_nos[0] ("009923001") -> Duplicate row in file
    csv_r1 = io.StringIO()
    w1 = csv.writer(csv_r1)
    w1.writerow(["Registration Number", "Student Name"])
    w1.writerow([reg_nos[0], "Student 001"])
    w1.writerow([reg_nos[1], "Student 002"])
    w1.writerow([reg_nos[2], "Student 003"])
    w1.writerow([reg_nos[4], "Student 005 - Did not apply"])
    w1.writerow(["009999999", "Ghost Student"])
    w1.writerow([reg_nos[0], "Student 001 Duplicate"])

    r1_bytes = csv_r1.getvalue().encode("utf-8")

    # Preview Round 1
    r_preview1 = await async_client.post(
        f"/api/v1/drives/{drive_id}/stages/{stage_1_id}/qualified/preview",
        files={"file": ("round_1_qualified.csv", r1_bytes, "text/csv")},
        headers=officer_headers,
    )
    assert r_preview1.status_code == 200
    prev1 = r_preview1.json()
    assert prev1["total_rows"] == 6
    assert prev1["matched_count"] == 3
    assert prev1["not_applied_count"] == 1
    assert prev1["unknown_count"] == 1
    assert prev1["duplicate_count"] == 1
    assert len(prev1["valid_student_ids"]) == 3

    # Confirm Round 1
    r_conf1 = await async_client.post(
        f"/api/v1/drives/{drive_id}/stages/{stage_1_id}/qualified/confirm",
        json={"filename": "round_1_qualified.csv", "student_ids": prev1["valid_student_ids"]},
        headers=officer_headers,
    )
    assert r_conf1.status_code == 200
    assert r_conf1.json()["newly_assigned_count"] == 3

    # Verify student 4 (reg_nos[3]) was NOT short-listed but is NOT auto-rejected (remains REGISTERED)
    stmt_s4 = select(DriveRegistration).where(
        DriveRegistration.drive_id == drive_id,
        DriveRegistration.student_user_id == students[3].id,
    )
    reg_s4 = (await db_session.execute(stmt_s4)).scalar_one()
    assert reg_s4.status == "REGISTERED"

    # Verify AuditLog created
    stmt_audit = select(AuditLog).where(
        AuditLog.action == "STAGE_QUALIFIED_IMPORT_CONFIRMED",
        AuditLog.entity_id == stage_1_id,
    )
    audit = (await db_session.execute(stmt_audit)).scalar_one_or_none()
    assert audit is not None
    assert audit.new_state["stage_name"] == "Aptitude Assessment"

    # 6. Round 2 Qualified Upload: Company sends 2 students (reg_nos[0], reg_nos[1])
    csv_r2 = io.StringIO()
    w2 = csv.writer(csv_r2)
    w2.writerow(["Roll Number", "Candidate Name"])
    w2.writerow([reg_nos[0], "Student 001"])
    w2.writerow([reg_nos[1], "Student 002"])
    r2_bytes = csv_r2.getvalue().encode("utf-8")

    r_preview2 = await async_client.post(
        f"/api/v1/drives/{drive_id}/stages/{stage_2_id}/qualified/preview",
        files={"file": ("round_2_tech_qualified.csv", r2_bytes, "text/csv")},
        headers=officer_headers,
    )
    assert r_preview2.status_code == 200
    prev2 = r_preview2.json()
    assert prev2["matched_count"] == 2

    # Confirm Round 2
    r_conf2 = await async_client.post(
        f"/api/v1/drives/{drive_id}/stages/{stage_2_id}/qualified/confirm",
        json={"filename": "round_2_tech_qualified.csv", "student_ids": prev2["valid_student_ids"]},
        headers=officer_headers,
    )
    assert r_conf2.status_code == 200
    assert r_conf2.json()["newly_assigned_count"] == 2

    # 7. Student Portal Reflection:
    # Student 1 (reg_nos[0]) views drive stages:
    r_student_stages = await async_client.get(
        f"/api/v1/drives/{drive_id}/stages",
        headers=student_headers,
    )
    assert r_student_stages.status_code == 200
    stages_data = r_student_stages.json()
    assert len(stages_data) == 2  # Stage 1 and Stage 2 are published
    # Stage 1 has my_status = "SHORTLISTED"
    assert stages_data[0]["my_status"] == "SHORTLISTED"
    # Stage 2 has my_status = "SHORTLISTED"
    assert stages_data[1]["my_status"] == "SHORTLISTED"

    # 8. Security / RBAC:
    # Student cannot upload or preview round qualified lists
    r_stu_upload = await async_client.post(
        f"/api/v1/drives/{drive_id}/stages/{stage_1_id}/qualified/preview",
        files={"file": ("hack.csv", r1_bytes, "text/csv")},
        headers=student_headers,
    )
    assert r_stu_upload.status_code == 403

    r_stu_confirm = await async_client.post(
        f"/api/v1/drives/{drive_id}/stages/{stage_1_id}/qualified/confirm",
        json={"filename": "hack.csv", "student_ids": [str(students[0].id)]},
        headers=student_headers,
    )
    assert r_stu_confirm.status_code == 403

    # Officer can view qualified students list endpoint
    r_qualified_students = await async_client.get(
        f"/api/v1/drives/{drive_id}/stages/{stage_1_id}/qualified/students",
        headers=officer_headers,
    )
    assert r_qualified_students.status_code == 200
    q_list = r_qualified_students.json()
    assert len(q_list) == 3
    assert q_list[0]["roll_number"] in [reg_nos[0], reg_nos[1], reg_nos[2]]
