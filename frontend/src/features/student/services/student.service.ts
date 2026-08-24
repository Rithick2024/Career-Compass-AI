import api from '../../../api/axios';
import { StudentProfileResponse, StudentProfileUpdateRequest } from '../types/api';

export const studentService = {
  async getMyProfile(): Promise<StudentProfileResponse> {
    const response = await api.get<StudentProfileResponse>('/students/me');
    return response.data;
  },

  async updateMyProfile(data: StudentProfileUpdateRequest): Promise<StudentProfileResponse> {
    const response = await api.patch<StudentProfileResponse>('/students/me', data);
    return response.data;
  },
};
