from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.modules.job_rounds.models import JobRound
from app.modules.job_rounds.schemas import JobRoundCreate, JobRoundUpdate


class JobRoundRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_job(self, job_id: int, active_only: bool = False) -> Sequence[JobRound]:
        stmt = select(JobRound).where(JobRound.job_id == job_id)
        if active_only:
            stmt = stmt.where(JobRound.is_active == True)
        stmt = stmt.order_by(JobRound.round_number.asc(), JobRound.created_at.asc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, round_id: int) -> JobRound | None:
        stmt = select(JobRound).where(JobRound.id == round_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_round_number(self, job_id: int, round_number: int) -> JobRound | None:
        stmt = select(JobRound).where(
            JobRound.job_id == job_id,
            JobRound.round_number == round_number
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, job_id: int, data: JobRoundCreate) -> JobRound:
        db_obj = JobRound(
            job_id=job_id,
            round_number=data.round_number,
            round_type=data.round_type,
            title=data.title,
            description=data.description,
            schedule_type=data.schedule_type,
            available_from=data.available_from,
            available_until=data.available_until,
            duration_minutes=data.duration_minutes,
            meeting_link=data.meeting_link,
            test_link=data.test_link,
            instructions=data.instructions,
            is_required=data.is_required,
            is_active=data.is_active,
        )
        self.session.add(db_obj)
        try:
            await self.session.commit()
            await self.session.refresh(db_obj)
        except IntegrityError:
            await self.session.rollback()
            raise
        return db_obj

    async def update(self, db_obj: JobRound, data: JobRoundUpdate) -> JobRound:
        update_data = data.model_dump(exclude_unset=True)
        if "scheduled_at" in update_data:
            del update_data["scheduled_at"]
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.session.add(db_obj)
        try:
            await self.session.commit()
            await self.session.refresh(db_obj)
        except IntegrityError:
            await self.session.rollback()
            raise
        return db_obj

    async def delete(self, db_obj: JobRound) -> None:
        await self.session.delete(db_obj)
        await self.session.commit()
