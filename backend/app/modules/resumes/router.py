"""
Resume endpoints. Routers stay thin: parse request -> call service ->
return response. All business logic lives in `ResumeService`.

Nested under the existing `/students/me` resource for consistency with
the student and skills modules — there is no `GET /students/{id}/resume`
or any other endpoint that accepts a client-supplied student id; the
student is always derived from the authenticated JWT.

File endpoints (`/students/me/resume/file`) extend the same resource:
uploading/downloading/deleting the file attached to the student's
existing resume record, never a separate top-level resource.
"""

from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import FileResponse

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
    """Delete the authenticated student's resume profile (and its file, if any)."""
    await resume_service.delete_my_resume(current_user.id)


@router.post("/file", response_model=ResumeResponse, status_code=status.HTTP_200_OK)
async def upload_my_resume_file(
    current_user: RequireStudent,
    resume_service: ResumeServiceDep,
    file: UploadFile = File(...),
) -> ResumeResponse:
    """
    Upload (or replace) the file attached to the student's existing
    resume. The resume profile must already exist — 404 if not; the
    frontend is expected to create it first via `POST` above.
    """
    return await resume_service.upload_my_resume_file(current_user.id, file)


@router.get("/file")
async def download_my_resume_file(
    current_user: RequireStudent, resume_service: ResumeServiceDep
) -> FileResponse:
    """
    Download the authenticated student's uploaded resume file.

    404 if there's no resume, no uploaded file, or the file is
    unexpectedly missing on disk. Never accepts a path or filename
    from the client — the file is located entirely from the
    authenticated student's own resume record.
    """
    absolute_path, file_name, media_type = await resume_service.get_my_resume_file_location(
        current_user.id
    )
    return FileResponse(path=absolute_path, filename=file_name, media_type=media_type)


@router.delete("/file", response_model=ResumeResponse, status_code=status.HTTP_200_OK)
async def delete_my_resume_file(
    current_user: RequireStudent, resume_service: ResumeServiceDep
) -> ResumeResponse:
    """
    Remove only the uploaded file, keeping the resume profile
    (professional_summary/career_objective) intact. 404 if there's no
    resume, or the resume has no file to remove.
    """
    return await resume_service.delete_my_resume_file(current_user.id)
