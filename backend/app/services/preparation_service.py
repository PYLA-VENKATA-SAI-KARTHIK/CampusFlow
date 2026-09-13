"""
Preparation Hub service.
"""
from typing import Sequence
from uuid import UUID

from fastapi import HTTPException, status

from app.models.audit_log import AuditLog
from app.models.preparation import (
    PreparationCategory,
    PreparationMaterial,
    PreparationRole,
)
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.preparation_repository import PreparationRepository
from app.schemas.preparation import (
    OfficerCreateMaterialRequest,
    OfficerReviewSubmissionRequest,
    RoleRoadmapResponse,
    RoleRoadmapTopicResponse,
    StudentSuggestMaterialRequest,
)


class PreparationService:
    def __init__(
        self,
        prep_repo: PreparationRepository,
        audit_repo: AuditLogRepository,
    ):
        self.prep_repo = prep_repo
        self.audit_repo = audit_repo

    async def get_roles(self) -> Sequence[PreparationRole]:
        return await self.prep_repo.list_roles()

    async def get_categories_with_topics(self) -> Sequence[PreparationCategory]:
        return await self.prep_repo.list_categories_with_topics()

    async def get_materials(
        self,
        category_id: UUID | None = None,
        topic_id: UUID | None = None,
        role_id: UUID | None = None,
        difficulty: str | None = None,
        material_type: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[PreparationMaterial], int]:
        return await self.prep_repo.list_materials(
            category_id=category_id,
            topic_id=topic_id,
            role_id=role_id,
            difficulty=difficulty,
            material_type=material_type,
            search=search,
            status="APPROVED",
            page=page,
            page_size=page_size,
        )

    async def get_role_roadmap(self, role_code: str) -> RoleRoadmapResponse:
        role = await self.prep_repo.get_role_by_code(role_code)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Preparation role '{role_code}' not found.",
            )

        topics_with_counts: list[RoleRoadmapTopicResponse] = []
        for rt in role.role_topics:
            count = await self.prep_repo.count_materials_for_topic(rt.topic_id)
            topics_with_counts.append(
                RoleRoadmapTopicResponse(
                    topic=rt.topic,
                    importance=rt.importance,
                    material_count=count,
                )
            )

        return RoleRoadmapResponse(role=role, topics=topics_with_counts)

    async def suggest_material(
        self, user_id: UUID, data: StudentSuggestMaterialRequest
    ) -> PreparationMaterial:
        material = PreparationMaterial(
            topic_id=data.topic_id,
            role_id=data.role_id,
            title=data.title.strip(),
            description=data.description.strip() if data.description else None,
            url=data.url.strip(),
            material_type=data.material_type,
            difficulty=data.difficulty,
            source=data.source.strip() if data.source else None,
            status="PENDING",
            submitted_by_user_id=user_id,
        )
        created = await self.prep_repo.create_material(material)
        await self.prep_repo.session.commit()
        await self.prep_repo.session.refresh(created)
        return created

    async def get_student_suggestions(
        self, user_id: UUID, page: int = 1, page_size: int = 20
    ) -> tuple[Sequence[PreparationMaterial], int]:
        return await self.prep_repo.list_student_submissions(user_id=user_id, page=page, page_size=page_size)

    async def get_pending_submissions(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[Sequence[PreparationMaterial], int]:
        return await self.prep_repo.list_pending_submissions(page=page, page_size=page_size)

    async def review_submission(
        self, material_id: UUID, reviewer_user_id: UUID, data: OfficerReviewSubmissionRequest
    ) -> PreparationMaterial:
        material = await self.prep_repo.get_material_by_id(material_id)
        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preparation material not found.",
            )

        old_state = {
            "status": material.status,
            "reviewed_by_user_id": str(material.reviewed_by_user_id) if material.reviewed_by_user_id else None,
            "review_notes": material.review_notes,
        }

        material.status = data.status
        material.reviewed_by_user_id = reviewer_user_id
        material.review_notes = data.review_notes.strip() if data.review_notes else None

        new_state = {
            "status": material.status,
            "reviewed_by_user_id": str(material.reviewed_by_user_id),
            "review_notes": material.review_notes,
        }

        audit_entry = AuditLog(
            performed_by_user_id=reviewer_user_id,
            action=f"PREPARATION_MATERIAL_{data.status}",
            entity_type="PREPARATION_MATERIAL",
            entity_id=material.id,
            old_state=old_state,
            new_state=new_state,
        )
        self.audit_repo.add(audit_entry)
        await self.prep_repo.session.commit()
        await self.prep_repo.session.refresh(material)
        return material

    async def create_material_as_officer(
        self, creator_user_id: UUID, data: OfficerCreateMaterialRequest
    ) -> PreparationMaterial:
        material = PreparationMaterial(
            topic_id=data.topic_id,
            role_id=data.role_id,
            title=data.title.strip(),
            description=data.description.strip() if data.description else None,
            url=data.url.strip(),
            material_type=data.material_type,
            difficulty=data.difficulty,
            source=data.source.strip() if data.source else None,
            status="APPROVED",
            submitted_by_user_id=creator_user_id,
            reviewed_by_user_id=creator_user_id,
        )
        created = await self.prep_repo.create_material(material)

        audit_entry = AuditLog(
            performed_by_user_id=creator_user_id,
            action="PREPARATION_MATERIAL_CREATED",
            entity_type="PREPARATION_MATERIAL",
            entity_id=created.id,
            old_state=None,
            new_state={"title": created.title, "url": created.url, "topic_id": str(created.topic_id)},
        )
        self.audit_repo.add(audit_entry)
        await self.prep_repo.session.commit()
        await self.prep_repo.session.refresh(created)
        return created
