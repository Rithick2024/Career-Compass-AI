"""
Student repository — the only layer that issues SQLAlchemy queries
against `students`/`departments`. The service layer depends on this,
never on the ORM/session directly.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.students.models import Department, Student


class StudentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_user_id(self, user_id: int) -> Optional[Student]:
        result = await self._db.execute(select(Student).where(Student.user_id == user_id))
        return result.scalar_one_or_none()

    async def create_for_user(self, user_id: int) -> Student:
        student = Student(user_id=user_id)
        self._db.add(student)
        await self._db.flush()  # assigns PK/defaults without ending the transaction
        await self._db.refresh(student)
        return student

    async def get_department_by_id(self, department_id: int) -> Optional[Department]:
        result = await self._db.execute(select(Department).where(Department.id == department_id))
        return result.scalar_one_or_none()
