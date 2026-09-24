import api from '@/api/axios';
import { Department } from './department.service';

export interface StaffStudentListItem {
  id: number;
  user_id: number;
  email: string;
  full_name?: string | null;
  department?: Department | null;
  graduation_year?: number | null;
  cgpa?: number | null;
  skills_count: number;
  resumes_count: number;
  is_active: boolean;
}

export interface StaffStudentSkill {
  id: number;
  skill_id: number;
  skill_name: string;
  category?: string | null;
  proficiency: 'beginner' | 'intermediate' | 'advanced';
}

export interface StaffStudentResume {
  id: number;
  title: string;
  description?: string | null;
  file_name: string;
  file_type: string;
  file_size: number;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface StaffStudentDetail {
  id: number;
  user_id: number;
  email: string;
  full_name?: string | null;
  phone?: string | null;
  date_of_birth?: string | null;
  address?: string | null;
  linkedin_url?: string | null;
  github_url?: string | null;
  department?: Department | null;
  graduation_year?: number | null;
  cgpa?: number | null;
  skills: StaffStudentSkill[];
  resumes: StaffStudentResume[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export const staffStudentService = {
  async getStaffStudents(
    search?: string,
    departmentId?: number,
    graduationYear?: number
  ): Promise<StaffStudentListItem[]> {
    const params = new URLSearchParams();
    if (search && search.trim()) {
      params.append('search', search.trim());
    }
    if (departmentId) {
      params.append('department_id', String(departmentId));
    }
    if (graduationYear) {
      params.append('graduation_year', String(graduationYear));
    }
    const queryString = params.toString();
    const url = `/staff/students${queryString ? `?${queryString}` : ''}`;
    const response = await api.get<StaffStudentListItem[]>(url);
    return response.data;
  },

  async getStaffStudentDetail(studentId: number): Promise<StaffStudentDetail> {
    const response = await api.get<StaffStudentDetail>(`/staff/students/${studentId}`);
    return response.data;
  },

  async downloadResumeFile(studentId: number, resumeId: number, fileName: string): Promise<void> {
    const response = await api.get(`/staff/students/${studentId}/resumes/${resumeId}/file`, {
      responseType: 'blob',
    });
    const contentType = (response.headers['content-type'] as string) || 'application/octet-stream';
    const url = window.URL.createObjectURL(new Blob([response.data], { type: contentType }));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', fileName);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  async previewResumeFileBlob(studentId: number, resumeId: number): Promise<string> {
    const response = await api.get(`/staff/students/${studentId}/resumes/${resumeId}/file`, {
      responseType: 'blob',
    });
    const contentType = (response.headers['content-type'] as string) || 'application/pdf';
    return window.URL.createObjectURL(new Blob([response.data], { type: contentType }));
  },
};
