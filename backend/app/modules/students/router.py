"""
Student profile endpoints. Routers stay thin: parse request -> call
service -> return response. All business logic lives in
`StudentService`.
"""

from fastapi import APIRouter, status

from app.api.deps import RequireStudent, StudentServiceDep
from app.modules.students.schemas import StudentProfileResponse, StudentProfileUpdateRequest

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/me", response_model=StudentProfileResponse, status_code=status.HTTP_200_OK)
async def get_my_profile(
    current_user: RequireStudent, student_service: StudentServiceDep
) -> StudentProfileResponse:
    """
    Return the authenticated student's profile.

    If no profile row exists yet (first time this account has touched
    the endpoint), an empty one is created transparently — see
    `StudentService._get_or_create_profile` / docs/student-module.md.
    """
    return await student_service.get_my_profile(current_user.id)


@router.patch("/me", response_model=StudentProfileResponse, status_code=status.HTTP_200_OK)
async def update_my_profile(
    data: StudentProfileUpdateRequest,
    current_user: RequireStudent,
    student_service: StudentServiceDep,
) -> StudentProfileResponse:
    """Update the authenticated student's own profile. Only supplied fields change."""
    return await student_service.update_my_profile(current_user.id, data)
