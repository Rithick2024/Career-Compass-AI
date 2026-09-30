"""
Application ORM model.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.modules.students.models import Student
from app.modules.jobs.models import Job
from app.modules.resumes.models import Resume

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.modules.placements.models import Placement
    from app.modules.application_rounds.models import ApplicationRound
    from typing import List


class ApplicationStatus(str, Enum):
    PENDING = "Pending"
    REVIEWING = "Reviewing"
    INTERVIEW = "Interview"
    OFFERED = "Offered"
    REJECTED = "Rejected"
    WITHDRAWN = "Withdrawn"


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("student_id", "job_id", name="uq_applications_student_id_job_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(
            ApplicationStatus,
            name="application_status",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=ApplicationStatus.PENDING.value,
        index=True
    )

    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    student: Mapped["Student"] = relationship(lazy="selectin")
    job: Mapped["Job"] = relationship(lazy="selectin")
    resume: Mapped["Resume"] = relationship(lazy="selectin")
    placement: Mapped["Placement"] = relationship(back_populates="application", uselist=False, lazy="selectin")
    rounds: Mapped[list["ApplicationRound"]] = relationship(back_populates="application", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Application id={self.id} student_id={self.student_id} job_id={self.job_id} status={self.status.value}>"
