"""
Pydantic v2 schemas for the skills module — request/response contracts
only. The SQLAlchemy `Skill`/`StudentSkill` models are never returned
directly from a router.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.shared.enums import ProficiencyLevel


class SkillOut(BaseModel):
    """
    Minimal skill representation — used both for the platform catalog
    and nested inside a student's own skill list.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: Optional[str] = None
    is_active: bool = True


class SkillResponse(BaseModel):
    """Full skill representation for staff and catalog management."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SkillCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: Optional[str] = Field(default=None, max_length=100)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Skill name cannot be blank.")
        return value

    @field_validator("category")
    @classmethod
    def clean_category(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            value = value.strip()
            return value if value else None
        return None


class SkillUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: Optional[str] = Field(default=None, max_length=100)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Skill name cannot be blank.")
        return value

    @field_validator("category")
    @classmethod
    def clean_category(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            value = value.strip()
            return value if value else None
        return None


class SkillStatusUpdateRequest(BaseModel):
    is_active: bool


class StudentSkillResponse(BaseModel):
    """A single skill on a student's profile, with the skill's own
    details nested (matches how `StudentProfileResponse` nests
    `department: DepartmentOut`)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    skill: SkillOut
    proficiency: ProficiencyLevel
    created_at: datetime
    updated_at: datetime


class AddStudentSkillRequest(BaseModel):
    """POST body to add a catalog skill to the authenticated student's
    profile. `extra="forbid"` — same convention as the student-profile
    PATCH schema — rejects any field not listed here."""

    model_config = ConfigDict(extra="forbid")

    skill_id: int
    proficiency: ProficiencyLevel


class UpdateStudentSkillProficiencyRequest(BaseModel):
    """PATCH body — the only editable attribute of a student_skill row
    is its proficiency; `skill_id`/`student_id` are structural (path
    parameter + JWT-derived) and never re-assignable through this
    schema."""

    model_config = ConfigDict(extra="forbid")

    proficiency: ProficiencyLevel
