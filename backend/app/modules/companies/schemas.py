"""
Pydantic v2 schemas for the Company module — request/response contracts only.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class CompanyResponse(BaseModel):
    """Outward-facing company representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CompanyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: Optional[str] = Field(default=None, max_length=2000)
    industry: Optional[str] = Field(default=None, max_length=100)
    website: Optional[HttpUrl] = None
    location: Optional[str] = Field(default=None, max_length=150)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Company name cannot be blank.")
        return value

    @field_validator("description", "industry", "location", mode="before")
    @classmethod
    def empty_str_to_none(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
        return value

    @field_validator("website", mode="before")
    @classmethod
    def validate_website_input(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
        return value


class CompanyUpdateRequest(BaseModel):
    """
    PATCH payload — all fields optional; extra="forbid" prevents smuggling
    id, created_at, updated_at, or is_active.
    """

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    description: Optional[str] = Field(default=None, max_length=2000)
    industry: Optional[str] = Field(default=None, max_length=100)
    website: Optional[HttpUrl] = None
    location: Optional[str] = Field(default=None, max_length=150)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("Company name cannot be blank.")
        return value

    @field_validator("description", "industry", "location", mode="before")
    @classmethod
    def empty_str_to_none(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
        return value

    @field_validator("website", mode="before")
    @classmethod
    def validate_website_input(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
        return value


class CompanyStatusUpdateRequest(BaseModel):
    is_active: bool
