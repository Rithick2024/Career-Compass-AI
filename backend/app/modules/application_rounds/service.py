from typing import Sequence
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import NotFoundError, ConflictError, BadRequestError
from app.modules.application_rounds.models import (
    ApplicationRound,
    RoundStatus,
    RoundResult,
    ScheduleType,
    StudentAttendance,
    StaffVerification,
)
from app.modules.application_rounds.schemas import (
    ApplicationRoundCreate,
    ApplicationRoundUpdate,
    ApplicationRoundResponse,
    StaffRescheduleRequest,
)
from app.modules.application_rounds.repository import ApplicationRoundRepository
from app.modules.application_rounds.utils import get_now_utc, get_round_derived_metadata
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

    def _validate_schedule(
        self,
        schedule_type: ScheduleType,
        available_from: datetime | None,
        available_until: datetime | None,
        duration_minutes: int | None,
        applied_at: datetime | None = None,
    ):
        if duration_minutes is not None and duration_minutes <= 0:
            raise BadRequestError("duration_minutes must be greater than 0.")

        if not available_from:
            raise BadRequestError("available_from is required for round scheduling.")

        from_at = available_from if available_from.tzinfo else available_from.replace(tzinfo=timezone.utc)

        if applied_at:
            app_at = applied_at if applied_at.tzinfo else applied_at.replace(tzinfo=timezone.utc)
            if from_at < app_at:
                raise BadRequestError("Round available_from cannot be before application submission time.")

        if schedule_type == ScheduleType.FIXED_TIME:
            if available_until is not None:
                raise BadRequestError("available_until must be None for FIXED_TIME rounds.")
        elif schedule_type == ScheduleType.AVAILABILITY_WINDOW:
            if not available_until:
                raise BadRequestError("available_until is required for AVAILABILITY_WINDOW rounds.")
            until_at = available_until if available_until.tzinfo else available_until.replace(tzinfo=timezone.utc)
            if until_at <= from_at:
                raise BadRequestError("available_until must be strictly after available_from.")

    def build_response(self, round_obj: ApplicationRound, now: datetime | None = None) -> ApplicationRoundResponse:
        metadata = get_round_derived_metadata(round_obj, now=now)

        resp = ApplicationRoundResponse.model_validate(round_obj)
        resp.scheduled_at = round_obj.available_from
        resp.session_end_at = metadata["session_end_at"]
        resp.derived_state = metadata["derived_state"]
        resp.can_student_respond = metadata["can_student_respond"]
        resp.can_staff_verify = metadata["can_staff_verify"]
        resp.can_staff_set_result = metadata["can_staff_set_result"]
        resp.is_upcoming = metadata["is_upcoming"]
        resp.is_due = metadata["is_due"]
        resp.is_overdue = metadata["is_overdue"]
        return resp

    async def list_for_staff(self, application_id: int) -> Sequence[ApplicationRoundResponse]:
        await self._verify_application_exists(application_id)
        rounds = await self._round_repo.list_by_application(application_id)
        now = get_now_utc()
        return [self.build_response(r, now=now) for r in rounds]

    async def create_for_staff(self, application_id: int, data: ApplicationRoundCreate) -> ApplicationRoundResponse:
        app = await self._verify_application_exists(application_id)

        sched_type = data.schedule_type or ScheduleType.FIXED_TIME
        self._validate_schedule(
            schedule_type=sched_type,
            available_from=data.available_from,
            available_until=data.available_until,
            duration_minutes=data.duration_minutes,
            applied_at=app.applied_at,
        )

        # Auto-transition Pending/Reviewing -> Interview on first round creation
        if app.status in (ApplicationStatus.PENDING, ApplicationStatus.REVIEWING):
            app.status = ApplicationStatus.INTERVIEW

        # Validate status/result combination
        self._validate_status_result(data.status, data.result)

        if data.status == RoundStatus.COMPLETED and not data.completed_at:
            data.completed_at = get_now_utc()

        try:
            created_round = await self._round_repo.create(application_id, data)
            return self.build_response(created_round)
        except IntegrityError:
            raise ConflictError(f"Round number {data.round_number} already exists for this application.")

    async def update_for_staff(
        self, application_id: int, round_id: int, data: ApplicationRoundUpdate
    ) -> ApplicationRoundResponse:
        app = await self._verify_application_exists(application_id)
        db_obj = await self._round_repo.get_by_id(round_id)
        if not db_obj or db_obj.application_id != application_id:
            raise NotFoundError("Application round not found")

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
            applied_at=app.applied_at,
        )

        # Determine new status and result
        new_status = data.status if data.status is not None else db_obj.status
        new_result = data.result if data.result is not None else db_obj.result

        if data.status is not None or data.result is not None:
            self._validate_status_result(new_status, new_result)

        if new_status == RoundStatus.COMPLETED and data.completed_at is None and not db_obj.completed_at:
            data.completed_at = get_now_utc()

        updated_round = await self._round_repo.update(db_obj, data)
        return self.build_response(updated_round)

    async def report_student_attendance(
        self, application_id: int, round_id: int, user_id: int, attendance: StudentAttendance
    ) -> ApplicationRoundResponse:
        app = await self._verify_application_exists(application_id)
        student = await self._student_repo.get_by_user_id(user_id)
        if not student or app.student_id != student.id:
            raise NotFoundError("Application round not found")

        db_obj = await self._round_repo.get_by_id(round_id)
        if not db_obj or db_obj.application_id != application_id:
            raise NotFoundError("Application round not found")

        if db_obj.status == RoundStatus.CANCELLED:
            raise BadRequestError("Cannot report attendance for a cancelled round.")

        now = get_now_utc()
        if not db_obj.available_from:
            raise BadRequestError("Round does not have a scheduled start time.")

        from_at = db_obj.available_from if db_obj.available_from.tzinfo else db_obj.available_from.replace(tzinfo=timezone.utc)

        if db_obj.schedule_type == ScheduleType.AVAILABILITY_WINDOW:
            if not db_obj.available_until:
                raise BadRequestError("Availability window end time is missing.")
            until_at = db_obj.available_until if db_obj.available_until.tzinfo else db_obj.available_until.replace(tzinfo=timezone.utc)

            if now < from_at:
                raise BadRequestError("Cannot report attendance before the availability window opens.")
            if now > until_at:
                raise BadRequestError("Cannot report attendance after the availability window has closed.")
        else:
            if now < from_at:
                raise BadRequestError("Cannot report attendance before the scheduled round time.")

        if db_obj.staff_verification == StaffVerification.VERIFIED:
            raise BadRequestError("Cannot modify attendance after staff verification.")

        db_obj.student_attendance = attendance
        db_obj.student_action_at = now
        db_obj.staff_verification = StaffVerification.PENDING

        self._round_repo.session.add(db_obj)
        await self._round_repo.session.commit()
        await self._round_repo.session.refresh(db_obj)

        return self.build_response(db_obj, now=now)

    async def verify_staff_attendance(
        self, application_id: int, round_id: int, staff_user_id: int, verification: StaffVerification
    ) -> ApplicationRoundResponse:
        await self._verify_application_exists(application_id)
        db_obj = await self._round_repo.get_by_id(round_id)
        if not db_obj or db_obj.application_id != application_id:
            raise NotFoundError("Application round not found")

        if db_obj.status == RoundStatus.CANCELLED:
            raise BadRequestError("Cannot verify attendance for a cancelled round.")

        db_obj.staff_verification = verification
        db_obj.staff_verified_at = get_now_utc()
        db_obj.staff_verified_by_id = staff_user_id

        if verification == StaffVerification.REJECTED and db_obj.result == RoundResult.PASSED:
            db_obj.result = RoundResult.PENDING

        self._round_repo.session.add(db_obj)
        await self._round_repo.session.commit()
        await self._round_repo.session.refresh(db_obj)

        return self.build_response(db_obj)

    async def set_staff_result(
        self, application_id: int, round_id: int, result: RoundResult
    ) -> ApplicationRoundResponse:
        await self._verify_application_exists(application_id)
        db_obj = await self._round_repo.get_by_id(round_id)
        if not db_obj or db_obj.application_id != application_id:
            raise NotFoundError("Application round not found")

        if db_obj.status == RoundStatus.CANCELLED and result != RoundResult.PENDING:
            raise BadRequestError("Cannot set a non-pending result on a cancelled round.")

        if db_obj.staff_verification == StaffVerification.REJECTED and result == RoundResult.PASSED:
            raise BadRequestError("Cannot set result to PASSED when staff verification is REJECTED.")

        db_obj.result = result
        if result in (RoundResult.PASSED, RoundResult.FAILED, RoundResult.NOT_ATTENDED) and not db_obj.completed_at:
            db_obj.completed_at = get_now_utc()

        self._round_repo.session.add(db_obj)
        await self._round_repo.session.commit()
        await self._round_repo.session.refresh(db_obj)

        return self.build_response(db_obj)

    async def reschedule_staff_round(
        self,
        application_id: int,
        round_id: int,
        data: StaffRescheduleRequest,
    ) -> ApplicationRoundResponse:
        app = await self._verify_application_exists(application_id)
        db_obj = await self._round_repo.get_by_id(round_id)
        if not db_obj or db_obj.application_id != application_id:
            raise NotFoundError("Application round not found")

        if db_obj.status == RoundStatus.CANCELLED:
            raise BadRequestError("Cannot reschedule a cancelled round.")

        sched_type = data.schedule_type or db_obj.schedule_type
        new_from = data.new_available_from or data.new_scheduled_at or db_obj.available_from
        new_until = data.new_available_until if sched_type == ScheduleType.AVAILABILITY_WINDOW else None

        self._validate_schedule(
            schedule_type=sched_type,
            available_from=new_from,
            available_until=new_until,
            duration_minutes=db_obj.duration_minutes,
            applied_at=app.applied_at,
        )

        db_obj.schedule_type = sched_type
        db_obj.available_from = new_from
        db_obj.available_until = new_until
        db_obj.rescheduled_at = get_now_utc()
        db_obj.reschedule_reason = data.reason
        db_obj.student_attendance = StudentAttendance.NOT_REPORTED
        db_obj.student_action_at = None
        db_obj.staff_verification = StaffVerification.PENDING
        db_obj.staff_verified_at = None
        db_obj.staff_verified_by_id = None
        db_obj.result = RoundResult.PENDING
        db_obj.completed_at = None

        self._round_repo.session.add(db_obj)
        await self._round_repo.session.commit()
        await self._round_repo.session.refresh(db_obj)

        return self.build_response(db_obj)

    async def list_for_student(self, application_id: int, user_id: int) -> Sequence[ApplicationRoundResponse]:
        app = await self._verify_application_exists(application_id)
        student = await self._student_repo.get_by_user_id(user_id)
        if not student or app.student_id != student.id:
            raise NotFoundError("Application not found")

        rounds = await self._round_repo.list_by_application(application_id)
        now = get_now_utc()
        return [self.build_response(r, now=now) for r in rounds]

    async def get_for_student(self, application_id: int, round_id: int, user_id: int) -> ApplicationRoundResponse:
        app = await self._verify_application_exists(application_id)
        student = await self._student_repo.get_by_user_id(user_id)
        if not student or app.student_id != student.id:
            raise NotFoundError("Application round not found")

        db_obj = await self._round_repo.get_by_id(round_id)
        if not db_obj or db_obj.application_id != application_id:
            raise NotFoundError("Application round not found")

        return self.build_response(db_obj, now=get_now_utc())

    def _validate_status_result(self, status: RoundStatus, result: RoundResult | None):
        if status in [RoundStatus.NOT_STARTED, RoundStatus.SCHEDULED, RoundStatus.IN_PROGRESS]:
            if result and result != RoundResult.PENDING:
                raise BadRequestError(f"Round result cannot be {result} when status is {status}")

        if status == RoundStatus.CANCELLED:
            if result and result != RoundResult.PENDING:
                raise BadRequestError(f"Round result cannot be {result} when status is Cancelled")
