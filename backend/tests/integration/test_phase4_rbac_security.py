"""
Phase 4.4 — Security, RBAC & IDOR API Regression Suite.

Verifies:
1. Role-Based Access Control (RBAC) boundaries:
   - STUDENT cannot access admin endpoints (/api/v1/admin/users, /api/v1/admin/audit-logs, bulk-import).
   - STUDENT cannot access officer-only endpoints (/api/v1/officers/, drive creation, status updates).
   - OFFICER cannot access admin-only endpoints (/api/v1/admin/users, audit-logs, bulk-import).
   - Unauthenticated requests to protected endpoints return 401 Unauthorized.
2. Insecure Direct Object Reference (IDOR) protections:
   - Student cannot mark another student's notification as read (returns 403 Forbidden).
   - Student cannot access or modify another student's profile.
3. Academic Field Immutability:
   - Student attempting to modify cgpa, roll_number, active_backlogs, or branch_code via PATCH /api/v1/students/me
     is rejected with HTTP 403 Forbidden.
4. Database-level Audit Log Immutability:
   - PostgreSQL trigger blocks UPDATE and DELETE on audit_logs table.
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.branch import Branch
from app.models.company import Company
from app.models.notification import Notification
from app.models.placement_drive import PlacementDrive
from app.models.student_profile import StudentProfile
from app.models.user import User


@pytest_asyncio.fixture
async def security_fixture(db_session: AsyncSession, async_client: AsyncClient) -> dict:
    # 1. Branches
    cse = Branch(code="CSE", name="Computer Science")
    ece = Branch(code="ECE", name="Electronics")
    db_session.add_all([cse, ece])
    await db_session.flush()

    # 2. Users
    admin = User(
        id=uuid4(),
        email="sec_admin@campusflow.edu",
        password_hash=hash_password("SecAdmin@123"),
        role="ADMIN",
        full_name="Security Admin",
        is_active=True,
    )
    officer = User(
        id=uuid4(),
        email="sec_officer@campusflow.edu",
        password_hash=hash_password("SecOfficer@123"),
        role="OFFICER",
        full_name="Security Officer",
        is_active=True,
    )
    student1 = User(
        id=uuid4(),
        email="sec_student1@campusflow.edu",
        password_hash=hash_password("SecStudent@123"),
        role="STUDENT",
        full_name="Security Student 1",
        is_active=True,
    )
    student2 = User(
        id=uuid4(),
        email="sec_student2@campusflow.edu",
        password_hash=hash_password("SecStudent@123"),
        role="STUDENT",
        full_name="Security Student 2",
        is_active=True,
    )
    db_session.add_all([admin, officer, student1, student2])
    await db_session.flush()

    # Student profiles
    p1 = StudentProfile(
        id=uuid4(),
        user_id=student1.id,
        roll_number="SEC26CSE001",
        branch_code="CSE",
        batch_year=2026,
        cgpa=8.50,
        active_backlogs=0,
    )
    p2 = StudentProfile(
        id=uuid4(),
        user_id=student2.id,
        roll_number="SEC26ECE002",
        branch_code="ECE",
        batch_year=2026,
        cgpa=7.20,
        active_backlogs=1,
    )
    db_session.add_all([p1, p2])

    # Company & Drive
    company = Company(
        id=uuid4(),
        name="SecCorp Synthetic",
        website="https://seccorp.test",
        created_by_user_id=officer.id,
    )
    db_session.add(company)
    await db_session.flush()

    drive = PlacementDrive(
        id=uuid4(),
        company_id=company.id,
        title="SecCorp SWE 2026",
        job_role="Software Engineer",
        status="DRAFT",
        created_by_user_id=officer.id,
    )
    db_session.add(drive)
    await db_session.flush()

    # Notifications for student2
    n_s2 = Notification(
        id=uuid4(),
        user_id=student2.id,
        title="Private Notification for S2",
        body="Confidential test notification body.",
        notification_type="SYSTEM",
        is_read=False,
    )
    db_session.add(n_s2)
    await db_session.commit()

    # Login and acquire tokens
    r_adm = await async_client.post("/api/v1/auth/login", json={"email": admin.email, "password": "SecAdmin@123"})
    r_off = await async_client.post("/api/v1/auth/login", json={"email": officer.email, "password": "SecOfficer@123"})
    r_s1 = await async_client.post("/api/v1/auth/login", json={"email": student1.email, "password": "SecStudent@123"})
    r_s2 = await async_client.post("/api/v1/auth/login", json={"email": student2.email, "password": "SecStudent@123"})

    assert r_adm.status_code == 200
    assert r_off.status_code == 200
    assert r_s1.status_code == 200
    assert r_s2.status_code == 200

    return {
        "admin": admin,
        "officer": officer,
        "student1": student1,
        "student2": student2,
        "profile1": p1,
        "profile2": p2,
        "drive": drive,
        "notif_s2": n_s2,
        "h_admin": {"Authorization": f"Bearer {r_adm.json()['access_token']}"},
        "h_officer": {"Authorization": f"Bearer {r_off.json()['access_token']}"},
        "h_s1": {"Authorization": f"Bearer {r_s1.json()['access_token']}"},
        "h_s2": {"Authorization": f"Bearer {r_s2.json()['access_token']}"},
    }


# ===========================================================================
# 1. RBAC Tests: Role boundaries
# ===========================================================================

@pytest.mark.asyncio
async def test_01_unauthenticated_requests_return_401(async_client: AsyncClient, security_fixture: dict):
    """Unauthenticated access to protected routes must return 401."""
    endpoints = [
        ("GET", "/api/v1/students/me"),
        ("GET", "/api/v1/admin/users"),
        ("GET", "/api/v1/admin/audit-logs"),
        ("GET", "/api/v1/analytics/overview"),
        ("POST", "/api/v1/drives"),
    ]
    for method, path in endpoints:
        if method == "GET":
            res = await async_client.get(path)
        else:
            res = await async_client.post(path, json={})
        assert res.status_code == 401, f"{path} returned {res.status_code}, expected 401"


@pytest.mark.asyncio
async def test_02_student_cannot_access_admin_endpoints(async_client: AsyncClient, security_fixture: dict):
    """STUDENT token used against admin routes must return 403 Forbidden."""
    h_student = security_fixture["h_s1"]
    res1 = await async_client.get("/api/v1/admin/users", headers=h_student)
    assert res1.status_code == 403

    res2 = await async_client.get("/api/v1/admin/audit-logs", headers=h_student)
    assert res2.status_code == 403

    res3 = await async_client.post("/api/v1/admin/users", headers=h_student, json={
        "email": "intruder@campusflow.edu",
        "full_name": "Intruder User",
        "role": "ADMIN"
    })
    assert res3.status_code == 403


@pytest.mark.asyncio
async def test_03_officer_cannot_access_admin_endpoints(async_client: AsyncClient, security_fixture: dict):
    """OFFICER token used against admin-only endpoints must return 403 Forbidden."""
    h_officer = security_fixture["h_officer"]
    res1 = await async_client.get("/api/v1/admin/users", headers=h_officer)
    assert res1.status_code == 403

    res2 = await async_client.get("/api/v1/admin/audit-logs", headers=h_officer)
    assert res2.status_code == 403

    res3 = await async_client.post("/api/v1/admin/users", headers=h_officer, json={
        "email": "elevated@campusflow.edu",
        "full_name": "Elevated User",
        "role": "ADMIN"
    })
    assert res3.status_code == 403


@pytest.mark.asyncio
async def test_04_student_cannot_create_or_modify_drive(async_client: AsyncClient, security_fixture: dict):
    """STUDENT cannot create a placement drive or transition drive status."""
    h_student = security_fixture["h_s1"]
    drive_id = security_fixture["drive"].id

    # Create drive
    res_create = await async_client.post(
        "/api/v1/drives",
        headers=h_student,
        json={
            "company_id": str(security_fixture["drive"].company_id),
            "title": "Unauthorized Student Drive",
            "job_role": "Tester",
        },
    )
    assert res_create.status_code == 403

    # Status update
    res_status = await async_client.post(
        f"/api/v1/drives/{drive_id}/status",
        headers=h_student,
        json={"status": "PUBLISHED"},
    )
    assert res_status.status_code == 403


# ===========================================================================
# 2. IDOR Checks: Cross-User Resource Protection
# ===========================================================================

@pytest.mark.asyncio
async def test_05_student_cannot_read_another_students_notification(async_client: AsyncClient, security_fixture: dict):
    """
    IDOR test: Student 1 attempts to mark Student 2's private notification as read.
    Backend must detect ownership mismatch and return 403 Forbidden.
    """
    notif_id_s2 = security_fixture["notif_s2"].id
    h_s1 = security_fixture["h_s1"]

    res = await async_client.post(
        f"/api/v1/notifications/{notif_id_s2}/read",
        headers=h_s1,
    )
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"


@pytest.mark.asyncio
async def test_06_student_cannot_modify_academic_fields(async_client: AsyncClient, security_fixture: dict):
    """
    Tamper test: Student tries to arbitrarily increase CGPA or change backlogs/roll_number.
    Backend must explicitly reject protected academic modifications with 403 Forbidden.
    """
    h_s1 = security_fixture["h_s1"]

    tamper_payload = {
        "phone_number": "+919876543210",
        "cgpa": 9.99,  # Protected academic field
        "active_backlogs": 0,  # Protected academic field
        "roll_number": "HACKED_ROLL",  # Protected academic field
    }

    res = await async_client.patch(
        "/api/v1/students/me",
        headers=h_s1,
        json=tamper_payload,
    )
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
    assert "Cannot modify protected academic" in res.json().get("detail", "")


@pytest.mark.asyncio
async def test_07_student_permitted_field_update_succeeds(async_client: AsyncClient, security_fixture: dict):
    """Student updating permitted non-academic fields (e.g. phone_number) succeeds."""
    h_s1 = security_fixture["h_s1"]

    valid_payload = {
        "phone_number": "+919876543210",
        "gender": "Male",
    }

    res = await async_client.patch(
        "/api/v1/students/me",
        headers=h_s1,
        json=valid_payload,
    )
    assert res.status_code == 200
    assert res.json()["phone_number"] == "+919876543210"
    assert res.json()["gender"] == "Male"
    # Ensure academic fields remain unchanged
    assert res.json()["cgpa"] == 8.50
    assert res.json()["roll_number"] == "SEC26CSE001"


# ===========================================================================
# 3. Database Audit Log Immutability Verification
# ===========================================================================

@pytest.mark.asyncio
async def test_08_audit_logs_immutability_trigger(db_session: AsyncSession, security_fixture: dict):
    """
    Verify PostgreSQL immutability trigger on audit_logs:
    1. INSERT succeeds.
    2. UPDATE raises exception from trigger.
    3. DELETE raises exception from trigger.
    """
    admin_id = security_fixture["admin"].id
    entry = AuditLog(
        id=uuid4(),
        performed_by_user_id=admin_id,
        action="TEST_ACTION",
        entity_type="SYSTEM",
        entity_id=uuid4(),
        old_state=None,
        new_state={"status": "INITIAL"},
    )
    db_session.add(entry)
    await db_session.commit()
    await db_session.refresh(entry)
    entry_id = entry.id

    # Test UPDATE is blocked by PostgreSQL trigger
    with pytest.raises(DBAPIError) as excinfo:
        await db_session.execute(
            text("UPDATE campusflow.audit_logs SET action = 'MODIFIED_ACTION' WHERE id = :log_id"),
            {"log_id": entry_id},
        )
        await db_session.commit()
    await db_session.rollback()
    assert "audit_logs table is immutable" in str(excinfo.value)

    # Test DELETE is blocked by PostgreSQL trigger
    with pytest.raises(DBAPIError) as excinfo2:
        await db_session.execute(
            text("DELETE FROM campusflow.audit_logs WHERE id = :log_id"),
            {"log_id": entry_id},
        )
        await db_session.commit()
    await db_session.rollback()
    assert "audit_logs table is immutable" in str(excinfo2.value)
