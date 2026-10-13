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
    MentorChatRequest,
    MentorChatResponse,
    MentorSessionSummaryResponse,
    MentorSessionDetailResponse,
    JobReadinessAssessmentResponse,
    ImprovementPlanResponse,
    ImprovementPlanActionResponse,
    UpdateActionStatusRequest,
    JobMentorAdviceRequest,
    JobMentorAdviceResponse,
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


@router.post("/mentor/chat", response_model=MentorChatResponse)
async def chat_with_mentor(
    request: MentorChatRequest,
    current_user: RequireStudent,
    intelligence_service: IntelligenceServiceDep,
) -> MentorChatResponse:
    """
    Chat with the AI Career Mentor grounded in the authenticated student's
    academic standing, registered skills, applications, and campus placement drives.
    """
    return await intelligence_service.ask_career_mentor(current_user.id, request)


@router.get("/mentor/sessions", response_model=list[MentorSessionSummaryResponse])
async def list_mentor_sessions(
    current_user: RequireStudent,
    intelligence_service: IntelligenceServiceDep,
) -> list[MentorSessionSummaryResponse]:
    """
    List all chat sessions and conversation history summaries for the authenticated student.
    """
    return await intelligence_service.list_mentor_sessions(current_user.id)


@router.post("/mentor/sessions", response_model=MentorSessionDetailResponse)
async def create_mentor_session(
    current_user: RequireStudent,
    intelligence_service: IntelligenceServiceDep,
) -> MentorSessionDetailResponse:
    """
    Start a fresh, clean chat session.
    """
    return await intelligence_service.create_new_mentor_session(current_user.id)


@router.get("/mentor/sessions/{session_id}", response_model=MentorSessionDetailResponse)
async def get_mentor_session(
    session_id: int,
    current_user: RequireStudent,
    intelligence_service: IntelligenceServiceDep,
) -> MentorSessionDetailResponse:
    """
    Retrieve full message history for a specific chat session.
    """
    return await intelligence_service.get_mentor_session_detail(current_user.id, session_id)


@router.delete("/mentor/sessions/{session_id}")
async def delete_mentor_session(
    session_id: int,
    current_user: RequireStudent,
    intelligence_service: IntelligenceServiceDep,
) -> dict:
    """
    Delete a specific chat session and all its messages.
    """
    return await intelligence_service.delete_mentor_session(current_user.id, session_id)



@router.get("/jobs/{job_id}/readiness", response_model=JobReadinessAssessmentResponse)
async def get_job_readiness(
    job_id: int,
    current_user: RequireStudent,
    intelligence_service: IntelligenceServiceDep,
) -> JobReadinessAssessmentResponse:
    """
    Get an explainable job-specific readiness assessment evaluating eligibility,
    demonstrated/partially supported/missing skill evidence, and past round signals.
    """
    return await intelligence_service.assess_job_readiness(current_user.id, job_id)


@router.post("/jobs/{job_id}/plan", response_model=ImprovementPlanResponse)
async def generate_or_get_improvement_plan(
    job_id: int,
    current_user: RequireStudent,
    intelligence_service: IntelligenceServiceDep,
) -> ImprovementPlanResponse:
    """
    Generate or retrieve a personalized improvement plan with prioritized actions
    targeting identified skill and evidence gaps for the selected job.
    """
    return await intelligence_service.get_or_create_improvement_plan(current_user.id, job_id)


@router.get("/jobs/{job_id}/plan", response_model=ImprovementPlanResponse | None)
async def get_job_improvement_plan(
    job_id: int,
    current_user: RequireStudent,
    intelligence_service: IntelligenceServiceDep,
) -> ImprovementPlanResponse | None:
    """
    Retrieve existing personalized improvement plan for the specified job, if any.
    """
    return await intelligence_service.get_improvement_plan(current_user.id, job_id)


@router.patch("/plans/actions/{action_id}", response_model=ImprovementPlanActionResponse)
async def update_improvement_action_status(
    action_id: int,
    request: UpdateActionStatusRequest,
    current_user: RequireStudent,
    intelligence_service: IntelligenceServiceDep,
) -> ImprovementPlanActionResponse:
    """
    Update progress status for an improvement plan action item (PENDING -> IN_PROGRESS -> COMPLETED).
    """
    return await intelligence_service.update_plan_action_status(
        current_user.id,
        action_id,
        request.status,
        evidence_source=request.evidence_source,
        evidence_reference=request.evidence_reference,
    )


@router.post("/jobs/{job_id}/mentor-advice", response_model=JobMentorAdviceResponse)
async def get_job_mentor_advice(
    job_id: int,
    request: JobMentorAdviceRequest,
    current_user: RequireStudent,
    intelligence_service: IntelligenceServiceDep,
) -> JobMentorAdviceResponse:
    """
    Ask the AI Career Mentor for contextual advice about readiness for a target job
    and its improvement plan actions (with resilient fallback if the provider fails).
    """
    return await intelligence_service.ask_job_mentor_advice(
        current_user.id, job_id, request
    )

