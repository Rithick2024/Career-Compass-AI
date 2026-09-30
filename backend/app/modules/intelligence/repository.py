"""
Intelligence repository for fetching student profiles, active jobs, skills, resumes, and placements.
"""

from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.students.models import Student
from app.modules.skills.models import StudentSkill, Skill
from app.modules.resumes.models import Resume
from app.modules.jobs.models import Job, JobRequiredSkill, JobEligibleDepartment
from app.modules.companies.models import Company
from app.modules.applications.models import Application
from app.modules.placements.models import Placement


class IntelligenceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_student_by_user_id(self, user_id: int) -> Student:
        """Fetch Student profile by user_id, auto-creating an empty profile if needed."""
        stmt = (
            select(Student)
            .options(selectinload(Student.department))
            .where(Student.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        student = result.scalar_one_or_none()
        if student is None:
            student = Student(user_id=user_id)
            self.db.add(student)
            await self.db.flush()
            result = await self.db.execute(stmt)
            student = result.scalar_one_or_none()
        return student

    async def get_student_skills(self, student_id: int) -> List[StudentSkill]:
        """Fetch all StudentSkills for a student, eager loading skill master record."""
        stmt = (
            select(StudentSkill)
            .options(selectinload(StudentSkill.skill))
            .where(StudentSkill.student_id == student_id)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_student_resumes(self, student_id: int) -> List[Resume]:
        """Fetch all uploaded Resumes for a student."""
        stmt = select(Resume).where(Resume.student_id == student_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def has_accepted_placement(self, student_id: int) -> bool:
        """Check if student has an accepted placement (offer_accepted=True)."""
        stmt = (
            select(Placement.id)
            .join(Application, Placement.application_id == Application.id)
            .where(
                Application.student_id == student_id,
                Placement.offer_accepted.is_(True)
            )
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_active_visible_jobs(self) -> List[Job]:
        """
        Fetch all active visible jobs:
        - job.is_active is True
        - company.is_active is True
        - deadline is None or deadline >= current time
        """
        stmt = (
            select(Job)
            .join(Company, Job.company_id == Company.id)
            .options(
                selectinload(Job.company),
                selectinload(Job.required_skills).selectinload(JobRequiredSkill.skill),
                selectinload(Job.eligible_departments).selectinload(JobEligibleDepartment.department),
            )
            .where(
                Job.is_active.is_(True),
                Company.is_active.is_(True),
                (Job.deadline.is_(None) | (Job.deadline >= func.now())),
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_active_visible_job_by_id(self, job_id: int) -> Optional[Job]:
        """
        Fetch a single active visible job by job_id under identical visibility rules.
        """
        stmt = (
            select(Job)
            .join(Company, Job.company_id == Company.id)
            .options(
                selectinload(Job.company),
                selectinload(Job.required_skills).selectinload(JobRequiredSkill.skill),
                selectinload(Job.eligible_departments).selectinload(JobEligibleDepartment.department),
            )
            .where(
                Job.id == job_id,
                Job.is_active.is_(True),
                Company.is_active.is_(True),
                (Job.deadline.is_(None) | (Job.deadline >= func.now())),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
