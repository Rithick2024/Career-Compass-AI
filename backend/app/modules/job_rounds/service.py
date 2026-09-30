from typing import Sequence
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import NotFoundError, ConflictError, BadRequestError
from app.modules.application_rounds.models import ScheduleType
from app.modules.job_rounds.models import JobRound
from app.modules.job_rounds.schemas import (
    JobRoundCreate,
    JobRoundUpdate,
    JobRoundResponse,
)
from app.modules.job_rounds.repository import JobRoundRepository
from app.modules.jobs.repository import JobRepository
from app.modules.application_rounds.models import ApplicationRound


class JobRoundService:
    def __init__(self, round_repo: JobRoundRepository, job_repo: JobRepository):
        self._round_repo = round_repo
        self._job_repo = job_repo

    async def _verify_job_exists(self, job_id: int):
        job = await self._job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError("Job posting not found")
        return job

    def _validate_schedule(
        self,
        schedule_type: ScheduleType,
        available_from: datetime | None,
        available_until: datetime | None,
        duration_minutes: int | None,
    ):
        if duration_minutes is not None and duration_minutes <= 0:
            raise BadRequestError("duration_minutes must be greater than 0.")

        if not available_from:
            raise BadRequestError("available_from is required for round scheduling.")

        from_at = available_from if available_from.tzinfo else available_from.replace(tzinfo=timezone.utc)

        if schedule_type == ScheduleType.FIXED_TIME:
            if available_until is not None:
                raise BadRequestError("available_until must be None for FIXED_TIME rounds.")
        elif schedule_type == ScheduleType.AVAILABILITY_WINDOW:
            if not available_until:
                raise BadRequestError("available_until is required for AVAILABILITY_WINDOW rounds.")
            until_at = available_until if available_until.tzinfo else available_until.replace(tzinfo=timezone.utc)
            if until_at <= from_at:
                raise BadRequestError("available_until must be strictly after available_from.")

    async def list_for_staff(self, job_id: int) -> Sequence[JobRound]:
        await self._verify_job_exists(job_id)
        return await self._round_repo.list_by_application if hasattr(self._round_repo, "list_by_application") else await self._round_repo.list_by_job(job_id)

    async def create_for_staff(self, job_id: int, data: JobRoundCreate) -> JobRound:
        await self._verify_job_exists(job_id)

        sched_type = data.schedule_type or ScheduleType.FIXED_TIME
        self._validate_schedule(
            schedule_type=sched_type,
            available_from=data.available_from,
            available_until=data.available_until,
            duration_minutes=data.duration_minutes,
        )

        try:
            return await self._round_repo.create(job_id, data)
        except IntegrityError:
            raise ConflictError(f"Round number {data.round_number} already exists for this job.")

    async def update_for_staff(self, job_id: int, round_id: int, data: JobRoundUpdate) -> JobRound:
        await self._verify_job_exists(job_id)
        db_obj = await self._round_repo.get_by_id(round_id)
        if not db_obj or db_obj.job_id != job_id:
            raise NotFoundError("Job round not found")

        sched_type = data.schedule_type if data.schedule_type is not None else db_obj.schedule_type
        avail_from = data.available_from if data.available_from is not None else db_obj.available_from
        avail_until = (
            data.available_until
            if data.available_until is not None
            else (db_obj.available_until if sched_type == ScheduleType.AVAILABILITY_WINDOW else None)
        )
        duration_mins = data.duration_minutes if data.duration_minutes is not None else db_obj.duration_minutes

        self._validate_schedule(
            schedule_type=sched_type,
            available_from=avail_from,
            available_until=avail_until,
            duration_minutes=duration_mins,
        )

        try:
            return await self._round_repo.update(db_obj, data)
        except IntegrityError:
            raise ConflictError(f"Round number {data.round_number} already exists for this job.")

    async def delete_for_staff(self, job_id: int, round_id: int) -> dict:
        await self._verify_job_exists(job_id)
        db_obj = await self._round_repo.get_by_id(round_id)
        if not db_obj or db_obj.job_id != job_id:
            raise NotFoundError("Job round not found")

        await self._round_repo.delete(db_obj)
        return {"message": "Job round deleted successfully.", "deleted": True}
