"""
Student Profile service.
"""
from __future__ import annotations

from typing import Sequence
from uuid import UUID

from fastapi import HTTPException, status

from app.models.audit_log import AuditLog
from app.models.student_profile import StudentProfile
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.student_profile_repository import StudentProfileRepository
from app.schemas.student_profile import StudentProfileUpdate


class StudentProfileService:
    def __init__(
        self,
        profile_repo: StudentProfileRepository,
        audit_repo: AuditLogRepository,
    ) -> None:
        self.profile_repo = profile_repo
        self.audit_repo = audit_repo

    def _log_audit(
        self,
        user_id: UUID,
        action: str,
        entity_id: UUID,
        old_state: dict | None = None,
        new_state: dict | None = None,
    ) -> None:
        audit_log = AuditLog(
            performed_by_user_id=user_id,
            action=action,
            entity_type="STUDENT_PROFILE",
            entity_id=entity_id,
            old_state=old_state,
            new_state=new_state,
        )
        self.audit_repo.add(audit_log)

    async def get_profile_by_user_id(self, user_id: UUID | str) -> StudentProfile:
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        
        profile = await self.profile_repo.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found."
            )
        return profile

    async def get_profile_by_id(self, profile_id: UUID) -> StudentProfile:
        profile = await self.profile_repo.get_by_id(profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found."
            )
        return profile

    async def update_my_profile(
        self, user_id: UUID | str, data: StudentProfileUpdate
    ) -> StudentProfile:
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        try:
            profile = await self.get_profile_by_user_id(user_id)
            is_new = False
        except HTTPException:
            # For simplicity, if they don't have one, we could create it, but they need to provide all required fields.
            # But StudentProfileUpdate has all fields optional! So we can't safely create from an update.
            # We assume it must exist (e.g. seeded or created via another process), or we just return 404.
            # Wait, if they don't have one and try to PATCH, it's 404.
            raise

        old_state = {
            "full_name": profile.user.full_name if profile.user else None,
            "phone_number": profile.phone_number,
            "personal_email": profile.personal_email,
            "gender": profile.gender,
            "section": profile.section,
            "tenth_mark": float(profile.tenth_mark) if profile.tenth_mark is not None else None,
            "twelfth_mark": float(profile.twelfth_mark) if profile.twelfth_mark is not None else None,
            "diploma_mark": float(profile.diploma_mark) if profile.diploma_mark is not None else None,
            "portfolio_url": profile.portfolio_url,
            "cgpa": float(profile.cgpa) if profile.cgpa is not None else None,
            "branch_code": profile.branch_code,
            "active_backlogs": profile.active_backlogs,
        }

        if data.model_extra:
            forbidden_fields = {
                "roll_number", "branch_code", "batch_year", "cgpa", 
                "active_backlogs", "resume_gcs_path", "resume_uploaded_at"
            }
            if any(k in forbidden_fields for k in data.model_extra):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot modify protected academic or system fields."
                )

        # Update full_name on User model if provided
        if data.full_name is not None and data.full_name.strip() and profile.user:
            profile.user.full_name = data.full_name.strip()
            self.profile_repo.session.add(profile.user)

        # Only update fields explicitly defined in the schema (which excludes model_extra)
        update_data = data.model_dump(exclude_unset=True, exclude_none=False)
        for key, value in update_data.items():
            if key != "full_name" and hasattr(profile, key):
                setattr(profile, key, value)

        new_state = {
            "full_name": profile.user.full_name if profile.user else None,
            "phone_number": profile.phone_number,
            "personal_email": profile.personal_email,
            "gender": profile.gender,
            "section": profile.section,
            "tenth_mark": float(profile.tenth_mark) if profile.tenth_mark is not None else None,
            "twelfth_mark": float(profile.twelfth_mark) if profile.twelfth_mark is not None else None,
            "diploma_mark": float(profile.diploma_mark) if profile.diploma_mark is not None else None,
            "portfolio_url": profile.portfolio_url,
            "cgpa": float(profile.cgpa) if profile.cgpa is not None else None,
            "branch_code": profile.branch_code,
            "active_backlogs": profile.active_backlogs,
        }

        self._log_audit(
            user_id=user_id,
            action="PROFILE_UPDATED",
            entity_id=profile.id,
            old_state=old_state,
            new_state=new_state
        )

        await self.profile_repo.session.commit()
        return await self.get_profile_by_user_id(user_id)

    async def list_students(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        branch_code: str | None = None,
        batch_year: int | None = None,
        min_cgpa: float | None = None,
        search: str | None = None
    ) -> tuple[Sequence[StudentProfile], int]:
        return await self.profile_repo.list_students(
            skip=skip, 
            limit=limit, 
            branch_code=branch_code,
            batch_year=batch_year,
            min_cgpa=min_cgpa,
            search=search
        )
