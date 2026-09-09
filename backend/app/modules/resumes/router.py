"""
Resume endpoints. Routers stay thin: parse request -> call service ->
return response. All business logic lives in `ResumeService`.

Nested under the existing `/students/me` resource for consistency with
the student and skills modules — there is no `GET /students/{id}/resume`
or any other endpoint that accepts a client-supplied student id; the
student is always derived from the authenticated JWT.
"""

from fastapi import APIRouter, status

from app.api.deps import RequireStudent, ResumeServiceDep
from app.modules.resumes.schemas import ResumeCreate, ResumeResponse, ResumeUpdate

router = APIRouter(prefix="/students/me/resume", tags=["Resume"])


@router.get("", response_model=ResumeResponse, status_code=status.HTTP_200_OK)
async def get_my_resume(
    current_user: RequireStudent, resume_service: ResumeServiceDep
) -> ResumeResponse:
    """
    Return the authenticated student's resume profile.

    404 if no resume has been created yet — see
    `ResumeService`'s module docstring / docs/resume-module.md for why
    this doesn't auto-provision an empty resume the way the student
    profile does.
    """
    return await resume_service.get_my_resume(current_user.id)


@router.post("", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def create_my_resume(
    data: ResumeCreate,
    current_user: RequireStudent,
    resume_service: ResumeServiceDep,
) -> ResumeResponse:
    """Create the authenticated student's resume profile. 409 if one already exists."""
    return await resume_service.create_my_resume(current_user.id, data)


@router.patch("", response_model=ResumeResponse, status_code=status.HTTP_200_OK)
async def update_my_resume(
    data: ResumeUpdate,
    current_user: RequireStudent,
    resume_service: ResumeServiceDep,
) -> ResumeResponse:
    """Update the authenticated student's own resume. Only supplied fields change."""
    return await resume_service.update_my_resume(current_user.id, data)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_resume(
    current_user: RequireStudent, resume_service: ResumeServiceDep
) -> None:
    """Delete the authenticated student's resume profile."""
    await resume_service.delete_my_resume(current_user.id)
