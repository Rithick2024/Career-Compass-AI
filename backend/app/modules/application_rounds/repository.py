from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.modules.application_rounds.models import ApplicationRound
from app.modules.application_rounds.schemas import ApplicationRoundCreate, ApplicationRoundUpdate


class ApplicationRoundRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_application(self, application_id: int) -> Sequence[ApplicationRound]:
        stmt = (
            select(ApplicationRound)
            .where(ApplicationRound.application_id == application_id)
            .order_by(ApplicationRound.round_number.asc(), ApplicationRound.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, round_id: int) -> ApplicationRound | None:
        stmt = select(ApplicationRound).where(ApplicationRound.id == round_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_round_number(self, application_id: int, round_number: int) -> ApplicationRound | None:
        stmt = select(ApplicationRound).where(
            ApplicationRound.application_id == application_id,
            ApplicationRound.round_number == round_number
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, application_id: int, data: ApplicationRoundCreate) -> ApplicationRound:
        db_obj = ApplicationRound(
            application_id=application_id,
            round_number=data.round_number,
            round_type=data.round_type,
            title=data.title,
            status=data.status,
            result=data.result,
            scheduled_at=data.scheduled_at,
            completed_at=data.completed_at,
            external_link=str(data.external_link) if data.external_link else None,
            notes=data.notes,
        )
        self.session.add(db_obj)
        try:
            await self.session.commit()
            await self.session.refresh(db_obj)
        except IntegrityError:
            await self.session.rollback()
            raise
        return db_obj

    async def update(self, db_obj: ApplicationRound, data: ApplicationRoundUpdate) -> ApplicationRound:
        update_data = data.model_dump(exclude_unset=True)
        if "external_link" in update_data and update_data["external_link"] is not None:
            update_data["external_link"] = str(update_data["external_link"])
            
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
