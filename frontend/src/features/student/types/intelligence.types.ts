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
