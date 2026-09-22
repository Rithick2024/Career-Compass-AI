"""
Resume service layer — business logic and orchestration only.

Raises `app.core.exceptions.AppException` subclasses; never touches
HTTP or SQLAlchemy directly (those belong to the router and
repository respectively). File-system operations are delegated to
`app.modules.resumes.storage` — this service coordinates *when* those
calls happen (ownership checks, DB-then-disk ordering) but never opens
a file handle itself.

DESIGN DECISION — GET/PATCH/DELETE 404 rather than auto-provisioning
(unlike `StudentService._get_or_create_profile`):

`StudentProfileResponse` auto-creates an empty profile on first
access because a student profile is implicitly tied to the account —
there's no separate "create" step in that module's API at all, so
auto-provisioning is the only way GET/PATCH are ever usable.

Resume is different: it has its own explicit `POST` (create) with
duplicate detection (409) and its own explicit `DELETE`, and the task
brief names it a "Student 1 ── 0..1 Resume" relationship — a resume
genuinely may or may not exist, and that's a meaningful, testable
state, not just a startup formality. Auto-provisioning here would make
"duplicate POST" and "DELETE then GET" behave confusingly (a resume
would always already exist by the time `POST` runs). So: no resume
row → `NotFoundError` (404) from `get_my_resume` / `update_my_resume`
/ `delete_my_resume` / the file endpoints alike, and a resume is only
ever created via an explicit `POST`. See docs/resume-module.md.

FILE LIFECYCLE ORDERING — the same "commit the source of truth first,
clean up the filesystem after" principle applies everywhere a file is
replaced or removed, so a mid-operation failure never leaves a student
with neither an old nor a new file:
- Upload/replace: save the new file → commit the DB row pointing at
  it → only then delete the old file (if any). If the commit itself
  fails, the just-saved new file is removed before the error
  propagates, so it's never orphaned either.
- Delete file / delete whole resume: commit the DB change first, then
  delete the physical file. A file left on disk after a DB row is
  already gone is a harmless, cleanable leftover; the reverse (a DB
  row pointing at a file that's already gone) is what `storage`'s
  "missing file is not an error" handling exists for, but this
  ordering avoids relying on that as anything but a safety net.
"""

from pathlib import Path
from typing import Tuple

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.resumes import storage
from app.modules.resumes.repository import ResumeRepository
from app.modules.resumes.schemas import ResumeCreate, ResumeResponse, ResumeUpdate
from app.modules.students.repository import StudentRepository


