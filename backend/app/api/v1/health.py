"""
Health check endpoints.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def health_check() -> dict[str, str]:
    """
    Basic health check endpoint.
    Must not expose DB credentials or internal state.
    """
    return {"status": "ok"}
