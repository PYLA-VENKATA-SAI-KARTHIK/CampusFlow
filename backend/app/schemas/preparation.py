"""
Preparation Hub Pydantic schemas.
"""
from datetime import datetime
from uuid import UUID
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PreparationRoleBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    description: str | None = None
    icon: str | None = None
    is_active: bool = True


class PreparationRoleResponse(PreparationRoleBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PreparationTopicBase(BaseModel):
    category_id: UUID
    name: str = Field(..., max_length=150)
    slug: str = Field(..., max_length=150)
    description: str | None = None


class PreparationTopicResponse(PreparationTopicBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PreparationCategoryBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    description: str | None = None
    icon: str | None = None
    sequence_order: int = 0


class PreparationCategoryResponse(PreparationCategoryBase):
    id: UUID
    created_at: datetime
    topics: list[PreparationTopicResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PreparationMaterialResponse(BaseModel):
    id: UUID
    topic_id: UUID
    role_id: UUID | None = None
    title: str
    description: str | None = None
    url: str
    material_type: str
    difficulty: str
    source: str | None = None
    status: str
    submitted_by_user_id: UUID | None = None
    reviewed_by_user_id: UUID | None = None
    review_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentSuggestMaterialRequest(BaseModel):
    topic_id: UUID
    role_id: UUID | None = None
    title: str = Field(..., min_length=3, max_length=255)
    url: str = Field(..., max_length=500)
    description: str | None = Field(None, max_length=1000)
    material_type: str = Field(default="ARTICLE")
    difficulty: str = Field(default="BEGINNER")
    source: str | None = Field(None, max_length=100)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("URL must be a valid HTTP or HTTPS address.")
        return v

    @field_validator("material_type")
    @classmethod
    def validate_material_type(cls, v: str) -> str:
        valid_types = {
            "ARTICLE", "VIDEO", "PDF", "PRACTICE_QUESTIONS",
            "DOCUMENTATION", "COURSE", "OTHER"
        }
        if v.upper() not in valid_types:
            raise ValueError(f"material_type must be one of: {', '.join(sorted(valid_types))}")
        return v.upper()

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        valid_diffs = {"BEGINNER", "INTERMEDIATE", "ADVANCED"}
        if v.upper() not in valid_diffs:
            raise ValueError(f"difficulty must be one of: {', '.join(sorted(valid_diffs))}")
        return v.upper()


class OfficerCreateMaterialRequest(StudentSuggestMaterialRequest):
    pass


class OfficerReviewSubmissionRequest(BaseModel):
    status: str = Field(..., pattern="^(APPROVED|REJECTED)$")
    review_notes: str | None = Field(None, max_length=500)


class RoleRoadmapTopicResponse(BaseModel):
    topic: PreparationTopicResponse
    importance: str
    material_count: int = 0


class RoleRoadmapResponse(BaseModel):
    role: PreparationRoleResponse
    topics: list[RoleRoadmapTopicResponse] = []
