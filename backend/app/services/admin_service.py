"""
Admin Service — User management, bulk student import, audit log listing.

Security invariants enforced in this service:
  - Admin cannot deactivate their own account
  - Admin cannot demote/deactivate the LAST remaining active ADMIN
  - On deactivation: revoke all refresh tokens for that user
  - Never expose: password_hash, raw passwords, token hashes, secrets
  - Bulk import: partial-success — valid rows succeed, invalid rows produce per-row errors
  - Audit log old_state/new_state: secrets stripped before persistence
"""
from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.email import EmailService, ActivationEmailData
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.security import generate_secure_token, hash_password, hash_token
from app.models.account_activation import AccountActivation
from app.models.audit_log import AuditLog
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.branch_repository import BranchRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin import (
    AdminAuditLogListParams,
    AdminAuditLogResponse,
    AdminCreateUserRequest,
    AdminUpdateUserRequest,
    AdminUserListParams,
    AdminUserResponse,
    BulkImportResponse,
    BulkImportRowError,
)
from app.schemas.common import PaginatedResponse

logger = logging.getLogger(__name__)

# Fields that MUST NEVER appear in audit log state snapshots
_SENSITIVE_FIELDS = frozenset({
    "password_hash", "password", "token_hash", "activation_token",
    "raw_token", "secret", "api_key",
})


def _safe_state(data: dict) -> dict:
    """Strip sensitive fields from audit log state snapshots."""
    return {k: v for k, v in data.items() if k not in _SENSITIVE_FIELDS}


