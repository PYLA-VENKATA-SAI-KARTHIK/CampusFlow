"""
JWKS endpoint for token verification by external services/micro-frontends.
"""
from fastapi import APIRouter

from app.core.security import get_jwt_manager

router = APIRouter()


@router.get("/jwks.json", tags=["System"])
async def get_jwks() -> dict:
    """
    Return the JSON Web Key Set (JWKS).
    Allows consumers to cryptographically verify JWTs issued by this service
    without needing a shared secret.
    """
    return get_jwt_manager().get_jwks()
