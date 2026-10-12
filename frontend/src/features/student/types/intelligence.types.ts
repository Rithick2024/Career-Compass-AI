export interface ReadinessComponent {
  name: string;
  score: number;
  max_score: number;
  weight_percentage: number;
  explanation: string;
}

export interface ReadinessResponse {
  readiness_score: number;
  status_category: string;
  is_placed: boolean;
  components: ReadinessComponent[];
  actionable_recommendations: string[];
}

export interface SkillGapItem {
  skill_id: number;
  skill_name: string;
  category?: string | null;
  jobs_requiring_skill: number;
  required_proficiency: string;
  student_proficiency?: string | null;
  gap_type: 'MISSING' | 'INSUFFICIENT_PROFICIENCY';
}

export interface MarketSkillGapResponse {
  total_active_jobs_evaluated: number;
  gaps: SkillGapItem[];
  explanation: string;
}

export interface JobMatchSkillItem {
  skill_id: number;
  skill_name: string;
  min_proficiency: string;
  student_proficiency?: string | null;
  status: 'MATCHED' | 'STRONG_MATCH' | 'INSUFFICIENT_PROFICIENCY' | 'MISSING';
}

export interface JobMatchResponse {
  job_id: number;
  job_title: string;
  company_name: string;
  is_eligible: boolean;
  cgpa_eligible: boolean;
  department_eligible: boolean;
  eligibility_explanation: string;
  skill_match_percentage: number;
  total_required_skills: number;
  matched_skills: JobMatchSkillItem[];
  strong_matches: JobMatchSkillItem[];
  insufficient_proficiency: JobMatchSkillItem[];
  missing_skills: JobMatchSkillItem[];
  skill_match_explanation: string;
}

export interface ChatMessage {
  role: 'user' | 'model' | 'assistant';
  content: string;
}

export interface MentorChatRequest {
  message: string;
  history?: ChatMessage[];
}

export interface MentorContextSummary {
  department?: string | null;
  graduation_year?: number | null;
  cgpa_available: boolean;
  skills_count: number;
  top_skills: string[];
  active_campus_jobs_count: number;
}

export interface MentorChatResponse {
  response: string;
  grounded_context: MentorContextSummary;
  model_used: string;
}

export interface SkillEvidenceItem {
  skill_id: number;
  skill_name: string;
  required_proficiency: string;
  student_proficiency?: string | null;
  status: 'DEMONSTRATED' | 'PARTIAL_EVIDENCE' | 'UNVERIFIED_OR_MISSING';
  is_verified?: boolean;
  evidence_source?: string | null;
  evidence_reference?: string | null;
  practice_completed?: boolean;
  evidence_summary: string;
}

export interface HistoricalRoundSignal {
  round_type: string;
  result: string;
  notes?: string | null;
  signal_type: string;
}

export interface JobReadinessAssessmentResponse {
  job_id: number;
  job_title: string;
  company_name: string;
  ctc_lpa?: number | null;
  readiness_score: number;
  readiness_tier: string;
  is_eligible: boolean;
  cgpa_eligible: boolean;
  student_cgpa?: number | null;
  min_cgpa?: number | null;
  department_eligible: boolean;
  student_department?: string | null;
  eligible_departments: string[];
  eligibility_reasons: string[];
  total_required_skills: number;
  demonstrated_count: number;
  partial_count: number;
  missing_evidence_count: number;
  skills_breakdown: SkillEvidenceItem[];
  historical_signals: HistoricalRoundSignal[];
  score_breakdown: {
    academic_points?: number;
    skill_points?: number;
    preparation_points?: number;
  };
  scoring_explanation: string;
  limitations_notice: string;
}

export interface ImprovementPlanActionResponse {
  id: number;
  plan_id: number;
  skill_id?: number | null;
  skill_name: string;
  current_proficiency?: string | null;
  target_proficiency: string;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED';
  reason: string;
  suggested_activity: string;
  completion_criteria: string;
  evidence_source?: string | null;
  evidence_reference?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ImprovementPlanResponse {
  id: number;
  student_id: number;
  job_id: number;
  job_title: string;
  company_name: string;
  target_readiness_score: number;
  progress_percentage: number;
  total_actions: number;
  completed_actions: number;
  actions: ImprovementPlanActionResponse[];
  created_at: string;
  updated_at: string;
}

export interface JobMentorAdviceRequest {
  question?: string | null;
}

export interface JobMentorAdviceResponse {
  advice: string;
  grounded_job_title: string;
  grounded_company: string;
  readiness_score: number;
  model_used: string;
}

export interface DepartmentOverviewItem {
  department_id: number;
  department_name: string;
  student_count: number;
  in_demand_skills: string[];
  top_missing_skills: string[];
}

export interface DepartmentSkillGapsOverview {
  departments: DepartmentOverviewItem[];
  total_active_jobs_analyzed: number;
}


