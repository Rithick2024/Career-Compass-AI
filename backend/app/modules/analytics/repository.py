from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, or_, and_, desc
from datetime import datetime, timezone

from app.modules.students.models import Student, Department
from app.modules.jobs.models import Job, JobRequiredSkill, JobEligibleDepartment
from app.modules.skills.models import Skill, StudentSkill
from app.modules.companies.models import Company
from app.modules.applications.models import Application, ApplicationStatus
from app.modules.placements.models import Placement
from app.modules.application_rounds.models import ApplicationRound, RoundStatus, RoundResult, RoundType


class AnalyticsRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def count_students(self) -> int:
        stmt = select(func.count(Student.id))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() or 0

    async def count_active_jobs(self) -> int:
        now = datetime.now(timezone.utc)
        stmt = (
            select(func.count(Job.id))
            .join(Company, Company.id == Job.company_id)
            .where(
                Job.is_active == True,
                Company.is_active == True,
                or_(Job.deadline == None, Job.deadline >= now)
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() or 0

    async def count_pending_applications(self) -> int:
        stmt = select(func.count(Application.id)).where(Application.status == ApplicationStatus.PENDING)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() or 0

    async def count_accepted_placements(self) -> int:
        stmt = select(func.count(Placement.id)).where(Placement.offer_accepted == True)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() or 0

    async def average_accepted_package(self) -> float:
        stmt = select(func.avg(Placement.final_package_ctc)).where(Placement.offer_accepted == True)
        result = await self._session.execute(stmt)
        val = result.scalar_one_or_none()
        return float(val) if val is not None else 0.0

    async def applications_by_status(self) -> dict[str, int]:
        stmt = select(Application.status, func.count(Application.id)).group_by(Application.status)
        result = await self._session.execute(stmt)
        return {status.value: count for status, count in result.all()}

    async def placements_by_department(self) -> list[tuple[str, int]]:
        stmt = (
            select(Department.name, func.count(Placement.id))
            .select_from(Placement)
            .join(Application, Application.id == Placement.application_id)
            .join(Student, Student.id == Application.student_id)
            .outerjoin(Department, Department.id == Student.department_id)
            .where(Placement.offer_accepted == True)
            .group_by(Department.name)
        )
        result = await self._session.execute(stmt)
        return [(name if name else "Unknown Department", count) for name, count in result.all()]

    async def staff_round_summary(self) -> dict:
        stmt = select(
            func.count(ApplicationRound.id).label('total'),
            func.sum(case((ApplicationRound.status == RoundStatus.SCHEDULED, 1), else_=0)).label('scheduled'),
            func.sum(case((ApplicationRound.status == RoundStatus.COMPLETED, 1), else_=0)).label('completed'),
            func.sum(case((ApplicationRound.result == RoundResult.PASSED, 1), else_=0)).label('passed'),
            func.sum(case((ApplicationRound.result == RoundResult.FAILED, 1), else_=0)).label('failed'),
        )
        result = await self._session.execute(stmt)
        row = result.first()
        if not row:
            return {"total": 0, "scheduled": 0, "completed": 0, "passed": 0, "failed": 0}
        
        return {
            "total": row.total or 0,
            "scheduled": row.scheduled or 0,
            "completed": row.completed or 0,
            "passed": row.passed or 0,
            "failed": row.failed or 0
        }

    async def staff_rounds_by_type(self) -> dict[str, int]:
        stmt = select(ApplicationRound.round_type, func.count(ApplicationRound.id)).group_by(ApplicationRound.round_type)
        result = await self._session.execute(stmt)
        return {rtype.value: count for rtype, count in result.all()}

    # --- Student Methods ---

    async def count_student_active_applications(self, student_id: int) -> int:
        stmt = (
            select(func.count(Application.id))
            .where(
                Application.student_id == student_id,
                Application.status.not_in([ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN])
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() or 0

    async def count_student_offers(self, student_id: int) -> int:
        stmt = (
            select(func.count(Application.id))
            .where(
                Application.student_id == student_id,
                Application.status == ApplicationStatus.OFFERED
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() or 0

    async def get_student_upcoming_rounds(self, student_id: int, limit: int = 5):
        now = datetime.now(timezone.utc)
        stmt = (
            select(
                ApplicationRound.id,
                ApplicationRound.round_type,
                Job.title.label("job_title"),
                Company.name.label("company_name"),
                ApplicationRound.available_from.label("scheduled_at"),
                ApplicationRound.status
            )
            .join(Application, Application.id == ApplicationRound.application_id)
            .join(Job, Job.id == Application.job_id)
            .join(Company, Company.id == Job.company_id)
            .where(
                Application.student_id == student_id,
                ApplicationRound.status == RoundStatus.SCHEDULED,
                ApplicationRound.available_from > now
            )
            .order_by(ApplicationRound.available_from.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.all()

    async def get_student_recent_applications(self, student_id: int, limit: int = 5):
        stmt = (
            select(
                Application.id,
                Job.title.label("job_title"),
                Company.name.label("company_name"),
                Application.status,
                Application.applied_at
            )
            .join(Job, Job.id == Application.job_id)
            .join(Company, Company.id == Job.company_id)
            .where(Application.student_id == student_id)
            .order_by(Application.applied_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.all()

    async def student_applications_by_status(self, student_id: int) -> dict[str, int]:
        stmt = (
            select(Application.status, func.count(Application.id))
            .where(Application.student_id == student_id)
            .group_by(Application.status)
        )
        result = await self._session.execute(stmt)
        return {status.value: count for status, count in result.all()}

    async def student_round_summary(self, student_id: int) -> dict:
        stmt = (
            select(
                func.count(ApplicationRound.id).label('total'),
                func.sum(case((ApplicationRound.status == RoundStatus.SCHEDULED, 1), else_=0)).label('scheduled'),
                func.sum(case((ApplicationRound.status == RoundStatus.COMPLETED, 1), else_=0)).label('completed'),
                func.sum(case((ApplicationRound.result == RoundResult.PASSED, 1), else_=0)).label('passed'),
                func.sum(case((ApplicationRound.result == RoundResult.FAILED, 1), else_=0)).label('failed'),
            )
            .join(Application, Application.id == ApplicationRound.application_id)
            .where(Application.student_id == student_id)
        )
        result = await self._session.execute(stmt)
        row = result.first()
        if not row:
            return {"total": 0, "scheduled": 0, "completed": 0, "passed": 0, "failed": 0}
        
        return {
            "total": row.total or 0,
            "scheduled": row.scheduled or 0,
            "completed": row.completed or 0,
            "passed": row.passed or 0,
            "failed": row.failed or 0
        }

    async def student_placement_summary(self, student_id: int) -> dict:
        stmt_count = (
            select(func.count(Placement.id))
            .join(Application, Application.id == Placement.application_id)
            .where(Application.student_id == student_id, Placement.offer_accepted == True)
        )
        count_res = await self._session.execute(stmt_count)
        accepted_count = count_res.scalar_one_or_none() or 0

        if accepted_count == 0:
            return {
                "has_accepted_placement": False,
                "accepted_placement_count": 0,
                "latest_accepted_placement_company": None,
                "latest_accepted_placement_package": None,
                "latest_accepted_placement_date": None,
            }

        stmt_latest = (
            select(
                Company.name,
                Placement.final_package_ctc,
                Placement.placement_date
            )
            .join(Application, Application.id == Placement.application_id)
            .join(Job, Job.id == Application.job_id)
            .join(Company, Company.id == Job.company_id)
            .where(Application.student_id == student_id, Placement.offer_accepted == True)
            .order_by(Placement.placement_date.desc())
            .limit(1)
        )
        latest_res = await self._session.execute(stmt_latest)
        latest_row = latest_res.first()

        return {
            "has_accepted_placement": True,
            "accepted_placement_count": accepted_count,
            "latest_accepted_placement_company": latest_row[0] if latest_row else None,
            "latest_accepted_placement_package": float(latest_row[1]) if latest_row and latest_row[1] else None,
            "latest_accepted_placement_date": latest_row[2] if latest_row else None,
        }

    async def get_department_skill_gaps(self) -> dict:
        """
        Aggregate in-demand skills and top missing skills per department across active jobs.
        """
        now = datetime.now(timezone.utc)
        jobs_stmt = (
            select(Job)
            .join(Company, Company.id == Job.company_id)
            .where(
                Job.is_active == True,
                Company.is_active == True,
                or_(Job.deadline == None, Job.deadline >= now),
            )
        )
        jobs_res = await self._session.execute(jobs_stmt)
        active_jobs = list(jobs_res.scalars().all())

        depts_stmt = select(Department).order_by(Department.name)
        depts_res = await self._session.execute(depts_stmt)
        departments = list(depts_res.scalars().all())

        results = []
        for dept in departments:
            # Count students in department
            st_stmt = select(Student.id).where(Student.department_id == dept.id)
            st_res = await self._session.execute(st_stmt)
            dept_student_ids = list(st_res.scalars().all())
            dept_student_count = len(dept_student_ids)

            # Determine jobs open to this department
            eligible_jobs = [
                j for j in active_jobs
                if not j.eligible_departments or any(ed.department_id == dept.id for ed in j.eligible_departments)
            ]

            # Count demand for skills among eligible jobs
            skill_demand_counts: dict[str, int] = {}
            for j in eligible_jobs:
                for req in j.required_skills:
                    if req.skill:
                        skill_demand_counts[req.skill.name] = skill_demand_counts.get(req.skill.name, 0) + 1

            # Top in-demand skills (ordered by job frequency)
            sorted_demand = sorted(skill_demand_counts.items(), key=lambda x: x[1], reverse=True)
            in_demand_skill_names = [k for k, _ in sorted_demand[:6]]

            # Determine missing skills among students in this department
            top_missing_skills = []
            if dept_student_ids and in_demand_skill_names:
                # Count how many students in dept possess each in-demand skill
                st_skills_stmt = (
                    select(Skill.name, func.count(StudentSkill.student_id.distinct()))
                    .join(StudentSkill, StudentSkill.skill_id == Skill.id)
                    .where(
                        StudentSkill.student_id.in_(dept_student_ids),
                        Skill.name.in_(in_demand_skill_names),
                    )
                    .group_by(Skill.name)
                )
                st_skills_res = await self._session.execute(st_skills_stmt)
                dept_skill_holders = {name: count for name, count in st_skills_res.all()}

                # Missing rate: students without the skill
                missing_rates = []
                for s_name in in_demand_skill_names:
                    holders = dept_skill_holders.get(s_name, 0)
                    missing_count = dept_student_count - holders
                    if missing_count > 0:
                        missing_rates.append((s_name, missing_count))

                missing_rates.sort(key=lambda x: x[1], reverse=True)
                top_missing_skills = [s for s, _ in missing_rates[:4]]
            elif not dept_student_ids:
                top_missing_skills = in_demand_skill_names[:3]

            results.append({
                "department_id": dept.id,
                "department_name": dept.name,
                "student_count": dept_student_count,
                "in_demand_skills": in_demand_skill_names[:5],
                "top_missing_skills": top_missing_skills,
            })

        return {
            "departments": results,
            "total_active_jobs_analyzed": len(active_jobs),
        }

