"""
Pydantic schemas for Placement Readiness and Skill Gap Intelligence.
"""

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
