"""
CampusFlow — Security: Password Hashing, JWT (RS256 + kid), JWKS

Key design decisions:
- RS256 asymmetric signing (private key signs, public key verifies)
- Every token carries a `kid` (Key ID) header for zero-downtime key rotation
- JWKS endpoint publishes public key(s) for external verification
- Private key loaded from environment — never hardcoded
- Raw tokens are never logged
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import JWTError, jwt
import bcrypt

from app.core.config import Settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

BCRYPT_ROUNDS = 12


def hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt."""
    password = plain.encode("utf-8")

    if len(password) > 72:
        raise ValueError("Password cannot be longer than 72 bytes.")

    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(password, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    password = plain.encode("utf-8")

    if len(password) > 72:
        return False

    return bcrypt.checkpw(
        password,
        hashed.encode("utf-8"),
    )

# ---------------------------------------------------------------------------
# Secure token utilities
# ---------------------------------------------------------------------------


def generate_secure_token() -> str:
    """
    Generate a cryptographically secure URL-safe token.
    Suitable for activation links and refresh tokens.
    The raw value is returned to the caller; only the hash is stored.
    NEVER log the return value of this function.
    """
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    """SHA-256 hash a raw token for safe storage. The hash is safe to log."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


# ---------------------------------------------------------------------------
# JWT / JWKS
# ---------------------------------------------------------------------------


class JWTManager:
    """
    Manages RS256 JWT issuance and verification with JWKS support.

    The `kid` claim in every token header enables multiple active keys,
    which allows zero-downtime key rotation:
      1. Add new key (v2) alongside old (v1)
      2. New tokens use v2; old tokens still verify via v1
      3. After 15 min (access token lifetime), v1 can be retired
    """

    ALGORITHM = "RS256"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._private_key_pem = settings.jwt_private_key_pem
        self._public_key_pem = settings.jwt_public_key_pem
        self._kid = settings.jwt_key_id
        self._issuer = settings.jwt_issuer
        self._access_expire = settings.jwt_access_token_expire_seconds
        self._refresh_expire = settings.jwt_refresh_token_expire_seconds

        # Load public key once for JWKS generation
        self._public_key = serialization.load_pem_public_key(
            self._public_key_pem.encode()
        )
        logger.info("JWTManager initialized with key_id=%s", self._kid)

    # ------------------------------------------------------------------
    # Token issuance
    # ------------------------------------------------------------------

    def create_access_token(self, user_id: str, role: str, email: str) -> str:
        """Issue a 15-minute RS256 access token with kid header."""
        now = datetime.now(timezone.utc)
        payload: dict[str, Any] = {
            "sub": user_id,
            "role": role,
            "email": email,
            "iss": self._issuer,
            "iat": now,
            "exp": now + timedelta(seconds=self._access_expire),
            "type": "access",
        }
        # python-jose reads `kid` from the `headers` kwarg
        return jwt.encode(
            payload,
            self._private_key_pem,
            algorithm=self.ALGORITHM,
            headers={"kid": self._kid},
        )

    def create_refresh_token(self, user_id: str) -> str:
        """Issue a 7-day RS256 refresh token with kid header."""
        now = datetime.now(timezone.utc)
        payload: dict[str, Any] = {
            "sub": user_id,
            "iss": self._issuer,
            "iat": now,
            "exp": now + timedelta(seconds=self._refresh_expire),
            "type": "refresh",
        }
        return jwt.encode(
            payload,
            self._private_key_pem,
            algorithm=self.ALGORITHM,
            headers={"kid": self._kid},
        )

    # ------------------------------------------------------------------
    # Token verification
    # ------------------------------------------------------------------

    def decode_access_token(self, token: str) -> dict[str, Any]:
        """
        Verify and decode an access token.
        Raises JWTError on any validation failure.
        NEVER log the raw token.
        """
        try:
            payload = jwt.decode(
                token,
                self._public_key_pem,
                algorithms=[self.ALGORITHM],
                issuer=self._issuer,
                options={"verify_aud": False},
            )
        except JWTError as exc:
            logger.debug("Access token verification failed: %s", type(exc).__name__)
            raise

        if payload.get("type") != "access":
            raise JWTError("Token type mismatch: expected access token")
        return payload

    def decode_refresh_token(self, token: str) -> dict[str, Any]:
        """Verify and decode a refresh token. NEVER log the raw token."""
        try:
            payload = jwt.decode(
                token,
                self._public_key_pem,
                algorithms=[self.ALGORITHM],
                issuer=self._issuer,
                options={"verify_aud": False},
            )
        except JWTError as exc:
            logger.debug("Refresh token verification failed: %s", type(exc).__name__)
            raise

        if payload.get("type") != "refresh":
            raise JWTError("Token type mismatch: expected refresh token")
        return payload

    # ------------------------------------------------------------------
    # JWKS
    # ------------------------------------------------------------------

    def get_jwks(self) -> dict[str, list[dict[str, str]]]:
        """
        Return the JSON Web Key Set for this key.
        Supports multiple active keys for rotation; currently serves one.
        """
        jwk = self._public_key_to_jwk()
        return {"keys": [jwk]}

    def _public_key_to_jwk(self) -> dict[str, str]:
        """Convert RSA public key to JWK format (RFC 7517)."""
        pub = self._public_key
        pub_numbers = pub.public_key().public_numbers() if hasattr(pub, "public_key") else pub.public_numbers()  # type: ignore[attr-defined]

        def _int_to_base64url(n: int) -> str:
            byte_length = (n.bit_length() + 7) // 8
            return base64.urlsafe_b64encode(
                n.to_bytes(byte_length, byteorder="big")
            ).rstrip(b"=").decode("ascii")

        return {
            "kty": "RSA",
            "use": "sig",
            "alg": "RS256",
            "kid": self._kid,
            "n": _int_to_base64url(pub_numbers.n),
            "e": _int_to_base64url(pub_numbers.e),
        }


# ---------------------------------------------------------------------------
# Module-level singleton (initialized lazily by the app factory)
# ---------------------------------------------------------------------------

_jwt_manager: JWTManager | None = None


def init_jwt_manager(settings: Settings) -> JWTManager:
    global _jwt_manager
    _jwt_manager = JWTManager(settings)
    return _jwt_manager


def get_jwt_manager() -> JWTManager:
    if _jwt_manager is None:
        raise RuntimeError("JWTManager not initialized. Call init_jwt_manager() at startup.")
    return _jwt_manager
