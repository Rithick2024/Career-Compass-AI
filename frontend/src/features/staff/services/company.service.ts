import api from '@/api/axios';

export interface Company {
  id: number;
  name: string;
  description?: string | null;
  industry?: string | null;
  website?: string | null;
  location?: string | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface CreateCompanyPayload {
  name: string;
  description?: string;
  industry?: string;
  website?: string;
  location?: string;
}

export interface UpdateCompanyPayload {
  name?: string;
  description?: string;
  industry?: string;
  website?: string;
  location?: string;
}

export const companyService = {
  async getStaffCompanies(search?: string, status?: 'all' | 'active' | 'inactive'): Promise<Company[]> {
    const params = new URLSearchParams();
    if (search && search.trim()) {
      params.append('search', search.trim());
    }
    if (status && status !== 'all') {
      params.append('status', status);
    }
    const queryString = params.toString();
    const url = `/staff/companies${queryString ? `?${queryString}` : ''}`;
    const response = await api.get<Company[]>(url);
    return response.data;
  },

  async getCompany(id: number): Promise<Company> {
    const response = await api.get<Company>(`/staff/companies/${id}`);
    return response.data;
  },

  async createCompany(data: CreateCompanyPayload): Promise<Company> {
    const response = await api.post<Company>('/staff/companies', data);
    return response.data;
  },

  async updateCompany(id: number, data: UpdateCompanyPayload): Promise<Company> {
    const response = await api.patch<Company>(`/staff/companies/${id}`, data);
    return response.data;
  },

  async updateCompanyStatus(id: number, is_active: boolean): Promise<Company> {
    const response = await api.patch<Company>(`/staff/companies/${id}/status`, { is_active });
    return response.data;
  },
};
