"""
Skill / StudentSkill repositories — the only layer that issues
SQLAlchemy queries against `skills`/`student_skills`. The service
layer depends on these, never on the ORM/session directly.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.skills.models import Skill, StudentSkill
from app.shared.enums import ProficiencyLevel


class SkillRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_all(self) -> List[Skill]:
        result = await self._db.execute(select(Skill).order_by(Skill.name))
        return list(result.scalars().all())

    async def list_active(self) -> List[Skill]:
        result = await self._db.execute(
            select(Skill).where(Skill.is_active == True).order_by(Skill.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, skill_id: int) -> Optional[Skill]:
        result = await self._db.execute(select(Skill).where(Skill.id == skill_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Skill]:
        result = await self._db.execute(
            select(Skill).where(Skill.name.ilike(name.strip()))
        )
        return result.scalar_one_or_none()

    async def create(self, name: str, category: Optional[str] = None) -> Skill:
        skill = Skill(name=name.strip(), category=category)
        self._db.add(skill)
        await self._db.flush()
        await self._db.refresh(skill)
        return skill

    async def update(self, skill: Skill, name: str, category: Optional[str] = None) -> Skill:
        skill.name = name.strip()
        skill.category = category
        await self._db.flush()
        await self._db.refresh(skill)
        return skill

    async def update_status(self, skill: Skill, is_active: bool) -> Skill:
        skill.is_active = is_active
        await self._db.flush()
        await self._db.refresh(skill)
        return skill


class StudentSkillRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_for_student(self, student_id: int) -> List[StudentSkill]:
        result = await self._db.execute(
            select(StudentSkill)
            .where(StudentSkill.student_id == student_id)
            .order_by(StudentSkill.created_at)
        )
        return list(result.scalars().all())

    async def get_for_student_and_skill(
        self, student_id: int, skill_id: int
    ) -> Optional[StudentSkill]:
        result = await self._db.execute(
            select(StudentSkill).where(
                StudentSkill.student_id == student_id, StudentSkill.skill_id == skill_id
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self, student_id: int, skill_id: int, proficiency: ProficiencyLevel
    ) -> StudentSkill:
        student_skill = StudentSkill(
            student_id=student_id, skill_id=skill_id, proficiency=proficiency
        )
        self._db.add(student_skill)
        await self._db.flush()  # assigns PK/defaults without ending the transaction
        await self._db.refresh(student_skill)
        return student_skill

    async def delete(self, student_skill: StudentSkill) -> None:
        await self._db.delete(student_skill)
        await self._db.flush()
