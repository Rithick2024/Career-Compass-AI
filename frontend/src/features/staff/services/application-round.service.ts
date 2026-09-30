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
export type RoundStatus = 'Not Started' | 'Scheduled' | 'In Progress' | 'Completed' | 'Cancelled';
export type RoundResult = 'Pending' | 'Passed' | 'Failed' | 'Not Attended';
export type StudentAttendance = 'NOT_REPORTED' | 'ATTENDED' | 'ABSENT';
export type StaffVerification = 'PENDING' | 'VERIFIED' | 'REJECTED';

export interface ApplicationRoundResponse {
  id: number;
  application_id: number;
  round_number: number;
  round_type: RoundType;
  title: string | null;
  schedule_type: ScheduleType;
  available_from: string | null;
  available_until: string | null;
  scheduled_at: string | null;
  session_end_at: string | null;
  status: RoundStatus;
  result: RoundResult | null;
  completed_at: string | null;
  duration_minutes: number;
  student_attendance: StudentAttendance;
  student_action_at: string | null;
  staff_verification: StaffVerification;
  staff_verified_at: string | null;
  staff_verified_by_id: number | null;
  rescheduled_at: string | null;
  reschedule_reason: string | null;
  external_link: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;

  derived_state: string;
  can_student_respond: boolean;
  can_staff_verify: boolean;
  can_staff_set_result: boolean;
  is_upcoming: boolean;
  is_due: boolean;
  is_overdue: boolean;
}

export interface ApplicationRoundCreate {
  round_number: number;
  round_type: RoundType;
  title?: string;
  schedule_type?: ScheduleType;
  available_from?: string;
  available_until?: string;
  scheduled_at?: string;
  status?: RoundStatus;
  result?: RoundResult;
  completed_at?: string;
  duration_minutes?: number;
  external_link?: string;
  notes?: string;
}

export interface ApplicationRoundUpdate {
  round_type?: RoundType;
  title?: string;
  schedule_type?: ScheduleType;
  available_from?: string;
  available_until?: string;
  scheduled_at?: string;
  status?: RoundStatus;
  result?: RoundResult;
  completed_at?: string;
  duration_minutes?: number;
  external_link?: string;
  notes?: string;
}

export interface StaffReschedulePayload {
  schedule_type?: ScheduleType;
  new_available_from?: string;
  new_available_until?: string;
  new_scheduled_at?: string;
  reason?: string;
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

  async verifyAttendance(
    applicationId: number,
    roundId: number,
    verification: StaffVerification
  ): Promise<ApplicationRoundResponse> {
    const res = await api.patch<ApplicationRoundResponse>(
      `/staff/applications/${applicationId}/rounds/${roundId}/verification`,
      { verification }
    );
    return res.data;
  },

  async setResult(
    applicationId: number,
    roundId: number,
    result: RoundResult
  ): Promise<ApplicationRoundResponse> {
    const res = await api.patch<ApplicationRoundResponse>(
      `/staff/applications/${applicationId}/rounds/${roundId}/result`,
      { result }
    );
    return res.data;
  },

  async rescheduleRound(
    applicationId: number,
    roundId: number,
    payload: StaffReschedulePayload
  ): Promise<ApplicationRoundResponse> {
    const res = await api.patch<ApplicationRoundResponse>(
      `/staff/applications/${applicationId}/rounds/${roundId}/reschedule`,
      payload
    );
    return res.data;
  },
};
