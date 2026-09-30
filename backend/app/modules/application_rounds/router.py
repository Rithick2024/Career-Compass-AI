from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequireStaff, RequireStudent, get_db
from app.modules.application_rounds.schemas import (
    ApplicationRoundCreate,
    ApplicationRoundUpdate,
    ApplicationRoundResponse,
    StudentAttendanceRequest,
    StaffVerificationRequest,
    StaffResultRequest,
    StaffRescheduleRequest,
)
from app.modules.application_rounds.service import ApplicationRoundService
from app.modules.application_rounds.repository import ApplicationRoundRepository
from app.modules.applications.repository import ApplicationRepository
from app.modules.students.repository import StudentRepository

staff_router = APIRouter(prefix="/staff/applications/{application_id}/rounds", tags=["Staff Application Rounds"])
student_router = APIRouter(prefix="/student/applications/{application_id}/rounds", tags=["Student Application Rounds"])


def get_application_round_service(db: AsyncSession = Depends(get_db)) -> ApplicationRoundService:
    round_repo = ApplicationRoundRepository(db)
    app_repo = ApplicationRepository(db)
    student_repo = StudentRepository(db)
    return ApplicationRoundService(round_repo, app_repo, student_repo)


@staff_router.get("", response_model=List[ApplicationRoundResponse])
async def list_staff_rounds(
    application_id: int,
    _: RequireStaff,
    service: ApplicationRoundService = Depends(get_application_round_service),
):
    return await service.list_for_staff(application_id)


@staff_router.post("", response_model=ApplicationRoundResponse, status_code=201)
async def create_round(
    application_id: int,
    data: ApplicationRoundCreate,
    _: RequireStaff,
    service: ApplicationRoundService = Depends(get_application_round_service),
):
    return await service.create_for_staff(application_id, data)


@staff_router.patch("/{round_id}", response_model=ApplicationRoundResponse)
async def update_round(
    application_id: int,
    round_id: int,
    data: ApplicationRoundUpdate,
    _: RequireStaff,
    service: ApplicationRoundService = Depends(get_application_round_service),
):
    return await service.update_for_staff(application_id, round_id, data)


@staff_router.patch("/{round_id}/verification", response_model=ApplicationRoundResponse)
async def verify_round_attendance(
    application_id: int,
    round_id: int,
    data: StaffVerificationRequest,
    staff_user: RequireStaff,
    service: ApplicationRoundService = Depends(get_application_round_service),
):
    return await service.verify_staff_attendance(
        application_id, round_id, staff_user.id, data.verification
    )


@staff_router.patch("/{round_id}/result", response_model=ApplicationRoundResponse)
async def set_round_result(
    application_id: int,
    round_id: int,
    data: StaffResultRequest,
    _: RequireStaff,
    service: ApplicationRoundService = Depends(get_application_round_service),
):
    return await service.set_staff_result(application_id, round_id, data.result)


@staff_router.patch("/{round_id}/reschedule", response_model=ApplicationRoundResponse)
async def reschedule_round(
    application_id: int,
    round_id: int,
    data: StaffRescheduleRequest,
    _: RequireStaff,
    service: ApplicationRoundService = Depends(get_application_round_service),
):
    return await service.reschedule_staff_round(application_id, round_id, data)


@student_router.get("", response_model=List[ApplicationRoundResponse])
async def list_student_rounds(
    application_id: int,
    user: RequireStudent,
    service: ApplicationRoundService = Depends(get_application_round_service),
):
    return await service.list_for_student(application_id, user.id)


@student_router.get("/{round_id}", response_model=ApplicationRoundResponse)
async def get_student_round(
    application_id: int,
    round_id: int,
    user: RequireStudent,
    service: ApplicationRoundService = Depends(get_application_round_service),
):
    return await service.get_for_student(application_id, round_id, user.id)


@student_router.post("/{round_id}/attendance", response_model=ApplicationRoundResponse)
async def report_attendance(
    application_id: int,
    round_id: int,
    data: StudentAttendanceRequest,
    user: RequireStudent,
    service: ApplicationRoundService = Depends(get_application_round_service),
):
    return await service.report_student_attendance(
        application_id, round_id, user.id, data.attendance
    )
