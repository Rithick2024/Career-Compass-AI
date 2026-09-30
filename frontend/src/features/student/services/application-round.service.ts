import api from '@/api/axios';

export type RoundType =
  | 'Online Assessment'
  | 'Coding Test'
  | 'Aptitude Test'
  | 'Technical Interview'
  | 'Managerial Interview'
  | 'HR Interview'
  | 'Group Discussion'
  | 'Other';

export type RoundStatus = 'Not Started' | 'Scheduled' | 'In Progress' | 'Completed' | 'Cancelled';
export type RoundResult = 'Pending' | 'Passed' | 'Failed' | 'Not Attended';

export interface ApplicationRoundResponse {
  id: number;
  application_id: number;
  round_number: number;
  round_type: RoundType;
  title: string | null;
  status: RoundStatus;
  result: RoundResult | null;
  scheduled_at: string | null;
  completed_at: string | null;
  external_link: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export const studentApplicationRoundService = {
  async listRounds(applicationId: number): Promise<ApplicationRoundResponse[]> {
    const res = await api.get<ApplicationRoundResponse[]>(`/student/applications/${applicationId}/rounds`);
    return res.data;
  },

  async getRound(applicationId: number, roundId: number): Promise<ApplicationRoundResponse> {
    const res = await api.get<ApplicationRoundResponse>(`/student/applications/${applicationId}/rounds/${roundId}`);
    return res.data;
  },
};
