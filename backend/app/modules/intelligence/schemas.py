"""
Pydantic schemas for Placement Readiness and Skill Gap Intelligence.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ReadinessComponent(BaseModel):
    name: str = Field(..., description="Name of the readiness pillar")
    score: float = Field(..., description="Calculated score for this pillar")
    max_score: float = Field(..., description="Maximum possible score for this pillar")
    weight_percentage: int = Field(..., description="Weight percentage of total readiness score")
    explanation: str = Field(..., description="Human-readable explanation of pillar calculation")

    model_config = ConfigDict(from_attributes=True)


class ReadinessResponse(BaseModel):
    readiness_score: float = Field(..., description="Composite readiness score (0.0 to 100.0)")
    status_category: str = Field(..., description="Descriptive status: Needs Improvement, Developing, Good, or Strong")
    is_placed: bool = Field(..., description="True if student has an accepted placement offer")
    components: List[ReadinessComponent] = Field(..., description="Breakdown across four core pillars")
    actionable_recommendations: List[str] = Field(..., description="Top deterministic recommendations to improve readiness")

    model_config = ConfigDict(from_attributes=True)


class SkillGapItem(BaseModel):
    skill_id: int
    skill_name: str
    category: Optional[str] = None
    jobs_requiring_skill: int = Field(..., description="Number of active visible jobs requiring this skill")
    required_proficiency: str = Field(..., description="Required proficiency level (beginner, intermediate, advanced)")
    student_proficiency: Optional[str] = Field(None, description="Student current proficiency level if possessed, else None")
    gap_type: str = Field(..., description="MISSING or INSUFFICIENT_PROFICIENCY")

    model_config = ConfigDict(from_attributes=True)


class MarketSkillGapResponse(BaseModel):
    total_active_jobs_evaluated: int = Field(..., description="Total active visible jobs evaluated for gaps")
    gaps: List[SkillGapItem] = Field(..., description="Top market skill gaps relevant to student profile")
    explanation: str = Field(..., description="Summary explanation of market gap findings")

    model_config = ConfigDict(from_attributes=True)


class JobMatchSkillItem(BaseModel):
    skill_id: int
    skill_name: str
    min_proficiency: str
    student_proficiency: Optional[str] = None
    status: str = Field(..., description="MATCHED, STRONG_MATCH, INSUFFICIENT_PROFICIENCY, or MISSING")

    model_config = ConfigDict(from_attributes=True)


class JobMatchResponse(BaseModel):
    job_id: int
    job_title: str
    company_name: str
    is_eligible: bool = Field(..., description="True if student meets both CGPA and Department criteria")
    cgpa_eligible: bool = Field(..., description="True if student meets job min CGPA requirement")
    department_eligible: bool = Field(..., description="True if student department is eligible for job")
    eligibility_explanation: str = Field(..., description="Summary of academic and department eligibility")
    skill_match_percentage: float = Field(..., description="Percentage of required skills matched (0.0 to 100.0)")
    total_required_skills: int = Field(..., description="Total required active skills for this job")
    matched_skills: List[JobMatchSkillItem] = Field(default_factory=list)
    strong_matches: List[JobMatchSkillItem] = Field(default_factory=list)
    insufficient_proficiency: List[JobMatchSkillItem] = Field(default_factory=list)
    missing_skills: List[JobMatchSkillItem] = Field(default_factory=list)
    skill_match_explanation: str = Field(..., description="Summary explanation of skill match results")

    model_config = ConfigDict(from_attributes=True)


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'model'/'assistant'")
    content: str = Field(..., max_length=1500, description="Message content")


class MentorChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=1500,
        description="Career, skill, project, or interview question from the student",
    )
    history: List[ChatMessage] = Field(
        default_factory=list,
        max_length=6,
        description="Recent conversation turns (up to 6) for conversational context",
    )


class MentorContextSummary(BaseModel):
    department: Optional[str] = None
    graduation_year: Optional[int] = None
    cgpa_available: bool = False
    skills_count: int = 0
    top_skills: List[str] = Field(default_factory=list)
    active_campus_jobs_count: int = 0


class MentorChatResponse(BaseModel):
    response: str = Field(..., description="Grounded career guidance and actionable recommendations")
    grounded_context: MentorContextSummary = Field(
        ..., description="Anonymized student profile metrics used to ground this guidance"
    )
    model_used: str = Field(..., description="Configured Gemini model ID that produced this response")


class SkillEvidenceItem(BaseModel):
    skill_id: int
    skill_name: str
    required_proficiency: str
    student_proficiency: Optional[str] = None
    status: str = Field(
        ...,
        description="DEMONSTRATED (matched/exceeded), PARTIAL_EVIDENCE (lower tier), or UNVERIFIED_OR_MISSING",
    )
    is_verified: bool = Field(default=False, description="Whether supported by passed assessment/interview verification")
    evidence_source: Optional[str] = Field(default=None, description="ASSESSMENT_VERIFIED, SELF_REPORTED, PRACTICE_COMPLETED, or NONE")
    evidence_reference: Optional[str] = Field(default=None, description="Evaluation round reference or practice artifact URL")
    practice_completed: bool = Field(default=False, description="Whether improvement plan practice task was completed")
    evidence_summary: str = Field(..., description="Factual evidence explanation")

    model_config = ConfigDict(from_attributes=True)



class HistoricalRoundSignal(BaseModel):
    round_type: str
    result: str
    notes: Optional[str] = None
    signal_type: str = Field(..., description="POSITIVE, NEUTRAL, or ATTENTION_NEEDED")

    model_config = ConfigDict(from_attributes=True)


class JobReadinessAssessmentResponse(BaseModel):
    job_id: int
    job_title: str
    company_name: str
    ctc_lpa: Optional[float] = None
    readiness_score: float = Field(..., description="Deterministic 0-100 readiness score")
    readiness_tier: str = Field(..., description="High Match, Moderate Match, Developing, Action Required")
    is_eligible: bool
    cgpa_eligible: bool
    student_cgpa: Optional[float] = None
    min_cgpa: Optional[float] = None
    department_eligible: bool
    student_department: Optional[str] = None
    eligible_departments: List[str] = Field(default_factory=list)
    eligibility_reasons: List[str] = Field(default_factory=list)
    total_required_skills: int
    demonstrated_count: int
    partial_count: int
    missing_evidence_count: int
    skills_breakdown: List[SkillEvidenceItem] = Field(default_factory=list)
    historical_signals: List[HistoricalRoundSignal] = Field(default_factory=list)
    score_breakdown: dict = Field(default_factory=dict)
    scoring_explanation: str
    limitations_notice: str

    model_config = ConfigDict(from_attributes=True)


class ImprovementPlanActionResponse(BaseModel):
    id: int
    plan_id: int
    skill_id: Optional[int] = None
    skill_name: str
    current_proficiency: Optional[str] = None
    target_proficiency: str
    priority: str
    status: str
    reason: str
    suggested_activity: str
    completion_criteria: str
    evidence_source: Optional[str] = None
    evidence_reference: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ImprovementPlanResponse(BaseModel):
    id: int
    student_id: int
    job_id: int
    job_title: str
    company_name: str
    total_actions: int
    completed_actions: int
    progress_percentage: float
    actions: List[ImprovementPlanActionResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UpdateActionStatusRequest(BaseModel):
    status: str = Field(..., pattern="^(PENDING|IN_PROGRESS|COMPLETED)$")
    evidence_source: Optional[str] = Field(None, max_length=100, description="Evidence source, e.g. PRACTICE_ARTIFACT, ASSESSMENT_ROUND")
    evidence_reference: Optional[str] = Field(None, max_length=500, description="Artifact URL, submission link, or round reference")



class JobMentorAdviceRequest(BaseModel):
    question: Optional[str] = Field(
        None, max_length=1500, description="Optional targeted question about this job"
    )


class JobMentorAdviceResponse(BaseModel):
    advice: str
    grounded_job_title: str
    grounded_company: str
    readiness_score: float
    model_used: str


class DepartmentOverviewItem(BaseModel):
    department_id: int
    department_name: str
    student_count: int
    in_demand_skills: List[str] = Field(default_factory=list)
    top_missing_skills: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DepartmentSkillGapsOverview(BaseModel):
    departments: List[DepartmentOverviewItem] = Field(default_factory=list)
    total_active_jobs_analyzed: int = 0

    model_config = ConfigDict(from_attributes=True)

