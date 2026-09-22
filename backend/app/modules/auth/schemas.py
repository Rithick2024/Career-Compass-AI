"""
Pydantic v2 schemas for the auth module — request/response contracts
only. No business logic here (that's the service layer's job).
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.shared.enums import RoleEnum

# bcrypt silently ignores/truncates bytes beyond 72 — cap input so
# every accepted password is actually fully honored by the hash.
_PASSWORD_MIN_LENGTH = 8
_PASSWORD_MAX_LENGTH = 72


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=_PASSWORD_MIN_LENGTH, max_length=_PASSWORD_MAX_LENGTH)
    # Optional and intentionally restricted: public registration may only
    # ever produce a `student` account. See docs/authentication.md for the
    # reasoning. Accepting the field (rather than rejecting it outright)
    # keeps the request shape self-documenting while `validate_role`
    # below refuses anything other than "student".
    role: Optional[RoleEnum] = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: Optional[RoleEnum]) -> RoleEnum:
        if value is not None and value != RoleEnum.STUDENT:
            raise ValueError(
                "Public registration can only create student accounts. "
                "Staff accounts must be provisioned separately."
            )
        return RoleEnum.STUDENT


class StaffRegisterRequest(BaseModel):
    """Developer/testing request schema to provision a staff account via Swagger UI."""

    email: EmailStr
    password: str = Field(min_length=_PASSWORD_MIN_LENGTH, max_length=_PASSWORD_MAX_LENGTH)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserPublic(BaseModel):
    """Safe, outward-facing user representation. Never includes password_hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: RoleEnum
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
