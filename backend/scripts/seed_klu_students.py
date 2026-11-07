#!/usr/bin/env python3
"""
Seed KLU Master Student List into CampusFlow Database.
Reads backend/data/klu_students_master.csv and idempotently populates:
- branches
- users (role=STUDENT, is_active=False)
- student_profiles (with CGPA, branch, section, personal email)
"""
import asyncio
import csv
import os
import sys
from pathlib import Path
import uuid

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://campusflow:campusflow_dev@localhost:5432/campusflow_dev",
)

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


async def seed_klu_students():
    clean_db_url = DATABASE_URL
    if clean_db_url.startswith("postgres://"):
        clean_db_url = clean_db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif clean_db_url.startswith("postgresql://") and not clean_db_url.startswith("postgresql+asyncpg://"):
        clean_db_url = clean_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print(f"Connecting to database: {clean_db_url.split('@')[-1]}...")
    engine = create_async_engine(clean_db_url, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    csv_path = BASE_DIR / "data" / "klu_students_master.csv"
    if not csv_path.exists():
        print(f"CSV not found at {csv_path}")
        return

    with open(csv_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Loaded {len(rows)} student records from CSV.")

    async with session_maker() as session:
        # 1. Branches
        for code, name in BRANCHES_TO_SEED:
            await session.execute(
                text("""
                    INSERT INTO branches (id, code, name, is_active, created_at, updated_at)
                    VALUES (:id, :code, :name, true, now(), now())
                    ON CONFLICT (code) DO NOTHING;
                """),
                {"id": str(uuid.uuid4()), "code": code, "name": name}
            )
        await session.commit()
        print("[OK] Branches synchronized.")

        # 2. Existing users and profiles
        existing_users_res = await session.execute(text("SELECT id, email FROM users"))
        email_to_uid = {row[1].lower(): str(row[0]) for row in existing_users_res if row[1]}

        existing_profs_res = await session.execute(text("SELECT roll_number FROM student_profiles"))
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

        CHUNK_SIZE = 250
        insert_user_sql = text("""
            INSERT INTO users (id, email, password_hash, role, full_name, is_active, must_change_password, created_at, updated_at)
            VALUES (:id, :email, :password_hash, :role, :full_name, :is_active, :must_change_password, now(), now())
            ON CONFLICT (email) DO NOTHING;
        """)
        for i in range(0, len(new_users), CHUNK_SIZE):
            chunk = new_users[i : i + CHUNK_SIZE]
            if chunk:
                await session.execute(insert_user_sql, chunk)

        insert_profile_sql = text("""
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
                await session.execute(insert_profile_sql, chunk)

        update_profile_sql = text("""
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
                await session.execute(update_profile_sql, chunk)

        await session.commit()
        print(f"[SUCCESS] Seeded/updated {len(rows)} students in master database.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_klu_students())
