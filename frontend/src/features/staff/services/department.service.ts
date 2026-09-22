import api from '@/api/axios';

export interface Department {
  id: number;
  name: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface CreateDepartmentPayload {
  name: string;
}

export interface UpdateDepartmentPayload {
  name: string;
}

export const departmentService = {
  // Public/student-facing: returns only active departments
  async getActiveDepartments(): Promise<Department[]> {
    const response = await api.get<Department[]>('/departments');
    return response.data;
  },

  // Staff-facing: returns all departments (active & inactive)
  async getStaffDepartments(): Promise<Department[]> {
    const response = await api.get<Department[]>('/staff/departments');
    return response.data;
  },

  async createDepartment(data: CreateDepartmentPayload): Promise<Department> {
    const response = await api.post<Department>('/staff/departments', data);
    return response.data;
  },

  async updateDepartment(id: number, data: UpdateDepartmentPayload): Promise<Department> {
    const response = await api.patch<Department>(`/staff/departments/${id}`, data);
    return response.data;
  },

  async updateDepartmentStatus(id: number, is_active: boolean): Promise<Department> {
    const response = await api.patch<Department>(`/staff/departments/${id}/status`, { is_active });
    return response.data;
  },
};
