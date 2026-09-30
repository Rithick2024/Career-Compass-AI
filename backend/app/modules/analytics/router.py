from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.db.session import get_db
from app.api.deps import get_current_user, RequireStaff, RequireStudent
from app.modules.auth.models import User
from app.modules.students.repository import StudentRepository
from app.core.exceptions import ForbiddenError

from app.modules.analytics.schemas import StaffAnalyticsOverview, StudentAnalyticsOverview
from app.modules.analytics.repository import AnalyticsRepository
from app.modules.analytics.service import AnalyticsService

router = APIRouter()

def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    repo = AnalyticsRepository(db)
    return AnalyticsService(repo)

@router.get("/staff/analytics/overview", response_model=StaffAnalyticsOverview)
async def get_staff_overview(
    _: RequireStaff,
    service: AnalyticsService = Depends(get_analytics_service)
):
    return await service.get_staff_overview()

@router.get("/student/analytics/overview", response_model=StudentAnalyticsOverview)
async def get_student_overview(
    user: RequireStudent,
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(get_analytics_service)
):
    student_repo = StudentRepository(db)
    student = await student_repo.get_by_user_id(user.id)
    if not student:
        raise ForbiddenError("Student profile required.")

    return await service.get_student_overview(student.id)
