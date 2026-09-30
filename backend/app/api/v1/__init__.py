"""
Aggregates all v1 routers into a single `api_router`.

Further feature-module routers (placements, etc.) will be included
here in later tasks.
"""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.modules.auth.router import router as auth_router
from app.modules.companies.router import staff_companies_router
from app.modules.jobs.router import staff_jobs_router, student_jobs_router
from app.modules.applications.router import staff_applications_router, student_applications_router
from app.modules.resumes.router import router as resumes_router
from app.modules.skills.router import (
    router as skills_router,
    staff_skills_router,
    student_skills_router,
)
from app.modules.staff_students.router import staff_students_router
from app.modules.students.router import (
    departments_router,
    router as students_router,
    staff_departments_router,
)

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(students_router)
api_router.include_router(departments_router)
api_router.include_router(staff_departments_router)
api_router.include_router(skills_router)
api_router.include_router(student_skills_router)
api_router.include_router(staff_skills_router)
api_router.include_router(staff_companies_router)
api_router.include_router(staff_students_router)
api_router.include_router(staff_jobs_router)
api_router.include_router(student_jobs_router)
api_router.include_router(resumes_router)
from app.modules.placements.router import staff_router as staff_placements_router, student_router as student_placements_router
from app.modules.application_rounds.router import staff_router as staff_rounds_router, student_router as student_rounds_router

api_router.include_router(student_applications_router, prefix="/student/applications", tags=["student-applications"])
api_router.include_router(staff_applications_router, prefix="/staff/applications", tags=["staff-applications"])
api_router.include_router(student_placements_router)
api_router.include_router(staff_placements_router)
api_router.include_router(student_rounds_router)
api_router.include_router(staff_rounds_router)

from app.modules.analytics.router import router as analytics_router
api_router.include_router(analytics_router, tags=["analytics"])

from app.modules.intelligence.router import router as intelligence_router
api_router.include_router(intelligence_router)

