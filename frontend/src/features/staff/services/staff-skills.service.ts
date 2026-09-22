import api from '@/api/axios';

export interface StaffSkill {
  id: number;
  name: string;
  category?: string | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface CreateSkillPayload {
  name: string;
  category?: string | null;
}

export interface UpdateSkillPayload {
  name: string;
  category?: string | null;
}

export const staffSkillService = {
  async getStaffSkills(): Promise<StaffSkill[]> {
    const response = await api.get<StaffSkill[]>('/staff/skills');
    return response.data;
  },

  async createSkill(data: CreateSkillPayload): Promise<StaffSkill> {
    const response = await api.post<StaffSkill>('/staff/skills', data);
    return response.data;
  },

  async updateSkill(id: number, data: UpdateSkillPayload): Promise<StaffSkill> {
    const response = await api.patch<StaffSkill>(`/staff/skills/${id}`, data);
    return response.data;
  },

  async updateSkillStatus(id: number, is_active: boolean): Promise<StaffSkill> {
    const response = await api.patch<StaffSkill>(`/staff/skills/${id}/status`, { is_active });
    return response.data;
  },
};
