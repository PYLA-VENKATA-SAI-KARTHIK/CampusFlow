"""
CampusFlow — Custom Exception Hierarchy

All exceptions map to structured RFC 7807 Problem Details responses.
Never include stack traces, SQL queries, or internal paths in HTTP responses.
"""
from __future__ import annotations

from fastapi import Request, status
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class CampusFlowError(Exception):
    """Base application exception."""

    http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "internal_error"
    title: str | None = None
    default_message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: str | None = None,
        detail: str | None = None,
        title: str | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.detail = detail
        if title:
            self.title = title
        super().__init__(self.message)



# ---------------------------------------------------------------------------
# 400 Bad Request
# ---------------------------------------------------------------------------


class ValidationError(CampusFlowError):
    http_status = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "validation_error"
    default_message = "Request validation failed."


class BadRequestError(CampusFlowError):
    http_status = status.HTTP_400_BAD_REQUEST
    error_code = "bad_request"
    default_message = "Bad request."


# ---------------------------------------------------------------------------
# 401 Unauthorized
# ---------------------------------------------------------------------------


class AuthenticationError(CampusFlowError):
    http_status = status.HTTP_401_UNAUTHORIZED
    error_code = "authentication_failed"
    default_message = "Authentication failed."


class InvalidTokenError(CampusFlowError):
    http_status = status.HTTP_401_UNAUTHORIZED
    error_code = "invalid_token"
    default_message = "Token is invalid or expired."


class AccountNotActiveError(CampusFlowError):
    http_status = status.HTTP_401_UNAUTHORIZED
    error_code = "account_not_active"
    default_message = "Account is not active. Please complete account activation."


# ---------------------------------------------------------------------------
# 403 Forbidden
# ---------------------------------------------------------------------------


class PermissionDeniedError(CampusFlowError):
    http_status = status.HTTP_403_FORBIDDEN
    error_code = "permission_denied"
    default_message = "You do not have permission to perform this action."


class MustChangePasswordError(CampusFlowError):
    http_status = status.HTTP_403_FORBIDDEN
    error_code = "must_change_password"
    default_message = "You must change your password before proceeding."


# ---------------------------------------------------------------------------
# 404 Not Found
# ---------------------------------------------------------------------------


class NotFoundError(CampusFlowError):
    http_status = status.HTTP_404_NOT_FOUND
    error_code = "not_found"
    default_message = "The requested resource was not found."


# ---------------------------------------------------------------------------
# 409 Conflict
# ---------------------------------------------------------------------------


class ConflictError(CampusFlowError):
    http_status = status.HTTP_409_CONFLICT
    error_code = "conflict"
    default_message = "A conflict occurred with the current state of the resource."


# ---------------------------------------------------------------------------
# 429 Too Many Requests
# ---------------------------------------------------------------------------


class RateLimitError(CampusFlowError):
    http_status = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = "rate_limit_exceeded"
    default_message = "Too many requests. Please try again later."


# ---------------------------------------------------------------------------
# Activation-specific
# ---------------------------------------------------------------------------


class ActivationTokenExpiredError(CampusFlowError):
    http_status = status.HTTP_400_BAD_REQUEST
    error_code = "activation_token_expired"
    default_message = "The activation link has expired. Please request a new one."


class ActivationTokenUsedError(CampusFlowError):
    http_status = status.HTTP_400_BAD_REQUEST
    error_code = "activation_token_used"
    default_message = "This activation link has already been used."


class ActivationTokenInvalidError(CampusFlowError):
    http_status = status.HTTP_400_BAD_REQUEST
    error_code = "activation_token_invalid"
    default_message = "The activation link is invalid."


class ResendRateLimitError(CampusFlowError):
    http_status = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = "resend_rate_limit"
    default_message = "Activation email resend limit reached. Please contact your placement officer."


# ---------------------------------------------------------------------------
# Registration-specific
# ---------------------------------------------------------------------------


class StudentNotFoundError(CampusFlowError):
    http_status = status.HTTP_404_NOT_FOUND
    error_code = "student_registration_not_found"
    title = "Registration Number Not Found"
    default_message = "Registration number not found. Please contact your placement office."


class AccountAlreadyRegisteredError(CampusFlowError):
    http_status = status.HTTP_409_CONFLICT
    error_code = "account_already_registered"
    title = "Account Already Registered"
    default_message = "This student account is already registered. Please sign in."


class AccountNotEligibleForRegistrationError(CampusFlowError):
    http_status = status.HTTP_400_BAD_REQUEST
    error_code = "account_not_eligible_for_registration"
    title = "Account Not Eligible"
    default_message = "This student account is not eligible for registration."


# ---------------------------------------------------------------------------
# Exception → HTTP response handler
# ---------------------------------------------------------------------------


def _problem_detail_response(exc: CampusFlowError) -> JSONResponse:
    """Convert a CampusFlowError into an RFC 7807 Problem Details response."""
    body: dict = {
        "type": f"https://campusflow.internal/errors/{exc.error_code}",
        "title": exc.title or exc.error_code.replace("_", " ").title(),
        "status": exc.http_status,
        "detail": exc.message,
    }
    if exc.detail:
        body["more_detail"] = exc.detail
    return JSONResponse(status_code=exc.http_status, content=body)



async def campus_flow_exception_handler(
    request: Request, exc: CampusFlowError
) -> JSONResponse:
    return _problem_detail_response(exc)


from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Format Pydantic RequestValidationErrors into an RFC 7807 response with a
    clean human-readable string detail and structured errors list.
    """
    messages: list[str] = []
    for err in exc.errors():
        loc = err.get("loc", ())
        field = str(loc[-1]) if loc else "field"
        msg = str(err.get("msg", "Invalid value"))
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, ") :]
        if field and field not in ("body", "__root__"):
            messages.append(f"{field}: {msg}")
        else:
            messages.append(msg)

    summary = ". ".join(messages) if messages else "Request validation failed."
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "type": "https://campusflow.internal/errors/validation_error",
            "title": "Validation Error",
            "status": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "detail": summary,
            "errors": jsonable_encoder(exc.errors()),
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler — never expose internal details.
    Log the real error server-side; return a safe generic response.
    """
    import logging

    logger = logging.getLogger(__name__)
    logger.error("Unhandled exception on %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "type": "https://campusflow.internal/errors/internal_error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred. Please try again later.",
        },
    )
