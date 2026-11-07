"""
Health check and diagnostic endpoints.
"""
import traceback
from fastapi import APIRouter, Query

from app.core.config import get_settings

router = APIRouter()


@router.get("")
async def health_check() -> dict[str, str]:
    """
    Basic health check endpoint.
    Must not expose DB credentials or internal state.
    """
    return {"status": "ok"}


@router.get("/smtp")
async def smtp_diagnostic(
    send_test: bool = Query(False, description="Whether to attempt sending a test email"),
    target_email: str = Query("pylasai43@gmail.com", description="Target recipient for test email"),
) -> dict:
    """
    Diagnostic endpoint to verify production SMTP configuration and connectivity.
    """
    settings = get_settings()
    pw = settings.smtp_password or ""
    clean_pw = pw.replace(" ", "").strip()

    info = {
        "email_provider": settings.email_provider,
        "smtp_host": settings.smtp_host,
        "smtp_port": settings.smtp_port,
        "smtp_user": settings.smtp_user,
        "smtp_password_set": bool(pw),
        "smtp_password_len": len(pw),
        "clean_pw_len": len(clean_pw),
        "smtp_from_email": settings.smtp_from_email,
        "smtp_from_name": settings.smtp_from_name,
        "smtp_use_tls": settings.smtp_use_tls,
    }

    if not pw:
        info["error"] = "SMTP_PASSWORD is empty or unset in environment variables."
        return info

    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            info["tcp_connect"] = "SUCCESS"
            server.ehlo()
            if settings.smtp_use_tls:
                server.starttls()
                server.ehlo()
                info["tls_handshake"] = "SUCCESS"

            if settings.smtp_user and clean_pw:
                server.login(settings.smtp_user, clean_pw)
                info["smtp_login"] = "SUCCESS"

            if send_test and target_email:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = "[CampusFlow Diagnostic] SMTP Live Test"
                msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
                msg["To"] = target_email
                msg.attach(MIMEText("This is an automated SMTP connectivity test from CampusFlow on Render.", "plain", "utf-8"))
                server.send_message(msg)
                info["test_email_sent"] = f"Delivered to {target_email}"
    except Exception as e:
        info["error"] = f"{type(e).__name__}: {str(e)}"
        info["traceback"] = traceback.format_exc()

    return info
