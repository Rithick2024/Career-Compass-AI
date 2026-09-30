from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.application_rounds.models import RoundType, ScheduleType


class JobRoundBase(BaseModel):
    round_number: int = Field(..., gt=0)
    round_type: RoundType
    title: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    schedule_type: ScheduleType = ScheduleType.FIXED_TIME
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    duration_minutes: int = Field(60, gt=0)
    meeting_link: Optional[str] = Field(None, max_length=500)
    test_link: Optional[str] = Field(None, max_length=500)
    instructions: Optional[str] = None
    is_required: bool = True
    is_active: bool = True

    # Legacy alias support
    scheduled_at: Optional[datetime] = None

    @model_validator(mode="after")
    def sync_legacy_scheduled_at(self):
        if self.scheduled_at and not self.available_from:
            self.available_from = self.scheduled_at
        return self


class JobRoundCreate(JobRoundBase):
    pass


class JobRoundUpdate(BaseModel):
    round_number: Optional[int] = Field(None, gt=0)
    round_type: Optional[RoundType] = None
    title: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    schedule_type: Optional[ScheduleType] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    meeting_link: Optional[str] = Field(None, max_length=500)
    test_link: Optional[str] = Field(None, max_length=500)
    instructions: Optional[str] = None
    is_required: Optional[bool] = None
    is_active: Optional[bool] = None

    @model_validator(mode="after")
    def sync_legacy_scheduled_at(self):
        if self.scheduled_at and not self.available_from:
            self.available_from = self.scheduled_at
        return self


class JobRoundResponse(JobRoundBase):
    id: int
    job_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
