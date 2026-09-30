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

  // Derived UI states
  derived_state: string;
  can_student_respond: boolean;
  can_staff_verify: boolean;
  can_staff_set_result: boolean;
  is_upcoming: boolean;
  is_due: boolean;
  is_overdue: boolean;
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

  async reportAttendance(
    applicationId: number,
    roundId: number,
    attendance: 'ATTENDED' | 'ABSENT'
  ): Promise<ApplicationRoundResponse> {
    const res = await api.post<ApplicationRoundResponse>(
      `/student/applications/${applicationId}/rounds/${roundId}/attendance`,
      { attendance }
    );
    return res.data;
  },
};
