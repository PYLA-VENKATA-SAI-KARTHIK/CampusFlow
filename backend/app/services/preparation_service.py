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


ROLE_TOPIC_MODULES: dict[str, dict[str, tuple[str, int]]] = {
    "SYSTEM_DESIGN": {
        "high-level-system-design": ("Module 1: High-Level Architecture & Microservices", 1),
        "low-level-system-design": ("Module 1: High-Level Architecture & Microservices", 1),
        "distributed-caching-sharding": ("Module 2: Scalability, Caching & Sharding", 2),
        "cap-theorem-consistency": ("Module 2: Scalability, Caching & Sharding", 2),
        "sql-dbms": ("Module 2: Scalability, Caching & Sharding", 2),
        "message-queues-streaming": ("Module 3: Asynchronous Systems & Event Streaming", 3),
        "concurrency-multithreading": ("Module 3: Asynchronous Systems & Event Streaming", 3),
        "system-design-case-studies": ("Module 4: Real-World Case Studies & Mock Drills", 4),
        "behavioral-hr": ("Module 4: Real-World Case Studies & Mock Drills", 4),
    },
    "SOFTWARE_DEVELOPER": {
        "dsa": ("Module 1: Algorithms & Data Structures Core", 1),
        "python-programming": ("Module 1: Algorithms & Data Structures Core", 1),
        "python": ("Module 1: Algorithms & Data Structures Core", 1),
        "java": ("Module 1: Algorithms & Data Structures Core", 1),
        "operating-systems": ("Module 1: Computer Science & OS Fundamentals", 1),
        "computer-networks": ("Module 1: Computer Science & OS Fundamentals", 1),
        "sql-dbms": ("Module 2: Databases, Storage & Concurrency", 2),
        "sql": ("Module 2: Databases, Storage & Concurrency", 2),
        "dbms": ("Module 2: Databases, Storage & Concurrency", 2),
        "oop": ("Module 2: Databases, Storage & Concurrency", 2),
        "concurrency-multithreading": ("Module 2: Databases, Storage & Concurrency", 2),
        "low-level-system-design": ("Module 2: Databases, Storage & Concurrency", 2),
        "high-level-system-design": ("Module 3: Distributed Systems & Architecture", 3),
        "distributed-caching-sharding": ("Module 3: Distributed Systems & Architecture", 3),
        "quant-math": ("Module 4: Placement Drills & Behavioral", 4),
        "quantitative-aptitude": ("Module 4: Placement Drills & Behavioral", 4),
        "logical-reasoning": ("Module 4: Placement Drills & Behavioral", 4),
        "behavioral-hr": ("Module 4: Placement Drills & Behavioral", 4),
        "hr-behavioral": ("Module 4: Placement Drills & Behavioral", 4),
        "technical-interview": ("Module 4: Placement Drills & Behavioral", 4),
        "project-defense": ("Module 4: Placement Drills & Behavioral", 4),
    },
    "GENAI_ENGINEER": {
        "python-programming": ("Module 1: Python & AI Foundations", 1),
        "dsa": ("Module 1: Algorithms & Data Structures Core", 1),
        "rag-architectures": ("Module 2: Vector Databases & RAG Pipelines", 2),
        "high-level-system-design": ("Module 2: Vector Databases & RAG Pipelines", 2),
        "message-queues-streaming": ("Module 3: Production LLM Pipelines & Agents", 3),
        "distributed-caching-sharding": ("Module 3: Production LLM Pipelines & Agents", 3),
        "behavioral-hr": ("Module 4: Project Defense & Behavioral", 4),
    },
    "DEVOPS_ENGINEER": {
        "python-programming": ("Module 1: Linux & Systems Fundamentals", 1),
        "concurrency-multithreading": ("Module 1: Linux & Systems Fundamentals", 1),
        "docker-kubernetes": ("Module 2: Containers & Orchestration", 2),
        "high-level-system-design": ("Module 2: Containers & Orchestration", 2),
        "message-queues-streaming": ("Module 3: Infrastructure Scaling & Streaming", 3),
        "distributed-caching-sharding": ("Module 3: Infrastructure Scaling & Streaming", 3),
        "cap-theorem-consistency": ("Module 4: Reliability & Production Resilience", 4),
        "behavioral-hr": ("Module 4: Reliability & Production Resilience", 4),
    },
    "DATA_ENGINEER": {
        "sql-dbms": ("Module 1: SQL & Data Foundations", 1),
        "python-programming": ("Module 1: SQL & Data Foundations", 1),
        "quant-math": ("Module 1: SQL & Data Foundations", 1),
        "spark-data-pipelines": ("Module 2: Distributed Data Processing", 2),
        "distributed-caching-sharding": ("Module 2: Distributed Data Processing", 2),
        "message-queues-streaming": ("Module 3: Real-Time Event Streaming", 3),
        "high-level-system-design": ("Module 3: Real-Time Event Streaming", 3),
        "system-design-case-studies": ("Module 4: Lakehouse Design & Mock Drills", 4),
        "behavioral-hr": ("Module 4: Lakehouse Design & Mock Drills", 4),
    },
    "FULLSTACK_DEVELOPER": {
        "web-development": ("Module 1: Frontend Architecture & React", 1),
        "dsa": ("Module 1: Algorithms & Data Structures Core", 1),
        "python-programming": ("Module 2: Backend APIs & Microservices", 2),
        "sql-dbms": ("Module 2: Backend APIs & Microservices", 2),
        "low-level-system-design": ("Module 3: Low-Level Design & Patterns", 3),
        "distributed-caching-sharding": ("Module 3: Low-Level Design & Patterns", 3),
        "behavioral-hr": ("Module 4: System Integration & STAR Drills", 4),
    },
    "AI_ML_ENGINEER": {
        "python-programming": ("Module 1: Mathematical & Python Foundations", 1),
        "quant-math": ("Module 1: Mathematical & Python Foundations", 1),
        "dsa": ("Module 1: Mathematical & Python Foundations", 1),
        "sql-dbms": ("Module 2: Data Modeling & SQL Feature Stores", 2),
        "spark-data-pipelines": ("Module 2: Data Modeling & SQL Feature Stores", 2),
        "rag-architectures": ("Module 3: Deep Learning & Neural Architectures", 3),
        "high-level-system-design": ("Module 3: Deep Learning & Neural Architectures", 3),
        "behavioral-hr": ("Module 4: ML System Design & Case Studies", 4),
    },
    "QA_TEST_ENGINEER": {
        "python-programming": ("Module 1: Programming & Test Foundations", 1),
        "dsa": ("Module 1: Programming & Test Foundations", 1),
        "web-development": ("Module 2: Web APIs & End-to-End Testing", 2),
        "sql-dbms": ("Module 2: Web APIs & End-to-End Testing", 2),
        "docker-kubernetes": ("Module 3: CI/CD Test Automation Pipelines", 3),
        "concurrency-multithreading": ("Module 3: CI/CD Test Automation Pipelines", 3),
        "behavioral-hr": ("Module 4: Quality Strategy & STAR Defense", 4),
    },
}


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
        role_map = ROLE_TOPIC_MODULES.get(role.code, {})
        for rt in role.role_topics:
            count = await self.prep_repo.count_materials_for_topic(rt.topic_id)
            mod_info = role_map.get(rt.topic.slug, ("Module 1: Core Curriculum", 1))
            topics_with_counts.append(
                RoleRoadmapTopicResponse(
                    topic=rt.topic,
                    importance=rt.importance,
                    material_count=count,
                    module=mod_info[0],
                    module_order=mod_info[1],
                )
            )

        topics_with_counts.sort(key=lambda t: (t.module_order, 0 if t.importance == "CORE" else 1))
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
        refreshed = await self.prep_repo.get_material_by_id(created.id)
        return refreshed if refreshed is not None else created

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
        refreshed = await self.prep_repo.get_material_by_id(material.id)
        return refreshed if refreshed is not None else material

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
        refreshed = await self.prep_repo.get_material_by_id(created.id)
        return refreshed if refreshed is not None else created

    async def delete_material_as_officer(
        self, material_id: UUID, user_id: UUID
    ) -> None:
        material = await self.prep_repo.get_material_by_id(material_id)
        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preparation material not found.",
            )
        audit_entry = AuditLog(
            performed_by_user_id=user_id,
            action="PREPARATION_MATERIAL_DELETED",
            entity_type="PREPARATION_MATERIAL",
            entity_id=material.id,
            old_state={"title": material.title, "url": material.url},
            new_state=None,
        )
        self.audit_repo.add(audit_entry)
        await self.prep_repo.delete_material(material)
        await self.prep_repo.session.commit()

