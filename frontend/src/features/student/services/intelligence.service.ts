import api from '../../../api/axios';
import {
  ReadinessResponse,
  MarketSkillGapResponse,
  JobMatchResponse,
  MentorChatRequest,
  MentorChatResponse,
  JobReadinessAssessmentResponse,
  ImprovementPlanResponse,
  ImprovementPlanActionResponse,
  JobMentorAdviceRequest,
  JobMentorAdviceResponse,
  DepartmentSkillGapsOverview,
} from '../types/intelligence.types';

export const intelligenceService = {
  async getReadiness(): Promise<ReadinessResponse> {
    const response = await api.get<ReadinessResponse>('/student/intelligence/readiness');
    return response.data;
  },

  async getSkillGaps(): Promise<MarketSkillGapResponse> {
    const response = await api.get<MarketSkillGapResponse>('/student/intelligence/skills/gap');
    return response.data;
  },

  async getJobMatch(jobId: number): Promise<JobMatchResponse> {
    const response = await api.get<JobMatchResponse>(`/student/intelligence/jobs/${jobId}/match`);
    return response.data;
  },

  async askMentor(request: MentorChatRequest): Promise<MentorChatResponse> {
    const response = await api.post<MentorChatResponse>(
      '/student/intelligence/mentor/chat',
      request
    );
    return response.data;
  },

  async getJobReadiness(jobId: number): Promise<JobReadinessAssessmentResponse> {
    const response = await api.get<JobReadinessAssessmentResponse>(
      `/student/intelligence/jobs/${jobId}/readiness`
    );
    return response.data;
  },

  async generateJobPlan(jobId: number): Promise<ImprovementPlanResponse> {
    const response = await api.post<ImprovementPlanResponse>(
      `/student/intelligence/jobs/${jobId}/plan`
    );
    return response.data;
  },

  async getJobPlan(jobId: number): Promise<ImprovementPlanResponse | null> {
    const response = await api.get<ImprovementPlanResponse | null>(
      `/student/intelligence/jobs/${jobId}/plan`
    );
    return response.data;
  },

  async updateActionStatus(
    actionId: number,
    status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED',
    evidenceSource?: string,
    evidenceReference?: string
  ): Promise<ImprovementPlanActionResponse> {
    const payload: { status: string; evidence_source?: string; evidence_reference?: string } = { status };
    if (evidenceSource) payload.evidence_source = evidenceSource;
    if (evidenceReference) payload.evidence_reference = evidenceReference;
    const response = await api.patch<ImprovementPlanActionResponse>(
      `/student/intelligence/plans/actions/${actionId}`,
      payload
    );
    return response.data;
  },

  async askJobMentorAdvice(
    jobId: number,
    request: JobMentorAdviceRequest
  ): Promise<JobMentorAdviceResponse> {
    const response = await api.post<JobMentorAdviceResponse>(
      `/student/intelligence/jobs/${jobId}/mentor-advice`,
      request
    );
    return response.data;
  },

  async getDepartmentSkillGaps(): Promise<DepartmentSkillGapsOverview> {
    const response = await api.get<DepartmentSkillGapsOverview>(
      '/staff/analytics/department-skill-gaps'
    );
    return response.data;
  },
};

