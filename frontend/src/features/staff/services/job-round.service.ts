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

export type ScheduleType = 'FIXED_TIME' | 'AVAILABILITY_WINDOW';

export interface JobRound {
  id: number;
  job_id: number;
  round_number: number;
  round_type: RoundType;
  title?: string | null;
  description?: string | null;
  schedule_type: ScheduleType;
  available_from?: string | null;
  available_until?: string | null;
  duration_minutes: number;
  meeting_link?: string | null;
  test_link?: string | null;
  instructions?: string | null;
  is_required: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateJobRoundPayload {
  round_number: number;
  round_type: RoundType;
  title?: string | null;
  description?: string | null;
  schedule_type?: ScheduleType;
  available_from?: string | null;
  available_until?: string | null;
  duration_minutes?: number;
  meeting_link?: string | null;
  test_link?: string | null;
  instructions?: string | null;
  is_required?: boolean;
  is_active?: boolean;
}

export interface UpdateJobRoundPayload {
  round_number?: number;
  round_type?: RoundType;
  title?: string | null;
  description?: string | null;
  schedule_type?: ScheduleType;
  available_from?: string | null;
  available_until?: string | null;
  duration_minutes?: number;
  meeting_link?: string | null;
  test_link?: string | null;
  instructions?: string | null;
  is_required?: boolean;
  is_active?: boolean;
}

export const jobRoundService = {
  async getJobRounds(jobId: number): Promise<JobRound[]> {
    const response = await api.get<JobRound[]>(`/staff/jobs/${jobId}/rounds`);
    return response.data;
  },

  async createJobRound(jobId: number, payload: CreateJobRoundPayload): Promise<JobRound> {
    const response = await api.post<JobRound>(`/staff/jobs/${jobId}/rounds`, payload);
    return response.data;
  },

  async updateJobRound(jobId: number, roundId: number, payload: UpdateJobRoundPayload): Promise<JobRound> {
    const response = await api.patch<JobRound>(`/staff/jobs/${jobId}/rounds/${roundId}`, payload);
    return response.data;
  },

  async deleteJobRound(jobId: number, roundId: number): Promise<void> {
    await api.delete(`/staff/jobs/${jobId}/rounds/${roundId}`);
  },
};
