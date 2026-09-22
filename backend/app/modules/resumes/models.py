"""
Resume ORM model for multiple resume documents per student.

`resumes` represents a 1..N relationship with `students` (`student_id` FK,
`ON DELETE CASCADE`). A student may create multiple resume documents (e.g.,
Frontend Developer, Data Analyst, General), each tied to a physical file.

Exactly one resume per student can be designated as the default (`is_default=True`).
This invariant is enforced at the service level and via a partial unique index.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 1..N with students (unique=False so a student can have multiple resumes)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # File metadata
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
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

    __table_args__ = (
        Index(
            "idx_student_default_resume",
            "student_id",
            unique=True,
            postgresql_where=(is_default.is_(True)),
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Resume id={self.id} student_id={self.student_id} title={self.title!r} is_default={self.is_default}>"
