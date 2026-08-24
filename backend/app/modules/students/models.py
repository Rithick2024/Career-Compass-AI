"""
Student profile and Department ORM models.

`departments` is a small lookup table (per the finalized Day 2 design —
students reference an existing department rather than each entering
free-text department names). `students` holds one profile row per
`users` row (1:1) via a unique `user_id` foreign key; authentication
fields (email, password, role, is_active) live on `User` and are never
duplicated here.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Department id={self.id} name={self.name!r}>"


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 1:1 with users — every student profile belongs to exactly one
    # existing user account; `unique=True` enforces at most one profile
    # per user. Deleting a user takes its student profile with it.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    # Deliberately nullable: a fresh profile starts empty and the
    # student fills it in progressively via PATCH — see
    # docs/student-module.md for why there's no separate "create"
    # step. If a department is deleted, students referencing it are
    # not deleted — just orphaned back to NULL.
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )

    full_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    graduation_year: Mapped[Optional[int]] = mapped_column(nullable=True)
    # CGPA on a 0-10 scale (precision 4, scale 2 -> up to 99.99, comfortably
    # covers 0.00-10.00).
    cgpa: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # lazy="selectin": always eager-load department with the student row.
    # Async SQLAlchemy can't lazily fetch a relationship attribute outside
    # an active await (raises MissingGreenlet) once the object crosses
    # into the response-serialization layer, so eager loading here — not
    # per-query `selectinload()` calls the repository would have to
    # remember every time — is what keeps that safe by default.
    department: Mapped[Optional["Department"]] = relationship(lazy="selectin")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Student id={self.id} user_id={self.user_id}>"
