"""
CampusFlow — Email Service Abstraction

Architecture:
  EmailService (abstract interface)
    ├── MockEmailAdapter   — development/test: logs to console, no credentials
    └── SendGridAdapter    — production: real delivery via SendGrid API

The provider is selected by EMAIL_PROVIDER env var.
Credentials are NEVER hardcoded — loaded from settings only.
Raw activation tokens are NEVER passed to log statements.
"""
from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data transfer objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ActivationEmailData:
    """All data needed to send an account activation email."""

    recipient_email: str
    recipient_name: str
    activation_url: str  # Contains the raw token — NEVER log this field directly


@dataclass(frozen=True)
class DriveNotificationEmailData:
    """All data needed to send a placement drive announcement email."""

    recipient_email: str
    recipient_name: str
    drive_title: str
    company_name: str
    job_role: str
    ctc_lpa: float | None = None
    location: str | None = None
    registration_deadline: str | None = None
    drive_url: str = ""


# ---------------------------------------------------------------------------
# Abstract interface
# ---------------------------------------------------------------------------


class EmailService(ABC):
    """
    Abstract email service interface.
    All email-sending logic must go through this interface.
    The concrete implementation is determined at startup via factory.
    """

    @abstractmethod
    async def send_activation_email(self, data: ActivationEmailData) -> None:
        """Send an account activation email to a newly-imported student."""
        ...

    @abstractmethod
    async def send_drive_notification_email(self, data: DriveNotificationEmailData) -> None:
        """Send a drive announcement email to an eligible student."""
        ...


# ---------------------------------------------------------------------------
# Mock adapter — for local development and tests
# ---------------------------------------------------------------------------


class MockEmailAdapter(EmailService):
    """
    Development email adapter — does NOT send real emails.
    Logs the email details to stdout so developers can inspect it locally.
    Safe to use without any email credentials.
    """

    def __init__(self) -> None:
        self.sent_activation_emails: list[ActivationEmailData] = []
        self.sent_drive_emails: list[DriveNotificationEmailData] = []

    async def send_activation_email(self, data: ActivationEmailData) -> None:
        self.sent_activation_emails.append(data)
        logger.info(
            "[MOCK EMAIL] Activation email would be sent to: %s (%s)",
            data.recipient_email,
            data.recipient_name,
        )
        print(
            f"\n{'='*60}\n"
            f"  [DEV] Account Activation Email\n"
            f"  To: {data.recipient_email} ({data.recipient_name})\n"
            f"  Activation URL: {data.activation_url}\n"
            f"{'='*60}\n"
        )

    async def send_drive_notification_email(self, data: DriveNotificationEmailData) -> None:
        self.sent_drive_emails.append(data)
        logger.info(
            "[MOCK EMAIL] Drive notification email would be sent to: %s (%s) for drive '%s'",
            data.recipient_email,
            data.recipient_name,
            data.drive_title,
        )
        ctc_info = f"{data.ctc_lpa} LPA" if data.ctc_lpa else "N/A"
        print(
            f"\n{'='*60}\n"
            f"  [DEV] Placement Drive Announcement Email\n"
            f"  To: {data.recipient_email} ({data.recipient_name})\n"
            f"  Drive: {data.drive_title} ({data.company_name})\n"
            f"  Role: {data.job_role} | CTC: {ctc_info}\n"
            f"  Deadline: {data.registration_deadline or 'N/A'}\n"
            f"  Link: {data.drive_url}\n"
            f"{'='*60}\n"
        )


# ---------------------------------------------------------------------------
# SendGrid adapter — for production
# ---------------------------------------------------------------------------


