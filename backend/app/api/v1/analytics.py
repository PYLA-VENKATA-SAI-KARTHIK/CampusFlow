"""
Overview Analytics endpoints for Officers and Admins.
"""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserContext, get_db, require_role
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.placement_drive_repository import PlacementDriveRepository
from app.repositories.student_profile_repository import StudentProfileRepository
from app.schemas.analytics import OverviewAnalyticsResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter()


def get_analytics_service(session: AsyncSession = Depends(get_db)) -> AnalyticsService:
    analytics_repo = AnalyticsRepository(session)
    drive_repo = PlacementDriveRepository(session)
    student_repo = StudentProfileRepository(session)
    return AnalyticsService(analytics_repo, drive_repo, student_repo)


@router.get("/overview", response_model=OverviewAnalyticsResponse, summary="Get platform overview analytics")
async def get_overview_analytics(
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> OverviewAnalyticsResponse:
    """
    Get aggregate platform-wide placement metrics, branch placement rates, and recent drive stats.
    Restricted to OFFICER and ADMIN.
    """
    return await service.get_overview_analytics()
