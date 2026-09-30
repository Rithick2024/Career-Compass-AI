from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.modules.applications.models import Application, ApplicationStatus
from app.modules.auth.models import User
from app.modules.jobs.models import Job, Company
from app.modules.students.models import Student, Department
from app.modules.resumes.models import Resume


class ApplicationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, obj_in: Application) -> Application:
        self.session.add(obj_in)
        await self.session.flush()
        # Refresh to load relationships if needed, or caller can do it
        return obj_in

    async def get_by_id(self, application_id: int) -> Optional[Application]:
        stmt = select(Application).where(Application.id == application_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_id_for_student(self, application_id: int, student_id: int) -> Optional[Application]:
        stmt = (
            select(Application)
            .options(
                joinedload(Application.job).joinedload(Job.company),
                joinedload(Application.resume)
            )
            .where(
                Application.id == application_id,
                Application.student_id == student_id
            )
        )
        res = await self.session.execute(stmt)
        return res.unique().scalar_one_or_none()

    async def list_for_student(self, student_id: int) -> List[Application]:
        stmt = (
            select(Application)
            .options(
                joinedload(Application.job).joinedload(Job.company),
                joinedload(Application.resume)
            )
            .where(Application.student_id == student_id)
            .order_by(Application.applied_at.desc())
        )
        res = await self.session.execute(stmt)
        return list(res.unique().scalars().all())

    async def get_by_id_for_staff(self, application_id: int) -> Optional[Application]:
        stmt = (
            select(Application, User)
            .join(Application.student)
            .join(User, Student.user_id == User.id)
            .options(
                joinedload(Application.student).joinedload(Student.department),
                joinedload(Application.job).joinedload(Job.company),
                joinedload(Application.resume)
            )
            .where(Application.id == application_id)
        )
        res = await self.session.execute(stmt)
        row = res.unique().first()
        if not row:
            return None
        app_obj, user_obj = row
        app_obj.student.user = user_obj
        return app_obj

    async def list_for_staff(
        self,
        search: Optional[str] = None,
        job_id: Optional[int] = None,
        student_id: Optional[int] = None,
        status: Optional[str] = None,
        company_id: Optional[int] = None
    ) -> List[Application]:
        stmt = (
            select(Application, User)
            .join(Application.student)
            .join(User, Student.user_id == User.id)
            .outerjoin(Student.department)
            .join(Application.job)
            .join(Job.company)
            .join(Application.resume)
            .options(
                selectinload(Application.student).selectinload(Student.department),
                selectinload(Application.job).selectinload(Job.company),
                selectinload(Application.resume)
            )
        )

        if job_id is not None:
            stmt = stmt.where(Application.job_id == job_id)
        if student_id is not None:
            stmt = stmt.where(Application.student_id == student_id)
        if status and status.lower() != "all":
            stmt = stmt.where(Application.status == status)
        if company_id is not None:
            stmt = stmt.where(Job.company_id == company_id)
        
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                (User.email.ilike(search_pattern)) |
                (Student.full_name.ilike(search_pattern)) |
                (Job.title.ilike(search_pattern)) |
                (Company.name.ilike(search_pattern))
            )

        stmt = stmt.order_by(Application.applied_at.desc())
        res = await self.session.execute(stmt)
        apps = []
        for app_obj, user_obj in res.unique():
            app_obj.student.user = user_obj
            apps.append(app_obj)
        return apps
