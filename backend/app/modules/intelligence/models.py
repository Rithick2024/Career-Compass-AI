"""
ORM models for Improvement Plans and Action Items.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ImprovementPlan(Base):
    __tablename__ = "improvement_plans"
    __table_args__ = (
        UniqueConstraint("student_id", "job_id", name="uq_improvement_plans_student_job"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
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

    actions: Mapped[List["ImprovementPlanAction"]] = relationship(
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="ImprovementPlanAction.id",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ImprovementPlan id={self.id} student_id={self.student_id} job_id={self.job_id}>"


class ImprovementPlanAction(Base):
    __tablename__ = "improvement_plan_actions"

    id: Mapped[int] = mapped_column(primary_key=True)

    plan_id: Mapped[int] = mapped_column(
        ForeignKey("improvement_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("skills.id", ondelete="SET NULL"), nullable=True
    )

    skill_name: Mapped[str] = mapped_column(String(100), nullable=False)
    current_proficiency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_proficiency: Mapped[str] = mapped_column(String(50), nullable=False)

    priority: Mapped[str] = mapped_column(String(20), nullable=False, server_default="MEDIUM")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="PENDING")

    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    suggested_activity: Mapped[str] = mapped_column(Text, nullable=False)
    completion_criteria: Mapped[str] = mapped_column(String(500), nullable=False)

    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    evidence_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    evidence_reference: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
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
        return f"<ImprovementPlanAction id={self.id} plan_id={self.plan_id} skill={self.skill_name!r} status={self.status}>"
