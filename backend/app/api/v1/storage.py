"""
CampusFlow — Storage API Endpoints for Local Development & Mock Storage.

Provides local upload and download handlers mirroring signed object storage URLs:
- PUT /upload/{object_path}: Validates PDF magic bytes, 5MB size limit, and saves binary object.
- GET /download/{object_path}: Streams object content with correct headers and MIME types.
"""
from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.core.config import get_settings
from app.core.dependencies import get_storage_service
from app.services.storage_service import StorageService

router = APIRouter()


@router.put("/upload/{object_path:path}")
async def upload_object(
    object_path: str,
    request: Request,
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> dict:
    """
    Local storage endpoint for receiving direct binary uploads from the client.
    Validates PDF header signature and 5MB size limit.
    """
    # 1. Path traversal security check
    if ".." in object_path or object_path.startswith("/"):
        raise HTTPException(status_code=422, detail="Invalid object path.")

    # 2. Read raw binary body
    content = await request.body()
    if not content:
        raise HTTPException(status_code=422, detail="Upload body cannot be empty.")

    settings = get_settings()
    # 3. Size validation (5 MB limit)
    if len(content) > settings.resume_max_size_bytes:
        raise HTTPException(
            status_code=422,
            detail=f"Resume exceeds maximum allowed size of {settings.resume_max_size_bytes // (1024 * 1024)}MB."
        )

    # 4. File type / Magic bytes validation (PDF check)
    if object_path.endswith(".pdf"):
        if not content.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=422,
                detail="Resume must be a valid PDF document."
            )
        content_type = "application/pdf"
    else:
        content_type = request.headers.get("content-type", "application/octet-stream")

    # 5. Persist to storage abstraction
    meta = await storage.save_object(object_path=object_path, content=content, content_type=content_type)
    return {
        "status": "ok",
        "object_path": object_path,
        "size": meta.get("size", len(content)),
        "content_type": content_type,
    }


@router.get("/download/{object_path:path}")
async def download_object(
    object_path: str,
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> Response:
    """
    Local storage endpoint for downloading/viewing stored documents.
    """
    if ".." in object_path or object_path.startswith("/"):
        raise HTTPException(status_code=422, detail="Invalid object path.")

    result = await storage.get_object(object_path=object_path)
    if result is None:
        raise HTTPException(status_code=404, detail="Requested document not found in storage.")

    content, content_type = result
    filename = Path(object_path).name

    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f"inline; filename={filename}",
            "Cache-Control": "private, max-age=300",
        },
    )
