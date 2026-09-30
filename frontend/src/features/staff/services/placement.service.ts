import api from '@/api/axios';

export interface PlacementResponse {
  final_package_ctc: number;
  placement_date: string;
  offer_accepted: boolean;
  id: number;
  application_id: number;
  created_at: string;
  updated_at: string;
}

export interface PlacementCreateRequest {
  application_id: number;
  final_package_ctc: number;
  placement_date: string;
  offer_accepted?: boolean;
}

export interface PlacementUpdateRequest {
  final_package_ctc?: number;
  placement_date?: string;
  offer_accepted?: boolean;
}

export interface StaffPlacementResponse {
  placement: PlacementResponse;
  student: {
    id: number;
    full_name: string | null;
    department_id: number | null;
    cgpa: number | null;
  };
  job: {
    id: number;
    title: string;
    role_category: string | null;
    location: string | null;
    employment_type: string | null;
    package_ctc: number | null;
    application_deadline: string | null;
  };
  company: {
    id: number;
    name: string;
    industry: string | null;
    location: string | null;
    website_url: string | null;
  };
  application: {
    id: number;
    status: string;
    applied_at: string;
  };
}

export interface PlacementFilters {
  search?: string;
  company_id?: number;
  department_id?: number;
  offer_accepted?: boolean;
}

export const listStaffPlacements = async (filters?: PlacementFilters): Promise<StaffPlacementResponse[]> => {
  const response = await api.get('/staff/placements', { params: filters });
  return response.data;
};

export const getStaffPlacement = async (id: number): Promise<StaffPlacementResponse> => {
  const response = await api.get(`/staff/placements/${id}`);
  return response.data;
};

export const createPlacement = async (data: PlacementCreateRequest): Promise<StaffPlacementResponse> => {
  const response = await api.post('/staff/placements', data);
  return response.data;
};

export const updatePlacement = async (id: number, data: PlacementUpdateRequest): Promise<StaffPlacementResponse> => {
  const response = await api.patch(`/staff/placements/${id}`, data);
  return response.data;
};
