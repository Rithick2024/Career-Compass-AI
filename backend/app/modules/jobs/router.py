"""
Staff Job Management API endpoints.
"""

from typing import List, Optional

from fastapi import APIRouter, Query, status

from app.api.deps import JobServiceDep, RequireStaff, RequireStudent
from app.modules.jobs.schemas import (
    JobCreateRequest,
    JobResponse,
    JobStatusUpdateRequest,
    JobUpdateRequest,
    StudentJobResponse,
)

staff_jobs_router = APIRouter(prefix="/staff/jobs", tags=["Staff Jobs"])


@staff_jobs_router.get("", response_model=List[JobResponse], status_code=status.HTTP_200_OK)
async def list_jobs(
    current_user: RequireStaff,
    job_service: JobServiceDep,
    search: Optional[str] = Query(default=None, description="Search by title, company, location, role"),
    company_id: Optional[int] = Query(default=None, description="Filter by company ID"),
    department_id: Optional[int] = Query(default=None, description="Filter by eligible department ID"),
    status_filter: str = Query(default="all", alias="status", pattern="^(all|active|inactive|expired)$"),
) -> List[JobResponse]:
    """Return list of job postings for staff management."""
    return await job_service.list_jobs(
        search=search,
        company_id=company_id,
        department_id=department_id,
        status=status_filter,
    )


@staff_jobs_router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    data: JobCreateRequest,
    current_user: RequireStaff,
    job_service: JobServiceDep,
) -> JobResponse:
    """Create a new job posting with required skills and eligible departments atomically."""
    return await job_service.create_job(data)


@staff_jobs_router.get("/{job_id}", response_model=JobResponse, status_code=status.HTTP_200_OK)
async def get_job(
    job_id: int,
    current_user: RequireStaff,
    job_service: JobServiceDep,
) -> JobResponse:
    """Get a single job posting by ID."""
    return await job_service.get_job(job_id)


@staff_jobs_router.patch("/{job_id}", response_model=JobResponse, status_code=status.HTTP_200_OK)
async def update_job(
    job_id: int,
    data: JobUpdateRequest,
    current_user: RequireStaff,
    job_service: JobServiceDep,
) -> JobResponse:
    """Update editable details, required skills, or eligible departments of a job posting."""
    return await job_service.update_job(job_id, data)


@staff_jobs_router.patch("/{job_id}/status", response_model=JobResponse, status_code=status.HTTP_200_OK)
async def update_job_status(
    job_id: int,
    data: JobStatusUpdateRequest,
    current_user: RequireStaff,
    job_service: JobServiceDep,
) -> JobResponse:
    """Update job active status (soft activation/deactivation)."""
    return await job_service.update_job_status(job_id, data)


student_jobs_router = APIRouter(prefix="/student/jobs", tags=["Student Jobs"])


@student_jobs_router.get("", response_model=List[StudentJobResponse], status_code=status.HTTP_200_OK)
async def list_student_jobs(
    current_user: RequireStudent,
    job_service: JobServiceDep,
    search: Optional[str] = Query(default=None, description="Search by title, company, or role category"),
    company_id: Optional[int] = Query(default=None, description="Filter by company ID"),
    employment_type: Optional[str] = Query(default=None, description="Filter by employment type"),
    eligible_only: bool = Query(default=False, description="Show only eligible jobs"),
) -> List[StudentJobResponse]:
    """Return list of open and visible jobs for student discovery."""
    return await job_service.list_student_jobs(
        user_id=current_user.id,
        search=search,
        company_id=company_id,
        employment_type=employment_type,
        eligible_only=eligible_only,
    )


@student_jobs_router.get("/{job_id}", response_model=StudentJobResponse, status_code=status.HTTP_200_OK)
async def get_student_job(
    job_id: int,
    current_user: RequireStudent,
    job_service: JobServiceDep,
) -> StudentJobResponse:
    """Get a single visible job posting by ID for student."""
    return await job_service.get_student_job(
        user_id=current_user.id,
        job_id=job_id,
    )
