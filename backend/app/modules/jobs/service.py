"""
Job service layer — business logic, validation, and transaction management.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.modules.companies.repository import CompanyRepository
from app.modules.companies.schemas import CompanyResponse
from app.modules.jobs.models import Job
from app.modules.jobs.repository import JobRepository
from app.modules.jobs.schemas import (
    JobCreateRequest,
    JobEligibleDepartmentResponse,
    JobRequiredSkillResponse,
    JobResponse,
    JobStatusUpdateRequest,
    JobUpdateRequest,
    StudentCompanyResponse,
    StudentJobResponse,
)
from app.modules.job_rounds.schemas import JobRoundResponse
from app.modules.skills.repository import SkillRepository
from app.modules.students.repository import StudentRepository


def get_job_derived_status(job: Job, now: Optional[datetime] = None) -> str:
    if now is None:
        now = datetime.now(timezone.utc)
    if not job.is_active or (job.company and not job.company.is_active):
        return "Inactive"
    if job.application_start_at and job.application_start_at > now:
        return "Upcoming"
    if job.deadline and job.deadline <= now:
        return "Closed"
    if job.deadline and now < job.deadline <= (now + timedelta(hours=24)):
        return "Closing Soon"
    return "Open"


class JobService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = JobRepository(db)
        self._companies = CompanyRepository(db)
        self._skills = SkillRepository(db)
        self._students = StudentRepository(db)  # Has department lookup helper

    def _to_response(self, job: Job) -> JobResponse:
        now = datetime.now(timezone.utc)
        is_expired = bool(job.deadline and job.deadline < now)
        derived_status = get_job_derived_status(job, now)

        company_resp = CompanyResponse.model_validate(job.company)

        skill_responses = [
            JobRequiredSkillResponse(
                id=jrs.id,
                skill_id=jrs.skill_id,
                skill_name=jrs.skill.name if jrs.skill else "",
                category=jrs.skill.category if jrs.skill else None,
                min_proficiency=jrs.min_proficiency,
            )
            for jrs in job.required_skills
        ]

        dept_responses = [
            JobEligibleDepartmentResponse(
                id=jed.id,
                department_id=jed.department_id,
                department_name=jed.department.name if jed.department else "",
            )
            for jed in job.eligible_departments
        ]

        round_responses = [
            JobRoundResponse.model_validate(r)
            for r in sorted(job.rounds, key=lambda x: (x.round_number, x.created_at))
        ] if job.rounds else []

        return JobResponse(
            id=job.id,
            company_id=job.company_id,
            company=company_resp,
            title=job.title,
            description=job.description,
            role_category=job.role_category,
            location=job.location,
            employment_type=job.employment_type,
            ctc_lpa=float(job.ctc_lpa) if job.ctc_lpa is not None else None,
            min_cgpa=float(job.min_cgpa) if job.min_cgpa is not None else None,
            application_start_at=job.application_start_at,
            deadline=job.deadline,
            work_mode=job.work_mode,
            instructions=job.instructions,
            is_active=job.is_active,
            is_expired=is_expired,
            derived_status=derived_status,
            required_skills=skill_responses,
            eligible_departments=dept_responses,
            rounds=round_responses,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )

    async def list_jobs(
        self,
        search: Optional[str] = None,
        company_id: Optional[int] = None,
        department_id: Optional[int] = None,
        status: Optional[str] = "all",
    ) -> List[JobResponse]:
        jobs = await self._repo.list_jobs(
            search=search,
            company_id=company_id,
            department_id=department_id,
            status=status,
        )
        return [self._to_response(j) for j in jobs]

    async def get_job(self, job_id: int) -> JobResponse:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise NotFoundError(
                "The specified job posting does not exist.",
                error_code="JOB_NOT_FOUND",
            )
        return self._to_response(job)

    async def create_job(self, data: JobCreateRequest) -> JobResponse:
        # 1. Validate Company
        company = await self._companies.get_by_id(data.company_id)
        if company is None:
            raise NotFoundError(
                "The specified company does not exist.",
                error_code="COMPANY_NOT_FOUND",
            )
        if not company.is_active:
            raise ValidationError(
                "Cannot post a new job for an inactive company.",
                error_code="INVALID_COMPANY",
            )

        # 2. Validate Deadline
        now = datetime.now(timezone.utc)
        if data.deadline and data.deadline < now:
            raise ValidationError(
                "Application deadline must be in the future.",
                error_code="INVALID_DEADLINE",
            )

        # 3. Validate Skills
        seen_skill_ids = set()
        for req_skill in data.required_skills:
            if req_skill.skill_id not in seen_skill_ids:
                seen_skill_ids.add(req_skill.skill_id)
                skill = await self._skills.get_by_id(req_skill.skill_id)
                if skill is None:
                    raise ValidationError(
                        f"Skill ID {req_skill.skill_id} does not exist.",
                        error_code="INVALID_SKILL",
                    )

        # 4. Validate Departments
        seen_dept_ids = set()
        for dept_id in data.eligible_department_ids:
            if dept_id not in seen_dept_ids:
                seen_dept_ids.add(dept_id)
                dept = await self._students.get_department_by_id(dept_id)
                if dept is None:
                    raise ValidationError(
                        f"Department ID {dept_id} does not exist.",
                        error_code="INVALID_DEPARTMENT",
                    )

        # 5. Atomic DB Insertion
        job_data = {
            "company_id": data.company_id,
            "title": data.title.strip(),
            "description": data.description,
            "role_category": data.role_category,
            "location": data.location,
            "employment_type": data.employment_type or "Full-time",
            "ctc_lpa": data.ctc_lpa,
            "min_cgpa": data.min_cgpa,
            "application_start_at": data.application_start_at,
            "deadline": data.deadline,
            "work_mode": data.work_mode,
            "instructions": data.instructions,
        }

        try:
            job = await self._repo.create_job(
                job_data=job_data,
                required_skills=data.required_skills,
                eligible_department_ids=data.eligible_department_ids,
            )
            await self._db.commit()
            return self._to_response(job)
        except Exception:
            await self._db.rollback()
            raise

    async def update_job(self, job_id: int, data: JobUpdateRequest) -> JobResponse:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise NotFoundError(
                "The specified job posting does not exist.",
                error_code="JOB_NOT_FOUND",
            )

        updates = data.model_dump(exclude_unset=True)

        # 1. Validate Company change if supplied
        if "company_id" in updates and updates["company_id"] is not None:
            comp_id = updates["company_id"]
            company = await self._companies.get_by_id(comp_id)
            if company is None:
                raise NotFoundError(
                    "The specified company does not exist.",
                    error_code="COMPANY_NOT_FOUND",
                )
            if not company.is_active:
                raise ValidationError(
                    "Cannot assign job to an inactive company.",
                    error_code="INVALID_COMPANY",
                )

        # 2. Validate Skills if updated
        required_skills = updates.pop("required_skills", None)
        if required_skills is not None:
            seen_skill_ids = set()
            for req_skill_data in required_skills:
                sk_id = req_skill_data["skill_id"]
                if sk_id not in seen_skill_ids:
                    seen_skill_ids.add(sk_id)
                    skill = await self._skills.get_by_id(sk_id)
                    if skill is None:
                        raise ValidationError(
                            f"Skill ID {sk_id} does not exist.",
                            error_code="INVALID_SKILL",
                        )

        # 3. Validate Departments if updated
        eligible_department_ids = updates.pop("eligible_department_ids", None)
        if eligible_department_ids is not None:
            seen_dept_ids = set()
            for dept_id in eligible_department_ids:
                if dept_id not in seen_dept_ids:
                    seen_dept_ids.add(dept_id)
                    dept = await self._students.get_department_by_id(dept_id)
                    if dept is None:
                        raise ValidationError(
                            f"Department ID {dept_id} does not exist.",
                            error_code="INVALID_DEPARTMENT",
                        )

        # Format title if present
        if "title" in updates and updates["title"] is not None:
            updates["title"] = updates["title"].strip()

        # Convert required_skills dict back to pydantic model if supplied
        req_skills_models = None
        if required_skills is not None:
            from app.modules.jobs.schemas import JobRequiredSkillRequest
            req_skills_models = [JobRequiredSkillRequest(**s) for s in required_skills]

        try:
            updated_job = await self._repo.update_job(
                job=job,
                job_updates=updates,
                required_skills=req_skills_models,
                eligible_department_ids=eligible_department_ids,
            )
            await self._db.commit()
            return self._to_response(updated_job)
        except Exception:
            await self._db.rollback()
            raise

    async def update_job_status(self, job_id: int, data: JobStatusUpdateRequest) -> JobResponse:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise NotFoundError(
                "The specified job posting does not exist.",
                error_code="JOB_NOT_FOUND",
            )

        updated_job = await self._repo.update_job_status(job, data.is_active)
        await self._db.commit()
        return self._to_response(updated_job)

    # --- Student Endpoints ---

    def _to_student_response(self, job: Job, student: Optional[Any]) -> StudentJobResponse:
        company_resp = StudentCompanyResponse.model_validate(job.company)

        skill_responses = [
            JobRequiredSkillResponse(
                id=jrs.id,
                skill_id=jrs.skill_id,
                skill_name=jrs.skill.name if jrs.skill else "",
                category=jrs.skill.category if jrs.skill else None,
                min_proficiency=jrs.min_proficiency,
            )
            for jrs in job.required_skills
        ]

        dept_responses = [
            JobEligibleDepartmentResponse(
                id=jed.id,
                department_id=jed.department_id,
                department_name=jed.department.name if jed.department else "",
            )
            for jed in job.eligible_departments
        ]

        # Calculate Department Eligibility
        is_department_eligible = True
        if job.eligible_departments:
            if student and student.department_id:
                is_department_eligible = any(
                    jed.department_id == student.department_id
                    for jed in job.eligible_departments
                )
            else:
                is_department_eligible = False

        # Calculate CGPA Eligibility
        is_cgpa_eligible = True
        if job.min_cgpa is not None:
            if student and student.cgpa is not None:
                is_cgpa_eligible = float(student.cgpa) >= float(job.min_cgpa)
            else:
                is_cgpa_eligible = False

        derived_status = get_job_derived_status(job)

        round_responses = [
            JobRoundResponse.model_validate(r)
            for r in sorted(job.rounds, key=lambda x: (x.round_number, x.created_at))
            if r.is_active
        ] if job.rounds else []

        return StudentJobResponse(
            id=job.id,
            title=job.title,
            description=job.description,
            role_category=job.role_category,
            location=job.location,
            employment_type=job.employment_type,
            ctc_lpa=float(job.ctc_lpa) if job.ctc_lpa is not None else None,
            min_cgpa=float(job.min_cgpa) if job.min_cgpa is not None else None,
            application_start_at=job.application_start_at,
            deadline=job.deadline,
            work_mode=job.work_mode,
            instructions=job.instructions,
            derived_status=derived_status,
            company=company_resp,
            required_skills=skill_responses,
            eligible_departments=dept_responses,
            rounds=round_responses,
            is_department_eligible=is_department_eligible,
            is_cgpa_eligible=is_cgpa_eligible,
            is_fully_eligible=is_department_eligible and is_cgpa_eligible,
        )

    async def list_student_jobs(
        self,
        user_id: int,
        search: Optional[str] = None,
        company_id: Optional[int] = None,
        employment_type: Optional[str] = None,
        eligible_only: bool = False,
    ) -> List[StudentJobResponse]:
        student = await self._students.get_by_user_id(user_id)
        jobs = await self._repo.list_student_jobs(
            search=search,
            company_id=company_id,
            employment_type=employment_type,
        )

        responses = [self._to_student_response(j, student) for j in jobs]
        
        if eligible_only:
            responses = [r for r in responses if r.is_fully_eligible]
            
        return responses

    async def get_student_job(self, user_id: int, job_id: int) -> StudentJobResponse:
        student = await self._students.get_by_user_id(user_id)
        job = await self._repo.get_student_job(job_id)
        
        if job is None:
            raise NotFoundError(
                "The specified job posting does not exist or is no longer available.",
                error_code="JOB_NOT_FOUND",
            )
            
        return self._to_student_response(job, student)