class ResumeService:
    """
    Owns the transaction boundary for resume operations, same pattern
    as `AuthService`/`StudentService`/`SkillService`.

    Reuses `StudentRepository` (not `StudentService`) to resolve — and,
    on first access, auto-provision — the current user's `students.id`.
    `resumes.student_id` references `students.id`, not `users.id`, so
    this resolution step is required before any resume operation. Note
    this get-or-create only applies to the *student profile* row
    (consistent with the rest of the app) — it does NOT mean the
    resume itself is auto-created; see the module docstring above.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._resumes = ResumeRepository(db)
        self._students = StudentRepository(db)

    async def _get_or_create_student_id(self, user_id: int) -> int:
        student = await self._students.get_by_user_id(user_id)
        if student is None:
            student = await self._students.create_for_user(user_id)
            await self._db.commit()
        return student.id

    async def _get_existing_resume(self, student_id: int):
        resume = await self._resumes.get_by_student_id(student_id)
        if resume is None:
            raise NotFoundError(
                "No resume profile exists for this student yet.",
                error_code="RESUME_NOT_FOUND",
            )
        return resume

    async def get_my_resume(self, user_id: int) -> ResumeResponse:
        student_id = await self._get_or_create_student_id(user_id)
        resume = await self._get_existing_resume(student_id)
        return ResumeResponse.model_validate(resume)

    async def create_my_resume(self, user_id: int, data: ResumeCreate) -> ResumeResponse:
        student_id = await self._get_or_create_student_id(user_id)

        existing = await self._resumes.get_by_student_id(student_id)
        if existing is not None:
            raise ConflictError(
                "A resume profile already exists for this student.",
                error_code="RESUME_ALREADY_EXISTS",
            )

        resume = await self._resumes.create(
            student_id=student_id,
            professional_summary=data.professional_summary,
            career_objective=data.career_objective,
        )
        await self._db.commit()
        await self._db.refresh(resume)
        return ResumeResponse.model_validate(resume)

    async def update_my_resume(self, user_id: int, data: ResumeUpdate) -> ResumeResponse:
        student_id = await self._get_or_create_student_id(user_id)
        resume = await self._get_existing_resume(student_id)

        # Only fields actually present in the request are applied —
        # this is what makes a PATCH partial rather than a full
        # overwrite. A field explicitly sent as null (e.g. clearing
        # `career_objective`) is still "set" and is applied as null.
        updates = data.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(resume, field, value)

        await self._db.commit()
        await self._db.refresh(resume)
        return ResumeResponse.model_validate(resume)

    async def delete_my_resume(self, user_id: int) -> None:
        student_id = await self._get_or_create_student_id(user_id)
        resume = await self._get_existing_resume(student_id)

        old_file_path = resume.file_path

        await self._resumes.delete(resume)
        await self._db.commit()

        # Deleting the Resume record also removes its physical file,
        # if one was ever uploaded — the DB row (the source of truth)
        # is gone first; the file cleanup afterward is best-effort.
        if old_file_path:
            storage.delete_file(old_file_path)

    # --- File upload / download / delete-file ---------------------------

    async def upload_my_resume_file(self, user_id: int, upload: UploadFile) -> ResumeResponse:
        """
        Attach (or replace) the uploaded file on the student's existing
        resume. 404 if no resume exists yet — the frontend is expected
        to create the resume profile first (see docs/resume-module.md).
        """
        student_id = await self._get_or_create_student_id(user_id)
        resume = await self._get_existing_resume(student_id)

        old_file_path = resume.file_path

        saved = await storage.save_upload(student_id, upload)

        resume.file_name = saved.file_name
        resume.file_path = saved.file_path
        resume.file_type = saved.file_type
        resume.file_size = saved.file_size

        try:
            await self._db.commit()
        except Exception:
            await self._db.rollback()
            # The DB update never took effect, so the just-saved file
            # would otherwise be an orphan nothing ever points to.
            storage.delete_file(saved.file_path)
            raise

        await self._db.refresh(resume)

        # Only now, after the new file is safely stored AND the DB
        # update has committed, remove the previous file (if any).
        if old_file_path and old_file_path != saved.file_path:
            storage.delete_file(old_file_path)

        return ResumeResponse.model_validate(resume)

    async def get_my_resume_file_location(self, user_id: int) -> Tuple[Path, str, str]:
        """
        Resolve the current student's uploaded file for download.
        Returns (absolute_path, original_file_name, media_type).
        404 if no resume, no file metadata, or the physical file is
        unexpectedly missing on disk despite the metadata.
        """
        student_id = await self._get_or_create_student_id(user_id)
        resume = await self._get_existing_resume(student_id)

        if resume.file_path is None:
            raise NotFoundError(
                "This resume has no uploaded file.", error_code="RESUME_FILE_NOT_FOUND"
            )

        absolute_path = storage.resolve_absolute_path(resume.file_path)
        if absolute_path is None:
            raise NotFoundError(
                "The resume file could not be found.", error_code="RESUME_FILE_NOT_FOUND"
            )

        media_type = resume.file_type or "application/octet-stream"
        return absolute_path, resume.file_name, media_type

    async def delete_my_resume_file(self, user_id: int) -> ResumeResponse:
        """
        Remove only the uploaded file, clearing its metadata but
        keeping the resume profile (professional_summary/
        career_objective) intact. 404 if no resume, or the resume has
        no file to remove.
        """
        student_id = await self._get_or_create_student_id(user_id)
        resume = await self._get_existing_resume(student_id)

        if resume.file_path is None:
            raise NotFoundError(
                "This resume has no uploaded file.", error_code="RESUME_FILE_NOT_FOUND"
            )

        old_file_path = resume.file_path
        resume.file_name = None
        resume.file_path = None
        resume.file_type = None
        resume.file_size = None

        await self._db.commit()
        await self._db.refresh(resume)

        storage.delete_file(old_file_path)

        return ResumeResponse.model_validate(resume)
