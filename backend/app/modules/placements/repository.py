from typing import Sequence, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.placements.models import Placement
from app.modules.placements.schemas import PlacementCreate, PlacementUpdate
from app.modules.applications.models import Application
from app.modules.students.models import Student
from app.modules.auth.models import User
from app.modules.jobs.models import Job
from app.modules.companies.models import Company


class PlacementRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_id(self, placement_id: int) -> Optional[Placement]:
        stmt = (
            select(Placement)
            .options(
                joinedload(Placement.application).joinedload(Application.student),
                joinedload(Placement.application).joinedload(Application.job).joinedload(Job.company),
            )
            .where(Placement.id == placement_id)
        )
        result = await self._db.execute(stmt)
        return result.scalars().first()

    async def get_by_application_id(self, application_id: int) -> Optional[Placement]:
        stmt = select(Placement).where(Placement.application_id == application_id)
        result = await self._db.execute(stmt)
        return result.scalars().first()

    async def get_student_accepted_placement(self, student_id: int) -> Optional[Placement]:
        stmt = (
            select(Placement)
            .join(Application, Placement.application_id == Application.id)
            .where(
                and_(
                    Application.student_id == student_id,
                    Placement.offer_accepted == True
                )
            )
        )
        result = await self._db.execute(stmt)
        return result.scalars().first()

    async def list_for_staff(
        self,
        search: Optional[str] = None,
        company_id: Optional[int] = None,
        department_id: Optional[int] = None,
        offer_accepted: Optional[bool] = None,
    ) -> Sequence[Placement]:
        stmt = (
            select(Placement)
            .options(
                joinedload(Placement.application).joinedload(Application.student),
                joinedload(Placement.application).joinedload(Application.job).joinedload(Job.company),
            )
            .join(Application, Placement.application_id == Application.id)
            .join(Student, Application.student_id == Student.id)
            .join(Job, Application.job_id == Job.id)
            .join(Company, Job.company_id == Company.id)
        )

        if offer_accepted is not None:
            stmt = stmt.where(Placement.offer_accepted == offer_accepted)
        if company_id:
            stmt = stmt.where(Job.company_id == company_id)
        if department_id:
            stmt = stmt.where(Student.department_id == department_id)
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.join(User, Student.user_id == User.id).where(
                (Student.full_name.ilike(search_pattern))
                | (User.email.ilike(search_pattern))
                | (Job.title.ilike(search_pattern))
                | (Company.name.ilike(search_pattern))
            )

        stmt = stmt.order_by(Placement.created_at.desc())
        result = await self._db.execute(stmt)
        return result.scalars().all()

    async def list_for_student(self, student_id: int) -> Sequence[Placement]:
        stmt = (
            select(Placement)
            .options(
                joinedload(Placement.application).joinedload(Application.job).joinedload(Job.company),
            )
            .join(Application, Placement.application_id == Application.id)
            .where(Application.student_id == student_id)
            .order_by(Placement.created_at.desc())
        )
        result = await self._db.execute(stmt)
        return result.scalars().all()

    async def create(self, data: PlacementCreate) -> Placement:
        placement = Placement(
            application_id=data.application_id,
            final_package_ctc=data.final_package_ctc,
            placement_date=data.placement_date,
            offer_accepted=data.offer_accepted,
        )
        self._db.add(placement)
        await self._db.commit()
        await self._db.refresh(placement)
        return await self.get_by_id(placement.id)

    async def update(self, placement: Placement, data: PlacementUpdate) -> Placement:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(placement, key, value)
            
        await self._db.commit()
        await self._db.refresh(placement)
        return placement
