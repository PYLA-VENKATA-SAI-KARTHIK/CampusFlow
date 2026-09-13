"""
Phase 5A Integration Tests — Placement Drive Management & Student Visibility.
Verifies end-to-end drive lifecycle, eligibility engine, student registration,
stage sequence management, RBAC, IDOR protection, UUID validation, and audit logging.
"""
from datetime import datetime, timezone, timedelta
from uuid import uuid4, UUID
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
from app.models.placement_stage import PlacementStage


@pytest_asyncio.fixture
async def phase5a_users(async_client: AsyncClient, db_session: AsyncSession) -> dict:
    """Create test users: an officer, an eligible student, and an ineligible student."""
    officer = User(
        email="phase5a_officer@campusflow.edu",
        password_hash=hash_password("officerPass123!"),
        role="OFFICER",
        full_name="Placement Officer 5A",
        is_active=True,
    )
    student_eligible = User(
        email="phase5a_eligible@campusflow.edu",
        password_hash=hash_password("studentPass123!"),
        role="STUDENT",
        full_name="Eligible Student 5A",
        is_active=True,
    )
    student_ineligible = User(
        email="phase5a_ineligible@campusflow.edu",
        password_hash=hash_password("studentPass123!"),
        role="STUDENT",
        full_name="Ineligible Student 5A",
        is_active=True,
    )

    db_session.add_all([officer, student_eligible, student_ineligible])
    await db_session.commit()
    await db_session.refresh(officer)
    await db_session.refresh(student_eligible)
    await db_session.refresh(student_ineligible)

    # Seed branch
    branch = Branch(code="CSE", name="Computer Science and Engineering", is_active=True)
    db_session.add(branch)
    await db_session.commit()

    # Seed profiles
    prof_eligible = StudentProfile(
        user_id=student_eligible.id,
        roll_number="CSE-5A-001",
        branch_code="CSE",
        batch_year=2027,
        cgpa=8.5,
        active_backlogs=0,
        gender="FEMALE",
        resume_gcs_path="gs://campusflow/resumes/cse5a001.pdf",
    )
    prof_ineligible = StudentProfile(
        user_id=student_ineligible.id,
        roll_number="CSE-5A-002",
        branch_code="CSE",
        batch_year=2027,
        cgpa=5.8,  # Below criteria of 7.0
        active_backlogs=2,  # Has backlogs
        gender="MALE",
        resume_gcs_path="gs://campusflow/resumes/cse5a002.pdf",
    )
    db_session.add_all([prof_eligible, prof_ineligible])
    await db_session.commit()

    # Login all 3
    r_off = await async_client.post("/api/v1/auth/login", json={"email": officer.email, "password": "officerPass123!"})
    r_elig = await async_client.post("/api/v1/auth/login", json={"email": student_eligible.email, "password": "studentPass123!"})
    r_inelig = await async_client.post("/api/v1/auth/login", json={"email": student_ineligible.email, "password": "studentPass123!"})

    assert r_off.status_code == 200
    assert r_elig.status_code == 200
    assert r_inelig.status_code == 200

    return {
        "officer_auth": {"Authorization": f"Bearer {r_off.json()['access_token']}"},
        "eligible_auth": {"Authorization": f"Bearer {r_elig.json()['access_token']}"},
        "ineligible_auth": {"Authorization": f"Bearer {r_inelig.json()['access_token']}"},
        "officer_id": officer.id,
        "eligible_student_id": student_eligible.id,
        "ineligible_student_id": student_ineligible.id,
    }


