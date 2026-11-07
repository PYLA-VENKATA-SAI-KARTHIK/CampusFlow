"""
Health check and diagnostic endpoints.
"""
from fastapi import APIRouter, Query

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
        "resend_api_key_prefix": settings.resend_api_key[:8] + "..." if settings.resend_api_key else "(not set)",
        "resend_from_email": settings.resend_from_email,
        "resend_configured": bool(settings.resend_api_key),
        "brevo_api_key_prefix": settings.brevo_api_key[:8] + "..." if settings.brevo_api_key else "(not set)",
        "brevo_from_email": settings.brevo_from_email,
        "brevo_configured": bool(settings.brevo_api_key),
        "sendgrid_configured": bool(settings.sendgrid_api_key),
    }


@router.get("/email-test")
async def email_test(to: str = Query(default="pylasai43@gmail.com")) -> dict:
    """
    Live email delivery test — sends a real test email via the configured provider.
    Use ?to=email@example.com to override the recipient.
    """
    import asyncio
    from app.core.email import get_email_service, DriveNotificationEmailData

    settings = get_settings()
    svc = get_email_service()
    provider = settings.email_provider

    try:
        data = DriveNotificationEmailData(
            recipient_email=to,
            recipient_name="Test Student",
            drive_title="[TEST] CampusFlow Email Diagnostic",
            company_name="Diagnostic Corp",
            job_role="Software Engineer",
            ctc_lpa=10.0,
            location="Hyderabad",
            registration_deadline="31 Dec 2026, 11:59 PM UTC",
            drive_url=settings.frontend_base_url + "/drives",
        )
        await svc.send_drive_notification_email(data)
        return {
            "status": "sent",
            "provider": provider,
            "recipient": to,
            "message": f"Email dispatched via {provider} to {to}. Check inbox (and spam folder).",
        }
    except Exception as exc:
        return {
            "status": "error",
            "provider": provider,
            "recipient": to,
            "error": str(exc),
        }
