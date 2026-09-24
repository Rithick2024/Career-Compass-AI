"""
Company service layer — business logic and orchestration.
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.companies.models import Company
from app.modules.companies.repository import CompanyRepository
from app.modules.companies.schemas import (
    CompanyCreateRequest,
    CompanyResponse,
    CompanyStatusUpdateRequest,
    CompanyUpdateRequest,
)


class CompanyService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = CompanyRepository(db)

    async def list_companies(
        self, search: Optional[str] = None, status: Optional[str] = None
    ) -> list[CompanyResponse]:
        companies = await self._repo.list_companies(search=search, status=status)
        return [CompanyResponse.model_validate(c) for c in companies]

    async def get_company(self, company_id: int) -> CompanyResponse:
        company = await self._repo.get_by_id(company_id)
        if company is None:
            raise NotFoundError(
                "The specified company does not exist.",
                error_code="COMPANY_NOT_FOUND",
            )
        return CompanyResponse.model_validate(company)

    async def create_company(self, data: CompanyCreateRequest) -> CompanyResponse:
        clean_name = data.name.strip()
        existing = await self._repo.get_by_name(clean_name)
        if existing is not None:
            raise ConflictError(
                "A company with this name already exists.",
                error_code="COMPANY_ALREADY_EXISTS",
            )

        website_str = str(data.website) if data.website is not None else None

        company = await self._repo.create_company(
            name=clean_name,
            description=data.description,
            industry=data.industry,
            website=website_str,
            location=data.location,
        )
        await self._db.commit()
        return CompanyResponse.model_validate(company)

    async def update_company(
        self, company_id: int, data: CompanyUpdateRequest
    ) -> CompanyResponse:
        company = await self._repo.get_by_id(company_id)
        if company is None:
            raise NotFoundError(
                "The specified company does not exist.",
                error_code="COMPANY_NOT_FOUND",
            )

        updates = data.model_dump(exclude_unset=True)

        if "name" in updates and updates["name"] is not None:
            clean_name = updates["name"].strip()
            existing = await self._repo.get_by_name(clean_name)
            if existing is not None and existing.id != company_id:
                raise ConflictError(
                    "A company with this name already exists.",
                    error_code="COMPANY_ALREADY_EXISTS",
                )
            updates["name"] = clean_name

        if "website" in updates:
            if updates["website"] is not None:
                updates["website"] = str(updates["website"])

        updated_company = await self._repo.update_company(company, updates)
        await self._db.commit()
        return CompanyResponse.model_validate(updated_company)

    async def update_company_status(
        self, company_id: int, data: CompanyStatusUpdateRequest
    ) -> CompanyResponse:
        company = await self._repo.get_by_id(company_id)
        if company is None:
            raise NotFoundError(
                "The specified company does not exist.",
                error_code="COMPANY_NOT_FOUND",
            )

        updated_company = await self._repo.update_company_status(company, data.is_active)
        await self._db.commit()
        return CompanyResponse.model_validate(updated_company)
