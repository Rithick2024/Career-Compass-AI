"""
Pydantic v2 schemas for the student module — request/response contracts
only. The SQLAlchemy `Student`/`Department` models are never returned
directly from a router.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

# Loose but real validation: optional leading '+', digits/spaces/hyphens/
# parentheses, 7-20 chars. Accepts "+91 98765 43210", "(044) 1234-5678",
# "9876543210", etc. without pinning to one country's format.
_PHONE_PATTERN = r"^\+?[0-9\s\-\(\)]{7,20}$"

# Graduation year: generous bounds rather than a narrow "current year
# +/- a few" window, since a profile might legitimately record a past
# graduate or someone admitted several years out.
_MIN_GRADUATION_YEAR = 1950
_MAX_GRADUATION_YEAR = date.today().year + 10


class DepartmentOut(BaseModel):
    """Minimal department representation nested in a student profile."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_active: bool = True


class DepartmentResponse(BaseModel):
    """Full department representation for staff and catalog management."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DepartmentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Department name cannot be blank.")
        return value


class DepartmentUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Department name cannot be blank.")
        return value


class DepartmentStatusUpdateRequest(BaseModel):
    is_active: bool


class StudentProfileResponse(BaseModel):
    """Safe, outward-facing student profile. Never includes any user
    authentication field (email, password, role, is_active) — those
    live on `User`, not `Student`, so there is nothing here to leak."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[DepartmentOut] = None
    graduation_year: Optional[int] = None
    cgpa: Optional[float] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class StudentProfileUpdateRequest(BaseModel):
    """
    PATCH payload — every field optional; only fields actually present
    in the request are applied (see `model_dump(exclude_unset=True)`
    in the service). `extra="forbid"` rejects any field not listed
    here — in particular, there is no way to smuggle `email`, `role`,
    or similar user-auth fields through this schema, since they don't
    exist on it at all.
    """

    model_config = ConfigDict(extra="forbid")

    full_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    phone: Optional[str] = Field(default=None, pattern=_PHONE_PATTERN)
    department_id: Optional[int] = None
    graduation_year: Optional[int] = Field(
        default=None, ge=_MIN_GRADUATION_YEAR, le=_MAX_GRADUATION_YEAR
    )
    cgpa: Optional[float] = Field(default=None, ge=0, le=10)
    date_of_birth: Optional[date] = None
    address: Optional[str] = Field(default=None, max_length=500)
    linkedin_url: Optional[HttpUrl] = None
    github_url: Optional[HttpUrl] = None

    @field_validator("full_name")
    @classmethod
    def full_name_not_blank(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("Full name cannot be blank.")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def dob_not_in_future(cls, value: Optional[date]) -> Optional[date]:
        if value is not None and value > date.today():
            raise ValueError("Date of birth cannot be in the future.")
        return value
