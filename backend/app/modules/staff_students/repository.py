"""
Staff Student repository — issues query calls for student directory data aggregation.
"""

from typing import List, Optional, Sequence, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.resumes.models import Resume
from app.modules.skills.models import StudentSkill
from app.modules.students.models import Student
from app.shared.enums import RoleEnum


class StaffStudentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_students(
        self,
        search: Optional[str] = None,
        department_id: Optional[int] = None,
        graduation_year: Optional[int] = None,
    ) -> List[Tuple[Student, User, int, int]]:
        """
        Retrieves student directory tuple (Student, User, skills_count, resumes_count)
        without N+1 query overhead.
        """
        skills_subq = (
            select(StudentSkill.student_id, func.count(StudentSkill.id).label("skills_count"))
            .group_by(StudentSkill.student_id)
            .subquery()
        )

        resumes_subq = (
            select(Resume.student_id, func.count(Resume.id).label("resumes_count"))
            .group_by(Resume.student_id)
            .subquery()
        )

        query = (
            select(
                Student,
                User,
                func.coalesce(skills_subq.c.skills_count, 0).label("skills_count"),
                func.coalesce(resumes_subq.c.resumes_count, 0).label("resumes_count"),
            )
            .join(User, Student.user_id == User.id)
            .outerjoin(skills_subq, Student.id == skills_subq.c.student_id)
            .outerjoin(resumes_subq, Student.id == resumes_subq.c.student_id)
            .where(User.role == RoleEnum.STUDENT)
        )

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Student.full_name.ilike(term),
                    User.email.ilike(term),
                    Student.phone.ilike(term),
                )
            )

        if department_id is not None:
            query = query.where(Student.department_id == department_id)

        if graduation_year is not None:
            query = query.where(Student.graduation_year == graduation_year)

        query = query.order_by(Student.full_name.nulls_last(), Student.id)
        result = await self._db.execute(query)
        return list(result.all())

    async def get_student_detail(self, student_id: int) -> Optional[Tuple[Student, User]]:
        query = (
            select(Student, User)
            .join(User, Student.user_id == User.id)
            .where(Student.id == student_id)
        )
        result = await self._db.execute(query)
        row = result.first()
        if not row:
            return None
        return row[0], row[1]

    async def get_student_skills(self, student_id: int) -> Sequence[StudentSkill]:
        query = (
            select(StudentSkill)
            .where(StudentSkill.student_id == student_id)
            .order_by(StudentSkill.id)
        )
        result = await self._db.execute(query)
        return result.scalars().all()

    async def get_student_resumes(self, student_id: int) -> Sequence[Resume]:
        query = (
            select(Resume)
            .where(Resume.student_id == student_id)
            .order_by(Resume.is_default.desc(), Resume.created_at.desc())
        )
        result = await self._db.execute(query)
        return result.scalars().all()

    async def get_resume_by_id_and_student_id(
        self, resume_id: int, student_id: int
    ) -> Optional[Resume]:
        query = select(Resume).where(
            Resume.id == resume_id,
            Resume.student_id == student_id,
        )
        result = await self._db.execute(query)
        return result.scalar_one_or_none()
