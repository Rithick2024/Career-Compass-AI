"""
Pydantic v2 schemas for the resume module — request/response contracts only.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

_TITLE_MAX_LENGTH = 100
_DESCRIPTION_MAX_LENGTH = 500


def _strip_or_none(value: Optional[str]) -> Optional[str]:
    """Trim whitespace; treat an empty/whitespace-only string as unset (None)."""
    if value is None:
        return None
    value = value.strip()
    return value or None


class ResumeResponse(BaseModel):
    """
    Safe, outward-facing resume document representation.
    Deliberately excludes `student_id` and `file_path`.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    file_name: str
    file_type: str
    file_size: int
    is_default: bool
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[misc]
    @property
    def has_file(self) -> bool:
        return True


class ResumeCreate(BaseModel):
    """Schema for validating title and description during resume upload."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=_TITLE_MAX_LENGTH)
    description: Optional[str] = Field(default=None, max_length=_DESCRIPTION_MAX_LENGTH)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        trimmed = value.strip() if value else ""
        if not trimmed:
            raise ValueError("Title cannot be empty or whitespace only.")
        return trimmed

    @field_validator("description")
    @classmethod
    def trim_description(cls, value: Optional[str]) -> Optional[str]:
        return _strip_or_none(value)


class ResumeUpdate(BaseModel):
    """
    PATCH body to update resume metadata (title, description).
    """

    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(default=None, min_length=1, max_length=_TITLE_MAX_LENGTH)
    description: Optional[str] = Field(default=None, max_length=_DESCRIPTION_MAX_LENGTH)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Title cannot be empty or whitespace only.")
        return trimmed

    @field_validator("description")
    @classmethod
    def trim_description(cls, value: Optional[str]) -> Optional[str]:
        return _strip_or_none(value)
