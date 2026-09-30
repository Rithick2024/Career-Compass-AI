"""
Application Round ORM model.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
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

if TYPE_CHECKING:
    from app.modules.applications.models import Application


class RoundType(str, Enum):
    ONLINE_ASSESSMENT = "Online Assessment"
    CODING_TEST = "Coding Test"
    APTITUDE_TEST = "Aptitude Test"
    TECHNICAL_INTERVIEW = "Technical Interview"
    MANAGERIAL_INTERVIEW = "Managerial Interview"
    HR_INTERVIEW = "HR Interview"
    GROUP_DISCUSSION = "Group Discussion"
    OTHER = "Other"


class RoundStatus(str, Enum):
    NOT_STARTED = "Not Started"
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class RoundResult(str, Enum):
    PENDING = "Pending"
    PASSED = "Passed"
    FAILED = "Failed"
    NOT_ATTENDED = "Not Attended"


class ApplicationRound(Base):
    __tablename__ = "application_rounds"
    __table_args__ = (
        UniqueConstraint("application_id", "round_number", name="uq_application_rounds_app_id_round_num"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )

    round_number: Mapped[int] = mapped_column(nullable=False)

    round_type: Mapped[RoundType] = mapped_column(
        SAEnum(
            RoundType,
            name="round_type",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False
    )

    title: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    status: Mapped[RoundStatus] = mapped_column(
        SAEnum(
            RoundStatus,
            name="round_status",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=RoundStatus.NOT_STARTED.value
    )

    result: Mapped[Optional[RoundResult]] = mapped_column(
        SAEnum(
            RoundResult,
            name="round_result",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=True
    )

    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    external_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    application: Mapped["Application"] = relationship(back_populates="rounds", lazy="selectin")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ApplicationRound id={self.id} application_id={self.application_id} round_number={self.round_number}>"
