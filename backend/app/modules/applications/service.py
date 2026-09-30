from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from asyncpg.exceptions import UniqueViolationError

from app.core.exceptions import NotFoundError, ValidationError, BadRequestError, ConflictError
from app.modules.applications.models import Application, ApplicationStatus
from app.modules.applications.repository import ApplicationRepository
from app.modules.applications.schemas import (
    ApplicationCreate,
    ApplicationStatusUpdate,
    StudentApplicationResponse,
    StaffApplicationListResponse,
    StaffApplicationDetailResponse,
)
from app.modules.jobs.repository import JobRepository
from app.modules.resumes.repository import ResumeRepository
from app.modules.students.repository import StudentRepository
from app.modules.job_rounds.models import JobRound
from app.modules.application_rounds.models import (
    ApplicationRound,
    StudentAttendance,
    StaffVerification,
    RoundResult,
)


class ApplicationService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._repo = ApplicationRepository(db)
        self._jobs = JobRepository(db)
        self._resumes = ResumeRepository(db)
        self._students = StudentRepository(db)

    def _to_student_response(self, app: Application) -> StudentApplicationResponse:
        return StudentApplicationResponse(
            id=app.id,
            student_id=app.student_id,
            job_id=app.job_id,
            resume_id=app.resume_id,
            status=app.status,
            applied_at=app.applied_at,
            updated_at=app.updated_at,
            job_title=app.job.title,
            role_category=app.job.role_category,
            location=app.job.location,
            employment_type=app.job.employment_type,
            ctc_lpa=float(app.job.ctc_lpa) if app.job.ctc_lpa else None,
            company_id=app.job.company_id,
            company_name=app.job.company.name,
            company_industry=app.job.company.industry,
            submitted_resume_title=app.resume.title,
        )

    def _to_staff_list_response(self, app: Application) -> StaffApplicationListResponse:
        return StaffApplicationListResponse(
            id=app.id,
            student_name=app.student.full_name or "Unknown Student",
            student_email=app.student.user.email,
            department=app.student.department.name if app.student.department else None,
            cgpa=float(app.student.cgpa) if app.student.cgpa else None,
            job_title=app.job.title,
            company_name=app.job.company.name,
            resume_title=app.resume.title,
            status=app.status,
            applied_at=app.applied_at,
            updated_at=app.updated_at,
        )

    def _to_staff_detail_response(self, app: Application) -> StaffApplicationDetailResponse:
        return StaffApplicationDetailResponse(
            id=app.id,
            status=app.status,
            applied_at=app.applied_at,
            updated_at=app.updated_at,
            student_name=app.student.full_name or "Unknown Student",
            student_email=app.student.user.email,
            department=app.student.department.name if app.student.department else None,
            cgpa=float(app.student.cgpa) if app.student.cgpa else None,
            job_title=app.job.title,
            company_name=app.job.company.name,
            location=app.job.location,
            employment_type=app.job.employment_type,
            ctc_lpa=float(app.job.ctc_lpa) if app.job.ctc_lpa else None,
            deadline=app.job.deadline,
            resume_id=app.resume.id,
            resume_title=app.resume.title,
            resume_file_name=app.resume.file_name,
            resume_file_type=app.resume.file_type,
            resume_file_size=app.resume.file_size,
        )

    async def create_application(self, user_id: int, data: ApplicationCreate) -> StudentApplicationResponse:
        student = await self._students.get_by_user_id(user_id)
        if not student:
            raise NotFoundError("Student profile not found.", error_code="STUDENT_NOT_FOUND")

        # Reuse student job discovery logic for visibility and active checks
        job = await self._jobs.get_student_job(data.job_id)
        if not job:
            raise BadRequestError("The specified job posting does not exist or is no longer available.", error_code="JOB_UNAVAILABLE")

        # Eligibility - Department
        if job.eligible_departments:
            if not student.department_id:
                raise BadRequestError("You must be assigned to a department to apply for this job.", error_code="INELIGIBLE_DEPARTMENT")
            if not any(jed.department_id == student.department_id for jed in job.eligible_departments):
                raise BadRequestError("Your department is not eligible for this job.", error_code="INELIGIBLE_DEPARTMENT")

        # Eligibility - CGPA
        if job.min_cgpa is not None:
            if student.cgpa is None or float(student.cgpa) < float(job.min_cgpa):
                raise BadRequestError("Your CGPA does not meet the minimum requirement for this job.", error_code="INELIGIBLE_CGPA")

        # Validate resume
        resume = await self._resumes.get_by_id_and_student_id(data.resume_id, student.id)
        if not resume:
            raise NotFoundError("The specified resume does not exist or does not belong to you.", error_code="RESUME_NOT_FOUND")

        # Fetch active job rounds for template snapshot creation
        job_rounds_stmt = (
            select(JobRound)
            .where(JobRound.job_id == data.job_id, JobRound.is_active == True)
            .order_by(JobRound.round_number.asc())
        )
        active_job_rounds = (await self._db.scalars(job_rounds_stmt)).all()

        initial_status = ApplicationStatus.INTERVIEW if active_job_rounds else ApplicationStatus.PENDING

        app_obj = Application(
            student_id=student.id,
            job_id=data.job_id,
            resume_id=data.resume_id,
            status=initial_status,
        )

        try:
            self._db.add(app_obj)
            await self._db.flush()

            for jr in active_job_rounds:
                app_round = ApplicationRound(
                    application_id=app_obj.id,
                    job_round_id=jr.id,
                    round_number=jr.round_number,
                    round_type=jr.round_type,
                    title=jr.title,
                    description=jr.description,
                    schedule_type=jr.schedule_type,
                    available_from=jr.available_from,
                    available_until=jr.available_until,
                    duration_minutes=jr.duration_minutes,
                    meeting_link=jr.meeting_link,
                    test_link=jr.test_link,
                    instructions=jr.instructions,
                    student_attendance=StudentAttendance.NOT_REPORTED,
                    staff_verification=StaffVerification.PENDING,
                    result=RoundResult.PENDING,
                )
                self._db.add(app_round)

            await self._db.commit()
            
            # Need to return fully loaded object
            return await self.get_student_application(user_id, app_obj.id)
        except IntegrityError as e:
            await self._db.rollback()
            if "uq_applications_student_id_job_id" in str(e):
                raise ConflictError("You have already applied for this job.", error_code="DUPLICATE_APPLICATION")
            raise

    async def get_student_application(self, user_id: int, application_id: int) -> StudentApplicationResponse:
        student = await self._students.get_by_user_id(user_id)
        if not student:
            raise NotFoundError("Student profile not found.", error_code="STUDENT_NOT_FOUND")

        app = await self._repo.get_by_id_for_student(application_id, student.id)
        if not app:
            raise NotFoundError("Application not found.", error_code="APPLICATION_NOT_FOUND")

        return self._to_student_response(app)

    async def list_student_applications(self, user_id: int) -> List[StudentApplicationResponse]:
        student = await self._students.get_by_user_id(user_id)
        if not student:
            return []

        apps = await self._repo.list_for_student(student.id)
        return [self._to_student_response(a) for a in apps]

    async def withdraw_application(self, user_id: int, application_id: int) -> StudentApplicationResponse:
        student = await self._students.get_by_user_id(user_id)
        if not student:
            raise NotFoundError("Student profile not found.", error_code="STUDENT_NOT_FOUND")

        app = await self._repo.get_by_id_for_student(application_id, student.id)
        if not app:
            raise NotFoundError("Application not found.", error_code="APPLICATION_NOT_FOUND")

        if app.placement is not None:
            raise BadRequestError("Cannot withdraw application after placement.", error_code="INVALID_STATUS_TRANSITION")

        if app.status not in (ApplicationStatus.PENDING, ApplicationStatus.REVIEWING, ApplicationStatus.INTERVIEW):
            raise BadRequestError(f"Cannot withdraw application in {app.status.value} status.", error_code="INVALID_STATUS_TRANSITION")

        app.status = ApplicationStatus.WITHDRAWN

        # Cancel future/uncompleted rounds
        if app.rounds:
            from app.modules.application_rounds.models import RoundStatus, RoundResult
            for rnd in app.rounds:
                if rnd.result is None or rnd.result == RoundResult.PENDING:
                    rnd.status = RoundStatus.CANCELLED

        await self._db.commit()

        # Re-fetch fully loaded
        return await self.get_student_application(user_id, application_id)

    async def list_staff_applications(
        self,
        search: str | None = None,
        job_id: int | None = None,
        status: str | None = None,
        company_id: int | None = None,
    ) -> List[StaffApplicationListResponse]:
        apps = await self._repo.list_for_staff(search, job_id=job_id, status=status, company_id=company_id)
        return [self._to_staff_list_response(a) for a in apps]

    async def get_staff_application(self, application_id: int) -> StaffApplicationDetailResponse:
        app = await self._repo.get_by_id_for_staff(application_id)
        if not app:
            raise NotFoundError("Application not found.", error_code="APPLICATION_NOT_FOUND")
        return self._to_staff_detail_response(app)

    async def update_staff_application_status(self, application_id: int, data: ApplicationStatusUpdate) -> StaffApplicationDetailResponse:
        app = await self._repo.get_by_id_for_staff(application_id)
        if not app:
            raise NotFoundError("Application not found.", error_code="APPLICATION_NOT_FOUND")

        if app.status == ApplicationStatus.WITHDRAWN:
            raise BadRequestError("Cannot update status of a withdrawn application.", error_code="INVALID_STATUS_TRANSITION")

        if app.placement and app.status == ApplicationStatus.OFFERED and data.status != ApplicationStatus.OFFERED:
            raise BadRequestError("Cannot change status from Offered because a placement record exists.", error_code="INVALID_STATUS_TRANSITION")

        app.status = data.status
        await self._db.commit()

        return await self.get_staff_application(application_id)
