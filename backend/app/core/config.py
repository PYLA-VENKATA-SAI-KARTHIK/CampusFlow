"""
CampusFlow Backend — Application Settings

Loads all configuration from environment variables / .env file.
Never reads secrets from source code.
"""
from __future__ import annotations

import base64
from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    app_env: Literal["development", "testing", "staging", "production"] = "development"
    app_name: str = "CampusFlow"
    debug: bool = False
    log_level: str = "INFO"

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    database_url: str
    database_echo: bool = False

    # -------------------------------------------------------------------------
    # CORS
    # -------------------------------------------------------------------------
    cors_allowed_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    # -------------------------------------------------------------------------
    # JWT / JWKS (RS256)
    # -------------------------------------------------------------------------
    jwt_key_id: str = "campusflow-dev-key-v1"
    jwt_private_key_base64: str
    jwt_public_key_base64: str
    jwt_access_token_expire_seconds: int = 900        # 15 min
    jwt_refresh_token_expire_seconds: int = 604800    # 7 days
    jwt_issuer: str = "http://localhost:8000"

    @property
    def jwt_private_key_pem(self) -> str:
        """Decode base64-encoded private key PEM."""
        return base64.b64decode(self.jwt_private_key_base64).decode("utf-8")

    @property
    def jwt_public_key_pem(self) -> str:
        """Decode base64-encoded public key PEM."""
        return base64.b64decode(self.jwt_public_key_base64).decode("utf-8")

    # -------------------------------------------------------------------------
    # Email
    # -------------------------------------------------------------------------
    email_provider: Literal["mock", "sendgrid"] = "mock"
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = "noreply@campusflow.internal"
    sendgrid_from_name: str = "CampusFlow"
    frontend_base_url: str = "http://localhost:5173"

    # -------------------------------------------------------------------------
    # Rate limiting
    # -------------------------------------------------------------------------
    rate_limit_login: str = "10/minute"
    rate_limit_activate: str = "5/15minutes"
    rate_limit_resend_activation_max: int = 5
    rate_limit_resend_activation_min_gap_minutes: int = 10

    # -------------------------------------------------------------------------
    # Bootstrap admin (optional, dev only)
    # -------------------------------------------------------------------------
    bootstrap_admin_email: str = ""
    bootstrap_admin_password: str = ""
    bootstrap_admin_name: str = ""

    # -------------------------------------------------------------------------
    # Validators
    # -------------------------------------------------------------------------
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"log_level must be one of {valid}")
        return upper

    @model_validator(mode="after")
    def validate_sendgrid_if_required(self) -> "Settings":
        if self.email_provider == "sendgrid" and not self.sendgrid_api_key:
            raise ValueError(
                "SENDGRID_API_KEY is required when EMAIL_PROVIDER=sendgrid"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — loaded once at startup."""
    return Settings()  # type: ignore[call-arg]
