"""
Job Round (Template / Workflow Definition) ORM model.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.modules.application_rounds.models import RoundType, ScheduleType

if TYPE_CHECKING:
    from app.modules.jobs.models import Job


class JobRound(Base):
    __tablename__ = "job_rounds"
    __table_args__ = (
        UniqueConstraint("job_id", "round_number", name="uq_job_rounds_job_id_round_num"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    round_number: Mapped[int] = mapped_column(nullable=False)

    round_type: Mapped[RoundType] = mapped_column(
        SAEnum(
            RoundType,
            name="round_type",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )

    title: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    schedule_type: Mapped[ScheduleType] = mapped_column(
        SAEnum(
            ScheduleType,
            name="schedule_type_enum",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=ScheduleType.FIXED_TIME.value,
        default=ScheduleType.FIXED_TIME,
    )

    available_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    available_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(nullable=False, server_default="60", default=60)

    meeting_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    test_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    job: Mapped["Job"] = relationship(back_populates="rounds", lazy="selectin")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<JobRound id={self.id} job_id={self.job_id} round_number={self.round_number}>"
