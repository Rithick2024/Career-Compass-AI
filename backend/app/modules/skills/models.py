"""
Skill catalog and per-student skill assignment ORM models.

`skills` is a small platform-level lookup/catalog table — students
pick from existing skills rather than each creating arbitrary
duplicate entries (same pattern as `departments` in the student
module). `student_skills` is the many-to-many association between
`students` and `skills`, carrying the student's proficiency for that
particular skill.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.shared.enums import ProficiencyLevel


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Skill id={self.id} name={self.name!r} is_active={self.is_active}>"


class StudentSkill(Base):
    __tablename__ = "student_skills"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "skill_id", name="uq_student_skills_student_id_skill_id"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    # ON DELETE CASCADE on both sides: if the student profile is
    # deleted, their skill entries go with it; if a skill is ever
    # removed from the catalog (no admin API for that exists yet),
    # any student assignment of it is removed too rather than left
    # pointing at nothing — `skill_id` is NOT NULL, so SET NULL
    # (the pattern used for the optional `students.department_id`)
    # isn't an option here.
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )

    proficiency: Mapped[ProficiencyLevel] = mapped_column(
        SAEnum(
            ProficiencyLevel,
            name="proficiency_level",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # lazy="selectin": same reasoning as Student.department — always
    # eager-load the related Skill so response serialization can read
    # it safely without a separate loader call the repository would
    # otherwise have to remember on every query.
    skill: Mapped["Skill"] = relationship(lazy="selectin")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<StudentSkill id={self.id} student_id={self.student_id} skill_id={self.skill_id}>"
