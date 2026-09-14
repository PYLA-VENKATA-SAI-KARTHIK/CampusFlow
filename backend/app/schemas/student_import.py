"""
Schemas for Master Student List import and preview.
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class StudentMasterImportPreviewItem(BaseModel):
    row_index: int
    roll_number: str
    full_name: str | None = None
    branch_code: str | None = None
    batch_year: int | None = None
    cgpa: float | None = None
    active_backlogs: int | None = None
    personal_email: str | None = None
    phone_number: str | None = None
    gender: str | None = None
    status: str = "VALID"  # "VALID", "DUPLICATE_IN_FILE", "MISSING_REG_NO", "INVALID_DATA"
    is_existing_in_db: bool = False
    is_active_in_db: bool = False
    error_message: str | None = None


class StudentMasterImportPreviewResponse(BaseModel):
    filename: str
    detected_headers: list[str]
    detected_mappings: dict[str, str]
    total_rows: int
    valid_count: int
    duplicate_in_file_count: int
    missing_reg_no_count: int
    invalid_count: int
    existing_in_db_count: int
    can_import: bool
    preview_items: list[StudentMasterImportPreviewItem]
    valid_items: list[StudentMasterImportItem] = Field(default_factory=list)


class StudentMasterImportItem(BaseModel):
    roll_number: str = Field(..., min_length=1, max_length=50)
    full_name: str | None = Field(None, max_length=255)
    branch_code: str = Field("CSE", max_length=20)
    batch_year: int = Field(2026, ge=2000, le=2100)
    cgpa: float = Field(0.0, ge=0.0, le=10.0)
    active_backlogs: int = Field(0, ge=0, le=100)
    personal_email: str | None = Field(None, max_length=255)
    phone_number: str | None = Field(None, max_length=15)
    gender: str | None = Field(None, max_length=10)


class StudentMasterImportConfirmRequest(BaseModel):
    filename: str = "import.xlsx"
    items: list[StudentMasterImportItem]


class StudentMasterImportConfirmResponse(BaseModel):
    total_processed: int
    created_count: int
    updated_count: int
    skipped_count: int
    message: str