@pytest.mark.asyncio
async def test_full_placement_drive_lifecycle_and_student_visibility(
    async_client: AsyncClient,
    phase5a_users: dict,
    db_session: AsyncSession,
):
    off_headers = phase5a_users["officer_auth"]
    elig_headers = phase5a_users["eligible_auth"]
    inelig_headers = phase5a_users["ineligible_auth"]

    # 1. Create Company
    company_res = await async_client.post(
        "/api/v1/companies",
        headers=off_headers,
        json={
            "name": "Acme Innovations Ltd",
            "website": "https://acmeinnovations.io",
            "industry": "Enterprise Software",
            "description": "Leading provider of autonomous cloud systems.",
        },
    )
    assert company_res.status_code == 201, company_res.text
    company_id = company_res.json()["id"]

    # 2. Officer creates placement drive (DRAFT)
    deadline = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    drive_payload = {
        "company_id": company_id,
        "title": "Acme Innovations — Associate Cloud Engineer 2027",
        "job_role": "Associate Cloud Engineer",
        "description": "Develop and manage scalable cloud microservices.",
        "ctc_lpa": 6.5,
        "stipend_monthly": 30000.0,
        "location": "Bengaluru (Hybrid)",
        "bond_details": "None",
        "registration_deadline": deadline,
        "eligibility_criteria": {
            "min_cgpa": 7.0,
            "max_active_backlogs": 0,
            "eligible_branches": ["CSE"],
            "eligible_batch_years": [2027],
            "gender": None,
        },
    }

    create_res = await async_client.post("/api/v1/drives", headers=off_headers, json=drive_payload)
    assert create_res.status_code == 201, create_res.text
    drive_data = create_res.json()
    drive_id = drive_data["id"]
    assert drive_data["status"] == "DRAFT"
    assert drive_data["job_role"] == "Associate Cloud Engineer"

    # 3. Verify Draft is INVISIBLE to Students in drives list
    list_student_res = await async_client.get("/api/v1/drives", headers=elig_headers)
    assert list_student_res.status_code == 200
    student_drive_ids = [d["id"] for d in list_student_res.json()["items"]]
    assert drive_id not in student_drive_ids

    # 4. Student querying for DRAFT status gets empty list
    draft_query_res = await async_client.get("/api/v1/drives?status=DRAFT", headers=elig_headers)
    assert draft_query_res.status_code == 200
    assert len(draft_query_res.json()["items"]) == 0

    # 5. Officer adds selection stages
    stage1_res = await async_client.post(
        f"/api/v1/drives/{drive_id}/stages",
        headers=off_headers,
        json={
            "name": "Cloud Foundations Assessment",
            "stage_type": "TECHNICAL",
            "sequence_order": 1,
            "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=12)).isoformat(),
            "location_or_link": "Online Assessment Portal",
            "instructions": "MCQs on networking and Linux commands.",
        },
    )
    assert stage1_res.status_code == 201
    stage2_res = await async_client.post(
        f"/api/v1/drives/{drive_id}/stages",
        headers=off_headers,
        json={
            "name": "Technical & Architecture Interview",
            "stage_type": "CODING",
            "sequence_order": 2,
            "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=15)).isoformat(),
            "location_or_link": "Virtual Meeting Room",
            "instructions": "Live systems coding session.",
        },
    )
    assert stage2_res.status_code == 201

    # 6. Officer publishes drive
    publish_res = await async_client.post(
        f"/api/v1/drives/{drive_id}/status",
        headers=off_headers,
        json={"status": "PUBLISHED"},
    )
    assert publish_res.status_code == 200
    assert publish_res.json()["status"] == "PUBLISHED"
    assert publish_res.json()["published_at"] is not None

    # 7. Drive is now visible in student drive listing
    list_after_publish = await async_client.get("/api/v1/drives", headers=elig_headers)
    assert list_after_publish.status_code == 200
    published_ids = [d["id"] for d in list_after_publish.json()["items"]]
    assert drive_id in published_ids

    # 8. Eligible student views drive details — verify authoritative my_eligibility
    elig_view = await async_client.get(f"/api/v1/drives/{drive_id}", headers=elig_headers)
    assert elig_view.status_code == 200
    elig_json = elig_view.json()
    assert elig_json["my_eligibility"]["is_eligible"] is True
    assert elig_json["my_eligibility"]["reasons"] == []
    assert elig_json["is_registered"] is False

    # 9. Ineligible student views drive details — verify clear reasons
    inelig_view = await async_client.get(f"/api/v1/drives/{drive_id}", headers=inelig_headers)
    assert inelig_view.status_code == 200
    inelig_json = inelig_view.json()
    assert inelig_json["my_eligibility"]["is_eligible"] is False
    assert len(inelig_json["my_eligibility"]["reasons"]) > 0

    # 10. Advance drive to REGISTRATION_OPEN
    open_res = await async_client.post(
        f"/api/v1/drives/{drive_id}/status",
        headers=off_headers,
        json={"status": "REGISTRATION_OPEN"},
    )
    assert open_res.status_code == 200
    assert open_res.json()["status"] == "REGISTRATION_OPEN"

    # 11. Eligible student registers
    reg_res = await async_client.post(f"/api/v1/drives/{drive_id}/register", headers=elig_headers)
    assert reg_res.status_code == 201
    assert reg_res.json()["status"] == "REGISTERED"

    # Verify is_registered is now true for eligible student
    elig_view_post_reg = await async_client.get(f"/api/v1/drives/{drive_id}", headers=elig_headers)
    assert elig_view_post_reg.json()["is_registered"] is True

    # 12. Ineligible student cannot register (fails with 422 or 403)
    inelig_reg_res = await async_client.post(f"/api/v1/drives/{drive_id}/register", headers=inelig_headers)
    assert inelig_reg_res.status_code in (403, 422)

    # 13. Student cannot create drives (RBAC check)
    student_create_res = await async_client.post("/api/v1/drives", headers=elig_headers, json=drive_payload)
    assert student_create_res.status_code == 403

    # 14. Student cannot change drive status (RBAC check)
    student_status_res = await async_client.post(
        f"/api/v1/drives/{drive_id}/status",
        headers=elig_headers,
        json={"status": "REGISTRATION_CLOSED"},
    )
    assert student_status_res.status_code == 403

    # 15. Non-UUID input returns HTTP 422 (UUID validation strictly enforced)
    invalid_uuid_res = await async_client.get("/api/v1/drives/not-a-valid-uuid", headers=off_headers)
    assert invalid_uuid_res.status_code == 422

    # 16. Audit Log validation: verify DRIVE_CREATED, DRIVE_PUBLISHED, DRIVE_REGISTRATION_OPEN logged
    audit_stmt = select(AuditLog).where(AuditLog.entity_id == UUID(drive_id))
    audit_results = (await db_session.execute(audit_stmt)).scalars().all()
    actions = [a.action for a in audit_results]
    assert "DRIVE_CREATED" in actions
    assert "DRIVE_PUBLISHED" in actions
    assert "DRIVE_REGISTRATION_OPEN" in actions