class AdminService:
    def __init__(
        self,
        session: AsyncSession,
        email_service: EmailService,
    ) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.audit_repo = AuditLogRepository(session)
        self.auth_repo = AuthRepository(session)
        self.branch_repo = BranchRepository(session)
        self.email_service = email_service
        self.settings = get_settings()

    # -------------------------------------------------------------------------
    # List Users
    # -------------------------------------------------------------------------

    async def list_users(
        self, params: AdminUserListParams
    ) -> PaginatedResponse[AdminUserResponse]:
        skip = (params.page - 1) * params.page_size
        users, total = await self.user_repo.list_users(
            skip=skip,
            limit=params.page_size,
            role=params.role,
            is_active=params.is_active,
            search=params.search,
        )
        items = [AdminUserResponse.model_validate(u) for u in users]
        return PaginatedResponse(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            has_next=(skip + params.page_size) < total,
        )

    # -------------------------------------------------------------------------
    # Create User (OFFICER or ADMIN only)
    # -------------------------------------------------------------------------

    async def create_user(
        self,
        data: AdminCreateUserRequest,
        performed_by_user_id: str,
        ip_address: str | None = None,
    ) -> AdminUserResponse:
        # Check duplicate email
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ConflictError(f"A user with email {data.email} already exists.")

        user = User(
            email=data.email.lower(),
            full_name=data.full_name,
            role=data.role,
            password_hash=hash_password(data.password),
            is_active=True,
            must_change_password=True,
        )
        self.user_repo.add(user)
        await self.session.flush()

        # Audit log — USER_CREATED
        self.audit_repo.add(AuditLog(
            performed_by_user_id=UUID(performed_by_user_id),
            action="USER_CREATED",
            entity_type="USER",
            entity_id=user.id,
            new_state=_safe_state({
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
            }),
            ip_address=ip_address,
        ))

        await self.session.commit()
        await self.session.refresh(user)

        return AdminUserResponse.model_validate(user)

    # -------------------------------------------------------------------------
    # Update User (role, is_active, full_name)
    # -------------------------------------------------------------------------

    async def update_user(
        self,
        user_id: UUID,
        data: AdminUpdateUserRequest,
        performed_by_user_id: str,
        ip_address: str | None = None,
    ) -> AdminUserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found.")

        old_state = _safe_state({
            "role": user.role,
            "is_active": user.is_active,
            "full_name": user.full_name,
        })

        # --- Security invariant: self-deactivation prevention ---
        if str(user_id) == performed_by_user_id and data.is_active is False:
            raise BadRequestError("Admin cannot deactivate their own account.")

        # --- Security invariant: last-admin protection ---
        is_demoting_admin = (
            user.role == "ADMIN"
            and data.role is not None
            and data.role != "ADMIN"
        )
        is_deactivating_admin = (
            user.role == "ADMIN"
            and user.is_active is True
            and data.is_active is False
        )

        if is_demoting_admin or is_deactivating_admin:
            active_admin_count = await self.user_repo.count_active_admins()
            if active_admin_count <= 1:
                raise BadRequestError(
                    "Cannot demote or deactivate the last remaining active admin."
                )

        # Apply updates
        if data.role is not None:
            user.role = data.role
        if data.is_active is not None:
            user.is_active = data.is_active
        if data.full_name is not None:
            user.full_name = data.full_name

        self.session.add(user)

        # --- Security invariant: revoke tokens on deactivation ---
        if data.is_active is False:
            await self.auth_repo.revoke_all_for_user(user_id)

        # Audit log — USER_UPDATED
        new_state = _safe_state({
            "role": user.role,
            "is_active": user.is_active,
            "full_name": user.full_name,
        })
        self.audit_repo.add(AuditLog(
            performed_by_user_id=UUID(performed_by_user_id),
            action="USER_UPDATED",
            entity_type="USER",
            entity_id=user.id,
            old_state=old_state,
            new_state=new_state,
            ip_address=ip_address,
        ))

        await self.session.commit()
        await self.session.refresh(user)

        return AdminUserResponse.model_validate(user)

    # -------------------------------------------------------------------------
    # Bulk Import Students (partial-success)
    # -------------------------------------------------------------------------

    async def bulk_import_students(
        self,
        csv_content: str,
        performed_by_user_id: str,
        ip_address: str | None = None,
    ) -> BulkImportResponse:
        """
        Parse CSV and import students. Partial-success model:
        each valid row succeeds independently; invalid rows produce per-row errors.

        CSV columns: email, full_name, roll_number, branch_code, batch_year, cgpa, active_backlogs
        """
        errors: list[BulkImportRowError] = []
        success_count = 0

        # Pre-load all valid branch codes in a single query
        all_branches = await self.branch_repo.get_all(include_inactive=False)
        valid_branch_codes = {b.code.upper() for b in all_branches}

        # Parse CSV
        try:
            reader = csv.DictReader(io.StringIO(csv_content))
        except Exception:
            raise BadRequestError("Invalid CSV format.")

        required_fields = {"email", "full_name", "roll_number", "branch_code", "batch_year", "cgpa", "active_backlogs"}

        rows = list(reader)
        total_rows = len(rows)

        if total_rows == 0:
            raise BadRequestError("CSV file is empty.")

        # Validate CSV headers
        if reader.fieldnames:
            missing_headers = required_fields - set(reader.fieldnames)
            if missing_headers:
                raise BadRequestError(
                    f"CSV missing required columns: {', '.join(sorted(missing_headers))}"
                )

        # Pre-load existing emails and roll numbers for duplicate checking (batch)
        existing_emails: set[str] = set()
        existing_rolls: set[str] = set()
        for row in rows:
            email = row.get("email", "").strip().lower()
            if email:
                existing_user = await self.user_repo.get_by_email(email)
                if existing_user:
                    existing_emails.add(email)
            roll = row.get("roll_number", "").strip()
            if roll:
                from sqlalchemy import select
                from app.models.student_profile import StudentProfile as SP
                stmt = select(SP.roll_number).where(SP.roll_number == roll)
                result = await self.session.execute(stmt)
                if result.scalar_one_or_none():
                    existing_rolls.add(roll)

        seen_emails: set[str] = set()
        seen_rolls: set[str] = set()

        for row_num, row in enumerate(rows, start=2):  # row 1 is header
            try:
                email = row.get("email", "").strip().lower()
                full_name = row.get("full_name", "").strip()
                roll_number = row.get("roll_number", "").strip()
                branch_code = row.get("branch_code", "").strip().upper()
                batch_year_str = row.get("batch_year", "").strip()
                cgpa_str = row.get("cgpa", "").strip()
                backlogs_str = row.get("active_backlogs", "").strip()

                # Required field validation
                if not email:
                    errors.append(BulkImportRowError(row_number=row_num, error="email is required"))
                    continue
                if not full_name:
                    errors.append(BulkImportRowError(row_number=row_num, error="full_name is required"))
                    continue
                if not roll_number:
                    errors.append(BulkImportRowError(row_number=row_num, error="roll_number is required"))
                    continue
                if not branch_code:
                    errors.append(BulkImportRowError(row_number=row_num, error="branch_code is required"))
                    continue

                # Type validation
                try:
                    batch_year = int(batch_year_str)
                except (ValueError, TypeError):
                    errors.append(BulkImportRowError(row_number=row_num, error="batch_year must be an integer"))
                    continue

                try:
                    cgpa = float(cgpa_str)
                except (ValueError, TypeError):
                    errors.append(BulkImportRowError(row_number=row_num, error="cgpa must be a number"))
                    continue

                try:
                    active_backlogs = int(backlogs_str)
                except (ValueError, TypeError):
                    errors.append(BulkImportRowError(row_number=row_num, error="active_backlogs must be an integer"))
                    continue

                # Branch validation
                if branch_code not in valid_branch_codes:
                    errors.append(BulkImportRowError(
                        row_number=row_num,
                        error=f"Invalid branch_code: {branch_code}",
                    ))
                    continue

                # Duplicate checks (within CSV)
                if email in seen_emails:
                    errors.append(BulkImportRowError(row_number=row_num, error=f"Duplicate email in CSV: {email}"))
                    continue
                if roll_number in seen_rolls:
                    errors.append(BulkImportRowError(row_number=row_num, error=f"Duplicate roll_number in CSV: {roll_number}"))
                    continue

                # Duplicate checks (against existing DB)
                if email in existing_emails:
                    errors.append(BulkImportRowError(row_number=row_num, error=f"Email already exists: {email}"))
                    continue
                if roll_number in existing_rolls:
                    errors.append(BulkImportRowError(row_number=row_num, error=f"Roll number already exists: {roll_number}"))
                    continue

                # --- Create User ---
                temp_password_hash = hash_password("temporary-placeholder")
                user = User(
                    email=email,
                    full_name=full_name,
                    role="STUDENT",
                    password_hash=temp_password_hash,
                    is_active=False,
                    must_change_password=True,
                )
                self.session.add(user)
                await self.session.flush()

                # --- Create StudentProfile ---
                profile = StudentProfile(
                    user_id=user.id,
                    roll_number=roll_number,
                    branch_code=branch_code,
                    batch_year=batch_year,
                    cgpa=cgpa,
                    active_backlogs=active_backlogs,
                )
                self.session.add(profile)

                # --- Create AccountActivation ---
                raw_token = generate_secure_token()
                activation = AccountActivation(
                    user_id=user.id,
                    token_hash=hash_token(raw_token),
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
                )
                self.session.add(activation)

                # --- Send activation email (best-effort) ---
                activation_url = f"{self.settings.frontend_base_url}/activate?token={raw_token}"
                try:
                    await self.email_service.send_activation_email(
                        ActivationEmailData(
                            recipient_email=email,
                            recipient_name=full_name,
                            activation_url=activation_url,
                        )
                    )
                except Exception:
                    # Email failure should not block import
                    logger.warning(
                        "Failed to send activation email for row %d (email delivery error)",
                        row_num,
                    )

                seen_emails.add(email)
                seen_rolls.add(roll_number)
                success_count += 1

            except Exception as exc:
                logger.error("Bulk import error at row %d: %s", row_num, type(exc).__name__)
                errors.append(BulkImportRowError(
                    row_number=row_num,
                    error="Internal processing error",
                ))

        # Audit log — BULK_IMPORT_COMPLETED (never includes sensitive data)
        self.audit_repo.add(AuditLog(
            performed_by_user_id=UUID(performed_by_user_id),
            action="BULK_IMPORT_COMPLETED",
            entity_type="STUDENT_IMPORT",
            new_state={
                "total_rows": total_rows,
                "success_count": success_count,
                "error_count": len(errors),
            },
            ip_address=ip_address,
        ))

        await self.session.commit()

        return BulkImportResponse(
            total_rows=total_rows,
            success_count=success_count,
            error_count=len(errors),
            errors=errors,
        )

    # -------------------------------------------------------------------------
    # List Audit Logs
    # -------------------------------------------------------------------------

    async def list_audit_logs(
        self, params: AdminAuditLogListParams
    ) -> PaginatedResponse[AdminAuditLogResponse]:
        skip = (params.page - 1) * params.page_size
        logs, total = await self.audit_repo.list_audit_logs(
            skip=skip,
            limit=params.page_size,
            user_id=params.user_id,
            entity_type=params.entity_type,
            action=params.action,
            start_date=params.start_date,
            end_date=params.end_date,
        )
        items = [AdminAuditLogResponse.model_validate(log) for log in logs]
        return PaginatedResponse(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            has_next=(skip + params.page_size) < total,
        )
