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
    from app.modules.job_rounds.models import JobRound


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


class StudentAttendance(str, Enum):
    NOT_REPORTED = "NOT_REPORTED"
    ATTENDED = "ATTENDED"
    ABSENT = "ABSENT"


class StaffVerification(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class ScheduleType(str, Enum):
    FIXED_TIME = "FIXED_TIME"
    AVAILABILITY_WINDOW = "AVAILABILITY_WINDOW"


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

    schedule_type: Mapped[ScheduleType] = mapped_column(
        SAEnum(
            ScheduleType,
            name="schedule_type_enum",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=ScheduleType.FIXED_TIME.value,
        default=ScheduleType.FIXED_TIME
    )

    available_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    available_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    duration_minutes: Mapped[int] = mapped_column(nullable=False, server_default="60", default=60)

    student_attendance: Mapped[StudentAttendance] = mapped_column(
        SAEnum(
            StudentAttendance,
            name="student_attendance_enum",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=StudentAttendance.NOT_REPORTED.value,
        default=StudentAttendance.NOT_REPORTED
    )
    student_action_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    staff_verification: Mapped[StaffVerification] = mapped_column(
        SAEnum(
            StaffVerification,
            name="staff_verification_enum",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=StaffVerification.PENDING.value,
        default=StaffVerification.PENDING
    )
    staff_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    staff_verified_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    rescheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reschedule_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    job_round_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("job_rounds.id", ondelete="SET NULL"), nullable=True, index=True
    )

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meeting_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    test_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
    job_round: Mapped[Optional["JobRound"]] = relationship(lazy="selectin")

    @property
    def scheduled_at(self) -> Optional[datetime]:
        return self.available_from

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ApplicationRound id={self.id} application_id={self.application_id} round_number={self.round_number}>"

