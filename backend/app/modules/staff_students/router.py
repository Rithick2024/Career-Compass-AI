"""
Staff Student Directory API endpoints.
"""

from typing import List, Optional

from fastapi import APIRouter, Query, status
from fastapi.responses import FileResponse

from app.api.deps import RequireStaff, StaffStudentServiceDep
from app.modules.staff_students.schemas import (
    StaffStudentDetailResponse,
    StaffStudentListItem,
)

staff_students_router = APIRouter(prefix="/staff/students", tags=["Staff Students"])


@staff_students_router.get("", response_model=List[StaffStudentListItem], status_code=status.HTTP_200_OK)
async def list_students(
    current_user: RequireStaff,
    staff_student_service: StaffStudentServiceDep,
    search: Optional[str] = Query(default=None, description="Search by name, email, or phone"),
    department_id: Optional[int] = Query(default=None, description="Filter by department ID"),
    graduation_year: Optional[int] = Query(default=None, description="Filter by graduation batch year"),
) -> List[StaffStudentListItem]:
    """Return list of registered students for staff directory."""
    return await staff_student_service.list_students(
        search=search,
        department_id=department_id,
        graduation_year=graduation_year,
    )


@staff_students_router.get("/{student_id}", response_model=StaffStudentDetailResponse, status_code=status.HTTP_200_OK)
async def get_student_detail(
    student_id: int,
    current_user: RequireStaff,
    staff_student_service: StaffStudentServiceDep,
) -> StaffStudentDetailResponse:
    """Return complete detailed student profile for staff view."""
    return await staff_student_service.get_student_detail(student_id)


@staff_students_router.get("/{student_id}/resumes/{resume_id}/file")
async def download_student_resume_file(
    student_id: int,
    resume_id: int,
    current_user: RequireStaff,
    staff_student_service: StaffStudentServiceDep,
) -> FileResponse:
    """Download/preview a student's resume document for staff review."""
    absolute_path, file_name, media_type = await staff_student_service.get_student_resume_file_location(
        student_id=student_id, resume_id=resume_id
    )
    return FileResponse(
        path=absolute_path,
        filename=file_name,
        media_type=media_type,
        content_disposition_type="inline",
    )
