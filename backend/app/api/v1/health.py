"""
Health check and diagnostic endpoints.
"""
import socket
import traceback
from fastapi import APIRouter, Query

from app.core.config import get_settings

router = APIRouter()


@router.get("")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
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

    # Test raw socket connections to port 587, 465, 2525, 443 (IPv4 only vs default)
    ports_to_test = [
        ("smtp.gmail.com", 587),
        ("smtp.gmail.com", 465),
        ("smtp.gmail.com", 25),
        ("smtp-relay.gmail.com", 587),
        ("smtp.sendgrid.net", 587),
        ("smtp.sendgrid.net", 2525),
        ("api.resend.com", 443),
    ]
    port_results = {}
    for host, p in ports_to_test:
        key = f"{host}:{p}"
        try:
            # Force IPv4
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect((host, p))
            s.close()
            port_results[key] = "OPEN / REACHABLE"
        except Exception as e:
            port_results[key] = f"BLOCKED: {type(e).__name__} - {e}"

    info["port_connectivity"] = port_results
    return info
