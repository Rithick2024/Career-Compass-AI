import api from '../../../api/axios';
import { ResumeResponse, CreateResumeData, UpdateResumeData } from '../types/api';

export const resumeService = {
  async getResumes(): Promise<ResumeResponse[]> {
    const response = await api.get<ResumeResponse[]>('/students/me/resumes');
    return response.data;
  },

  async getResume(id: number): Promise<ResumeResponse> {
    const response = await api.get<ResumeResponse>(`/students/me/resumes/${id}`);
    return response.data;
  },

  async createResume(data: CreateResumeData): Promise<ResumeResponse> {
    const formData = new FormData();
    formData.append('title', data.title);
    if (data.description) {
      formData.append('description', data.description);
    }
    formData.append('file', data.file);

    const response = await api.post<ResumeResponse>('/students/me/resumes', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async updateResume(id: number, data: UpdateResumeData): Promise<ResumeResponse> {
    const response = await api.patch<ResumeResponse>(`/students/me/resumes/${id}`, data);
    return response.data;
  },

  async deleteResume(id: number): Promise<void> {
    await api.delete(`/students/me/resumes/${id}`);
  },

  async downloadResumeFile(id: number): Promise<Blob> {
    const response = await api.get<Blob>(`/students/me/resumes/${id}/file`, {
      responseType: 'blob',
    });
    return response.data;
  },

  async setDefaultResume(id: number): Promise<ResumeResponse> {
    const response = await api.patch<ResumeResponse>(`/students/me/resumes/${id}/default`);
    return response.data;
  },
};
