import api from '../../../api/axios';
import {
  ReadinessResponse,
  MarketSkillGapResponse,
  JobMatchResponse,
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
};
