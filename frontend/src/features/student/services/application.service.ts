import api from '@/api/axios';

export type ApplicationStatus = 'Pending' | 'Reviewing' | 'Interview' | 'Offered' | 'Rejected' | 'Withdrawn';

export interface StudentApplication {
  id: number;
  job_id: number;
  resume_id: number;
  status: ApplicationStatus;
  applied_at: string;
  updated_at: string;
}

export interface ApplicationCreate {
  job_id: number;
  resume_id: number;
}

export const studentApplicationService = {
  async submitApplication(data: ApplicationCreate): Promise<StudentApplication> {
    const res = await api.post<StudentApplication>('/student/applications', data);
    return res.data;
  },

  async listApplications(): Promise<StudentApplication[]> {
    const res = await api.get<StudentApplication[]>('/student/applications');
    return res.data;
  },

  async getApplication(applicationId: number): Promise<StudentApplication> {
    const res = await api.get<StudentApplication>(`/student/applications/${applicationId}`);
    return res.data;
  },

  async withdrawApplication(applicationId: number): Promise<StudentApplication> {
    const res = await api.patch<StudentApplication>(`/student/applications/${applicationId}/withdraw`);
    return res.data;
  },
};
