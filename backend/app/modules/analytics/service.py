from app.modules.analytics.repository import AnalyticsRepository
from app.modules.analytics.schemas import (
    StaffAnalyticsOverview,
    ApplicationStatusCount,
    DepartmentPlacementCount,
    StaffRecruitmentSummary,
    RoundTypeCount,
    StudentAnalyticsOverview,
    UpcomingRound,
    RecentApplication,
    StudentRecruitmentSummary,
    PlacementSummary,
)
from app.modules.applications.models import ApplicationStatus
from app.modules.application_rounds.models import RoundType

class AnalyticsService:
    def __init__(self, repository: AnalyticsRepository):
        self._repo = repository

    async def get_staff_overview(self) -> StaffAnalyticsOverview:
        total_students = await self._repo.count_students()
        active_jobs = await self._repo.count_active_jobs()
        pending_applications = await self._repo.count_pending_applications()
        accepted_placements = await self._repo.count_accepted_placements()
        average_package = await self._repo.average_accepted_package()

        apps_by_status = await self._repo.applications_by_status()
        placements_by_dept = await self._repo.placements_by_department()

        round_summary = await self._repo.staff_round_summary()
        rounds_by_type = await self._repo.staff_rounds_by_type()

        # Format applications by status, ensuring all exist
        app_status_counts = []
        for status in [e.value for e in ApplicationStatus]:
            app_status_counts.append(ApplicationStatusCount(
                status=status,
                count=apps_by_status.get(status, 0)
            ))

        # Format placements by dept
        dept_counts = [DepartmentPlacementCount(department=dept, count=count) for dept, count in placements_by_dept]

        # Calculate pass rate
        passed = round_summary["passed"]
        failed = round_summary["failed"]
        pass_rate = 0.0
        if passed + failed > 0:
            pass_rate = (passed / (passed + failed)) * 100.0

        # Format rounds by type
        rtype_counts = []
        for rtype in [e.value for e in RoundType]:
            rtype_counts.append(RoundTypeCount(
                round_type=rtype,
                count=rounds_by_type.get(rtype, 0)
            ))

        recruitment_summary = StaffRecruitmentSummary(
            total_rounds=round_summary["total"],
            scheduled_rounds=round_summary["scheduled"],
            completed_rounds=round_summary["completed"],
            passed_rounds=passed,
            failed_rounds=failed,
            pass_rate=pass_rate,
            rounds_by_type=rtype_counts
        )

        return StaffAnalyticsOverview(
            total_students=total_students,
            active_jobs=active_jobs,
            pending_applications=pending_applications,
            accepted_placements=accepted_placements,
            average_package=average_package,
            applications_by_status=app_status_counts,
            placements_by_department=dept_counts,
            recruitment_summary=recruitment_summary
        )

    async def get_student_overview(self, student_id: int) -> StudentAnalyticsOverview:
        active_apps = await self._repo.count_student_active_applications(student_id)
        offers = await self._repo.count_student_offers(student_id)

        apps_by_status = await self._repo.student_applications_by_status(student_id)
        app_status_counts = []
        for status in [e.value for e in ApplicationStatus]:
            app_status_counts.append(ApplicationStatusCount(
                status=status,
                count=apps_by_status.get(status, 0)
            ))

        upcoming_rounds_rows = await self._repo.get_student_upcoming_rounds(student_id)
        upcoming_rounds = [
            UpcomingRound(
                id=row.id,
                round_type=row.round_type.value,
                job_title=row.job_title,
                company_name=row.company_name,
                scheduled_at=row.scheduled_at,
                status=row.status.value
            ) for row in upcoming_rounds_rows
        ]

        recent_apps_rows = await self._repo.get_student_recent_applications(student_id)
        recent_apps = [
            RecentApplication(
                id=row.id,
                job_title=row.job_title,
                company_name=row.company_name,
                status=row.status.value,
                applied_at=row.applied_at
            ) for row in recent_apps_rows
        ]

        round_summary = await self._repo.student_round_summary(student_id)
        recruitment_summary = StudentRecruitmentSummary(
            total_rounds=round_summary["total"],
            scheduled_rounds=round_summary["scheduled"],
            completed_rounds=round_summary["completed"],
            passed_rounds=round_summary["passed"],
            failed_rounds=round_summary["failed"]
        )

        placement_summary_dict = await self._repo.student_placement_summary(student_id)
        placement_summary = PlacementSummary(**placement_summary_dict)

        return StudentAnalyticsOverview(
            active_applications=active_apps,
            total_offers=offers,
            application_status_summary=app_status_counts,
            upcoming_rounds=upcoming_rounds,
            recent_applications=recent_apps,
            recruitment_summary=recruitment_summary,
            placement_summary=placement_summary
        )
