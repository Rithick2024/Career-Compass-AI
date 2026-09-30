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

export interface ApplicationRoundCreate {
  round_number: number;
  round_type: RoundType;
  title?: string;
  status?: RoundStatus;
  result?: RoundResult;
  scheduled_at?: string;
  completed_at?: string;
  external_link?: string;
  notes?: string;
}

export interface ApplicationRoundUpdate {
  round_type?: RoundType;
  title?: string;
  status?: RoundStatus;
  result?: RoundResult;
  scheduled_at?: string;
  completed_at?: string;
  external_link?: string;
  notes?: string;
}

export const staffApplicationRoundService = {
  async listRounds(applicationId: number): Promise<ApplicationRoundResponse[]> {
    const res = await api.get<ApplicationRoundResponse[]>(`/staff/applications/${applicationId}/rounds`);
    return res.data;
  },

  async createRound(applicationId: number, data: ApplicationRoundCreate): Promise<ApplicationRoundResponse> {
    const res = await api.post<ApplicationRoundResponse>(`/staff/applications/${applicationId}/rounds`, data);
    return res.data;
  },

  async updateRound(applicationId: number, roundId: number, data: ApplicationRoundUpdate): Promise<ApplicationRoundResponse> {
    const res = await api.patch<ApplicationRoundResponse>(`/staff/applications/${applicationId}/rounds/${roundId}`, data);
    return res.data;
  },
};
