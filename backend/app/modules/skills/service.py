"""
Skill service layer — business logic and orchestration only.

Raises `app.core.exceptions.AppException` subclasses; never touches
HTTP or SQLAlchemy directly (those belong to the router and
repository respectively).
"""

from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.modules.skills.repository import SkillRepository, StudentSkillRepository
from app.modules.skills.schemas import (
    AddStudentSkillRequest,
    SkillCreateRequest,
    SkillOut,
    SkillResponse,
    SkillStatusUpdateRequest,
    SkillUpdateRequest,
    StudentSkillResponse,
    UpdateStudentSkillProficiencyRequest,
)
from app.modules.students.repository import StudentRepository


class SkillService:
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
        skills = await self._skills.list_active()
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
        if skill is None or not skill.is_active:
            raise NotFoundError(
                "The specified skill does not exist or is inactive.", error_code="SKILL_NOT_FOUND"
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

    # --- Staff Skill Catalog Management ---

    async def list_all_skills(self) -> List[SkillResponse]:
        skills = await self._skills.list_all()
        return [SkillResponse.model_validate(s) for s in skills]

    async def create_skill(self, data: SkillCreateRequest) -> SkillResponse:
        clean_name = data.name.strip()
        existing = await self._skills.get_by_name(clean_name)
        if existing is not None:
            raise ConflictError(
                "A skill with this name already exists.",
                error_code="SKILL_ALREADY_EXISTS",
            )

        skill = await self._skills.create(clean_name, data.category)
        await self._db.commit()
        return SkillResponse.model_validate(skill)

    async def update_skill(self, skill_id: int, data: SkillUpdateRequest) -> SkillResponse:
        skill = await self._skills.get_by_id(skill_id)
        if skill is None:
            raise NotFoundError(
                "The specified skill does not exist.",
                error_code="SKILL_NOT_FOUND",
            )

        clean_name = data.name.strip()
        existing = await self._skills.get_by_name(clean_name)
        if existing is not None and existing.id != skill_id:
            raise ConflictError(
                "A skill with this name already exists.",
                error_code="SKILL_ALREADY_EXISTS",
            )

        updated_skill = await self._skills.update(skill, clean_name, data.category)
        await self._db.commit()
        return SkillResponse.model_validate(updated_skill)

    async def update_skill_status(
        self, skill_id: int, data: SkillStatusUpdateRequest
    ) -> SkillResponse:
        skill = await self._skills.get_by_id(skill_id)
        if skill is None:
            raise NotFoundError(
                "The specified skill does not exist.",
                error_code="SKILL_NOT_FOUND",
            )

        updated_skill = await self._skills.update_status(skill, data.is_active)
        await self._db.commit()
        return SkillResponse.model_validate(updated_skill)
