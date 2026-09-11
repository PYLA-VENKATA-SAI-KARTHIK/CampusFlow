#!/usr/bin/env python3
"""
CampusFlow — Safe Synthetic Data Generator.

Generates mock student and placement data for load testing (e.g. Locust) and local staging validation.

Safety invariants:
- NEVER uses real student PII.
- All email addresses use the reserved '.internal' or '.test' TLDs (e.g. @synthetic.campusflow.internal).
- Roll numbers use the 'SYN' prefix to clearly mark them as synthetic.
- Passwords are fixed dummy hashes ('synthetic-placeholder').
- Performs batched operations; avoids one DB query per row.

Usage Examples:
    # 1. Generate 5,000 synthetic student records to a CSV file (for Bulk Import or Locust)
    python scripts/generate_synthetic_data.py --students 5000 --output synthetic_students_5k.csv

    # 2. Directly seed 1,000 synthetic records into local database
    python scripts/generate_synthetic_data.py --students 1000 --db
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv

load_dotenv(BASE_DIR / ".env")

FIRST_NAMES = [
    "Aarav", "Aditi", "Akhil", "Ananya", "Arjun", "Bhavya", "Chetan", "Deepika",
    "Dev", "Divya", "Gautam", "Harsh", "Isha", "Kavya", "Karan", "Meera",
    "Nikhil", "Pooja", "Pranav", "Priya", "Rahul", "Rhea", "Rohan", "Siddharth",
    "Sneha", "Tanvi", "Varun", "Vikram", "Yash", "Zoya",
]

LAST_NAMES = [
    "Agarwal", "Bose", "Choudhury", "Das", "Deshmukh", "Gupta", "Iyer", "Jain",
    "Kapoor", "Kumar", "Mehta", "Nair", "Patel", "Reddy", "Sharma", "Singh",
    "Verma", "Yadav", "Rao", "Pillai", "Kulkarni", "Mishra", "Banerjee", "Bhat",
]

BRANCHES = ["CSE", "ECE", "MECH", "CIVIL", "IT"]
BATCH_YEARS = [2025, 2026]


def generate_synthetic_record(idx: int) -> dict:
    """Generate a single obviously synthetic student record."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    full_name = f"Synthetic {first} {last} {idx}"
    branch = random.choice(BRANCHES)
    batch = random.choice(BATCH_YEARS)

    # Deterministic or randomized but structured roll number
    roll_number = f"SYN{str(batch)[2:]}{branch}{idx:05d}"
    email = f"student.{idx:05d}@{branch.lower()}.synthetic.campusflow.internal"

    # Realistic CGPA distribution (bell-curve centered around 7.8, bounded between 6.0 and 10.0)
    cgpa = round(min(10.0, max(6.0, random.gauss(7.8, 0.8))), 2)

    # Backlogs (majority 0, some 1, few 2+)
    active_backlogs = random.choices([0, 1, 2, 3], weights=[75, 18, 5, 2])[0]

    return {
        "email": email,
        "full_name": full_name,
        "roll_number": roll_number,
        "branch_code": branch,
        "batch_year": batch,
        "cgpa": cgpa,
        "active_backlogs": active_backlogs,
    }


def export_to_csv(records: list[dict], output_path: str) -> None:
    """Write generated records to CSV in CampusFlow bulk-import format."""
    fieldnames = [
        "email",
        "full_name",
        "roll_number",
        "branch_code",
        "batch_year",
        "cgpa",
        "active_backlogs",
    ]

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with open(out_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"Successfully exported {len(records)} synthetic student records to: {out_file.resolve()}")


async def seed_to_database(records: list[dict], batch_size: int = 500) -> None:
    """Directly insert records into the database in batches."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.core.config import get_settings
    from app.core.security import hash_password
    from app.models.user import User
    from app.models.student_profile import StudentProfile

    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        connect_args={"server_settings": {"search_path": "campusflow, public"}},
    )
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    print(f"Seeding {len(records)} records directly into database: {settings.database_url.split('@')[-1]}...")
    default_pw_hash = hash_password("synthetic-default-password-123")

    total_inserted = 0
    async with session_factory() as session:
        for i in range(0, len(records), batch_size):
            chunk = records[i:i + batch_size]
            for r in chunk:
                user_id = uuid4()
                user = User(
                    id=user_id,
                    email=r["email"],
                    full_name=r["full_name"],
                    role="STUDENT",
                    password_hash=default_pw_hash,
                    is_active=False,
                    must_change_password=True,
                )
                session.add(user)

                profile = StudentProfile(
                    user_id=user_id,
                    roll_number=r["roll_number"],
                    branch_code=r["branch_code"],
                    batch_year=r["batch_year"],
                    cgpa=r["cgpa"],
                    active_backlogs=r["active_backlogs"],
                )
                session.add(profile)

            await session.commit()
            total_inserted += len(chunk)
            print(f"  Inserted {total_inserted}/{len(records)} records...")

    await engine.dispose()
    print(f"Successfully seeded {total_inserted} synthetic students into database.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate safe synthetic CampusFlow student records for load/stress testing."
    )
    parser.add_argument(
        "--students",
        type=int,
        default=100,
        help="Number of synthetic student records to generate (e.g. 5000). Default: 100",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="Optional CSV output file path (e.g. synthetic_students.csv).",
    )
    parser.add_argument(
        "--db",
        action="store_true",
        help="If set, directly seed records into the configured database.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible dataset generation. Default: 42",
    )

    args = parser.parse_args()

    if args.students <= 0:
        print("Error: --students must be greater than 0.")
        sys.exit(1)

    random.seed(args.seed)
    print(f"Generating {args.students} synthetic student records (seed={args.seed})...")

    records = [generate_synthetic_record(i + 1) for i in range(args.students)]

    if args.output:
        export_to_csv(records, args.output)

    if args.db:
        asyncio.run(seed_to_database(records))

    if not args.output and not args.db:
        # Default to standard CSV filename if neither is specified
        default_csv = f"synthetic_students_{args.students}.csv"
        export_to_csv(records, default_csv)


if __name__ == "__main__":
    main()
