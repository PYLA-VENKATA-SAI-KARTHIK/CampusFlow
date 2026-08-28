"""
CampusFlow — Structured Application Logging

Rules enforced here:
- Never log passwords, password hashes, JWTs, tokens, or API keys
- Never log raw activation tokens
- Include request correlation IDs where available
"""
from __future__ import annotations

import logging
import sys
from typing import Any


# Sensitive field names — scrubbed from any log record extras
_SENSITIVE_FIELDS = frozenset(
    {
        "password",
        "password_hash",
        "hashed_password",
        "access_token",
        "refresh_token",
        "activation_token",
        "token",
        "token_hash",
        "sendgrid_api_key",
        "api_key",
        "secret",
        "private_key",
        "jwt_private_key",
    }
)


class SensitiveDataFilter(logging.Filter):
    """Removes sensitive keys from log record extra dicts."""

    def filter(self, record: logging.LogRecord) -> bool:
        for field in _SENSITIVE_FIELDS:
            if hasattr(record, field):
                setattr(record, field, "[REDACTED]")
        # Also scrub the message string for common patterns
        if isinstance(record.msg, str):
            record.msg = _scrub_message(record.msg)
        return True


def _scrub_message(msg: str) -> str:
    """Best-effort scrubbing of obvious secrets in log messages."""
    import re

    patterns = [
        (r"(?i)(password\s*[:=]\s*)\S+", r"\1[REDACTED]"),
        (r"(?i)(token\s*[:=]\s*)\S+", r"\1[REDACTED]"),
        (r"(?i)(api_key\s*[:=]\s*)\S+", r"\1[REDACTED]"),
        (r"(?i)(Authorization:\s*Bearer\s+)\S+", r"\1[REDACTED]"),
    ]
    for pattern, replacement in patterns:
        msg = re.sub(pattern, replacement, msg)
    return msg


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure application-wide structured logging.
    Call once at startup from app factory.
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)
    handler.addFilter(SensitiveDataFilter())

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(fmt)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Quiet noisy third-party loggers in production
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if log_level == "DEBUG" else logging.WARNING
    )
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger. Use __name__ as the name in each module."""
    return logging.getLogger(name)
