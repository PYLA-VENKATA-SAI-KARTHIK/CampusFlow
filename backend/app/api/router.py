"""
API Routers.
"""
from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.branches import router as branches_router
from app.api.v1.companies import router as companies_router
from app.api.v1.drives import router as drives_router
from app.api.v1.health import router as health_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.students import router as students_router
from app.api.v1.officers import router as officers_router
from app.api.v1.analytics import router as analytics_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router, prefix="/health", tags=["System"])
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(branches_router, prefix="/branches", tags=["Branches"])
api_v1_router.include_router(companies_router, prefix="/companies", tags=["Companies"])
api_v1_router.include_router(drives_router, prefix="/drives", tags=["Placement Drives"])
api_v1_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
api_v1_router.include_router(students_router, prefix="/students", tags=["Students"])
api_v1_router.include_router(officers_router, prefix="/officers", tags=["Officers"])
api_v1_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
api_v1_router.include_router(analytics_router, prefix="/admin/analytics", tags=["Analytics"])
api_v1_router.include_router(admin_router, prefix="/admin", tags=["Admin"])


