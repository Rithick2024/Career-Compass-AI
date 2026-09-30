from datetime import date, datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class JobBaseSchema(BaseModel):
    id: int
    title: str
    role_category: str | None = None
    location: str | None = None
    employment_type: str | None = None
    package_ctc: Decimal | None = None
    application_deadline: date | None = None


class CompanyBaseSchema(BaseModel):
    id: int
    name: str
    industry: str | None = None
    location: str | None = None
    website_url: str | None = None


class StudentBaseSchema(BaseModel):
    id: int
    full_name: str | None = None
    department_id: int | None = None
    cgpa: Decimal | None = None


class ApplicationBaseSchema(BaseModel):
    id: int
    status: str
    applied_at: datetime


class PlacementBase(BaseModel):
    final_package_ctc: Decimal = Field(..., ge=0)
    placement_date: date
    offer_accepted: bool = True


class PlacementCreate(PlacementBase):
    application_id: int


class PlacementUpdate(BaseModel):
    final_package_ctc: Optional[Decimal] = Field(None, ge=0)
    placement_date: Optional[date] = None
    offer_accepted: Optional[bool] = None


class PlacementResponse(PlacementBase):
    id: int
    application_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StaffPlacementResponse(BaseModel):
    placement: PlacementResponse
    student: StudentBaseSchema
    job: JobBaseSchema
    company: CompanyBaseSchema
    application: ApplicationBaseSchema

    model_config = ConfigDict(from_attributes=True)


class StudentPlacementResponse(BaseModel):
    placement: PlacementResponse
    job: JobBaseSchema
    company: CompanyBaseSchema
    application: ApplicationBaseSchema

    model_config = ConfigDict(from_attributes=True)
