"""
Pydantic v2 schemas for the resume module — request/response contracts
only. The SQLAlchemy `Resume` model is never returned directly from a
router.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

# Reasonable maxima for resume content — generous enough for genuine
# summaries/objectives, not a hard technical limit. Mirrored on the
# `resumes.professional_summary` / `resumes.career_objective` DB
# columns (defense in depth, not just an API-layer check).
_PROFESSIONAL_SUMMARY_MAX_LENGTH = 2000
_CAREER_OBJECTIVE_MAX_LENGTH = 1000


def _strip_or_none(value: Optional[str]) -> Optional[str]:
    """Trim whitespace; treat an empty/whitespace-only string as unset (None)."""
    if value is None:
        return None
    value = value.strip()
    return value or None


class ResumeResponse(BaseModel):
    """Safe, outward-facing resume representation. Never duplicates any
    field already owned by `User`/`Student`/skills (email, full_name,
    department, cgpa, skills, etc.) — those live elsewhere.

    Deliberately excludes `file_path` — the server-internal storage
    path is never returned to a client (see docs/resume-module.md).
    `has_file` is derived, not a real column, so it can never drift
    from the actual presence of `file_name`.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    professional_summary: Optional[str] = None
    career_objective: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[misc]
    @property
    def has_file(self) -> bool:
        return self.file_name is not None


class ResumeCreate(BaseModel):
    """
    POST body to create the authenticated student's resume.

    `extra="forbid"` — same convention as the student-profile and
    skills request schemas — rejects any field not listed here; there
    is no `student_id` field on this schema at all, so it can never be
    supplied by the client (ownership is derived from the JWT in the
    service layer).
    """

    model_config = ConfigDict(extra="forbid")

    professional_summary: Optional[str] = Field(
        default=None, max_length=_PROFESSIONAL_SUMMARY_MAX_LENGTH
    )
    career_objective: Optional[str] = Field(
        default=None, max_length=_CAREER_OBJECTIVE_MAX_LENGTH
    )

    @field_validator("professional_summary", "career_objective")
    @classmethod
    def trim_whitespace(cls, value: Optional[str]) -> Optional[str]:
        return _strip_or_none(value)


class ResumeUpdate(BaseModel):
    """
    PATCH body — every field optional; only fields actually present in
    the request are applied (see `model_dump(exclude_unset=True)` in
    the service). A field explicitly sent as null clears it; a field
    omitted entirely leaves the existing value untouched.
    """

    model_config = ConfigDict(extra="forbid")

    professional_summary: Optional[str] = Field(
        default=None, max_length=_PROFESSIONAL_SUMMARY_MAX_LENGTH
    )
    career_objective: Optional[str] = Field(
        default=None, max_length=_CAREER_OBJECTIVE_MAX_LENGTH
    )

    @field_validator("professional_summary", "career_objective")
    @classmethod
    def trim_whitespace(cls, value: Optional[str]) -> Optional[str]:
        return _strip_or_none(value)
