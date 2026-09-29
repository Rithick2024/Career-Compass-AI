"""
Job repository — SQLAlchemy query execution for jobs, required skills, and eligible departments.
"""

from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import or_, select, and_
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.models import Company
from app.modules.jobs.models import Job, JobEligibleDepartment, JobRequiredSkill
from app.modules.jobs.schemas import JobRequiredSkillRequest


class JobRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, job_id: int) -> Optional[Job]:
        result = await self._db.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()

    async def list_jobs(
        self,
        search: Optional[str] = None,
        company_id: Optional[int] = None,
        department_id: Optional[int] = None,
        status: Optional[str] = "all",
    ) -> Sequence[Job]:
        query = select(Job).join(Company, Job.company_id == Company.id)

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Job.title.ilike(term),
                    Company.name.ilike(term),
                    Job.location.ilike(term),
                    Job.role_category.ilike(term),
                )
            )

        if company_id is not None:
            query = query.where(Job.company_id == company_id)

        if department_id is not None:
            dept_subq = select(JobEligibleDepartment.job_id).where(
                JobEligibleDepartment.department_id == department_id
            )
            query = query.where(Job.id.in_(dept_subq))

        now = datetime.now(timezone.utc)
        if status == "active":
            query = query.where(
                Job.is_active == True,  # noqa: E712
                or_(Job.deadline.is_(None), Job.deadline >= now),
            )
        elif status == "inactive":
            query = query.where(Job.is_active == False)  # noqa: E712
        elif status == "expired":
            query = query.where(
                Job.is_active == True,  # noqa: E712
                Job.deadline.is_not(None),
                Job.deadline < now,
            )

        query = query.order_by(Job.created_at.desc(), Job.id.desc())
        result = await self._db.execute(query)
        return result.scalars().all()

    async def create_job(
        self,
        job_data: dict,
        required_skills: list[JobRequiredSkillRequest],
        eligible_department_ids: list[int],
    ) -> Job:
        job = Job(**job_data)
        self._db.add(job)
        await self._db.flush()  # Assigns job.id

        # Unique skills normalization
        seen_skill_ids = set()
        for req_skill in required_skills:
            if req_skill.skill_id not in seen_skill_ids:
                seen_skill_ids.add(req_skill.skill_id)
                jrs = JobRequiredSkill(
                    job_id=job.id,
                    skill_id=req_skill.skill_id,
                    min_proficiency=req_skill.min_proficiency,
                )
                self._db.add(jrs)

        # Unique departments normalization
        seen_dept_ids = set()
        for dept_id in eligible_department_ids:
            if dept_id not in seen_dept_ids:
                seen_dept_ids.add(dept_id)
                jed = JobEligibleDepartment(job_id=job.id, department_id=dept_id)
                self._db.add(jed)

        await self._db.flush()
        await self._db.refresh(job)
        return job

    async def update_job(
        self,
        job: Job,
        job_updates: dict,
        required_skills: Optional[list[JobRequiredSkillRequest]] = None,
        eligible_department_ids: Optional[list[int]] = None,
    ) -> Job:
        for field, value in job_updates.items():
            setattr(job, field, value)

        if required_skills is not None:
            # Clear existing skills and insert updated list
            job.required_skills.clear()
            await self._db.flush()
            seen_skill_ids = set()
            for req_skill in required_skills:
                if req_skill.skill_id not in seen_skill_ids:
                    seen_skill_ids.add(req_skill.skill_id)
                    jrs = JobRequiredSkill(
                        job_id=job.id,
                        skill_id=req_skill.skill_id,
                        min_proficiency=req_skill.min_proficiency,
                    )
                    self._db.add(jrs)

        if eligible_department_ids is not None:
            # Clear existing departments and insert updated list
            job.eligible_departments.clear()
            await self._db.flush()
            seen_dept_ids = set()
            for dept_id in eligible_department_ids:
                if dept_id not in seen_dept_ids:
                    seen_dept_ids.add(dept_id)
                    jed = JobEligibleDepartment(job_id=job.id, department_id=dept_id)
                    self._db.add(jed)

        await self._db.flush()
        await self._db.refresh(job)
        return job

    async def update_job_status(self, job: Job, is_active: bool) -> Job:
        job.is_active = is_active
        await self._db.flush()
        await self._db.refresh(job)
        return job

    def get_active_student_jobs_query(self):
        now = datetime.now(timezone.utc)
        return (
            select(Job)
            .join(Company, Job.company_id == Company.id)
            .where(
                and_(
                    Job.is_active == True,
                    Company.is_active == True,
                    or_(Job.deadline.is_(None), Job.deadline >= now),
                )
            )
            .options(
                joinedload(Job.company),
                joinedload(Job.required_skills).joinedload(JobRequiredSkill.skill),
                joinedload(Job.eligible_departments).joinedload(JobEligibleDepartment.department),
            )
        )

    async def list_student_jobs(
        self,
        search: Optional[str] = None,
        company_id: Optional[int] = None,
        employment_type: Optional[str] = None,
    ) -> Sequence[Job]:
        query = self.get_active_student_jobs_query()

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Job.title.ilike(term),
                    Company.name.ilike(term),
                    Job.role_category.ilike(term),
                )
            )

        if company_id is not None:
            query = query.where(Job.company_id == company_id)

        if employment_type and employment_type.strip():
            query = query.where(Job.employment_type.ilike(employment_type.strip()))

        query = query.order_by(Job.created_at.desc(), Job.id.desc())
        result = await self._db.execute(query)
        # Using unique() is necessary when using joinedload with collections
        return result.scalars().unique().all()

    async def get_student_job(self, job_id: int) -> Optional[Job]:
        query = self.get_active_student_jobs_query().where(Job.id == job_id)
        result = await self._db.execute(query)
        return result.scalars().unique().one_or_none()

