import api from '../../../api/axios';
import { ResumeResponse, CreateResumeRequest, UpdateResumeRequest } from '../types/api';

export const resumeService = {
  async getResume(): Promise<ResumeResponse> {
    const response = await api.get<ResumeResponse>('/students/me/resume');
    return response.data;
  },

  async createResume(data: CreateResumeRequest): Promise<ResumeResponse> {
    const response = await api.post<ResumeResponse>('/students/me/resume', data);
    return response.data;
  },

  async updateResume(data: UpdateResumeRequest): Promise<ResumeResponse> {
    const response = await api.patch<ResumeResponse>('/students/me/resume', data);
    return response.data;
  },

  async deleteResume(): Promise<void> {
    await api.delete('/students/me/resume');
  },

  async uploadResumeFile(file: File): Promise<ResumeResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<ResumeResponse>('/students/me/resume/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async downloadResumeFile(): Promise<Blob> {
    const response = await api.get<Blob>('/students/me/resume/file', {
      responseType: 'blob',
    });
    return response.data;
  },

  async deleteResumeFile(): Promise<ResumeResponse> {
    const response = await api.delete<ResumeResponse>('/students/me/resume/file');
    return response.data;
  }
};
