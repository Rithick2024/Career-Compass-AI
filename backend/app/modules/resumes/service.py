"""
Resume service layer — business logic and orchestration only.

Raises `app.core.exceptions.AppException` subclasses; never touches
HTTP or SQLAlchemy directly (those belong to the router and
repository respectively).

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
/ `delete_my_resume` alike, and a resume is only ever created via an
explicit `POST`. See docs/resume-module.md.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
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

        await self._resumes.delete(resume)
        await self._db.commit()
