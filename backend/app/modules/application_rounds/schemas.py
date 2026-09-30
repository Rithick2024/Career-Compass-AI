from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, AnyHttpUrl

from app.modules.application_rounds.models import RoundType, RoundStatus, RoundResult


class ApplicationRoundBase(BaseModel):
    round_number: int = Field(..., gt=0)
    round_type: RoundType
    title: Optional[str] = Field(None, max_length=150)
    status: RoundStatus = RoundStatus.NOT_STARTED
    result: Optional[RoundResult] = None
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    external_link: Optional[AnyHttpUrl] = None
    notes: Optional[str] = None


class ApplicationRoundCreate(ApplicationRoundBase):
    pass


class ApplicationRoundUpdate(BaseModel):
    round_type: Optional[RoundType] = None
    title: Optional[str] = Field(None, max_length=150)
    status: Optional[RoundStatus] = None
    result: Optional[RoundResult] = None
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    external_link: Optional[AnyHttpUrl] = None
    notes: Optional[str] = None


class ApplicationRoundResponse(ApplicationRoundBase):
    id: int
    application_id: int
    created_at: datetime
    updated_at: datetime
    
    # We serialize the URL as string to avoid issues
    external_link: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
