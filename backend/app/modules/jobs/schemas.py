"""
Pydantic v2 schemas for the Job module — request/response contracts.
"""

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.companies.schemas import CompanyResponse
from app.modules.students.schemas import DepartmentOut
from app.shared.enums import ProficiencyLevel
from app.modules.job_rounds.schemas import JobRoundResponse


class JobRequiredSkillRequest(BaseModel):
    skill_id: int
    min_proficiency: Optional[ProficiencyLevel] = None


class JobRequiredSkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    skill_id: int
    skill_name: str
    category: Optional[str] = None
    min_proficiency: Optional[ProficiencyLevel] = None


class JobEligibleDepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    department_id: int
    department_name: str


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    company: CompanyResponse
    title: str
    description: Optional[str] = None
    role_category: Optional[str] = None
    location: Optional[str] = None
    employment_type: str = "Full-time"
    ctc_lpa: Optional[float] = None
    min_cgpa: Optional[float] = None
    application_start_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    work_mode: Optional[str] = None
    instructions: Optional[str] = None
    is_active: bool
    is_expired: bool = False
    derived_status: str = "Open"
    required_skills: List[JobRequiredSkillResponse] = Field(default_factory=list)
    eligible_departments: List[JobEligibleDepartmentResponse] = Field(default_factory=list)
    rounds: List[JobRoundResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class JobCreateRequest(BaseModel):
    company_id: int
    title: str = Field(min_length=1, max_length=150)
    description: Optional[str] = Field(default=None, max_length=5000)
    role_category: Optional[str] = Field(default=None, max_length=100)
    location: Optional[str] = Field(default=None, max_length=150)
    employment_type: str = Field(default="Full-time", max_length=50)
    ctc_lpa: Optional[float] = Field(default=None, ge=0)
    min_cgpa: Optional[float] = Field(default=None, ge=0, le=10)
    application_start_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    work_mode: Optional[str] = Field(default=None, max_length=50)
    instructions: Optional[str] = Field(default=None, max_length=5000)
    required_skills: List[JobRequiredSkillRequest] = Field(default_factory=list)
    eligible_department_ids: List[int] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Job title cannot be blank.")
        return value

    @field_validator("description", "role_category", "location", "work_mode", "instructions", mode="before")
    @classmethod
    def empty_str_to_none(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
        return value


class JobUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: Optional[int] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=150)
    description: Optional[str] = Field(default=None, max_length=5000)
    role_category: Optional[str] = Field(default=None, max_length=100)
    location: Optional[str] = Field(default=None, max_length=150)
    employment_type: Optional[str] = Field(default=None, max_length=50)
    ctc_lpa: Optional[float] = Field(default=None, ge=0)
    min_cgpa: Optional[float] = Field(default=None, ge=0, le=10)
    application_start_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    work_mode: Optional[str] = Field(default=None, max_length=50)
    instructions: Optional[str] = Field(default=None, max_length=5000)
    required_skills: Optional[List[JobRequiredSkillRequest]] = None
    eligible_department_ids: Optional[List[int]] = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("Job title cannot be blank.")
        return value

    @field_validator("description", "role_category", "location", "work_mode", "instructions", mode="before")
    @classmethod
    def empty_str_to_none(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
        return value


class JobStatusUpdateRequest(BaseModel):
    is_active: bool


class StudentCompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    industry: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None


class StudentJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    role_category: Optional[str] = None
    location: Optional[str] = None
    employment_type: str = "Full-time"
    ctc_lpa: Optional[float] = None
    min_cgpa: Optional[float] = None
    application_start_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    work_mode: Optional[str] = None
    instructions: Optional[str] = None
    derived_status: str = "Open"
    
    company: StudentCompanyResponse
    required_skills: List[JobRequiredSkillResponse] = Field(default_factory=list)
    eligible_departments: List[JobEligibleDepartmentResponse] = Field(default_factory=list)
    rounds: List[JobRoundResponse] = Field(default_factory=list)
    
    is_department_eligible: bool = False
    is_cgpa_eligible: bool = False
    is_fully_eligible: bool = False
