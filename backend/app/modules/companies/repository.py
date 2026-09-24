"""
Company repository — issues SQLAlchemy queries against the `companies` table.
"""

from typing import Optional, Sequence

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.models import Company


class CompanyRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, company_id: int) -> Optional[Company]:
        result = await self._db.execute(select(Company).where(Company.id == company_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Company]:
        result = await self._db.execute(
            select(Company).where(Company.name.ilike(name.strip()))
        )
        return result.scalar_one_or_none()

    async def list_companies(
        self, search: Optional[str] = None, status: Optional[str] = None
    ) -> Sequence[Company]:
        query = select(Company)

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Company.name.ilike(term),
                    Company.industry.ilike(term),
                    Company.location.ilike(term),
                )
            )

        if status == "active":
            query = query.where(Company.is_active == True)  # noqa: E712
        elif status == "inactive":
            query = query.where(Company.is_active == False)  # noqa: E712

        query = query.order_by(Company.name)
        result = await self._db.execute(query)
        return result.scalars().all()

    async def create_company(
        self,
        name: str,
        description: Optional[str] = None,
        industry: Optional[str] = None,
        website: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Company:
        company = Company(
            name=name.strip(),
            description=description,
            industry=industry,
            website=website,
            location=location,
        )
        self._db.add(company)
        await self._db.flush()
        await self._db.refresh(company)
        return company

    async def update_company(self, company: Company, updates: dict) -> Company:
        for field, value in updates.items():
            setattr(company, field, value)
        await self._db.flush()
        await self._db.refresh(company)
        return company

    async def update_company_status(self, company: Company, is_active: bool) -> Company:
        company.is_active = is_active
        await self._db.flush()
        await self._db.refresh(company)
        return company
