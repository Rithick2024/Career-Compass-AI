"""
Pydantic v2 schemas for the skills module — request/response contracts
only. The SQLAlchemy `Skill`/`StudentSkill` models are never returned
directly from a router.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.shared.enums import ProficiencyLevel


class SkillOut(BaseModel):
    """
    Minimal skill representation — used both for the platform catalog
    and nested inside a student's own skill list. Deliberately
    excludes `created_at`/`updated_at` (same minimalism as
    `DepartmentOut` in the student module — those timestamps track the
    catalog entry itself, not something an API consumer needs).
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: Optional[str] = None


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
