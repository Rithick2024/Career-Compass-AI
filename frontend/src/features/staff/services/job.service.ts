import api from '@/api/axios';
import { JobRound } from './job-round.service';

export interface JobCompany {
  id: number;
  name: string;
  industry?: string | null;
  location?: string | null;
  website?: string | null;
  is_active: boolean;
}

export interface JobSkillInfo {
  id: number;
  name: string;
  category?: string | null;
  is_active: boolean;
}

export interface JobRequiredSkill {
  id: number;
  job_id?: number;
  skill_id: number;
  skill_name?: string;
  category?: string;
  min_proficiency?: 'beginner' | 'intermediate' | 'advanced' | null;
  skill?: JobSkillInfo;
}

export interface JobDepartmentInfo {
  id: number;
  name: string;
  code: string;
  is_active: boolean;
}

export interface JobEligibleDepartment {
  id: number;
  job_id?: number;
  department_id: number;
  department_name?: string;
  department?: JobDepartmentInfo;
}

export interface JobListItem {
  id: number;
  company_id: number;
  company: JobCompany;
  title: string;
  role_category?: string | null;
  location?: string | null;
  employment_type: string;
  ctc_lpa?: number | null;
  min_cgpa?: number | null;
  deadline?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  required_skills_count?: number;
  eligible_departments_count?: number;
  required_skills: JobRequiredSkill[];
  eligible_departments: JobEligibleDepartment[];
  rounds?: JobRound[];
}

export interface JobDetail {
  id: number;
  company_id: number;
  company: JobCompany;
  title: string;
  description?: string | null;
  role_category?: string | null;
  location?: string | null;
  employment_type: string;
  ctc_lpa?: number | null;
  min_cgpa?: number | null;
  deadline?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  required_skills: JobRequiredSkill[];
  eligible_departments: JobEligibleDepartment[];
  rounds?: JobRound[];
}

export interface JobRequiredSkillInput {
  skill_id: number;
  min_proficiency?: 'beginner' | 'intermediate' | 'advanced' | null;
}

export interface CreateJobPayload {
  company_id: number;
  title: string;
  description?: string | null;
  role_category?: string | null;
  location?: string | null;
  employment_type?: string;
  ctc_lpa?: number | null;
  min_cgpa?: number | null;
  deadline?: string | null;
  required_skills?: JobRequiredSkillInput[];
  eligible_department_ids?: number[];
}

export interface UpdateJobPayload {
  company_id?: number;
  title?: string;
  description?: string | null;
  role_category?: string | null;
  location?: string | null;
  employment_type?: string;
  ctc_lpa?: number | null;
  min_cgpa?: number | null;
  deadline?: string | null;
  required_skills?: JobRequiredSkillInput[];
  eligible_department_ids?: number[];
}

export type JobStatusFilter = 'all' | 'active' | 'inactive' | 'expired';

export const jobService = {
  async getStaffJobs(
    search?: string,
    company_id?: number,
    department_id?: number,
    status?: JobStatusFilter
  ): Promise<JobListItem[]> {
    const params = new URLSearchParams();
    if (search && search.trim()) {
      params.append('search', search.trim());
    }
    if (company_id) {
      params.append('company_id', company_id.toString());
    }
    if (department_id) {
      params.append('department_id', department_id.toString());
    }
    if (status && status !== 'all') {
      params.append('status', status);
    }
    const queryString = params.toString();
    const url = `/staff/jobs${queryString ? `?${queryString}` : ''}`;
    const response = await api.get<JobListItem[]>(url);
    return response.data;
  },

  async getJobDetail(id: number): Promise<JobDetail> {
    const response = await api.get<JobDetail>(`/staff/jobs/${id}`);
    return response.data;
  },

  async createJob(payload: CreateJobPayload): Promise<JobDetail> {
    const response = await api.post<JobDetail>('/staff/jobs', payload);
    return response.data;
  },

  async updateJob(id: number, payload: UpdateJobPayload): Promise<JobDetail> {
    const response = await api.patch<JobDetail>(`/staff/jobs/${id}`, payload);
    return response.data;
  },

  async updateJobStatus(id: number, is_active: boolean): Promise<JobDetail> {
    const response = await api.patch<JobDetail>(`/staff/jobs/${id}/status`, { is_active });
    return response.data;
  },
};
