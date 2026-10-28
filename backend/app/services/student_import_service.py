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
    normalize_backlogs,
    normalize_batch_year,
    normalize_branch_code,
    normalize_cell_as_string,
    normalize_cgpa,
    normalize_gender,
    normalize_personal_email,
    normalize_phone_number,
    parse_tabular_file,
)

CHUNK_SIZE = 500


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
                valid_items=[],
            )

        # Pre-fetch existing roll numbers from DB
        stmt_profiles = select(StudentProfile.roll_number, User.is_active).join(User, StudentProfile.user_id == User.id)
        db_profiles = (await self.session.execute(stmt_profiles)).all()
        existing_db_map = {row[0].strip().lower(): bool(row[1]) for row in db_profiles if row[0]}

        seen_in_file: set[str] = set()
        preview_items: list[StudentMasterImportPreviewItem] = []
        valid_items: list[StudentMasterImportItem] = []

        valid_count = 0
        dup_count = 0
        missing_count = 0
        invalid_count = 0
        existing_in_db_count = 0

        for idx, row in enumerate(raw_rows, start=1):
            raw_reg = row.get(reg_col, "")
            clean_reg = normalize_cell_as_string(raw_reg).strip()

            raw_name = normalize_cell_as_string(row.get(name_col, "")).strip()[:255] if name_col else None
            if not raw_name:
                raw_name = None

            raw_branch = normalize_branch_code(row.get(branch_col)) if branch_col else "CSE"
            raw_batch = normalize_batch_year(row.get(batch_col)) if batch_col else 2026
            raw_cgpa = normalize_cgpa(row.get(cgpa_col)) if cgpa_col else 0.0
            raw_backlogs = normalize_backlogs(row.get(backlogs_col)) if backlogs_col else 0
            raw_email = normalize_personal_email(row.get(email_col)) if email_col else None
            raw_phone = normalize_phone_number(row.get(phone_col)) if phone_col else None
            raw_gender = normalize_gender(row.get(gender_col)) if gender_col else None

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
                valid_items.append(
                    StudentMasterImportItem(
                        roll_number=clean_reg,
                        full_name=raw_name,
                        branch_code=raw_branch,
                        batch_year=raw_batch,
                        cgpa=raw_cgpa,
                        active_backlogs=raw_backlogs,
                        personal_email=raw_email,
                        phone_number=raw_phone,
                        gender=raw_gender,
                    )
                )

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
            preview_items=preview_items[:100],  # Return first 100 preview rows for UI display
            valid_items=valid_items,  # Return ALL valid items for confirmation
        )

    async def confirm_student_import(
        self,
        request: StudentMasterImportConfirmRequest,
        current_user_id: UUID,
    ) -> StudentMasterImportConfirmResponse:
        """
        Safely, idempotently, and rapidly creates or updates master student records in database.
        Uses batch chunked lookups and single-pass placeholder password generation to process
        thousands of records in milliseconds without duplicate user constraints or event-loop freezing.
        """
        # 1. Clean and deduplicate request items by roll_number (last entry wins)
        valid_items_map: dict[str, StudentMasterImportItem] = {}
        for item in request.items:
            clean_reg = normalize_cell_as_string(item.roll_number).strip()
            if clean_reg:
                valid_items_map[clean_reg.lower()] = item

        skipped_count = len(request.items) - len(valid_items_map)
        if not valid_items_map:
            return StudentMasterImportConfirmResponse(
                total_processed=len(request.items),
                created_count=0,
                updated_count=0,
                skipped_count=skipped_count,
                message="No valid student rows to import.",
            )

        # 2. Pre-fetch existing branches and insert missing branches dynamically
        stmt_branches = select(Branch)
        branches = (await self.session.execute(stmt_branches)).scalars().all()
        branch_map = {b.code.upper(): b for b in branches}

        for item in valid_items_map.values():
            clean_b = normalize_branch_code(item.branch_code)
            if clean_b and clean_b not in branch_map:
                new_branch = Branch(code=clean_b, name=clean_b, is_active=True)
                self.session.add(new_branch)
                branch_map[clean_b] = new_branch

        await self.session.flush()

        # 3. Chunked lookups for existing StudentProfiles
        reg_lowers = list(valid_items_map.keys())
        profile_map: dict[str, StudentProfile] = {}
        user_id_to_profile: dict[UUID, StudentProfile] = {}

        for i in range(0, len(reg_lowers), CHUNK_SIZE):
            chunk = reg_lowers[i : i + CHUNK_SIZE]
            stmt_profiles = (
                select(StudentProfile)
                .options(selectinload(StudentProfile.user))
                .where(func.lower(StudentProfile.roll_number).in_(chunk))
            )
            for prof in (await self.session.execute(stmt_profiles)).scalars().all():
                if prof.roll_number:
                    profile_map[prof.roll_number.strip().lower()] = prof
                    if prof.user_id:
                        user_id_to_profile[prof.user_id] = prof

        # 4. Chunked lookups for existing Users by university email
        univ_emails = [f"{reg}@klu.ac.in".lower() for reg in reg_lowers]
        user_by_email_map: dict[str, User] = {}

        for i in range(0, len(univ_emails), CHUNK_SIZE):
            chunk = univ_emails[i : i + CHUNK_SIZE]
            stmt_users = select(User).where(func.lower(User.email).in_(chunk))
            for u in (await self.session.execute(stmt_users)).scalars().all():
                if u.email:
                    user_by_email_map[u.email.strip().lower()] = u

        # 5. Pre-compute placeholder hash once for unactivated student accounts
        placeholder_hash = hash_password("campusflow_unactivated_placeholder")

        created_count = 0
        updated_count = 0

        # 6. Fast in-memory resolution and staging
        for reg_lower, item in valid_items_map.items():
            clean_reg = normalize_cell_as_string(item.roll_number).strip()
            clean_branch = normalize_branch_code(item.branch_code)
            clean_batch = normalize_batch_year(item.batch_year)
            clean_cgpa = normalize_cgpa(item.cgpa)
            clean_backlogs = normalize_backlogs(item.active_backlogs)
            clean_phone = normalize_phone_number(item.phone_number)
            clean_email = normalize_personal_email(item.personal_email)
            clean_gender = normalize_gender(item.gender)
            clean_name = item.full_name.strip()[:255] if item.full_name and item.full_name.strip() else None

            existing_profile = profile_map.get(reg_lower)
            if existing_profile:
                # Update existing profile master data
                existing_profile.branch_code = clean_branch
                existing_profile.batch_year = clean_batch
                existing_profile.cgpa = clean_cgpa
                existing_profile.active_backlogs = clean_backlogs
                if clean_phone:
                    existing_profile.phone_number = clean_phone
                if clean_email:
                    existing_profile.personal_email = clean_email
                if clean_gender:
                    existing_profile.gender = clean_gender

                # Update full_name on associated user if placeholder or missing
                if clean_name and existing_profile.user:
                    if (
                        not existing_profile.user.full_name
                        or existing_profile.user.full_name.lower().startswith("student")
                        or not existing_profile.user.is_active
                    ):
                        existing_profile.user.full_name = clean_name

                updated_count += 1
            else:
                univ_email = f"{clean_reg.lower()}@klu.ac.in"
                email_lower = univ_email.lower()
                user = user_by_email_map.get(email_lower)

                if user:
                    # User exists in DB
                    linked_profile = user_id_to_profile.get(user.id)
                    if linked_profile:
                        # Existing profile attached to this user; update roll_number & fields
                        linked_profile.roll_number = clean_reg
                        linked_profile.branch_code = clean_branch
                        linked_profile.batch_year = clean_batch
                        linked_profile.cgpa = clean_cgpa
                        linked_profile.active_backlogs = clean_backlogs
                        if clean_phone:
                            linked_profile.phone_number = clean_phone
                        if clean_email:
                            linked_profile.personal_email = clean_email
                        if clean_gender:
                            linked_profile.gender = clean_gender
                        if clean_name and (not user.full_name or user.full_name.lower().startswith("student")):
                            user.full_name = clean_name
                        profile_map[reg_lower] = linked_profile
                        updated_count += 1
                        continue

                else:
                    # Create inactive User record for pre-provisioned student
                    user = User(
                        id=uuid4(),
                        email=univ_email,
                        password_hash=placeholder_hash,
                        role="STUDENT",
                        full_name=clean_name or f"Student {clean_reg}",
                        is_active=False,
                    )
                    self.session.add(user)
                    user_by_email_map[email_lower] = user

                # Create new StudentProfile
                new_profile = StudentProfile(
                    id=uuid4(),
                    user_id=user.id,
                    roll_number=clean_reg,
                    branch_code=clean_branch,
                    batch_year=clean_batch,
                    cgpa=clean_cgpa,
                    active_backlogs=clean_backlogs,
                    phone_number=clean_phone,
                    personal_email=clean_email,
                    gender=clean_gender,
                )
                self.session.add(new_profile)
                profile_map[reg_lower] = new_profile
                user_id_to_profile[user.id] = new_profile
                created_count += 1

        # 7. Audit log entry
        audit_log = AuditLog(
            id=uuid4(),
            performed_by_user_id=current_user_id,
            action="STUDENT_MASTER_IMPORT_CONFIRMED",
            entity_type="StudentProfile",
            new_state={
                "filename": request.filename,
                "created_count": created_count,
                "updated_count": updated_count,
                "skipped_count": skipped_count,
                "total_processed": len(valid_items_map),
            },
        )
        self.session.add(audit_log)

        await self.session.commit()

        return StudentMasterImportConfirmResponse(
            total_processed=len(valid_items_map),
            created_count=created_count,
            updated_count=updated_count,
            skipped_count=skipped_count,
            message=f"Successfully processed {len(valid_items_map)} students: {created_count} created, {updated_count} updated.",
        )
