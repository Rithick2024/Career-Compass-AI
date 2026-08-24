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
    ADMIN = "admin"