class SendGridAdapter(EmailService):
    """
    Production email adapter using SendGrid.
    Credentials loaded from settings — never hardcoded.
    """

    def __init__(self, api_key: str, from_email: str, from_name: str) -> None:
        self._api_key = api_key  # Not logged
        self._from_email = from_email
        self._from_name = from_name

    async def send_activation_email(self, data: ActivationEmailData) -> None:
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, To

            message = Mail(
                from_email=(self._from_email, self._from_name),
                to_emails=To(data.recipient_email, data.recipient_name),
                subject="Activate your CampusFlow account",
                html_content=_build_activation_html(data),
                plain_text_content=_build_activation_text(data),
            )

            sg = SendGridAPIClient(self._api_key)
            response = sg.send(message)

            logger.info(
                "Activation email sent via SendGrid to %s | status=%s",
                data.recipient_email,
                response.status_code,
            )
        except Exception as exc:
            # Log the error type but not credentials or token URL
            logger.error(
                "Failed to send activation email to %s via SendGrid: %s",
                data.recipient_email,
                type(exc).__name__,
            )
            raise

    async def send_drive_notification_email(self, data: DriveNotificationEmailData) -> None:
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, To

            message = Mail(
                from_email=(self._from_email, self._from_name),
                to_emails=To(data.recipient_email, data.recipient_name),
                subject=f"New Placement Drive: {data.drive_title} ({data.company_name})",
                html_content=_build_drive_notification_html(data),
                plain_text_content=_build_drive_notification_text(data),
            )

            sg = SendGridAPIClient(self._api_key)
            response = sg.send(message)

            logger.info(
                "Drive notification email sent via SendGrid to %s | status=%s",
                data.recipient_email,
                response.status_code,
            )
        except Exception as exc:
            logger.error(
                "Failed to send drive notification email to %s via SendGrid: %s",
                data.recipient_email,
                type(exc).__name__,
            )
            raise


# ---------------------------------------------------------------------------
# SMTP adapter — standard library SMTP (Gmail, Outlook, University SMTP)
# ---------------------------------------------------------------------------


