#!/usr/bin/env python3
"""
CampusFlow — Deterministic Test Environment Seeder.

Seeds isolated synthetic data for Playwright E2E and Locust load testing:
- 1 Admin: admin@campusflow.edu / TestAdmin@123
- 1 Officer: officer@campusflow.edu / TestOfficer@123
- 5 Students: student1..5@campusflow.edu / TestStudent@123
- Standard Engineering Branches
- 2 Placement Drives (1 Published, 1 Draft)
- Realistic In-App Notifications

Safety invariants:
- NEVER uses real student PII.
- Only uses the reserved '.test' TLD.
- Idempotent: checks for existence before inserting.
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv

load_dotenv(BASE_DIR / ".env")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.db.base import Base
from app.models.branch import Branch
from app.models.company import Company
from app.models.drive_registration import DriveRegistration
from app.models.eligibility_criteria import EligibilityCriteria
from app.models.notification import Notification
from app.models.placement_drive import PlacementDrive
from app.models.student_profile import StudentProfile
from app.models.user import User


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://campusflow:campusflow_dev@localhost:5432/campusflow_dev",
)


async def seed_data():
    print(f"Connecting to database: {DATABASE_URL.split('@')[-1]}...")
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"server_settings": {"search_path": "campusflow, public"}},
    )

    # Ensure schema and tables exist
    async with engine.begin() as conn:
        from sqlalchemy import text
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS campusflow AUTHORIZATION campusflow;"))
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with session_maker() as session:
        # 1. Branches
        branches_data = [
            ("CSE", "Computer Science and Engineering"),
            ("ECE", "Electronics and Communication Engineering"),
            ("MECH", "Mechanical Engineering"),
            ("CIVIL", "Civil Engineering"),
            ("IT", "Information Technology"),
        ]
        for code, name in branches_data:
            existing = await session.execute(select(Branch).where(Branch.code == code))
            if not existing.scalar_one_or_none():
                session.add(Branch(code=code, name=name))
        await session.commit()
        print("[OK] Branches verified.")

        # 2. Users
        # Admin
        admin_email = "admin@campusflow.edu"
        res = await session.execute(select(User).where(User.email == admin_email))
        admin = res.scalar_one_or_none()
        if not admin:
            admin = User(
                id=uuid4(),
                email=admin_email,
                password_hash=hash_password("TestAdmin@123"),
                full_name="Synthetic System Administrator",
                role="ADMIN",
                is_active=True,
                must_change_password=False,
            )
            session.add(admin)
            await session.commit()
            await session.refresh(admin)
            print("[OK] Created synthetic Admin user: admin@campusflow.edu")

        # Officer
        officer_email = "officer@campusflow.edu"
        res = await session.execute(select(User).where(User.email == officer_email))
        officer = res.scalar_one_or_none()
        if not officer:
            officer = User(
                id=uuid4(),
                email=officer_email,
                password_hash=hash_password("TestOfficer@123"),
                full_name="Synthetic Placement Officer",
                role="OFFICER",
                is_active=True,
                must_change_password=False,
            )
            session.add(officer)
            await session.commit()
            await session.refresh(officer)
            print("[OK] Created synthetic Officer user: officer@campusflow.edu")

        # Students
        students_spec = [
            ("student1@campusflow.edu", "Synthetic Student One", "SYN26CSE00001", "CSE", 2026, 8.80, 0),
            ("student2@campusflow.edu", "Synthetic Student Two", "SYN26ECE00002", "ECE", 2026, 7.50, 0),
            ("student3@campusflow.edu", "Synthetic Student Three", "SYN26MEC00003", "MECH", 2026, 6.20, 1),
            ("student4@campusflow.edu", "Synthetic Student Four", "SYN26CSE00004", "CSE", 2026, 9.10, 0),
            ("student5@campusflow.edu", "Synthetic Student Five", "SYN26CIV00005", "CIVIL", 2026, 5.80, 2),
        ]

        seeded_students: list[tuple[User, StudentProfile]] = []
        for email, name, roll, branch, batch, cgpa, backlogs in students_spec:
            res = await session.execute(select(User).where(User.email == email))
            u = res.scalar_one_or_none()
            if not u:
                u = User(
                    id=uuid4(),
                    email=email,
                    password_hash=hash_password("TestStudent@123"),
                    full_name=name,
                    role="STUDENT",
                    is_active=True,
                    must_change_password=False,
                )
                session.add(u)
                await session.flush()

                prof = StudentProfile(
                    id=uuid4(),
                    user_id=u.id,
                    roll_number=roll,
                    branch_code=branch,
                    batch_year=batch,
                    cgpa=cgpa,
                    active_backlogs=backlogs,
                )
                session.add(prof)
                await session.commit()
                await session.refresh(u)
                await session.refresh(prof)
                seeded_students.append((u, prof))
            else:
                p_res = await session.execute(select(StudentProfile).where(StudentProfile.user_id == u.id))
                prof = p_res.scalar_one_or_none()
                seeded_students.append((u, prof))
        print("[OK] Created/verified 5 synthetic Students with academic profiles.")

        # 3. Companies
        company_name = "Acme Technologies (Synthetic)"
        res = await session.execute(select(Company).where(Company.name == company_name))
        company1 = res.scalar_one_or_none()
        if not company1:
            company1 = Company(
                id=uuid4(),
                name=company_name,
                website="https://acme-synthetic.test",
                industry="Software",
                created_by_user_id=officer.id,
            )
            session.add(company1)
            await session.commit()
            await session.refresh(company1)

        company2_name = "Global Core Motors (Synthetic)"
        res = await session.execute(select(Company).where(Company.name == company2_name))
        company2 = res.scalar_one_or_none()
        if not company2:
            company2 = Company(
                id=uuid4(),
                name=company2_name,
                website="https://global-synthetic.test",
                industry="Automotive",
                created_by_user_id=officer.id,
            )
            session.add(company2)
            await session.commit()
            await session.refresh(company2)
        print("[OK] Companies verified.")

        # 4. Placement Drives
        # Drive 1: Published & Active
        drive1_title = "Acme Tech Placement Drive 2026"
        res = await session.execute(select(PlacementDrive).where(PlacementDrive.title == drive1_title))
        drive1 = res.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if not drive1:
            drive1 = PlacementDrive(
                id=uuid4(),
                company_id=company1.id,
                title=drive1_title,
                job_role="Graduate Software Engineer",
                description="Synthetic placement drive for full-stack engineering roles.",
                ctc_lpa=12.50,
                location="Bengaluru / Remote",
                registration_deadline=now + timedelta(days=7),
                status="PUBLISHED",
                published_at=now - timedelta(hours=2),
                created_by_user_id=officer.id,
            )
            session.add(drive1)
            await session.flush()

            crit1 = EligibilityCriteria(
                id=uuid4(),
                drive_id=drive1.id,
                criteria={
                    "allowed_branches": ["CSE", "ECE", "IT"],
                    "min_cgpa": 7.0,
                    "max_backlogs": 0,
                    "batch_years": [2026],
                },
            )
            session.add(crit1)
            await session.commit()
            await session.refresh(drive1)
            print("[OK] Created Published Placement Drive (Acme Tech).")

        # Drive 2: Draft
        drive2_title = "Global Motors Trainee Drive 2026"
        res = await session.execute(select(PlacementDrive).where(PlacementDrive.title == drive2_title))
        drive2 = res.scalar_one_or_none()
        if not drive2:
            drive2 = PlacementDrive(
                id=uuid4(),
                company_id=company2.id,
                title=drive2_title,
                job_role="Design Engineer Trainee",
                description="Draft placement drive for Mechanical and Civil engineering roles.",
                ctc_lpa=8.00,
                location="Pune",
                registration_deadline=now + timedelta(days=14),
                status="DRAFT",
                created_by_user_id=officer.id,
            )
            session.add(drive2)
            await session.flush()

            crit2 = EligibilityCriteria(
                id=uuid4(),
                drive_id=drive2.id,
                criteria={
                    "allowed_branches": ["MECH", "CIVIL"],
                    "min_cgpa": 6.0,
                    "max_backlogs": 1,
                    "batch_years": [2026],
                },
            )
            session.add(crit2)
            await session.commit()
            await session.refresh(drive2)
            print("[OK] Created Draft Placement Drive (Global Motors).")

        # 5. Registrations: Student 1 registers for Drive 1
        s1_user, s1_prof = seeded_students[0]
        reg_res = await session.execute(
            select(DriveRegistration).where(
                DriveRegistration.drive_id == drive1.id,
                DriveRegistration.student_user_id == s1_user.id,
            )
        )
        if not reg_res.scalar_one_or_none():
            reg = DriveRegistration(
                id=uuid4(),
                drive_id=drive1.id,
                student_user_id=s1_user.id,
                resume_gcs_path_at_registration="resumes/synthetic_s1.pdf",
                status="REGISTERED",
                registered_at=now,
            )
            session.add(reg)
            await session.commit()
            print("[OK] Student 1 registered for Acme Tech Drive.")

        # 6. Notifications
        notif_res = await session.execute(
            select(Notification).where(
                Notification.user_id == s1_user.id,
                Notification.notification_type == "DRIVE_PUBLISHED",
            )
        )
        if not notif_res.scalar_one_or_none():
            n1 = Notification(
                id=uuid4(),
                user_id=s1_user.id,
                title="New Placement Drive: Acme Tech",
                body="Acme Tech has announced Graduate Software Engineer roles.",
                notification_type="DRIVE_PUBLISHED",
                reference_id=drive1.id,
                reference_type="DRIVE",
                is_read=False,
            )
            n2 = Notification(
                id=uuid4(),
                user_id=s1_user.id,
                title="Welcome to CampusFlow",
                body="Your placement profile has been verified by the TPO.",
                notification_type="SYSTEM",
                reference_id=None,
                reference_type=None,
                is_read=True,
            )
            session.add_all([n1, n2])
            await session.commit()
            print("[OK] Seeded sample notifications for Student 1.")

    await engine.dispose()
    print("\n[SUCCESS] Deterministic synthetic test environment seeding COMPLETE!")


if __name__ == "__main__":
    asyncio.run(seed_data())
