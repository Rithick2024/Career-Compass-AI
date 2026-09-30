from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequireStaff, get_db
from app.modules.job_rounds.schemas import (
    JobRoundCreate,
    JobRoundUpdate,
    JobRoundResponse,
)
from app.modules.job_rounds.service import JobRoundService
from app.modules.job_rounds.repository import JobRoundRepository
from app.modules.jobs.repository import JobRepository

staff_job_rounds_router = APIRouter(prefix="/staff/jobs/{job_id}/rounds", tags=["Staff Job Rounds"])


def get_job_round_service(db: AsyncSession = Depends(get_db)) -> JobRoundService:
    round_repo = JobRoundRepository(db)
    job_repo = JobRepository(db)
    return JobRoundService(round_repo, job_repo)


@staff_job_rounds_router.get("", response_model=List[JobRoundResponse])
async def list_job_rounds(
    job_id: int,
    _: RequireStaff,
    service: JobRoundService = Depends(get_job_round_service),
):
    return await service.list_for_staff(job_id)


@staff_job_rounds_router.post("", response_model=JobRoundResponse, status_code=status.HTTP_201_CREATED)
async def create_job_round(
    job_id: int,
    data: JobRoundCreate,
    _: RequireStaff,
    service: JobRoundService = Depends(get_job_round_service),
):
    return await service.create_for_staff(job_id, data)


@staff_job_rounds_router.get("/{round_id}", response_model=JobRoundResponse)
async def get_job_round(
    job_id: int,
    round_id: int,
    _: RequireStaff,
    service: JobRoundService = Depends(get_job_round_service),
):
    job_round = await service._round_repo.get_by_id(round_id)
    if not job_round or job_round.job_id != job_id:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Job round not found")
    return job_round


@staff_job_rounds_router.patch("/{round_id}", response_model=JobRoundResponse)
async def update_job_round(
    job_id: int,
    round_id: int,
    data: JobRoundUpdate,
    _: RequireStaff,
    service: JobRoundService = Depends(get_job_round_service),
):
    return await service.update_for_staff(job_id, round_id, data)


@staff_job_rounds_router.delete("/{round_id}")
async def delete_job_round(
    job_id: int,
    round_id: int,
    _: RequireStaff,
    service: JobRoundService = Depends(get_job_round_service),
):
    return await service.delete_for_staff(job_id, round_id)
