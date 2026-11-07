"""seed admin, placement officers, demo student, companies, and published drives

Revision ID: 0014_seed_admin_officer_and_drives
Revises: 0013_seed_klu_students_master
Create Date: 2026-11-07 12:00:00.000000

"""
from datetime import datetime, timedelta, timezone
import json
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0014_seed_admin_officer'
down_revision: Union[str, None] = '0013_seed_klu_students_master'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ADMIN_HASH = '$2b$12$Q3cBQOOvylryK0XRWHzHV.ayYXOzA5g45LccfA6WqNSTUfIDIDNW6'
OFFICER_HASH = '$2b$12$Gcy4U00E1LAuic3b8JUzgulpyeo8Awk5tnTRglpVvC7u5/05qNlii'
STUDENT_HASH = '$2b$12$16bN8GkoRVusreY4XXORx.vPlMzg/5XvSBoNsi3KU8Yl2RwqHcbMi'


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Seed or Upsert Key User Accounts
    users_to_seed = [
        {
            "email": "admin@campusflow.edu",
            "password_hash": ADMIN_HASH,
            "full_name": "Institutional Administrator",
            "role": "ADMIN",
        },
        {
            "email": "officer@campusflow.edu",
            "password_hash": OFFICER_HASH,
            "full_name": "CDC Placement Officer",
            "role": "OFFICER",
        },
        {
            "email": "dhilipanrajkumar@gmail.com",
            "password_hash": OFFICER_HASH,
            "full_name": "Mr. Dhilipanrajkumar",
            "role": "OFFICER",
        },
        {
            "email": "placement@klu.ac.in",
            "password_hash": OFFICER_HASH,
            "full_name": "KARE Placement Cell",
            "role": "OFFICER",
        },
        {
            "email": "student1@campusflow.edu",
            "password_hash": STUDENT_HASH,
            "full_name": "Demo Student",
            "role": "STUDENT",
        },
    ]

    officer_user_id = None

    for u in users_to_seed:
        res = bind.execute(
            sa.text("SELECT id FROM users WHERE LOWER(email) = LOWER(:email)"),
            {"email": u["email"]}
        ).fetchone()

        if res:
            uid = str(res[0])
            bind.execute(
                sa.text("""
                    UPDATE users
                    SET password_hash = :pwd_hash,
                        role = :role,
                        full_name = :full_name,
                        is_active = true,
                        must_change_password = false,
                        updated_at = now()
                    WHERE id = CAST(:id AS uuid)
                """),
                {
                    "id": uid,
                    "pwd_hash": u["password_hash"],
                    "role": u["role"],
                    "full_name": u["full_name"],
                }
            )
        else:
            uid = str(uuid.uuid4())
            bind.execute(
                sa.text("""
                    INSERT INTO users (id, email, password_hash, role, full_name, is_active, must_change_password, created_at, updated_at)
                    VALUES (CAST(:id AS uuid), :email, :pwd_hash, :role, :full_name, true, false, now(), now())
                """),
                {
                    "id": uid,
                    "email": u["email"].lower(),
                    "pwd_hash": u["password_hash"],
                    "role": u["role"],
                    "full_name": u["full_name"],
                }
            )

        if u["role"] == "OFFICER" and not officer_user_id:
            officer_user_id = uid

    # 2. Student Profile for student1@campusflow.edu
    res_s1 = bind.execute(
        sa.text("SELECT id FROM users WHERE LOWER(email) = 'student1@campusflow.edu'")
    ).fetchone()
    if res_s1:
        s1_uid = str(res_s1[0])
        bind.execute(
            sa.text("""
                INSERT INTO student_profiles (id, user_id, roll_number, branch_code, batch_year, cgpa, active_backlogs, created_at, updated_at)
                VALUES (CAST(:id AS uuid), CAST(:user_id AS uuid), 'DEMO2026001', 'CSE', 2027, 8.80, 0, now(), now())
                ON CONFLICT (roll_number) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    cgpa = EXCLUDED.cgpa,
                    updated_at = now();
            """),
            {"id": str(uuid.uuid4()), "user_id": s1_uid}
        )

    # 3. Seed Companies
    companies_data = [
        {
            "name": "Tata Consultancy Services (TCS)",
            "website": "https://www.tcs.com",
            "industry": "IT Services & Consulting",
            "description": "Global leader in IT services, consulting, and business solutions.",
        },
        {
            "name": "Amazon Web Services (AWS)",
            "website": "https://aws.amazon.com",
            "industry": "Cloud Computing & AI",
            "description": "The world's most comprehensive and broadly adopted cloud platform.",
        },
        {
            "name": "Zoho Corporation",
            "website": "https://www.zoho.com",
            "industry": "Enterprise SaaS",
            "description": "Leading global provider of cloud-based business productivity and CRM software.",
        },
    ]

    company_id_map = {}
    for comp in companies_data:
        res_comp = bind.execute(
            sa.text("SELECT id FROM companies WHERE name = :name"),
            {"name": comp["name"]}
        ).fetchone()

        if res_comp:
            company_id_map[comp["name"]] = str(res_comp[0])
        else:
            cid = str(uuid.uuid4())
            bind.execute(
                sa.text("""
                    INSERT INTO companies (id, name, website, industry, description, created_by_user_id, created_at, updated_at)
                    VALUES (CAST(:id AS uuid), :name, :website, :industry, :description, CAST(:creator_id AS uuid), now(), now())
                """),
                {
                    "id": cid,
                    "name": comp["name"],
                    "website": comp["website"],
                    "industry": comp["industry"],
                    "description": comp["description"],
                    "creator_id": officer_user_id,
                }
            )
            company_id_map[comp["name"]] = cid

    # 4. Seed Placement Drives
    now = datetime.now(timezone.utc)
    all_branches = [
        "CSE", "IT", "ECE", "EEE", "CS", "CSE (SHIP)", "MECH", "CIVIL",
        "AERO", "AGRI", "BIOMEDICAL", "BIOTECH", "CHEMICAL", "FOODTECH", "MCA"
    ]

    drives_data = [
        {
            "company_name": "Tata Consultancy Services (TCS)",
            "title": "TCS National Qualifier Test (NQT) 2026-27",
            "job_role": "Ninja & Digital Software Engineer",
            "description": "Annual flagship campus placement drive by Tata Consultancy Services for engineering graduates. Roles span full-stack web engineering, cloud applications, and systems programming.",
            "ctc_lpa": 7.20,
            "location": "Chennai / Bengaluru / Pan India",
            "deadline": now + timedelta(days=30),
            "status": "PUBLISHED",
            "criteria": {
                "min_cgpa": 6.5,
                "max_active_backlogs": 0,
                "max_backlogs": 0,
                "eligible_branches": all_branches,
                "allowed_branches": all_branches,
                "eligible_batch_years": [2026, 2027],
                "batch_years": [2026, 2027],
            },
        },
        {
            "company_name": "Amazon Web Services (AWS)",
            "title": "Amazon AWS Cloud Support Associate 2026-27",
            "job_role": "Cloud Solutions & DevOps Engineer",
            "description": "Campus recruitment drive for Amazon Web Services cloud engineering, distributed infrastructure, and automated DevOps workflows.",
            "ctc_lpa": 16.50,
            "location": "Hyderabad / Bengaluru",
            "deadline": now + timedelta(days=21),
            "status": "PUBLISHED",
            "criteria": {
                "min_cgpa": 7.5,
                "max_active_backlogs": 0,
                "max_backlogs": 0,
                "eligible_branches": ["CSE", "IT", "ECE", "EEE", "CS", "CSE (SHIP)"],
                "allowed_branches": ["CSE", "IT", "ECE", "EEE", "CS", "CSE (SHIP)"],
                "eligible_batch_years": [2026, 2027],
                "batch_years": [2026, 2027],
            },
        },
        {
            "company_name": "Zoho Corporation",
            "title": "Zoho Software Development Engineer 2026-27",
            "job_role": "Product Software Developer (Full Stack)",
            "description": "Zoho Product Engineering hiring for high-performance SaaS applications, microservices, and modern frontend systems.",
            "ctc_lpa": 10.00,
            "location": "Chennai / Tenkasi",
            "deadline": now + timedelta(days=25),
            "status": "PUBLISHED",
            "criteria": {
                "min_cgpa": 7.0,
                "max_active_backlogs": 0,
                "max_backlogs": 0,
                "eligible_branches": ["CSE", "IT", "ECE", "CS", "CSE (SHIP)"],
                "allowed_branches": ["CSE", "IT", "ECE", "CS", "CSE (SHIP)"],
                "eligible_batch_years": [2026, 2027],
                "batch_years": [2026, 2027],
            },
        },
    ]

    for d in drives_data:
        res_drive = bind.execute(
            sa.text("SELECT id FROM placement_drives WHERE title = :title"),
            {"title": d["title"]}
        ).fetchone()

        comp_id = company_id_map.get(d["company_name"])
        if not comp_id:
            continue

        if not res_drive:
            drive_id = str(uuid.uuid4())
            bind.execute(
                sa.text("""
                    INSERT INTO placement_drives (
                        id, company_id, title, job_role, description, ctc_lpa, location,
                        registration_deadline, status, created_by_user_id, published_at, created_at, updated_at
                    ) VALUES (
                        CAST(:id AS uuid), CAST(:comp_id AS uuid), :title, :job_role, :desc, :ctc, :loc,
                        :deadline, :status, CAST(:creator_id AS uuid), :pub_at, now(), now()
                    )
                """),
                {
                    "id": drive_id,
                    "comp_id": comp_id,
                    "title": d["title"],
                    "job_role": d["job_role"],
                    "desc": d["description"],
                    "ctc": d["ctc_lpa"],
                    "loc": d["location"],
                    "deadline": d["deadline"],
                    "status": d["status"],
                    "creator_id": officer_user_id,
                    "pub_at": now,
                }
            )

            # Insert eligibility criteria with explicit CAST to jsonb
            bind.execute(
                sa.text("""
                    INSERT INTO eligibility_criteria (id, drive_id, criteria, created_at, updated_at)
                    VALUES (CAST(:id AS uuid), CAST(:drive_id AS uuid), CAST(:criteria AS jsonb), now(), now())
                    ON CONFLICT (drive_id) DO UPDATE SET
                        criteria = EXCLUDED.criteria,
                        updated_at = now();
                """),
                {
                    "id": str(uuid.uuid4()),
                    "drive_id": drive_id,
                    "criteria": json.dumps(d["criteria"]),
                }
            )


def downgrade() -> None:
    pass
