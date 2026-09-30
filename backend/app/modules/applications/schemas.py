"""
Schemas for applications.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.modules.applications.models import ApplicationStatus
from app.modules.jobs.schemas import JobResponse, StudentCompanyResponse
from app.modules.resumes.schemas import ResumeResponse


class ApplicationCreate(BaseModel):
    job_id: int
    resume_id: int


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


class StudentApplicationResponse(BaseModel):
    id: int
    student_id: int
    job_id: int
    resume_id: int
    status: ApplicationStatus
    applied_at: datetime
    updated_at: datetime
    
    # Flattened data as per requirements
    job_title: str
    role_category: Optional[str] = None
    location: Optional[str] = None
    employment_type: str
    ctc_lpa: Optional[float] = None
    company_id: int
    company_name: str
    company_industry: Optional[str] = None
    submitted_resume_title: str

    model_config = ConfigDict(from_attributes=True)


class StaffApplicationListResponse(BaseModel):
    id: int
    student_name: str
    student_email: str
    department: Optional[str] = None
    cgpa: Optional[float] = None
    job_title: str
    company_name: str
    resume_title: str
    status: ApplicationStatus
    applied_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StaffApplicationDetailResponse(BaseModel):
    id: int
    status: ApplicationStatus
    applied_at: datetime
    updated_at: datetime

    # Flattened detailed data
    student_name: str
    student_email: str
    department: Optional[str] = None
    cgpa: Optional[float] = None

    job_title: str
    company_name: str
    location: Optional[str] = None
    employment_type: str
    ctc_lpa: Optional[float] = None
    deadline: Optional[datetime] = None

    resume_id: int
    resume_title: str
    resume_file_name: str
    resume_file_type: str
    resume_file_size: int

    model_config = ConfigDict(from_attributes=True)
