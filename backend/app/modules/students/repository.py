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

    async def get_department_by_name(self, name: str) -> Optional[Department]:
        result = await self._db.execute(
            select(Department).where(Department.name.ilike(name.strip()))
        )
        return result.scalar_one_or_none()

    async def list_all_departments(self) -> list[Department]:
        result = await self._db.execute(select(Department).order_by(Department.name))
        return list(result.scalars().all())

    async def list_active_departments(self) -> list[Department]:
        result = await self._db.execute(
            select(Department).where(Department.is_active == True).order_by(Department.name)
        )
        return list(result.scalars().all())

    async def create_department(self, name: str) -> Department:
        dept = Department(name=name.strip())
        self._db.add(dept)
        await self._db.flush()
        await self._db.refresh(dept)
        return dept

    async def update_department(self, dept: Department, name: str) -> Department:
        dept.name = name.strip()
        await self._db.flush()
        await self._db.refresh(dept)
        return dept

    async def update_department_status(self, dept: Department, is_active: bool) -> Department:
        dept.is_active = is_active
        await self._db.flush()
        await self._db.refresh(dept)
        return dept
