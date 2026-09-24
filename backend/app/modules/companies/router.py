"""
Staff Company Management API endpoints.
"""

from typing import List, Optional

from fastapi import APIRouter, Query, status

from app.api.deps import RequireStaff, CompanyServiceDep
from app.modules.companies.schemas import (
    CompanyCreateRequest,
    CompanyResponse,
    CompanyStatusUpdateRequest,
    CompanyUpdateRequest,
)

staff_companies_router = APIRouter(prefix="/staff/companies", tags=["Staff Companies"])


@staff_companies_router.get("", response_model=List[CompanyResponse], status_code=status.HTTP_200_OK)
async def list_companies(
    current_user: RequireStaff,
    company_service: CompanyServiceDep,
    search: Optional[str] = Query(default=None, description="Search by name, industry, or location"),
    status_filter: str = Query(default="all", alias="status", pattern="^(all|active|inactive)$"),
) -> List[CompanyResponse]:
    """Return list of companies for staff management."""
    return await company_service.list_companies(search=search, status=status_filter)


@staff_companies_router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    data: CompanyCreateRequest,
    current_user: RequireStaff,
    company_service: CompanyServiceDep,
) -> CompanyResponse:
    """Create a new company record."""
    return await company_service.create_company(data)


@staff_companies_router.get("/{company_id}", response_model=CompanyResponse, status_code=status.HTTP_200_OK)
async def get_company(
    company_id: int,
    current_user: RequireStaff,
    company_service: CompanyServiceDep,
) -> CompanyResponse:
    """Get a single company by ID."""
    return await company_service.get_company(company_id)


@staff_companies_router.patch("/{company_id}", response_model=CompanyResponse, status_code=status.HTTP_200_OK)
async def update_company(
    company_id: int,
    data: CompanyUpdateRequest,
    current_user: RequireStaff,
    company_service: CompanyServiceDep,
) -> CompanyResponse:
    """Update editable company details (excluding status)."""
    return await company_service.update_company(company_id, data)


@staff_companies_router.patch(
    "/{company_id}/status", response_model=CompanyResponse, status_code=status.HTTP_200_OK
)
async def update_company_status(
    company_id: int,
    data: CompanyStatusUpdateRequest,
    current_user: RequireStaff,
    company_service: CompanyServiceDep,
) -> CompanyResponse:
    """Update company active status (soft activation/deactivation)."""
    return await company_service.update_company_status(company_id, data)
