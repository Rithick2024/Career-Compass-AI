from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class ApplicationStatusCount(BaseModel):
    status: str
    count: int

class DepartmentPlacementCount(BaseModel):
    department: str
    count: int

class RoundTypeCount(BaseModel):
    round_type: str
    count: int

class StaffRecruitmentSummary(BaseModel):
    total_rounds: int
    scheduled_rounds: int
    completed_rounds: int
    passed_rounds: int
    failed_rounds: int
    pass_rate: float
    rounds_by_type: List[RoundTypeCount]

class StaffAnalyticsOverview(BaseModel):
    total_students: int
    active_jobs: int
    pending_applications: int
    accepted_placements: int
    average_package: float
    applications_by_status: List[ApplicationStatusCount]
    placements_by_department: List[DepartmentPlacementCount]
    recruitment_summary: StaffRecruitmentSummary

class UpcomingRound(BaseModel):
    id: int
    round_type: str
    job_title: str
    company_name: str
    scheduled_at: datetime
    status: str

    model_config = ConfigDict(from_attributes=True)

class RecentApplication(BaseModel):
    id: int
    job_title: str
    company_name: str
    status: str
    applied_at: datetime

    model_config = ConfigDict(from_attributes=True)

class StudentRecruitmentSummary(BaseModel):
    total_rounds: int
    scheduled_rounds: int
    completed_rounds: int
    passed_rounds: int
    failed_rounds: int

class PlacementSummary(BaseModel):
    has_accepted_placement: bool
    accepted_placement_count: int
    latest_accepted_placement_company: Optional[str] = None
    latest_accepted_placement_package: Optional[float] = None
    latest_accepted_placement_date: Optional[datetime] = None

class StudentAnalyticsOverview(BaseModel):
    active_applications: int
    total_offers: int
    application_status_summary: List[ApplicationStatusCount]
    upcoming_rounds: List[UpcomingRound]
    recent_applications: List[RecentApplication]
    recruitment_summary: StudentRecruitmentSummary
    placement_summary: PlacementSummary
