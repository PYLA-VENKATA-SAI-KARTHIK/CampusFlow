"""
Admin and Officer API endpoints for Master Student List Import.
"""
import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserContext, get_db, require_role
from app.schemas.student_import import (
    StudentMasterImportConfirmRequest,
    StudentMasterImportConfirmResponse,
    StudentMasterImportPreviewResponse,
)
from app.services.student_import_service import StudentImportService

router = APIRouter(prefix="/admin/students/import", tags=["Student Master Import"])


def get_student_import_service(session: AsyncSession = Depends(get_db)) -> StudentImportService:
    return StudentImportService(session)


@router.post("/preview", response_model=StudentMasterImportPreviewResponse)
async def preview_student_import(
    file: UploadFile = File(...),
    custom_mapping: str | None = Form(None),
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))] = None,
    service: Annotated[StudentImportService, Depends(get_student_import_service)] = None,
) -> StudentMasterImportPreviewResponse:
    """
    Preview a Master Student List Excel (.xlsx) or CSV (.csv) file.
    Detects headers, validates registration numbers as strings, and returns validation counts.
    Restricted to OFFICER and ADMIN.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File must have a valid filename.",
        )

    ext = file.filename.lower().split(".")[-1]
    if ext not in ["xlsx", "xlsm", "csv"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported file format. Please upload an Excel (.xlsx) or CSV (.csv) file.",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty.",
        )

    parsed_mapping: dict[str, str] | None = None
    if custom_mapping:
        try:
            parsed_mapping = json.loads(custom_mapping)
        except Exception:
            pass

    try:
        return await service.preview_student_import(
            file_bytes=file_bytes,
            filename=file.filename,
            custom_mapping=parsed_mapping,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to process file: {str(e)}",
        )


@router.post("/confirm", response_model=StudentMasterImportConfirmResponse)
async def confirm_student_import(
    request: StudentMasterImportConfirmRequest,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))] = None,
    service: Annotated[StudentImportService, Depends(get_student_import_service)] = None,
) -> StudentMasterImportConfirmResponse:
    """
    Confirm and commit Master Student List into CampusFlow database.
    Creates or updates pre-provisioned student records idempotently without duplicate users.
    Restricted to OFFICER and ADMIN.
    """
    if not request.items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No student items provided to import.",
        )

    return await service.confirm_student_import(
        request=request,
        current_user_id=current_user.user_id,
    )
