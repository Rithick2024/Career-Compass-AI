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
from app.modules.application_rounds.models import (
    ApplicationRound,
    RoundType,
    RoundResult,
    StaffVerification,
)
from app.modules.placements.models import Placement
from app.modules.intelligence.models import ImprovementPlan, ImprovementPlanAction


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

    async def get_student_past_round_signals(self, student_id: int) -> List[ApplicationRound]:
        """Fetch past completed/evaluated application rounds for this student across drives."""
        stmt = (
            select(ApplicationRound)
            .join(Application, ApplicationRound.application_id == Application.id)
            .where(
                Application.student_id == student_id,
                ApplicationRound.result.isnot(None),
            )
            .order_by(ApplicationRound.created_at.desc())
            .limit(10)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_improvement_plan(self, student_id: int, job_id: int) -> Optional[ImprovementPlan]:
        """Fetch existing improvement plan for student and job with actions eagerly loaded."""
        stmt = (
            select(ImprovementPlan)
            .options(selectinload(ImprovementPlan.actions))
            .where(
                ImprovementPlan.student_id == student_id,
                ImprovementPlan.job_id == job_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update_improvement_plan(
        self, student_id: int, job_id: int, actions_data: List[dict]
    ) -> ImprovementPlan:
        """
        Create a new improvement plan or update existing plan actions idempotently.
        Preserves existing COMPLETED statuses if already completed.
        """
        existing_plan = await self.get_improvement_plan(student_id, job_id)
        if existing_plan is None:
            plan = ImprovementPlan(student_id=student_id, job_id=job_id)
            self.db.add(plan)
            await self.db.flush()

            for item in actions_data:
                action = ImprovementPlanAction(
                    plan_id=plan.id,
                    skill_id=item.get("skill_id"),
                    skill_name=item["skill_name"],
                    current_proficiency=item.get("current_proficiency"),
                    target_proficiency=item["target_proficiency"],
                    priority=item["priority"],
                    status=item.get("status", "PENDING"),
                    reason=item["reason"],
                    suggested_activity=item["suggested_activity"],
                    completion_criteria=item["completion_criteria"],
                )
                self.db.add(action)
            await self.db.commit()
            refreshed = await self.get_improvement_plan(student_id, job_id)
            return refreshed  # type: ignore

        existing_actions_map = {act.skill_name.lower(): act for act in existing_plan.actions}

        for item in actions_data:
            sk_key = item["skill_name"].lower()
            if sk_key in existing_actions_map:
                existing_act = existing_actions_map[sk_key]
                if existing_act.status != "COMPLETED":
                    existing_act.current_proficiency = item.get("current_proficiency")
                    existing_act.target_proficiency = item["target_proficiency"]
                    existing_act.priority = item["priority"]
                    existing_act.reason = item["reason"]
                    existing_act.suggested_activity = item["suggested_activity"]
                    existing_act.completion_criteria = item["completion_criteria"]
            else:
                new_act = ImprovementPlanAction(
                    plan_id=existing_plan.id,
                    skill_id=item.get("skill_id"),
                    skill_name=item["skill_name"],
                    current_proficiency=item.get("current_proficiency"),
                    target_proficiency=item["target_proficiency"],
                    priority=item["priority"],
                    status="PENDING",
                    reason=item["reason"],
                    suggested_activity=item["suggested_activity"],
                    completion_criteria=item["completion_criteria"],
                )
                self.db.add(new_act)

        await self.db.commit()
        refreshed = await self.get_improvement_plan(student_id, job_id)
        return refreshed  # type: ignore

    async def get_action_by_id_and_student(
        self, action_id: int, student_id: int
    ) -> Optional[ImprovementPlanAction]:
        """Ensure student ownership before allowing action status updates."""
        stmt = (
            select(ImprovementPlanAction)
            .join(ImprovementPlan, ImprovementPlanAction.plan_id == ImprovementPlan.id)
            .where(
                ImprovementPlanAction.id == action_id,
                ImprovementPlan.student_id == student_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_student_assessed_skills(self, student_id: int) -> dict[int, dict]:
        """
        Query completed application rounds where student passed a technical assessment or interview,
        returning evidence provenance per skill_id (round_type, company, job_title, result, date).
        """
        stmt = (
            select(
                JobRequiredSkill.skill_id,
                JobRequiredSkill.min_proficiency,
                ApplicationRound.round_type,
                ApplicationRound.result,
                ApplicationRound.staff_verification,
                ApplicationRound.completed_at,
                Job.title.label("job_title"),
                Company.name.label("company_name"),
            )
            .join(Application, Application.id == ApplicationRound.application_id)
            .join(Job, Job.id == Application.job_id)
            .join(Company, Company.id == Job.company_id)
            .join(JobRequiredSkill, JobRequiredSkill.job_id == Job.id)
            .where(
                Application.student_id == student_id,
                ApplicationRound.result == RoundResult.PASSED,
                ApplicationRound.round_type.in_([
                    RoundType.ONLINE_ASSESSMENT,
                    RoundType.CODING_TEST,
                    RoundType.TECHNICAL_INTERVIEW,
                    RoundType.MANAGERIAL_INTERVIEW,
                ]),
            )
            .order_by(ApplicationRound.completed_at.desc())
        )
        res = await self.db.execute(stmt)
        assessed_map: dict[int, dict] = {}
        for row in res.all():
            skill_id = row.skill_id
            if skill_id not in assessed_map:
                assessed_map[skill_id] = {
                    "skill_id": skill_id,
                    "min_proficiency": row.min_proficiency,
                    "round_type": row.round_type.value if hasattr(row.round_type, "value") else str(row.round_type),
                    "result": row.result.value if hasattr(row.result, "value") else str(row.result),
                    "staff_verification": row.staff_verification.value if hasattr(row.staff_verification, "value") else str(row.staff_verification),
                    "job_title": row.job_title,
                    "company_name": row.company_name,
                    "completed_at": row.completed_at,
                }
        return assessed_map

    async def update_action_status(
        self,
        action: ImprovementPlanAction,
        new_status: str,
        evidence_source: Optional[str] = None,
        evidence_reference: Optional[str] = None,
    ) -> ImprovementPlanAction:
        action.status = new_status
        if new_status == "COMPLETED":
            if not action.completed_at:
                action.completed_at = func.now()
            if evidence_source is not None:
                action.evidence_source = evidence_source
            elif not action.evidence_source:
                action.evidence_source = "PRACTICE_COMPLETED"
            if evidence_reference is not None:
                action.evidence_reference = evidence_reference
        elif new_status != "COMPLETED":
            action.completed_at = None
        await self.db.commit()
        await self.db.refresh(action)
        return action

