"""
Job, JobRequiredSkill, and JobEligibleDepartment ORM models.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.modules.companies.models import Company
from app.modules.skills.models import Skill
from app.modules.students.models import Department
from app.shared.enums import ProficiencyLevel


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    role_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    employment_type: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="Full-time"
    )

    ctc_lpa: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    min_cgpa: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)

    deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", index=True
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

    # Relationships
    company: Mapped["Company"] = relationship(lazy="selectin")
    required_skills: Mapped[list["JobRequiredSkill"]] = relationship(
        lazy="selectin", cascade="all, delete-orphan"
    )
    eligible_departments: Mapped[list["JobEligibleDepartment"]] = relationship(
        lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Job id={self.id} title={self.title!r} company_id={self.company_id} is_active={self.is_active}>"


class JobRequiredSkill(Base):
    __tablename__ = "job_required_skills"
    __table_args__ = (
        UniqueConstraint("job_id", "skill_id", name="uq_job_required_skills_job_id_skill_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )

    min_proficiency: Mapped[Optional[ProficiencyLevel]] = mapped_column(
        SAEnum(
            ProficiencyLevel,
            name="proficiency_level",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=True,
    )

    skill: Mapped["Skill"] = relationship(lazy="selectin")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<JobRequiredSkill job_id={self.job_id} skill_id={self.skill_id}>"


class JobEligibleDepartment(Base):
    __tablename__ = "job_eligible_departments"
    __table_args__ = (
        UniqueConstraint(
            "job_id", "department_id", name="uq_job_eligible_departments_job_id_department_id"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True
    )

    department: Mapped["Department"] = relationship(lazy="selectin")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<JobEligibleDepartment job_id={self.job_id} department_id={self.department_id}>"
