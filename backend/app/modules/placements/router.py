from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequireStaff, RequireStudent, get_db
from app.modules.placements.schemas import (
    PlacementCreate,
    PlacementUpdate,
    StaffPlacementResponse,
    StudentPlacementResponse,
)
from app.modules.placements.service import PlacementService
from app.modules.placements.repository import PlacementRepository
from app.modules.applications.repository import ApplicationRepository
from app.modules.students.repository import StudentRepository
from app.modules.auth.models import User

staff_router = APIRouter(prefix="/staff/placements", tags=["Staff Placements"])
student_router = APIRouter(prefix="/student/placements", tags=["Student Placements"])

def get_placement_service(db: AsyncSession = Depends(get_db)) -> PlacementService:
    placement_repo = PlacementRepository(db)
    application_repo = ApplicationRepository(db)
    student_repo = StudentRepository(db)
    return PlacementService(placement_repo, application_repo, student_repo)

def to_staff_response(p):
    return {
        "placement": p,
        "student": p.application.student,
        "job": p.application.job,
        "company": p.application.job.company,
        "application": p.application
    }

def to_student_response(p):
    return {
        "placement": p,
        "job": p.application.job,
        "company": p.application.job.company,
        "application": p.application
    }


@staff_router.get("", response_model=List[StaffPlacementResponse])
async def list_staff_placements(
    _: RequireStaff,
    search: Optional[str] = Query(None),
    company_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    offer_accepted: Optional[bool] = Query(None),
    service: PlacementService = Depends(get_placement_service),
):
    placements = await service.list_for_staff(
        search=search,
        company_id=company_id,
        department_id=department_id,
        offer_accepted=offer_accepted,
    )
    return [to_staff_response(p) for p in placements]


@staff_router.post("", response_model=StaffPlacementResponse)
async def create_placement(
    data: PlacementCreate,
    _: RequireStaff,
    service: PlacementService = Depends(get_placement_service),
):
    placement = await service.create_placement(data)
    # Return fully loaded response
    p = await service.get_placement_for_staff(placement.id)
    return to_staff_response(p)


@staff_router.get("/{placement_id}", response_model=StaffPlacementResponse)
async def get_staff_placement(
    placement_id: int,
    _: RequireStaff,
    service: PlacementService = Depends(get_placement_service),
):
    p = await service.get_placement_for_staff(placement_id)
    return to_staff_response(p)


@staff_router.patch("/{placement_id}", response_model=StaffPlacementResponse)
async def update_staff_placement(
    placement_id: int,
    data: PlacementUpdate,
    _: RequireStaff,
    service: PlacementService = Depends(get_placement_service),
):
    await service.update_placement(placement_id, data)
    p = await service.get_placement_for_staff(placement_id)
    return to_staff_response(p)


@student_router.get("", response_model=List[StudentPlacementResponse])
async def list_student_placements(
    user: RequireStudent,
    service: PlacementService = Depends(get_placement_service),
):
    placements = await service.list_for_student(user.id)
    return [to_student_response(p) for p in placements]


@student_router.get("/{placement_id}", response_model=StudentPlacementResponse)
async def get_student_placement(
    placement_id: int,
    user: RequireStudent,
    service: PlacementService = Depends(get_placement_service),
):
    p = await service.get_placement_for_student(user.id, placement_id)
    return to_student_response(p)
