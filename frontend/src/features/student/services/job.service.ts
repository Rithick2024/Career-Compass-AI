import api from '@/api/axios';
import { JobRound } from '@/features/staff/services/job-round.service';

export interface StudentCompany {
  id: number;
  name: string;
  industry?: string;
  location?: string;
  website?: string;
}

export interface StudentJobRequiredSkill {
  id: number;
  skill_id: number;
  skill_name: string;
  category?: string;
  min_proficiency?: string;
}

export interface StudentJobEligibleDepartment {
  id: number;
  department_id: number;
  department_name: string;
}

export interface StudentJob {
  id: number;
  title: string;
  description?: string;
  role_category?: string;
  location?: string;
  employment_type: string;
  ctc_lpa?: number;
  min_cgpa?: number;
  deadline?: string;

  company: StudentCompany;
  required_skills: StudentJobRequiredSkill[];
  eligible_departments: StudentJobEligibleDepartment[];
  rounds?: JobRound[];

  is_department_eligible: boolean;
  is_cgpa_eligible: boolean;
  is_fully_eligible: boolean;
}

export interface GetStudentJobsParams {
  search?: string;
  company_id?: number;
  employment_type?: string;
  eligible_only?: boolean;
}

export const studentJobService = {
  async getJobs(params?: GetStudentJobsParams): Promise<StudentJob[]> {
    const res = await api.get<StudentJob[]>('/student/jobs', { params });
    return res.data;
  },

  async getJob(jobId: number): Promise<StudentJob> {
    const res = await api.get<StudentJob>(`/student/jobs/${jobId}`);
    return res.data;
  },
};
