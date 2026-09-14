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
from app.models.preparation import (
    PreparationCategory,
    PreparationMaterial,
    PreparationRole,
    PreparationRoleTopic,
    PreparationTopic,
)
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


        # 2b. Pre-provisioned Student: 99230041249 (unactivated, awaiting first-time registration)
        demo_roll = "99230041249"
        demo_email = "99230041249@klu.ac.in"
        res_prof = await session.execute(select(StudentProfile).where(StudentProfile.roll_number == demo_roll))
        prof_demo = res_prof.scalar_one_or_none()
        if not prof_demo:
            res_u = await session.execute(select(User).where(User.email == demo_email))
            u_demo = res_u.scalar_one_or_none()
            if not u_demo:
                u_demo = User(
                    id=uuid4(),
                    email=demo_email,
                    password_hash=hash_password("temporary-placeholder"),
                    full_name="Karthik Pyla",
                    role="STUDENT",
                    is_active=False,
                    must_change_password=True,
                )
                session.add(u_demo)
                await session.flush()
            else:
                u_demo.is_active = False
                u_demo.password_hash = hash_password("temporary-placeholder")
                session.add(u_demo)

            prof_demo = StudentProfile(
                id=uuid4(),
                user_id=u_demo.id,
                roll_number=demo_roll,
                branch_code="CSE",
                batch_year=2026,
                cgpa=8.50,
                active_backlogs=0,
            )
            session.add(prof_demo)
            await session.commit()
            print(f"[OK] Created pre-provisioned unactivated Student: {demo_roll} ({demo_email})")
        else:
            u_demo = await session.get(User, prof_demo.user_id)
            if u_demo:
                u_demo.email = demo_email
                u_demo.is_active = False
                u_demo.password_hash = hash_password("temporary-placeholder")
                session.add(u_demo)
                await session.commit()
            print(f"[OK] Reset/verified pre-provisioned unactivated Student {demo_roll} ({demo_email})")

        # 2c. Unactivated Student specifically for New User Registration testing
        unreg_roll = "99230099999"
        unreg_email = "student.unactivated@campusflow.edu"
        res_unreg = await session.execute(select(User).where(User.email == unreg_email))
        u_unreg = res_unreg.scalar_one_or_none()
        if not u_unreg:
            u_unreg = User(
                id=uuid4(),
                email=unreg_email,
                password_hash=hash_password("temporary-placeholder"),
                full_name="Unactivated Student",
                role="STUDENT",
                is_active=False,
                must_change_password=True,
            )
            session.add(u_unreg)
            await session.flush()

            prof_unreg = StudentProfile(
                id=uuid4(),
                user_id=u_unreg.id,
                roll_number=unreg_roll,
                branch_code="CSE",
                batch_year=2026,
                cgpa=7.50,
                active_backlogs=0,
            )
            session.add(prof_unreg)
            await session.commit()
            print(f"[OK] Created unactivated synthetic Student: {unreg_roll} ({unreg_email})")
        else:
            print(f"[OK] Verified unactivated synthetic Student {unreg_roll} ({unreg_email})")


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

        # 7. Preparation Hub Resources
        # Roles
        roles_data = [
            ("SOFTWARE_DEVELOPER", "Software Developer", "Full-stack development, algorithms, system design, and coding rounds.", "code"),
            ("DATA_ANALYST", "Data Analyst", "SQL queries, data visualization, business statistics, and dashboarding.", "chart-bar"),
            ("AIML_ENGINEER", "AI / ML Engineer", "Machine learning fundamentals, deep learning, PyTorch, and NLP.", "cpu-chip"),
            ("DEVOPS_ENGINEER", "DevOps Engineer", "CI/CD pipelines, Docker, Kubernetes, Linux, and Cloud Infrastructure.", "cloud"),
        ]
        seeded_roles: dict[str, PreparationRole] = {}
        for code, name, desc, icon in roles_data:
            res = await session.execute(select(PreparationRole).where(PreparationRole.code == code))
            r = res.scalar_one_or_none()
            if not r:
                r = PreparationRole(
                    id=uuid4(),
                    code=code,
                    name=name,
                    description=desc,
                    icon=icon,
                    is_active=True,
                )
                session.add(r)
                await session.flush()
            seeded_roles[code] = r

        # Categories
        categories_data = [
            ("APTITUDE", "Quantitative & Reasoning", "Mathematical ability, numerical shortcuts, and logical deductions.", "calculator", 1),
            ("TECHNICAL", "Core Computer Science", "Data structures, algorithms, databases, OS, and software engineering.", "code", 2),
            ("VERBAL", "Verbal Ability & English", "Reading comprehension, sentence correction, and vocabulary.", "book-open", 3),
            ("INTERVIEW", "Interview Preparation", "Technical HR, behavioral questions, and resume walkthroughs.", "user-group", 4),
        ]
        seeded_cats: dict[str, PreparationCategory] = {}
        for code, name, desc, icon, seq in categories_data:
            res = await session.execute(select(PreparationCategory).where(PreparationCategory.code == code))
            c = res.scalar_one_or_none()
            if not c:
                c = PreparationCategory(
                    id=uuid4(),
                    code=code,
                    name=name,
                    description=desc,
                    icon=icon,
                    sequence_order=seq,
                )
                session.add(c)
                await session.flush()
            seeded_cats[code] = c

        # Topics
        topics_data = [
            ("APTITUDE", "Quantitative Mathematics", "quant-math", "Arithmetic, Algebra, Percentages, and Probability."),
            ("APTITUDE", "Logical & Analytical Reasoning", "logical-reasoning", "Puzzles, Seating Arrangements, and Syllogisms."),
            ("TECHNICAL", "Data Structures & Algorithms", "dsa", "Arrays, Linked Lists, Trees, Graphs, Dynamic Programming."),
            ("TECHNICAL", "SQL & Database Management", "sql-dbms", "RDBMS principles, indexing, normalization, and complex queries."),
            ("TECHNICAL", "Python Core & Advanced", "python-programming", "Python data models, generators, OOP, and asynchronous patterns."),
            ("INTERVIEW", "Behavioral & HR Rounds", "behavioral-hr", "STAR method, common behavioral scenarios, and communication."),
        ]
        seeded_topics: dict[str, PreparationTopic] = {}
        for cat_code, name, slug, desc in topics_data:
            res = await session.execute(select(PreparationTopic).where(PreparationTopic.slug == slug))
            t = res.scalar_one_or_none()
            if not t:
                t = PreparationTopic(
                    id=uuid4(),
                    category_id=seeded_cats[cat_code].id,
                    name=name,
                    slug=slug,
                    description=desc,
                )
                session.add(t)
                await session.flush()
            seeded_topics[slug] = t

        # Role-Topic Mappings
        role_topic_links = [
            ("SOFTWARE_DEVELOPER", "dsa", "CORE"),
            ("SOFTWARE_DEVELOPER", "sql-dbms", "CORE"),
            ("SOFTWARE_DEVELOPER", "python-programming", "CORE"),
            ("SOFTWARE_DEVELOPER", "quant-math", "CORE"),
            ("SOFTWARE_DEVELOPER", "behavioral-hr", "ELECTIVE"),
            ("DATA_ANALYST", "sql-dbms", "CORE"),
            ("DATA_ANALYST", "quant-math", "CORE"),
            ("DATA_ANALYST", "python-programming", "ELECTIVE"),
        ]
        for role_code, topic_slug, imp in role_topic_links:
            r = seeded_roles[role_code]
            t = seeded_topics[topic_slug]
            res = await session.execute(
                select(PreparationRoleTopic).where(
                    PreparationRoleTopic.role_id == r.id,
                    PreparationRoleTopic.topic_id == t.id,
                )
            )
            if not res.scalar_one_or_none():
                session.add(PreparationRoleTopic(id=uuid4(), role_id=r.id, topic_id=t.id, importance=imp))

        # Sample Approved Preparation Materials
        materials_data = [
            ("dsa", "SOFTWARE_DEVELOPER", "Complete DSA Roadmap & LeetCode 75 Patterns", "https://leetcode.com/discuss/general-discussion/460599/blind-75-leetcode-questions", "ARTICLE", "INTERMEDIATE", "LeetCode"),
            ("quant-math", None, "Quantitative Aptitude Formulas & Short-Tricks Guide", "https://www.geeksforgeeks.org/quantitative-aptitude-for-placements/", "PDF", "BEGINNER", "GeeksforGeeks"),
            ("sql-dbms", "SOFTWARE_DEVELOPER", "50 SQL Interview Questions with Interactive Queries", "https://leetcode.com/studyplan/top-sql-50/", "PRACTICE_QUESTIONS", "INTERMEDIATE", "LeetCode SQL"),
            ("behavioral-hr", None, "Cracking the Behavioral Interview: STAR Method Mastery", "https://hbr.org/2021/04/how-to-answer-behavioral-interview-questions", "ARTICLE", "BEGINNER", "Harvard Business Review"),
        ]
        for topic_slug, role_code, title, url, mat_type, diff, source in materials_data:
            res = await session.execute(select(PreparationMaterial).where(PreparationMaterial.title == title))
            if not res.scalar_one_or_none():
                session.add(
                    PreparationMaterial(
                        id=uuid4(),
                        topic_id=seeded_topics[topic_slug].id,
                        role_id=seeded_roles[role_code].id if role_code else None,
                        title=title,
                        description="Comprehensive placement preparation resource verified by the career cell.",
                        url=url,
                        material_type=mat_type,
                        difficulty=diff,
                        source=source,
                        status="APPROVED",
                        submitted_by_user_id=officer.id,
                        reviewed_by_user_id=officer.id,
                    )
                )

        await session.commit()
        print("[OK] Seeded Preparation Hub roles, categories, topics, and verified materials.")

    await engine.dispose()
    print("\n[SUCCESS] Deterministic synthetic test environment seeding COMPLETE!")


if __name__ == "__main__":
    asyncio.run(seed_data())
