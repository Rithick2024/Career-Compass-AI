from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, AnyHttpUrl, model_validator

from app.modules.application_rounds.models import (
    RoundType,
    RoundStatus,
    RoundResult,
    ScheduleType,
    StudentAttendance,
    StaffVerification,
)


class ApplicationRoundBase(BaseModel):
    round_number: int = Field(..., gt=0)
    round_type: RoundType
    title: Optional[str] = Field(None, max_length=150)
    schedule_type: ScheduleType = ScheduleType.FIXED_TIME
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    duration_minutes: int = Field(60, gt=0)
    status: RoundStatus = RoundStatus.NOT_STARTED
    result: Optional[RoundResult] = None
    completed_at: Optional[datetime] = None
    external_link: Optional[AnyHttpUrl] = None
    notes: Optional[str] = None

    # Support scheduled_at as legacy alias for available_from
    scheduled_at: Optional[datetime] = None

    @model_validator(mode="after")
    def sync_legacy_scheduled_at(self):
        if self.scheduled_at and not self.available_from:
            self.available_from = self.scheduled_at
        elif self.available_from and not self.scheduled_at:
            self.scheduled_at = self.available_from
        return self


class ApplicationRoundCreate(ApplicationRoundBase):
    pass


class ApplicationRoundUpdate(BaseModel):
    round_type: Optional[RoundType] = None
    title: Optional[str] = Field(None, max_length=150)
    schedule_type: Optional[ScheduleType] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[RoundStatus] = None
    result: Optional[RoundResult] = None
    completed_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    external_link: Optional[AnyHttpUrl] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def sync_legacy_scheduled_at(self):
        if self.scheduled_at and not self.available_from:
            self.available_from = self.scheduled_at
        return self


class StudentAttendanceRequest(BaseModel):
    attendance: StudentAttendance


class StaffVerificationRequest(BaseModel):
    verification: StaffVerification


class StaffResultRequest(BaseModel):
    result: RoundResult


class StaffRescheduleRequest(BaseModel):
    schedule_type: Optional[ScheduleType] = None
    new_available_from: Optional[datetime] = None
    new_available_until: Optional[datetime] = None
    new_scheduled_at: Optional[datetime] = None
    reason: Optional[str] = Field(None, max_length=255)

    @model_validator(mode="after")
    def sync_legacy_scheduled_at(self):
        if self.new_scheduled_at and not self.new_available_from:
            self.new_available_from = self.new_scheduled_at
        return self


class ApplicationRoundResponse(ApplicationRoundBase):
    id: int
    application_id: int
    job_round_id: Optional[int] = None
    description: Optional[str] = None
    meeting_link: Optional[str] = None
    test_link: Optional[str] = None
    instructions: Optional[str] = None
    schedule_type: ScheduleType = ScheduleType.FIXED_TIME
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    session_end_at: Optional[datetime] = None
    duration_minutes: int = 60
    student_attendance: StudentAttendance = StudentAttendance.NOT_REPORTED
    student_action_at: Optional[datetime] = None
    staff_verification: StaffVerification = StaffVerification.PENDING
    staff_verified_at: Optional[datetime] = None
    staff_verified_by_id: Optional[int] = None
    rescheduled_at: Optional[datetime] = None
    reschedule_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # We serialize the URL as string to avoid issues
    external_link: Optional[str] = None

    # Derived UI/presentation fields
    derived_state: str = "UPCOMING"
    can_student_respond: bool = False
    can_staff_verify: bool = False
    can_staff_set_result: bool = False
    is_upcoming: bool = False
    is_due: bool = False
    is_overdue: bool = False

    model_config = ConfigDict(from_attributes=True)
