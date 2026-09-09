"""
Skill service layer — business logic and orchestration only.

Raises `app.core.exceptions.AppException` subclasses; never touches
HTTP or SQLAlchemy directly (those belong to the router and
repository respectively).
"""

from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.skills.repository import SkillRepository, StudentSkillRepository
from app.modules.skills.schemas import (
    AddStudentSkillRequest,
    SkillOut,
    StudentSkillResponse,
    UpdateStudentSkillProficiencyRequest,
)
from app.modules.students.repository import StudentRepository


class SkillService:
    """
    Owns the transaction boundary for skill operations, same pattern
    as `AuthService`/`StudentService`.

    Reuses `StudentRepository` (not `StudentService`) to resolve —
    and, on first access, auto-provision — the current user's
    `students.id`. `student_skills.student_id` references `students.id`,
    not `users.id`, so this resolution step is required before any
    skill operation. Reusing the Student module's repository directly
    mirrors `StudentService._get_or_create_profile`'s own get-or-create
    logic instead of duplicating it — see docs/skills-module.md.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._skills = SkillRepository(db)
        self._student_skills = StudentSkillRepository(db)
        self._students = StudentRepository(db)

    async def _get_or_create_student_id(self, user_id: int) -> int:
        student = await self._students.get_by_user_id(user_id)
        if student is None:
            student = await self._students.create_for_user(user_id)
            await self._db.commit()
        return student.id

    async def list_catalog(self) -> List[SkillOut]:
        skills = await self._skills.list_all()
        return [SkillOut.model_validate(skill) for skill in skills]

    async def list_my_skills(self, user_id: int) -> List[StudentSkillResponse]:
        student_id = await self._get_or_create_student_id(user_id)
        rows = await self._student_skills.list_for_student(student_id)
        return [StudentSkillResponse.model_validate(row) for row in rows]

    async def add_skill(
        self, user_id: int, data: AddStudentSkillRequest
    ) -> StudentSkillResponse:
        student_id = await self._get_or_create_student_id(user_id)

        skill = await self._skills.get_by_id(data.skill_id)
        if skill is None:
            raise NotFoundError(
                "The specified skill does not exist.", error_code="SKILL_NOT_FOUND"
            )

        existing = await self._student_skills.get_for_student_and_skill(
            student_id, data.skill_id
        )
        if existing is not None:
            raise ConflictError(
                "This skill has already been added to the student's profile.",
                error_code="SKILL_ALREADY_ADDED",
            )

        student_skill = await self._student_skills.create(
            student_id, data.skill_id, data.proficiency
        )
        await self._db.commit()

        # Same defensive re-fetch as StudentService.update_my_profile:
        # `create()`'s plain `refresh()` reloads columns but does not
        # itself populate the `skill` relationship, so re-querying
        # (which does, via `lazy="selectin"`) avoids a MissingGreenlet
        # error during response serialization.
        self._db.expire(student_skill)
        student_skill = await self._student_skills.get_for_student_and_skill(
            student_id, data.skill_id
        )
        return StudentSkillResponse.model_validate(student_skill)

    async def update_skill_proficiency(
        self, user_id: int, skill_id: int, data: UpdateStudentSkillProficiencyRequest
    ) -> StudentSkillResponse:
        student_id = await self._get_or_create_student_id(user_id)

        student_skill = await self._student_skills.get_for_student_and_skill(
            student_id, skill_id
        )
        if student_skill is None:
            raise NotFoundError(
                "This skill is not on the student's profile.",
                error_code="STUDENT_SKILL_NOT_FOUND",
            )

        # Only `proficiency` changes here — `skill_id` is untouched, so
        # (unlike `add_skill`) the already-loaded `skill` relationship
        # stays valid and a plain refresh() is sufficient.
        student_skill.proficiency = data.proficiency
        await self._db.commit()
        await self._db.refresh(student_skill)
        return StudentSkillResponse.model_validate(student_skill)

    async def remove_skill(self, user_id: int, skill_id: int) -> None:
        student_id = await self._get_or_create_student_id(user_id)

        student_skill = await self._student_skills.get_for_student_and_skill(
            student_id, skill_id
        )
        if student_skill is None:
            raise NotFoundError(
                "This skill is not on the student's profile.",
                error_code="STUDENT_SKILL_NOT_FOUND",
            )

        await self._student_skills.delete(student_skill)
        await self._db.commit()
