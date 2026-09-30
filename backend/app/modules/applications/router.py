from typing import List, Optional
from fastapi import APIRouter, Depends

from app.api.deps import DBSession, RequireStudent, RequireStaff
from app.modules.auth.models import User
from app.modules.applications.schemas import (
    ApplicationCreate,
    ApplicationStatusUpdate,
    StudentApplicationResponse,
    StaffApplicationListResponse,
    StaffApplicationDetailResponse,
)
from app.modules.applications.service import ApplicationService


student_applications_router = APIRouter()
staff_applications_router = APIRouter()


@student_applications_router.post(
    "",
    response_model=StudentApplicationResponse,
    status_code=201,
    summary="Submit a job application",
)
async def submit_application(
    data: ApplicationCreate,
    db: DBSession,
    current_user: RequireStudent,
):
    service = ApplicationService(db)
    return await service.create_application(current_user.id, data)


@student_applications_router.get(
    "",
    response_model=List[StudentApplicationResponse],
    summary="List student applications",
)
async def list_student_applications(
    db: DBSession,
    current_user: RequireStudent,
):
    service = ApplicationService(db)
    return await service.list_student_applications(current_user.id)


@student_applications_router.get(
    "/{application_id}",
    response_model=StudentApplicationResponse,
    summary="Get application details",
)
async def get_student_application(
    application_id: int,
    db: DBSession,
    current_user: RequireStudent,
):
    service = ApplicationService(db)
    return await service.get_student_application(current_user.id, application_id)


@student_applications_router.patch(
    "/{application_id}/withdraw",
    response_model=StudentApplicationResponse,
    summary="Withdraw an application",
)
async def withdraw_application(
    application_id: int,
    db: DBSession,
    current_user: RequireStudent,
):
    service = ApplicationService(db)
    return await service.withdraw_application(current_user.id, application_id)


# Staff endpoints

@staff_applications_router.get(
    "",
    response_model=List[StaffApplicationListResponse],
    summary="List all applications",
)
async def list_staff_applications(
    db: DBSession,
    current_user: RequireStaff,
    search: Optional[str] = None,
    job_id: Optional[int] = None,
    status: Optional[str] = None,
    company_id: Optional[int] = None,
):
    service = ApplicationService(db)
    return await service.list_staff_applications(
        search=search, job_id=job_id, status=status, company_id=company_id
    )


@staff_applications_router.get(
    "/{application_id}",
    response_model=StaffApplicationDetailResponse,
    summary="Get application details",
)
async def get_staff_application(
    application_id: int,
    db: DBSession,
    current_user: RequireStaff,
):
    service = ApplicationService(db)
    return await service.get_staff_application(application_id)


@staff_applications_router.patch(
    "/{application_id}/status",
    response_model=StaffApplicationDetailResponse,
    summary="Update application status",
)
async def update_application_status(
    application_id: int,
    data: ApplicationStatusUpdate,
    db: DBSession,
    current_user: RequireStaff,
):
    service = ApplicationService(db)
    return await service.update_staff_application_status(application_id, data)
