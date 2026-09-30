"""
FastAPI router for Student Career Intelligence (Placement Readiness & Skill Gap Analysis).
"""

from fastapi import APIRouter, Depends

from app.api.deps import IntelligenceServiceDep, RequireStudent
from app.modules.auth.models import User
from app.modules.intelligence.schemas import (
    ReadinessResponse,
    MarketSkillGapResponse,
    JobMatchResponse,
)

router = APIRouter(prefix="/student/intelligence", tags=["Student Intelligence"])


@router.get("/readiness", response_model=ReadinessResponse)
async def get_readiness(
    current_user: RequireStudent,
    intelligence_service: IntelligenceServiceDep,
) -> ReadinessResponse:
    """
    Get the authenticated student's current placement readiness score,
    pillar breakdown, and top deterministic recommendations.
    """
    return await intelligence_service.calculate_readiness(current_user.id)


@router.get("/skills/gap", response_model=MarketSkillGapResponse)
async def get_market_skill_gaps(
    current_user: RequireStudent,
    intelligence_service: IntelligenceServiceDep,
) -> MarketSkillGapResponse:
    """
    Get relevant market skill gaps across active visible job postings for the authenticated student.
    """
    return await intelligence_service.calculate_market_skill_gaps(current_user.id)


@router.get("/jobs/{job_id}/match", response_model=JobMatchResponse)
async def get_job_match(
    job_id: int,
    current_user: RequireStudent,
    intelligence_service: IntelligenceServiceDep,
) -> JobMatchResponse:
    """
    Get eligibility breakdown and skill match analysis for a specific active visible job.
    """
    return await intelligence_service.calculate_job_match(current_user.id, job_id)
