"""
Shared enums, used across both the Pydantic (API) layer and the
SQLAlchemy (persistence) layer.

Convention: every enum here subclasses `str, Enum` so a single
definition works as a Pydantic field type (JSON-serializable,
validated) *and* as a SQLAlchemy `Enum` column type (native
PostgreSQL ENUM), without duplicating the value list in two places.
Feature modules import from here rather than declaring their own
ad hoc enums.
"""

from enum import Enum


class RoleEnum(str, Enum):
    """Application-wide user roles."""

    STUDENT = "student"
    STAFF = "staff"


class ProficiencyLevel(str, Enum):
    """
    Self-reported skill proficiency (used on `student_skills.proficiency`).

    Three levels, matching the existing frontend's confirmed contract
    (Beginner/Intermediate/Advanced — no Expert level exists in the
    UI). An earlier version of this backend included a fourth
    `EXPERT` value before the frontend contract was inspected; it was
    removed via a corrective migration
    (`alembic/versions/38f0da1163aa_remove_expert_proficiency_level.py`)
    rather than rewriting the migration that first created this enum.
    See docs/skills-module.md.
    """

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
