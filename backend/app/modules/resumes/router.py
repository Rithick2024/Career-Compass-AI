"""
Resume endpoints for multiple-resume document management.
"""

from typing import List, Optional

from fastapi import APIRouter, File, Form, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import RequireStudent, ResumeServiceDep
from app.modules.resumes.schemas import ResumeResponse, ResumeUpdate

router = APIRouter(prefix="/students/me/resumes", tags=["Resume"])


@router.get("", response_model=List[ResumeResponse], status_code=status.HTTP_200_OK)
async def get_my_resumes(
    current_user: RequireStudent, resume_service: ResumeServiceDep
) -> List[ResumeResponse]:
    """Return all resume documents belonging to the authenticated student."""
    return await resume_service.get_my_resumes(current_user.id)


@router.post("", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def create_my_resume(
    current_user: RequireStudent,
    resume_service: ResumeServiceDep,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
) -> ResumeResponse:
    """Create a new resume document with an uploaded file."""
    return await resume_service.create_my_resume(
        user_id=current_user.id,
        title=title,
        description=description,
        upload=file,
    )


@router.get("/{resume_id}", response_model=ResumeResponse, status_code=status.HTTP_200_OK)
async def get_my_resume(
    resume_id: int,
    current_user: RequireStudent,
    resume_service: ResumeServiceDep,
) -> ResumeResponse:
    """Return a single resume document belonging to the authenticated student."""
    return await resume_service.get_my_resume_by_id(current_user.id, resume_id)


@router.patch("/{resume_id}", response_model=ResumeResponse, status_code=status.HTTP_200_OK)
async def update_my_resume(
    resume_id: int,
    data: ResumeUpdate,
    current_user: RequireStudent,
    resume_service: ResumeServiceDep,
) -> ResumeResponse:
    """Update title and/or description of a resume document."""
    return await resume_service.update_my_resume(current_user.id, resume_id, data)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_resume(
    resume_id: int,
    current_user: RequireStudent,
    resume_service: ResumeServiceDep,
) -> None:
    """Delete a resume document and its physical file."""
    await resume_service.delete_my_resume(current_user.id, resume_id)


@router.get("/{resume_id}/file")
async def download_my_resume_file(
    resume_id: int,
    current_user: RequireStudent,
    resume_service: ResumeServiceDep,
) -> FileResponse:
    """Download the physical file of a resume document."""
    absolute_path, file_name, media_type = await resume_service.get_my_resume_file_location(
        current_user.id, resume_id
    )
    return FileResponse(
        path=absolute_path,
        filename=file_name,
        media_type=media_type,
        content_disposition_type="inline",
    )


@router.patch("/{resume_id}/default", response_model=ResumeResponse, status_code=status.HTTP_200_OK)
async def set_default_resume(
    resume_id: int,
    current_user: RequireStudent,
    resume_service: ResumeServiceDep,
) -> ResumeResponse:
    """Set a resume document as the student's default resume."""
    return await resume_service.set_default_resume(current_user.id, resume_id)
