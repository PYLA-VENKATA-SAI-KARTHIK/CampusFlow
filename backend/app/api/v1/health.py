"""
Health check and diagnostic endpoints.
"""
from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


@router.get("")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "ok"}


@router.get("/smtp")
async def smtp_diagnostic() -> dict:
    """
    Diagnostic endpoint to verify production email configuration and connectivity.
    """
    settings = get_settings()
    pw = settings.smtp_password or ""
    clean_pw = pw.replace(" ", "").strip()

    return {
        "email_provider": settings.email_provider,
        "smtp_host": settings.smtp_host,
        "smtp_port": settings.smtp_port,
        "smtp_user": settings.smtp_user,
        "smtp_password_set": bool(pw),
        "smtp_password_len": len(clean_pw),
        "smtp_from_email": settings.smtp_from_email,
        "smtp_use_tls": settings.smtp_use_tls,
        "resend_configured": bool(settings.resend_api_key),
        "brevo_configured": bool(settings.brevo_api_key),
        "sendgrid_configured": bool(settings.sendgrid_api_key),
    }
