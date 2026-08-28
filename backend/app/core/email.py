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


# ---------------------------------------------------------------------------
# Mock adapter — for local development and tests
# ---------------------------------------------------------------------------


class MockEmailAdapter(EmailService):
    """
    Development email adapter — does NOT send real emails.
    Logs the activation URL to stdout so developers can use it locally.
    Safe to use without any email credentials.
    """

    async def send_activation_email(self, data: ActivationEmailData) -> None:
        # Log recipient and URL separately so the URL can be filtered if needed
        logger.info(
            "[MOCK EMAIL] Activation email would be sent to: %s (%s)",
            data.recipient_email,
            data.recipient_name,
        )
        # Print to stdout for easy developer access in terminal
        # In a real dev flow, the developer clicks this link
        print(
            f"\n{'='*60}\n"
            f"  [DEV] Account Activation Email\n"
            f"  To: {data.recipient_email} ({data.recipient_name})\n"
            f"  Activation URL: {data.activation_url}\n"
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


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_email_service(
    provider: str,
    sendgrid_api_key: str = "",
    sendgrid_from_email: str = "noreply@campusflow.internal",
    sendgrid_from_name: str = "CampusFlow",
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

    logger.info("Email service: Mock adapter initialized (no real emails will be sent)")
    return MockEmailAdapter()
