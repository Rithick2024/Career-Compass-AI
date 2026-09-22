"""
Resume repository — DB access layer for `resumes`.
"""

from typing import List, Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.resumes.models import Resume


class ResumeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id_and_student_id(self, resume_id: int, student_id: int) -> Optional[Resume]:
        result = await self._db.execute(
            select(Resume).where(Resume.id == resume_id, Resume.student_id == student_id)
        )
        return result.scalar_one_or_none()

    async def get_all_by_student_id(self, student_id: int) -> List[Resume]:
        result = await self._db.execute(
            select(Resume)
            .where(Resume.student_id == student_id)
            .order_by(Resume.is_default.desc(), Resume.created_at.desc())
        )
        return list(result.scalars().all())

    async def count_by_student_id(self, student_id: int) -> int:
        result = await self._db.execute(
            select(func.count(Resume.id)).where(Resume.student_id == student_id)
        )
        return result.scalar_one() or 0

    async def create(
        self,
        student_id: int,
        title: str,
        description: Optional[str],
        file_name: str,
        file_path: str,
        file_type: str,
        file_size: int,
        is_default: bool,
    ) -> Resume:
        resume = Resume(
            student_id=student_id,
            title=title,
            description=description,
            file_name=file_name,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            is_default=is_default,
        )
        self._db.add(resume)
        await self._db.flush()
        await self._db.refresh(resume)
        return resume

    async def unset_default_for_student(self, student_id: int) -> None:
        await self._db.execute(
            update(Resume)
            .where(Resume.student_id == student_id, Resume.is_default.is_(True))
            .values(is_default=False)
        )
        await self._db.flush()

    async def get_latest_remaining_by_student_id(
        self, student_id: int, exclude_id: Optional[int] = None
    ) -> Optional[Resume]:
        stmt = select(Resume).where(Resume.student_id == student_id)
        if exclude_id is not None:
            stmt = stmt.where(Resume.id != exclude_id)
        stmt = stmt.order_by(Resume.created_at.desc()).limit(1)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, resume: Resume) -> None:
        await self._db.delete(resume)
        await self._db.flush()
