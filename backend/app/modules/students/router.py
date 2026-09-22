"""
Student profile endpoints. Routers stay thin: parse request -> call
service -> return response. All business logic lives in
`StudentService`.
"""

from typing import List

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, RequireStaff, RequireStudent, StudentServiceDep
from app.modules.students.schemas import (
    DepartmentCreateRequest,
    DepartmentResponse,
    DepartmentStatusUpdateRequest,
    DepartmentUpdateRequest,
    StudentProfileResponse,
    StudentProfileUpdateRequest,
)

router = APIRouter(prefix="/students", tags=["Students"])
departments_router = APIRouter(prefix="/departments", tags=["Departments"])
staff_departments_router = APIRouter(prefix="/staff/departments", tags=["Staff Departments"])


@router.get("/me", response_model=StudentProfileResponse, status_code=status.HTTP_200_OK)
async def get_my_profile(
    current_user: RequireStudent, student_service: StudentServiceDep
) -> StudentProfileResponse:
    """Return the authenticated student's profile."""
    return await student_service.get_my_profile(current_user.id)


@router.patch("/me", response_model=StudentProfileResponse, status_code=status.HTTP_200_OK)
async def update_my_profile(
    data: StudentProfileUpdateRequest,
    current_user: RequireStudent,
    student_service: StudentServiceDep,
) -> StudentProfileResponse:
    """Update the authenticated student's own profile. Only supplied fields change."""
    return await student_service.update_my_profile(current_user.id, data)


# --- Public / Student Department Endpoint ---

@departments_router.get("", response_model=List[DepartmentResponse], status_code=status.HTTP_200_OK)
async def list_active_departments(
    current_user: CurrentUser, student_service: StudentServiceDep
) -> List[DepartmentResponse]:
    """Return active departments for student selection."""
    return await student_service.list_active_departments()


# --- Staff Department Endpoints ---

@staff_departments_router.get("", response_model=List[DepartmentResponse], status_code=status.HTTP_200_OK)
async def list_staff_departments(
    current_user: RequireStaff, student_service: StudentServiceDep
) -> List[DepartmentResponse]:
    """Return all departments for staff management."""
    return await student_service.list_all_departments()


@staff_departments_router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    data: DepartmentCreateRequest,
    current_user: RequireStaff,
    student_service: StudentServiceDep,
) -> DepartmentResponse:
    """Create a new department."""
    return await student_service.create_department(data)


@staff_departments_router.patch("/{department_id}", response_model=DepartmentResponse, status_code=status.HTTP_200_OK)
async def update_department(
    department_id: int,
    data: DepartmentUpdateRequest,
    current_user: RequireStaff,
    student_service: StudentServiceDep,
) -> DepartmentResponse:
    """Update a department's name."""
    return await student_service.update_department(department_id, data)


@staff_departments_router.patch("/{department_id}/status", response_model=DepartmentResponse, status_code=status.HTTP_200_OK)
async def update_department_status(
    department_id: int,
    data: DepartmentStatusUpdateRequest,
    current_user: RequireStaff,
    student_service: StudentServiceDep,
) -> DepartmentResponse:
    """Update a department's active status."""
    return await student_service.update_department_status(department_id, data)