class SmtpEmailAdapter(EmailService):
    """
    Standard library SMTP email adapter.
    Supports TLS, SSL, authenticated or unauthenticated SMTP servers.
    """

    def __init__(
        self,
        host: str,
        port: int = 587,
        user: str = "",
        password: str = "",
        use_tls: bool = True,
        from_email: str = "noreply@campusflow.internal",
        from_name: str = "CampusFlow",
    ) -> None:
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.use_tls = use_tls
        self.from_email = from_email
        self.from_name = from_name

    def _send_sync(self, to_email: str, subject: str, text_content: str, html_content: str) -> None:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        if not self.password and "gmail.com" in self.host.lower():
            logger.warning(
                "[SMTP] Attempted to send from %s via %s without SMTP_PASSWORD. "
                "Please configure a 16-character Google App Password in backend/.env to deliver real emails.",
                self.from_email,
                self.host,
            )
            print(
                f"\n{'='*60}\n"
                f"  [SMTP PENDING AUTH] Outgoing Placement Drive Email\n"
                f"  From: {self.from_name} <{self.from_email}>\n"
                f"  To: {to_email}\n"
                f"  Subject: {subject}\n"
                f"  Note: Set SMTP_PASSWORD in backend/.env (16-character Google App Password) for live delivery.\n"
                f"{'='*60}\n"
            )
            return

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email
        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        clean_password = self.password.replace(" ", "").strip() if ("gmail.com" in self.host.lower() and self.password) else self.password

        if self.use_tls:
            with smtplib.SMTP(self.host, self.port) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                if self.user and clean_password:
                    server.login(self.user, clean_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(self.host, self.port) as server:
                if self.user and clean_password:
                    server.login(self.user, clean_password)
                server.send_message(msg)

    async def send_activation_email(self, data: ActivationEmailData) -> None:
        subject = "Activate your CampusFlow Account"
        text = _build_activation_text(data)
        html = _build_activation_html(data)
        try:
            await asyncio.to_thread(self._send_sync, data.recipient_email, subject, text, html)
            logger.info("Activation email sent via SMTP to %s", data.recipient_email)
        except Exception as exc:
            logger.error("Failed to send activation email to %s via SMTP: %s", data.recipient_email, exc)
            raise

    async def send_drive_notification_email(self, data: DriveNotificationEmailData) -> None:
        subject = f"New Placement Drive: {data.drive_title} ({data.company_name})"
        text = _build_drive_notification_text(data)
        html = _build_drive_notification_html(data)
        try:
            await asyncio.to_thread(self._send_sync, data.recipient_email, subject, text, html)
            logger.info("Drive notification email sent via SMTP to %s", data.recipient_email)
        except Exception as exc:
            logger.error("Failed to send drive notification email to %s via SMTP: %s", data.recipient_email, exc)
            raise


def _build_activation_html(data: ActivationEmailData) -> str:
    return f"""
    <html>
    <body>
      <h2>Welcome to CampusFlow, {data.recipient_name}!</h2>
      <p>Your placement cell has created an account for you.</p>
      <p>Click the button below to activate your account and set your password:</p>
      <p>
        <a href="{data.activation_url}"
           style="background:#2563eb;color:#fff;padding:12px 24px;
                  text-decoration:none;border-radius:6px;">
          Activate Account
        </a>
      </p>
      <p>This link expires in <strong>72 hours</strong>.</p>
      <p>If you did not expect this email, please ignore it.</p>
    </body>
    </html>
    """


def _build_activation_text(data: ActivationEmailData) -> str:
    return (
        f"Welcome to CampusFlow, {data.recipient_name}!\n\n"
        f"Your placement cell has created an account for you.\n\n"
        f"Activate your account here:\n{data.activation_url}\n\n"
        f"This link expires in 72 hours.\n"
        f"If you did not expect this email, please ignore it."
    )


def _build_drive_notification_html(data: DriveNotificationEmailData) -> str:
    ctc_text = f"{data.ctc_lpa} LPA" if data.ctc_lpa else "As per industry standards"
    location_text = data.location or "Not specified / Multiple locations"
    deadline_text = data.registration_deadline or "Please check drive details"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.5; margin: 0; padding: 20px; background-color: #f8fafc; }}
        .card {{ background: #ffffff; max-width: 600px; margin: 0 auto; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
        .header {{ background: #4f46e5; color: #ffffff; padding: 24px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 20px; font-weight: 700; }}
        .content {{ padding: 24px; }}
        .details-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .details-table td {{ padding: 10px 12px; border-bottom: 1px solid #f1f5f9; font-size: 14px; }}
        .details-table td.label {{ color: #64748b; font-weight: 600; width: 35%; }}
        .details-table td.value {{ color: #0f172a; font-weight: 500; }}
        .btn {{ display: inline-block; background: #4f46e5; color: #ffffff !important; padding: 12px 28px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 14px; text-align: center; }}
        .footer {{ padding: 16px 24px; background: #f8fafc; border-top: 1px solid #e2e8f0; text-align: center; font-size: 12px; color: #94a3b8; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <h1>New Placement Drive Announced</h1>
        </div>
        <div class="content">
          <p>Hello <strong>{data.recipient_name}</strong>,</p>
          <p>A new placement drive has been announced for which you meet the eligibility criteria:</p>
          
          <table class="details-table">
            <tr>
              <td class="label">Company</td>
              <td class="value">{data.company_name}</td>
            </tr>
            <tr>
              <td class="label">Drive Title</td>
              <td class="value">{data.drive_title}</td>
            </tr>
            <tr>
              <td class="label">Job Role</td>
              <td class="value">{data.job_role}</td>
            </tr>
            <tr>
              <td class="label">Package (CTC)</td>
              <td class="value">{ctc_text}</td>
            </tr>
            <tr>
              <td class="label">Location</td>
              <td class="value">{location_text}</td>
            </tr>
            <tr>
              <td class="label">Registration Deadline</td>
              <td class="value" style="color: #dc2626; font-weight: 600;">{deadline_text}</td>
            </tr>
          </table>

          <div style="text-align: center; margin: 28px 0 16px 0;">
            <a href="{data.drive_url}" class="btn">View Drive & Register</a>
          </div>

          <p style="font-size: 13px; color: #64748b; margin-top: 24px;">
            Please ensure you register before the deadline. If the button above does not work, copy and paste this link into your browser:<br>
            <a href="{data.drive_url}" style="color: #4f46e5; word-break: break-all;">{data.drive_url}</a>
          </p>
        </div>
        <div class="footer">
          CampusFlow Placement Management System &bull; Automated notification
        </div>
      </div>
    </body>
    </html>
    """


def _build_drive_notification_text(data: DriveNotificationEmailData) -> str:
    ctc_text = f"{data.ctc_lpa} LPA" if data.ctc_lpa else "As per industry standards"
    location_text = data.location or "Not specified"
    deadline_text = data.registration_deadline or "Please check drive details"

    return (
        f"Hello {data.recipient_name},\n\n"
        f"A new placement drive has been announced for which you meet the eligibility criteria:\n\n"
        f"  Company: {data.company_name}\n"
        f"  Drive Title: {data.drive_title}\n"
        f"  Job Role: {data.job_role}\n"
        f"  Package (CTC): {ctc_text}\n"
        f"  Location: {location_text}\n"
        f"  Registration Deadline: {deadline_text}\n\n"
        f"View Drive and Register here:\n"
        f"{data.drive_url}\n\n"
        f"Please ensure you complete your registration before the deadline.\n"
        f"— CampusFlow Placement Cell"
    )


# ---------------------------------------------------------------------------
# Factory & Singleton
# ---------------------------------------------------------------------------

_email_service_instance: EmailService | None = None


def create_email_service(
    provider: str,
    sendgrid_api_key: str = "",
    sendgrid_from_email: str = "noreply@campusflow.internal",
    sendgrid_from_name: str = "CampusFlow",
    smtp_host: str = "",
    smtp_port: int = 587,
    smtp_user: str = "",
    smtp_password: str = "",
    smtp_use_tls: bool = True,
    smtp_from_email: str = "noreply@campusflow.internal",
    smtp_from_name: str = "CampusFlow",
) -> EmailService:
    """
    Create the appropriate EmailService implementation based on the provider.
    Called once at application startup.
    """
    if provider == "sendgrid":
        if not sendgrid_api_key:
            raise ValueError("SENDGRID_API_KEY must be set when EMAIL_PROVIDER=sendgrid")
        logger.info("Email service: SendGrid adapter initialized")
        return SendGridAdapter(
            api_key=sendgrid_api_key,
            from_email=sendgrid_from_email,
            from_name=sendgrid_from_name,
        )

    if provider == "smtp":
        if not smtp_host:
            raise ValueError("SMTP_HOST must be set when EMAIL_PROVIDER=smtp")
        logger.info("Email service: SMTP adapter initialized (%s:%s)", smtp_host, smtp_port)
        return SmtpEmailAdapter(
            host=smtp_host,
            port=smtp_port,
            user=smtp_user,
            password=smtp_password,
            use_tls=smtp_use_tls,
            from_email=smtp_from_email,
            from_name=smtp_from_name,
        )

    logger.info("Email service: Mock adapter initialized (no real emails will be sent)")
    return MockEmailAdapter()


def get_email_service() -> EmailService:
    """Returns the singleton EmailService instance based on application settings."""
    global _email_service_instance
    if _email_service_instance is None:
        from app.core.config import get_settings
        settings = get_settings()
        _email_service_instance = create_email_service(
            provider=settings.email_provider,
            sendgrid_api_key=settings.sendgrid_api_key,
            sendgrid_from_email=settings.sendgrid_from_email,
            sendgrid_from_name=settings.sendgrid_from_name,
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_user=settings.smtp_user,
            smtp_password=settings.smtp_password,
            smtp_use_tls=settings.smtp_use_tls,
            smtp_from_email=settings.smtp_from_email,
            smtp_from_name=settings.smtp_from_name,
        )
    return _email_service_instance


def reset_email_service() -> None:
    """Reset the singleton EmailService instance (primarily for testing)."""
    global _email_service_instance
    _email_service_instance = None
