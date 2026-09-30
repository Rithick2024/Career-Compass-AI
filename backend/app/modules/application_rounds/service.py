from typing import Sequence
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import NotFoundError, ConflictError, BadRequestError
from app.modules.application_rounds.models import ApplicationRound, RoundStatus, RoundResult
from app.modules.application_rounds.schemas import ApplicationRoundCreate, ApplicationRoundUpdate
from app.modules.application_rounds.repository import ApplicationRoundRepository
from app.modules.applications.repository import ApplicationRepository
from app.modules.applications.models import ApplicationStatus


from app.modules.students.repository import StudentRepository

class ApplicationRoundService:
    def __init__(
        self,
        round_repo: ApplicationRoundRepository,
        application_repo: ApplicationRepository,
        student_repo: StudentRepository,
    ):
        self._round_repo = round_repo
        self._application_repo = application_repo
        self._student_repo = student_repo

    async def _verify_application_exists(self, application_id: int):
        app = await self._application_repo.get_by_id(application_id)
        if not app:
            raise NotFoundError("Application not found")
        return app

    async def list_for_staff(self, application_id: int) -> Sequence[ApplicationRound]:
        await self._verify_application_exists(application_id)
        return await self._round_repo.list_by_application(application_id)

    async def create_for_staff(self, application_id: int, data: ApplicationRoundCreate) -> ApplicationRound:
        await self._verify_application_exists(application_id)
        
        # Validate status/result combination
        self._validate_status_result(data.status, data.result)

        if data.status == RoundStatus.COMPLETED and not data.completed_at:
            data.completed_at = datetime.now(timezone.utc)

        try:
            return await self._round_repo.create(application_id, data)
        except IntegrityError:
            raise ConflictError(f"Round number {data.round_number} already exists for this application.")

    async def update_for_staff(self, application_id: int, round_id: int, data: ApplicationRoundUpdate) -> ApplicationRound:
        db_obj = await self._round_repo.get_by_id(round_id)
        if not db_obj or db_obj.application_id != application_id:
            raise NotFoundError("Application round not found")

        # Determine new status and result
        new_status = data.status if data.status is not None else db_obj.status
        new_result = data.result if data.result is not None else db_obj.result
        
        if data.status is not None or data.result is not None:
            self._validate_status_result(new_status, new_result)

        if new_status == RoundStatus.COMPLETED:
            if data.completed_at is None and not db_obj.completed_at:
                data.completed_at = datetime.now(timezone.utc)
        else:
            # If changed away from completed, leave completed_at alone as historical record or let staff clear it
            pass

        return await self._round_repo.update(db_obj, data)

    async def list_for_student(self, application_id: int, user_id: int) -> Sequence[ApplicationRound]:
        app = await self._verify_application_exists(application_id)
        student = await self._student_repo.get_by_user_id(user_id)
        if not student or app.student_id != student.id:
            raise NotFoundError("Application not found") # Prevent leaking existence to other students
            
        return await self._round_repo.list_by_application(application_id)

    async def get_for_student(self, application_id: int, round_id: int, user_id: int) -> ApplicationRound:
        app = await self._verify_application_exists(application_id)
        student = await self._student_repo.get_by_user_id(user_id)
        if not student or app.student_id != student.id:
            raise NotFoundError("Application round not found")
            
        db_obj = await self._round_repo.get_by_id(round_id)
        if not db_obj or db_obj.application_id != application_id:
            raise NotFoundError("Application round not found")
            
        return db_obj

    def _validate_status_result(self, status: RoundStatus, result: RoundResult | None):
        # Enforce sensible combinations
        if status in [RoundStatus.NOT_STARTED, RoundStatus.SCHEDULED, RoundStatus.IN_PROGRESS]:
            if result and result != RoundResult.PENDING:
                raise BadRequestError(f"Round result cannot be {result} when status is {status}")
        
        if status == RoundStatus.CANCELLED:
            if result and result != RoundResult.PENDING:
                raise BadRequestError(f"Round result cannot be {result} when status is Cancelled")
