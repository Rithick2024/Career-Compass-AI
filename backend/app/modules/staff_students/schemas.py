"""
Pydantic v2 schemas for Staff Read-Only Student Directory.
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.students.schemas import DepartmentOut
from app.shared.enums import ProficiencyLevel


class StaffStudentListItem(BaseModel):
    """Staff directory summary item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    email: str
    full_name: Optional[str] = None
    department: Optional[DepartmentOut] = None
    graduation_year: Optional[int] = None
    cgpa: Optional[float] = None
    skills_count: int = 0
    resumes_count: int = 0
    is_active: bool


class StaffStudentSkillResponse(BaseModel):
    """Skill assignment details for staff student view."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    skill_id: int
    skill_name: str
    category: Optional[str] = None
    proficiency: ProficiencyLevel


class StaffStudentResumeResponse(BaseModel):
    """Resume details for staff student view (never leaks file_path)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    file_name: str
    file_type: str
    file_size: int
    is_default: bool
    created_at: datetime
    updated_at: datetime


class StaffStudentDetailResponse(BaseModel):
    """Detailed student profile representation for staff."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    department: Optional[DepartmentOut] = None
    graduation_year: Optional[int] = None
    cgpa: Optional[float] = None
    skills: List[StaffStudentSkillResponse] = Field(default_factory=list)
    resumes: List[StaffStudentResumeResponse] = Field(default_factory=list)
    is_active: bool
    created_at: datetime
    updated_at: datetime
