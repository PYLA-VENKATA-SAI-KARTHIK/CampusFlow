"""seed KLU master student list (1378 students)

Revision ID: 0013_seed_klu_students_master
Revises: 0012_mock_interview_voice_agent
Create Date: 2026-11-07 11:30:00.000000

"""
import csv
import os
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0013_seed_klu_students_master'
down_revision: Union[str, None] = '0012_mock_interview_voice_agent'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PLACEHOLDER_HASH = '$2b$12$YQggNQoCFvACr07QQoLtyukeOeb3jVMubX/4JoQsfw6UHvOLWtw5O'

BRANCHES_TO_SEED = [
    ('CSE', 'Computer Science and Engineering'),
    ('ECE', 'Electronics and Communication Engineering'),
    ('IT', 'Information Technology'),
    ('MECH', 'Mechanical Engineering'),
    ('CIVIL', 'Civil Engineering'),
    ('EEE', 'Electrical and Electronics Engineering'),
    ('AERO', 'Aeronautical Engineering'),
    ('AGRI', 'Agricultural Engineering'),
    ('BIOMEDICAL', 'Biomedical Engineering'),
    ('BIOTECH', 'Biotechnology'),
    ('CHEMICAL', 'Chemical Engineering'),
    ('CS', 'Computer Science'),
    ('CSE (SHIP)', 'Computer Science and Engineering (SHIP)'),
    ('FOODTECH', 'Food Technology'),
    ('MCA', 'Master of Computer Applications'),
]


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Seed or ensure all branches exist
    for code, name in BRANCHES_TO_SEED:
        bind.execute(
            sa.text("""
                INSERT INTO branches (id, code, name, is_active, created_at, updated_at)
                VALUES (:id, :code, :name, true, now(), now())
                ON CONFLICT (code) DO NOTHING;
            """),
            {"id": str(uuid.uuid4()), "code": code, "name": name}
        )

    # 2. Locate CSV file
    csv_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "klu_students_master.csv")
    )
    if not os.path.exists(csv_path):
        print(f"[WARN] Master CSV file not found at: {csv_path}, skipping student seeding.")
        return

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return

    # 3. Pre-fetch existing users and profiles
    existing_users_res = bind.execute(sa.text("SELECT id, email FROM users"))
    email_to_uid = {row[1].lower(): str(row[0]) for row in existing_users_res if row[1]}

    existing_profs_res = bind.execute(sa.text("SELECT roll_number FROM student_profiles"))
    existing_rolls = {row[0].strip().lower() for row in existing_profs_res if row[0]}

    new_users = []
    new_profiles = []
    update_profiles = []

    for r in rows:
        clean_reg = r['Reg.No.'].strip()
        if not clean_reg:
            continue
        clean_name = r.get('Candidate Full Name', '').strip() or f"Student {clean_reg}"
        clean_dept = r.get('Dept.', '').strip().upper() or 'CSE'
        clean_sec = r.get('Sec.', '').strip() or 'A'
        clean_email = r.get('Candidate Email Id', '').strip().lower() or None
        
        cgpa_str = r.get('CGPA', '').strip()
        try:
            clean_cgpa = float(cgpa_str) if cgpa_str else 7.00
        except ValueError:
            clean_cgpa = 7.00

        univ_email = f"{clean_reg.lower()}@klu.ac.in"

        if univ_email in email_to_uid:
            user_id = email_to_uid[univ_email]
        else:
            user_id = str(uuid.uuid4())
            email_to_uid[univ_email] = user_id
            new_users.append({
                "id": user_id,
                "email": univ_email,
                "password_hash": PLACEHOLDER_HASH,
                "role": "STUDENT",
                "full_name": clean_name,
                "is_active": False,
                "must_change_password": True,
            })

        reg_lower = clean_reg.lower()
        if reg_lower in existing_rolls:
            update_profiles.append({
                "roll_number": clean_reg,
                "branch_code": clean_dept,
                "cgpa": clean_cgpa,
                "personal_email": clean_email,
                "section": clean_sec,
            })
        else:
            new_profiles.append({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "roll_number": clean_reg,
                "branch_code": clean_dept,
                "batch_year": 2027,
                "cgpa": clean_cgpa,
                "active_backlogs": 0,
                "personal_email": clean_email,
                "section": clean_sec,
            })
            existing_rolls.add(reg_lower)

    # 4. Chunked batch insert users
    CHUNK_SIZE = 250
    insert_user_sql = sa.text("""
        INSERT INTO users (id, email, password_hash, role, full_name, is_active, must_change_password, created_at, updated_at)
        VALUES (:id, :email, :password_hash, :role, :full_name, :is_active, :must_change_password, now(), now())
        ON CONFLICT (email) DO NOTHING;
    """)
    for i in range(0, len(new_users), CHUNK_SIZE):
        chunk = new_users[i : i + CHUNK_SIZE]
        if chunk:
            bind.execute(insert_user_sql, chunk)

    # 5. Chunked batch insert student profiles
    insert_profile_sql = sa.text("""
        INSERT INTO student_profiles (id, user_id, roll_number, branch_code, batch_year, cgpa, active_backlogs, personal_email, section, created_at, updated_at)
        VALUES (:id, :user_id, :roll_number, :branch_code, :batch_year, :cgpa, :active_backlogs, :personal_email, :section, now(), now())
        ON CONFLICT (roll_number) DO UPDATE SET
            branch_code = EXCLUDED.branch_code,
            cgpa = EXCLUDED.cgpa,
            personal_email = EXCLUDED.personal_email,
            section = EXCLUDED.section,
            updated_at = now();
    """)
    for i in range(0, len(new_profiles), CHUNK_SIZE):
        chunk = new_profiles[i : i + CHUNK_SIZE]
        if chunk:
            bind.execute(insert_profile_sql, chunk)

    # 6. Apply updates for existing profiles
    update_profile_sql = sa.text("""
        UPDATE student_profiles
        SET branch_code = :branch_code,
            cgpa = :cgpa,
            personal_email = :personal_email,
            section = :section,
            updated_at = now()
        WHERE lower(roll_number) = lower(:roll_number);
    """)
    for i in range(0, len(update_profiles), CHUNK_SIZE):
        chunk = update_profiles[i : i + CHUNK_SIZE]
        if chunk:
            bind.execute(update_profile_sql, chunk)

    print(f"[OK] Seeded/updated {len(rows)} KLU students in Master Student List successfully.")


def downgrade() -> None:
    pass
