from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, or_, and_, desc
from datetime import datetime, timezone

from app.modules.students.models import Student
from app.modules.jobs.models import Job
from app.modules.companies.models import Company
from app.modules.applications.models import Application, ApplicationStatus
from app.modules.placements.models import Placement
from app.modules.application_rounds.models import ApplicationRound, RoundStatus, RoundResult, RoundType
from app.modules.students.models import Department


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
                ApplicationRound.scheduled_at,
                ApplicationRound.status
            )
            .join(Application, Application.id == ApplicationRound.application_id)
            .join(Job, Job.id == Application.job_id)
            .join(Company, Company.id == Job.company_id)
            .where(
                Application.student_id == student_id,
                ApplicationRound.status == RoundStatus.SCHEDULED,
                ApplicationRound.scheduled_at > now
            )
            .order_by(ApplicationRound.scheduled_at.asc())
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
