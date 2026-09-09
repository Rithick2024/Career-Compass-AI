"""
Resume ORM model.

`resumes` is a 0..1 structured extension of `students` (unique
`student_id` FK, `ON DELETE CASCADE`) — a student may have at most one
resume profile, and it never exists without a student. Fields already
captured elsewhere (full_name, email, phone, department, graduation_year,
cgpa, skills) are deliberately NOT duplicated here; this table only
holds resume-specific structured content.

MVP scope: `professional_summary` and `career_objective` only — no
education/experience/projects/certifications sub-tables yet (see
docs/resume-module.md for the planned future extension and why this
model is designed so those can be added later as separate one-to-many
tables without breaking this API).
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 0..1 with students — `unique=True` enforces at most one resume
    # per student. Deleting a student's profile takes their resume
    # with it.
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    professional_summary: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    career_objective: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

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
        return f"<Resume id={self.id} student_id={self.student_id}>"
