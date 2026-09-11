"""
CampusFlow — Security Headers & CSP Middleware.

Applies standard defensive HTTP response headers to protect against:
- Clickjacking (X-Frame-Options, frame-ancestors)
- MIME-type sniffing (X-Content-Type-Options)
- XSS and resource injection (Content-Security-Policy)
- Referrer leakage (Referrer-Policy)
- Unintended browser capabilities (Permissions-Policy)
- Protocol downgrade attacks (Strict-Transport-Security in production/staging)
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


DEFAULT_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob: https://storage.googleapis.com; "
    "font-src 'self' data:; "
    "connect-src 'self' http://localhost:8000 https://storage.googleapis.com https://*.run.app; "
    "worker-src 'self'; "
    "frame-ancestors 'none'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self';"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware injecting strict security headers onto all outgoing HTTP responses.
    Environment-aware: HSTS is only enforced when is_production=True.
    """

    def __init__(
        self,
        app,
        is_production: bool = False,
        csp: str | None = None,
    ) -> None:
        super().__init__(app)
        self.is_production = is_production
        self.csp = csp or DEFAULT_CSP

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        response.headers["Content-Security-Policy"] = self.csp
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # HSTS only in production or staging over HTTPS
        if self.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response
