import api from '@/api/axios';

export type ApplicationStatus = 'Pending' | 'Reviewing' | 'Interview' | 'Offered' | 'Rejected' | 'Withdrawn';

export interface StaffApplicationListResponse {
  id: number;
  student_name: string;
  student_email: string;
  department: string | null;
  cgpa: number | null;
  job_title: string;
  company_name: string;
  resume_title: string;
  status: ApplicationStatus;
  applied_at: string;
  updated_at: string;
}

export interface StaffApplicationDetailResponse extends StaffApplicationListResponse {
  location: string | null;
  employment_type: string;
  ctc_lpa: number | null;
  deadline: string | null;
  resume_id: number;
  resume_file_name: string;
  resume_file_type: string;
  resume_file_size: number;
}

export interface GetStaffApplicationsParams {
  search?: string;
  job_id?: number;
  status?: string;
  company_id?: number;
}

export const staffApplicationService = {
  async listApplications(params?: GetStaffApplicationsParams): Promise<StaffApplicationListResponse[]> {
    const res = await api.get<StaffApplicationListResponse[]>('/staff/applications', { params });
    return res.data;
  },

  async getApplication(applicationId: number): Promise<StaffApplicationDetailResponse> {
    const res = await api.get<StaffApplicationDetailResponse>(`/staff/applications/${applicationId}`);
    return res.data;
  },

  async updateStatus(applicationId: number, status: ApplicationStatus): Promise<StaffApplicationDetailResponse> {
    const res = await api.patch<StaffApplicationDetailResponse>(`/staff/applications/${applicationId}/status`, { status });
    return res.data;
  },
};
