"""
Integration Tests for Placement Drive Deletion & Archiving.
Verifies RBAC, soft-delete archiving semantics, student exclusion,
audit logging, and data preservation of registrations and stages.
"""
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.models.branch import Branch
from app.models.company import Company
from app.models.student_profile import StudentProfile
from app.models.audit_log import AuditLog
from app.models.placement_drive import PlacementDrive
from app.models.drive_registration import DriveRegistration


@pytest_asyncio.fixture
async def delete_test_env(async_client: AsyncClient, db_session: AsyncSession) -> dict:
    """Create officer and student users and test company/branch."""
    suffix = uuid4().hex[:6]
    officer = User(
        email=f"del_officer_{suffix}@campusflow.edu",
        password_hash=hash_password("officerPass123!"),
        role="OFFICER",
        full_name="Delete Test Officer",
        is_active=True,
    )
    student = User(
        email=f"del_student_{suffix}@campusflow.edu",
        password_hash=hash_password("studentPass123!"),
        role="STUDENT",
        full_name="Delete Test Student",
        is_active=True,
    )

    db_session.add_all([officer, student])
    await db_session.commit()
    await db_session.refresh(officer)
    await db_session.refresh(student)

    # Ensure CSE branch exists
    stmt = select(Branch).where(Branch.code == "CSE")
    existing_branch = (await db_session.execute(stmt)).scalar_one_or_none()
    if not existing_branch:
        branch = Branch(code="CSE", name="Computer Science and Engineering", is_active=True)
        db_session.add(branch)
        await db_session.commit()

    # Seed profile
    prof = StudentProfile(
        user_id=student.id,
        roll_number=f"DEL-{suffix}",
        branch_code="CSE",
        batch_year=2027,
        cgpa=8.5,
        active_backlogs=0,
        gender="FEMALE",
        resume_gcs_path=f"gs://campusflow/resumes/del_{suffix}.pdf",
    )
    db_session.add(prof)

    # Seed Company
    company = Company(
        name=f"Acme Corp {suffix}",
        website="https://acme.example.com",
        created_by_user_id=officer.id,
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    # Login
    r_off = await async_client.post("/api/v1/auth/login", json={"email": officer.email, "password": "officerPass123!"})
    r_stu = await async_client.post("/api/v1/auth/login", json={"email": student.email, "password": "studentPass123!"})

    assert r_off.status_code == 200
    assert r_stu.status_code == 200

    return {
        "officer_auth": {"Authorization": f"Bearer {r_off.json()['access_token']}"},
        "student_auth": {"Authorization": f"Bearer {r_stu.json()['access_token']}"},
        "officer_id": officer.id,
        "student_id": student.id,
        "company_id": str(company.id),
    }


@pytest.mark.asyncio
async def test_drive_delete_and_archive_lifecycle(
    async_client: AsyncClient,
    delete_test_env: dict,
    db_session: AsyncSession,
):
    off_headers = delete_test_env["officer_auth"]
    stu_headers = delete_test_env["student_auth"]
    company_id = delete_test_env["company_id"]
    student_id = delete_test_env["student_id"]

    # 1. Officer creates drive
    create_payload = {
        "company_id": company_id,
        "title": "Software Engineer 2027 - Deletion Test",
        "job_role": "Software Engineer",
        "description": "Drive to test safe deletion and archiving.",
        "ctc_lpa": 12.0,
        "location": "Bengaluru",
        "registration_deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "eligibility_criteria": {
            "min_cgpa": 7.0,
            "max_active_backlogs": 0,
            "eligible_branches": ["CSE"],
            "eligible_batch_years": [2027],
        },
    }
    r = await async_client.post("/api/v1/drives", json=create_payload, headers=off_headers)
    assert r.status_code == 201
    drive_id = r.json()["id"]

    # 2. Officer publishes and opens registration
    r = await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "PUBLISHED"}, headers=off_headers)
    assert r.status_code == 200
    r = await async_client.post(f"/api/v1/drives/{drive_id}/status", json={"status": "REGISTRATION_OPEN"}, headers=off_headers)
    assert r.status_code == 200

    # 3. Student discovers drive and registers
    r_stu_get = await async_client.get(f"/api/v1/drives/{drive_id}", headers=stu_headers)
    assert r_stu_get.status_code == 200
    r_reg = await async_client.post(f"/api/v1/drives/{drive_id}/register", headers=stu_headers)
    assert r_reg.status_code == 201

    # 4. Student attempts to delete drive -> Must return 403 Forbidden
    r_stu_del = await async_client.delete(f"/api/v1/drives/{drive_id}", headers=stu_headers)
    assert r_stu_del.status_code == 403, "Student must not be allowed to delete a drive"

    # 5. Unauthenticated attempt -> Must return 401 Unauthorized
    r_unauth_del = await async_client.delete(f"/api/v1/drives/{drive_id}")
    assert r_unauth_del.status_code == 401

    # 6. Authorized officer deletes drive -> 200 OK with status ARCHIVED
    r_off_del = await async_client.delete(f"/api/v1/drives/{drive_id}", headers=off_headers)
    assert r_off_del.status_code == 200
    assert r_off_del.json()["status"] == "ARCHIVED"

    # 7. Check Student drive listing -> Drive must NOT appear
    r_stu_list = await async_client.get("/api/v1/drives", headers=stu_headers)
    assert r_stu_list.status_code == 200
    stu_drive_ids = [d["id"] for d in r_stu_list.json()["items"]]
    assert drive_id not in stu_drive_ids, "Archived drive must not appear in student drive list"

    # 8. Check Student direct get -> Must return 404
    r_stu_get_after = await async_client.get(f"/api/v1/drives/{drive_id}", headers=stu_headers)
    assert r_stu_get_after.status_code == 404, "Archived drive must return 404 for student"

    # 9. Check Default Officer drive listing -> Drive must NOT appear by default
    r_off_list = await async_client.get("/api/v1/drives", headers=off_headers)
    assert r_off_list.status_code == 200
    off_drive_ids = [d["id"] for d in r_off_list.json()["items"]]
    assert drive_id not in off_drive_ids, "Archived drive must not appear in normal officer list"

    # 10. Verify Audit Log was recorded
    audit_stmt = select(AuditLog).where(
        AuditLog.entity_id == drive_id,
        AuditLog.action == "DRIVE_DELETED"
    )
    audit_record = (await db_session.execute(audit_stmt)).scalar_one_or_none()
    assert audit_record is not None, "Audit record for DRIVE_DELETED must exist"
    assert audit_record.new_state.get("status") == "ARCHIVED"

    # 11. Verify Data Preservation: Registration record still exists in DB
    reg_stmt = select(DriveRegistration).where(
        DriveRegistration.drive_id == drive_id,
        DriveRegistration.student_user_id == student_id
    )
    reg_record = (await db_session.execute(reg_stmt)).scalar_one_or_none()
    assert reg_record is not None, "Student registration history must NOT be destroyed when drive is deleted"
