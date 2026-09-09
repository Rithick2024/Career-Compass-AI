"""
Resume repository — the only layer that issues SQLAlchemy queries
against `resumes`. The service layer depends on this, never on the
ORM/session directly.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.resumes.models import Resume


class ResumeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_student_id(self, student_id: int) -> Optional[Resume]:
        result = await self._db.execute(
            select(Resume).where(Resume.student_id == student_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        student_id: int,
        professional_summary: Optional[str],
        career_objective: Optional[str],
    ) -> Resume:
        resume = Resume(
            student_id=student_id,
            professional_summary=professional_summary,
            career_objective=career_objective,
        )
        self._db.add(resume)
        await self._db.flush()  # assigns PK/defaults without ending the transaction
        await self._db.refresh(resume)
        return resume

    async def delete(self, resume: Resume) -> None:
        await self._db.delete(resume)
        await self._db.flush()
