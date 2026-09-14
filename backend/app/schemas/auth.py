"""
Auth schemas.
"""
from pydantic import BaseModel, EmailStr, Field, model_validator

from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    email: str | None = None
    identifier: str | None = None
    password: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_identifier(self) -> "LoginRequest":
        raw = self.identifier or self.email
        if not raw or not str(raw).strip():
            raise ValueError("Email address or student registration number is required.")
        clean = str(raw).strip()
        self.email = clean
        self.identifier = clean
        return self


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class ActivateRequest(BaseModel):
    activation_token: str | None = None
    registration_number: str | None = None
    new_password: str = Field(min_length=8)


class StudentRegisterRequest(BaseModel):
    registration_number: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8, max_length=72)


class RegisterResponse(BaseModel):
    message: str = "Registration completed successfully. You can now sign in."
    email: str | None = None
    registration_number: str


