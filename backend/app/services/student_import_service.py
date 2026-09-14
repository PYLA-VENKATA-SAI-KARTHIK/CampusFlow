"""
Student Master List Import Service.
"""
from __future__ import annotations

import re
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.branch import Branch
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.student_import import (
    StudentMasterImportConfirmRequest,
    StudentMasterImportConfirmResponse,
    StudentMasterImportItem,
    StudentMasterImportPreviewItem,
    StudentMasterImportPreviewResponse,
)
from app.utils.excel_importer import (
    detect_column_mappings,
    normalize_cell_as_string,
    parse_tabular_file,
)


class StudentImportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def preview_student_import(
        self,
        file_bytes: bytes,
        filename: str,
        custom_mapping: dict[str, str] | None = None,
    ) -> StudentMasterImportPreviewResponse:
        """
        Parses Excel/CSV bytes, applies column normalization, validates rows against DB,
        and returns preview breakdown without modifying the database.
        """
        headers, raw_rows = parse_tabular_file(file_bytes, filename)
        
        detected_mappings = detect_column_mappings(headers)
        if custom_mapping:
            detected_mappings.update(custom_mapping)

        reg_col = detected_mappings.get("roll_number")
        name_col = detected_mappings.get("full_name")
        branch_col = detected_mappings.get("branch_code")
        batch_col = detected_mappings.get("batch_year")
        cgpa_col = detected_mappings.get("cgpa")
        backlogs_col = detected_mappings.get("active_backlogs")
        email_col = detected_mappings.get("personal_email")
        phone_col = detected_mappings.get("phone_number")
        gender_col = detected_mappings.get("gender")

        if not reg_col:
            return StudentMasterImportPreviewResponse(
                filename=filename,
                detected_headers=headers,
                detected_mappings=detected_mappings,
                total_rows=len(raw_rows),
                valid_count=0,
                duplicate_in_file_count=0,
                missing_reg_no_count=len(raw_rows),
                invalid_count=len(raw_rows),
                existing_in_db_count=0,
                can_import=False,
                preview_items=[],
            )

        # Pre-fetch existing roll numbers and branches from DB
        stmt_profiles = select(StudentProfile.roll_number, User.is_active).join(User, StudentProfile.user_id == User.id)
        db_profiles = (await self.session.execute(stmt_profiles)).all()
        existing_db_map = {row[0].strip().lower(): row[1] for row in db_profiles}

        stmt_branches = select(Branch.code)
        db_branches = (await self.session.execute(stmt_branches)).scalars().all()
        existing_branches = {b.strip().upper() for b in db_branches}

        seen_in_file: set[str] = set()
        preview_items: list[StudentMasterImportPreviewItem] = []

        valid_count = 0
        dup_count = 0
        missing_count = 0
        invalid_count = 0
        existing_in_db_count = 0

        for idx, row in enumerate(raw_rows, start=1):
            raw_reg = row.get(reg_col, "")
            clean_reg = normalize_cell_as_string(raw_reg).strip()

            raw_name = normalize_cell_as_string(row.get(name_col, "")).strip() if name_col else None
            raw_branch = normalize_cell_as_string(row.get(branch_col, "CSE")).strip().upper() if branch_col else "CSE"
            if not raw_branch:
                raw_branch = "CSE"

            raw_batch_str = normalize_cell_as_string(row.get(batch_col, "2026")).strip() if batch_col else "2026"
            try:
                raw_batch = int(float(raw_batch_str)) if raw_batch_str else 2026
            except ValueError:
                raw_batch = 2026

            raw_cgpa_str = normalize_cell_as_string(row.get(cgpa_col, "0.0")).strip() if cgpa_col else "0.0"
            try:
                raw_cgpa = float(raw_cgpa_str) if raw_cgpa_str else 0.0
                if raw_cgpa > 10.0 and raw_cgpa <= 100.0:
                    raw_cgpa = round(raw_cgpa / 10.0, 2)  # Convert percentage to 10-point scale
                raw_cgpa = max(0.0, min(10.0, raw_cgpa))
            except ValueError:
                raw_cgpa = 0.0

            raw_backlogs_str = normalize_cell_as_string(row.get(backlogs_col, "0")).strip() if backlogs_col else "0"
            try:
                raw_backlogs = int(float(raw_backlogs_str)) if raw_backlogs_str else 0
            except ValueError:
                raw_backlogs = 0

            raw_email = normalize_cell_as_string(row.get(email_col, "")).strip() if email_col else None
            raw_phone = normalize_cell_as_string(row.get(phone_col, "")).strip() if phone_col else None
            raw_gender = normalize_cell_as_string(row.get(gender_col, "")).strip().upper() if gender_col else None
            if raw_gender and raw_gender not in ["MALE", "FEMALE", "OTHER"]:
                if raw_gender.startswith("M"):
                    raw_gender = "MALE"
                elif raw_gender.startswith("F"):
                    raw_gender = "FEMALE"
                else:
                    raw_gender = "OTHER"

            # Validation logic
            status = "VALID"
            error_message = None

            if not clean_reg:
                status = "MISSING_REG_NO"
                error_message = "Registration number is missing or empty"
                missing_count += 1
                invalid_count += 1
            elif clean_reg.lower() in seen_in_file:
                status = "DUPLICATE_IN_FILE"
                error_message = f"Duplicate registration number in file: {clean_reg}"
                dup_count += 1
                invalid_count += 1
            else:
                seen_in_file.add(clean_reg.lower())
                valid_count += 1

            is_in_db = clean_reg.lower() in existing_db_map
            is_active = existing_db_map.get(clean_reg.lower(), False)
            if is_in_db:
                existing_in_db_count += 1

            item = StudentMasterImportPreviewItem(
                row_index=idx,
                roll_number=clean_reg,
                full_name=raw_name,
                branch_code=raw_branch,
                batch_year=raw_batch,
                cgpa=raw_cgpa,
                active_backlogs=raw_backlogs,
                personal_email=raw_email,
                phone_number=raw_phone,
                gender=raw_gender,
                status=status,
                is_existing_in_db=is_in_db,
                is_active_in_db=is_active,
                error_message=error_message,
            )
            preview_items.append(item)

        return StudentMasterImportPreviewResponse(
            filename=filename,
            detected_headers=headers,
            detected_mappings=detected_mappings,
            total_rows=len(raw_rows),
            valid_count=valid_count,
            duplicate_in_file_count=dup_count,
            missing_reg_no_count=missing_count,
            invalid_count=invalid_count,
            existing_in_db_count=existing_in_db_count,
            can_import=valid_count > 0,
            preview_items=preview_items[:100],  # Return first 100 preview rows
        )

    async def confirm_student_import(
        self,
        request: StudentMasterImportConfirmRequest,
        current_user_id: UUID,
    ) -> StudentMasterImportConfirmResponse:
        """
        Safely and idempotently creates or updates master student records in database.
        Never creates duplicate User accounts.
        """
        # 1. Pre-fetch existing branches and insert missing branches dynamically
        stmt_branches = select(Branch)
        branches = (await self.session.execute(stmt_branches)).scalars().all()
        branch_map = {b.code.upper(): b for b in branches}

        for item in request.items:
            clean_b = (item.branch_code or "CSE").strip().upper()
            if clean_b and clean_b not in branch_map:
                new_branch = Branch(code=clean_b, name=clean_b, is_active=True)
                self.session.add(new_branch)
                branch_map[clean_b] = new_branch

        await self.session.flush()

        created_count = 0
        updated_count = 0
        skipped_count = 0

        # Process each valid student record
        for item in request.items:
            clean_reg = normalize_cell_as_string(item.roll_number).strip()
            if not clean_reg:
                skipped_count += 1
                continue

            clean_branch = (item.branch_code or "CSE").strip().upper()
            if clean_branch not in branch_map:
                clean_branch = "CSE"

            # Check if StudentProfile already exists
            stmt_profile = (
                select(StudentProfile)
                .options(selectinload(StudentProfile.user))
                .where(func.lower(StudentProfile.roll_number) == clean_reg.lower())
            )
            existing_profile = (await self.session.execute(stmt_profile)).scalar_one_or_none()

            if existing_profile:
                # Update existing profile master data
                existing_profile.branch_code = clean_branch
                if item.batch_year:
                    existing_profile.batch_year = item.batch_year
                if item.cgpa is not None:
                    existing_profile.cgpa = item.cgpa
                if item.active_backlogs is not None:
                    existing_profile.active_backlogs = item.active_backlogs
                if item.phone_number:
                    existing_profile.phone_number = item.phone_number
                if item.gender:
                    existing_profile.gender = item.gender

                # If student full_name is unassigned or placeholder, update user.full_name
                if item.full_name and existing_profile.user:
                    if (
                        not existing_profile.user.full_name
                        or existing_profile.user.full_name.lower().startswith("student")
                        or not existing_profile.user.is_active
                    ):
                        existing_profile.user.full_name = item.full_name

                updated_count += 1
            else:
                # Check if User already exists with university email
                univ_email = f"{clean_reg}@klu.ac.in"
                stmt_user = select(User).where(func.lower(User.email) == univ_email.lower())
                existing_user = (await self.session.execute(stmt_user)).scalar_one_or_none()

                if not existing_user:
                    # Create inactive User record for pre-provisioned student
                    user = User(
                        id=uuid4(),
                        email=univ_email,
                        password_hash=hash_password(str(uuid4())),  # Random hashed placeholder until student self-registers
                        role="STUDENT",
                        full_name=item.full_name or f"Student {clean_reg}",
                        is_active=False,
                    )
                    self.session.add(user)
                    await self.session.flush()
                else:
                    user = existing_user

                # Create new StudentProfile
                new_profile = StudentProfile(
                    id=uuid4(),
                    user_id=user.id,
                    roll_number=clean_reg,
                    branch_code=clean_branch,
                    batch_year=item.batch_year or 2026,
                    cgpa=item.cgpa if item.cgpa is not None else 0.0,
                    active_backlogs=item.active_backlogs if item.active_backlogs is not None else 0,
                    phone_number=item.phone_number,
                    personal_email=item.personal_email,
                    gender=item.gender,
                )
                self.session.add(new_profile)
                created_count += 1

        # Audit log entry
        audit_log = AuditLog(
            performed_by_user_id=current_user_id,
            action="STUDENT_MASTER_IMPORT_CONFIRMED",
            entity_type="StudentProfile",
            new_state={
                "filename": request.filename,
                "created_count": created_count,
                "updated_count": updated_count,
                "skipped_count": skipped_count,
                "total_processed": len(request.items),
            },
        )
        self.session.add(audit_log)

        await self.session.commit()

        return StudentMasterImportConfirmResponse(
            total_processed=len(request.items),
            created_count=created_count,
            updated_count=updated_count,
            skipped_count=skipped_count,
            message=f"Successfully processed {len(request.items)} students: {created_count} created, {updated_count} updated.",
        )
