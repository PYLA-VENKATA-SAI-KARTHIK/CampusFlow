"""
Branch management endpoints.
"""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserContext, get_current_user, get_db, require_role
from app.repositories.branch_repository import BranchRepository
from app.schemas.branch import BranchResponse

router = APIRouter()


@router.get("", response_model=list[BranchResponse])
async def list_branches(
    current_user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    include_inactive: bool = False,
) -> list[BranchResponse]:
    """List all active branches. Can include inactive branches."""
    repo = BranchRepository(session)
    # The models are automatically translated to Pydantic responses
    return list(await repo.get_all(include_inactive=include_inactive))


@router.get("/protected", dependencies=[Depends(require_role("ADMIN", "OFFICER"))])
async def test_rbac(
    current_user: Annotated[UserContext, Depends(get_current_user)],
) -> dict[str, str]:
    """Test endpoint for RBAC enforcement."""
    return {"message": f"Hello {current_user.role}, you have access."}
