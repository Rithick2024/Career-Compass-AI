import api from '../../../api/axios';
import { 
  SkillOut, 
  StudentSkillResponse, 
  AddStudentSkillRequest, 
  UpdateStudentSkillProficiencyRequest 
} from '../types/api';

export const skillsService = {
  async getCatalogSkills(): Promise<SkillOut[]> {
    const response = await api.get<SkillOut[]>('/skills');
    return response.data;
  },

  async getMySkills(): Promise<StudentSkillResponse[]> {
    const response = await api.get<StudentSkillResponse[]>('/students/me/skills');
    return response.data;
  },

  async addSkill(data: AddStudentSkillRequest): Promise<StudentSkillResponse> {
    const response = await api.post<StudentSkillResponse>('/students/me/skills', data);
    return response.data;
  },

  async updateSkill(skillId: number, data: UpdateStudentSkillProficiencyRequest): Promise<StudentSkillResponse> {
    const response = await api.patch<StudentSkillResponse>(`/students/me/skills/${skillId}`, data);
    return response.data;
  },

  async removeSkill(skillId: number): Promise<void> {
    await api.delete(`/students/me/skills/${skillId}`);
  }
};
