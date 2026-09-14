"""
Integration & Unit tests for Master Student List Import, String Reg No Preservation,
RBAC Security, and Master-based Student Registration Workflow.
"""
from __future__ import annotations

import io
from uuid import uuid4
import openpyxl
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.branch import Branch
from app.models.student_profile import StudentProfile
from app.models.user import User


def create_sample_excel_bytes(rows: list[list[any]], headers: list[str]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "MasterList"
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest_asyncio.fixture
async def auth_headers(async_client: AsyncClient, db_session: AsyncSession) -> dict[str, dict[str, str]]:
    """Returns auth headers for both a STUDENT and an OFFICER."""
    student = User(
        email="master_student_test@campusflow.edu",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Master Student RBAC",
        is_active=True,
    )
    officer = User(
        email="master_officer_test@campusflow.edu",
        password_hash=hash_password("password123"),
        role="OFFICER",
        full_name="Master Officer RBAC",
        is_active=True,
    )
    admin = User(
        email="master_admin_test@campusflow.edu",
        password_hash=hash_password("password123"),
        role="ADMIN",
        full_name="Master Admin RBAC",
        is_active=True,
    )
    db_session.add_all([student, officer, admin])
    await db_session.commit()

    r_student = await async_client.post(
        "/api/v1/auth/login", json={"email": student.email, "password": "password123"}
    )
    r_officer = await async_client.post(
        "/api/v1/auth/login", json={"email": officer.email, "password": "password123"}
    )
    r_admin = await async_client.post(
        "/api/v1/auth/login", json={"email": admin.email, "password": "password123"}
    )

    return {
        "student": {"Authorization": f"Bearer {r_student.json()['access_token']}"},
        "officer": {"Authorization": f"Bearer {r_officer.json()['access_token']}"},
        "admin": {"Authorization": f"Bearer {r_admin.json()['access_token']}"},
    }


@pytest.fixture
async def sample_branches(db_session: AsyncSession):
    branches = [
        Branch(code="CSE", name="Computer Science and Engineering", is_active=True),
        Branch(code="ECE", name="Electronics and Communication Engineering", is_active=True),
        Branch(code="IT", name="Information Technology", is_active=True),
    ]
    for b in branches:
        db_session.add(b)
    await db_session.commit()


@pytest.mark.asyncio
async def test_preview_valid_excel_and_column_detection(
    async_client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
    sample_branches,
):
    """Verify Excel preview correctly normalizes headers and validates rows."""
    headers = ["Registration Number", "Student Name", "Department", "Graduation Year", "CGPA", "Active Backlogs"]
    rows = [
        ["009923004101", "Student Alpha", "CSE", 2026, 8.75, 0],
        ["99230041249", "Student Beta", "ECE", 2026, 9.10, 0],
        ["99230041035", "Student Gamma", "IT", 2026, 7.80, 1],
    ]
    excel_bytes = create_sample_excel_bytes(rows, headers)

    resp = await async_client.post(
        "/api/v1/admin/students/import/preview",
        files={"file": ("final_year_students.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers["officer"],
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total_rows"] == 3
    assert data["valid_count"] == 3
    assert data["duplicate_in_file_count"] == 0
    assert data["missing_reg_no_count"] == 0
    assert data["can_import"] is True
    assert data["detected_mappings"]["roll_number"] == "Registration Number"
    assert data["detected_mappings"]["full_name"] == "Student Name"
    assert data["detected_mappings"]["branch_code"] == "Department"

    # Verify string preservation with leading zero
    items = data["preview_items"]
    assert items[0]["roll_number"] == "009923004101"
    assert items[1]["roll_number"] == "99230041249"


@pytest.mark.asyncio
async def test_preview_duplicate_and_missing_reg_nos(
    async_client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
):
    """Verify preview flags duplicates and missing registration numbers."""
    headers = ["Reg No", "Full Name", "Branch"]
    rows = [
        ["99230041001", "Alice", "CSE"],
        ["99230041001", "Alice Duplicate", "CSE"],  # Duplicate in file
        ["", "Bob No Reg", "ECE"],                   # Missing registration number
        ["99230041003", "Charlie", "IT"],
    ]
    excel_bytes = create_sample_excel_bytes(rows, headers)

    resp = await async_client.post(
        "/api/v1/admin/students/import/preview",
        files={"file": ("students.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers["officer"],
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_rows"] == 4
    assert data["valid_count"] == 2
    assert data["duplicate_in_file_count"] == 1
    assert data["missing_reg_no_count"] == 1
    assert data["invalid_count"] == 2


@pytest.mark.asyncio
async def test_confirm_student_import_creates_records_and_audit(
    async_client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
    db_session: AsyncSession,
):
    """Verify confirming import creates inactive User and StudentProfile records with audit log."""
    confirm_payload = {
        "filename": "final_year_batch_2026.xlsx",
        "items": [
            {
                "roll_number": "009923004101",
                "full_name": "Test Master Student One",
                "branch_code": "CSE",
                "batch_year": 2026,
                "cgpa": 8.5,
                "active_backlogs": 0,
            },
            {
                "roll_number": "992300410202",
                "full_name": "Test Master Student Two",
                "branch_code": "ECE",
                "batch_year": 2026,
                "cgpa": 7.9,
                "active_backlogs": 1,
            },
        ],
    }

    resp = await async_client.post(
        "/api/v1/admin/students/import/confirm",
        json=confirm_payload,
        headers=auth_headers["officer"],
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["created_count"] == 2
    assert data["total_processed"] == 2

    # Verify student 1 in DB
    stmt1 = select(StudentProfile).where(StudentProfile.roll_number == "009923004101")
    prof1 = (await db_session.execute(stmt1)).scalar_one_or_none()
    assert prof1 is not None
    assert prof1.roll_number == "009923004101"
    assert prof1.batch_year == 2026
    assert prof1.branch_code == "CSE"

    # Verify associated user is inactive (pre-provisioned)
    stmt_user1 = select(User).where(User.id == prof1.user_id)
    user1 = (await db_session.execute(stmt_user1)).scalar_one_or_none()
    assert user1 is not None
    assert user1.is_active is False
    assert user1.email == "009923004101@klu.ac.in"
    assert user1.role == "STUDENT"

    # Verify audit log recorded
    stmt_audit = select(AuditLog).where(AuditLog.action == "STUDENT_MASTER_IMPORT_CONFIRMED")
    audit = (await db_session.execute(stmt_audit)).scalars().first()
    assert audit is not None


@pytest.mark.asyncio
async def test_idempotent_reimport_updates_existing_records(
    async_client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
    db_session: AsyncSession,
):
    """Verify re-importing updates academic fields and does NOT create duplicate users."""
    # 1. Initial Import
    initial_payload = {
        "filename": "batch1.xlsx",
        "items": [
            {
                "roll_number": "99230041999",
                "full_name": "Idempotent Student",
                "branch_code": "CSE",
                "batch_year": 2026,
                "cgpa": 7.0,
                "active_backlogs": 0,
            }
        ],
    }
    r1 = await async_client.post("/api/v1/admin/students/import/confirm", json=initial_payload, headers=auth_headers["officer"])
    assert r1.status_code == 200
    assert r1.json()["created_count"] == 1

    # 2. Re-import with updated CGPA and Backlogs
    update_payload = {
        "filename": "batch1_updated.xlsx",
        "items": [
            {
                "roll_number": "99230041999",
                "full_name": "Idempotent Student Updated",
                "branch_code": "CSE",
                "batch_year": 2026,
                "cgpa": 9.25,
                "active_backlogs": 0,
            }
        ],
    }
    r2 = await async_client.post("/api/v1/admin/students/import/confirm", json=update_payload, headers=auth_headers["officer"])
    assert r2.status_code == 200
    assert r2.json()["updated_count"] == 1
    assert r2.json()["created_count"] == 0

    # Verify no duplicate user created
    stmt_users = select(User).where(User.email == "99230041999@klu.ac.in")
    users = (await db_session.execute(stmt_users)).scalars().all()
    assert len(users) == 1

    # Verify profile updated
    stmt_prof = select(StudentProfile).where(StudentProfile.roll_number == "99230041999")
    prof = (await db_session.execute(stmt_prof)).scalar_one_or_none()
    assert float(prof.cgpa) == 9.25


@pytest.mark.asyncio
async def test_master_student_self_registration_and_dual_login(
    async_client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
    db_session: AsyncSession,
):
    """End-to-end test: Import master student -> student registers at /register -> logs in via reg no and email."""
    # 1. Officer imports student into master list
    reg_no = "99230045555"
    import_payload = {
        "filename": "master.xlsx",
        "items": [
            {
                "roll_number": reg_no,
                "full_name": "Karthik Master Student",
                "branch_code": "CSE",
                "batch_year": 2026,
                "cgpa": 8.8,
                "active_backlogs": 0,
            }
        ],
    }
    r_imp = await async_client.post("/api/v1/admin/students/import/confirm", json=import_payload, headers=auth_headers["officer"])
    assert r_imp.status_code == 200

    # 2. Student self-registers at /register
    reg_payload = {
        "registration_number": reg_no,
        "password": "MySecretPassword@2026",
    }
    r_reg = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert r_reg.status_code == 200, r_reg.text
    assert r_reg.json()["email"] == f"{reg_no}@klu.ac.in"

    # 3. Login using Registration Number
    r_login_reg = await async_client.post(
        "/api/v1/auth/login",
        json={"email": reg_no, "password": "MySecretPassword@2026"},
    )
    assert r_login_reg.status_code == 200, r_login_reg.text
    assert r_login_reg.json()["user"]["email"] == f"{reg_no}@klu.ac.in"

    # 4. Login using University Email
    r_login_email = await async_client.post(
        "/api/v1/auth/login",
        json={"email": f"{reg_no}@klu.ac.in", "password": "MySecretPassword@2026"},
    )
    assert r_login_email.status_code == 200, r_login_email.text

    # 5. Re-registration rejected with 409
    r_dup_reg = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert r_dup_reg.status_code == 409
    assert "already registered" in r_dup_reg.json()["detail"].lower()


@pytest.mark.asyncio
async def test_unknown_registration_number_rejected_with_clear_message(
    async_client: AsyncClient,
):
    """Verify non-existent registration number is rejected with exact instruction."""
    r_unknown = await async_client.post(
        "/api/v1/auth/register",
        json={"registration_number": "UNKNOWN999999", "password": "Password@123"},
    )
    assert r_unknown.status_code == 404
    assert r_unknown.json()["detail"] == "Registration number not found. Please contact your placement office."


@pytest.mark.asyncio
async def test_student_role_forbidden_from_import_endpoints(
    async_client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
):
    """Verify student role is denied (403 Forbidden) from preview and confirm endpoints."""
    headers = ["Registration Number", "Student Name"]
    rows = [["99230041001", "Hacker"]]
    excel_bytes = create_sample_excel_bytes(rows, headers)

    # Preview forbidden for student
    r_prev = await async_client.post(
        "/api/v1/admin/students/import/preview",
        files={"file": ("test.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers["student"],
    )
    assert r_prev.status_code == 403

    # Confirm forbidden for student
    r_conf = await async_client.post(
        "/api/v1/admin/students/import/confirm",
        json={"filename": "test.xlsx", "items": [{"roll_number": "99230041001", "branch_code": "CSE", "batch_year": 2026, "cgpa": 8.0, "active_backlogs": 0}]},
        headers=auth_headers["student"],
    )
    assert r_conf.status_code == 403
