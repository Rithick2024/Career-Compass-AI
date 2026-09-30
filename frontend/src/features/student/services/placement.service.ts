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

export interface StudentPlacementResponse {
  placement: PlacementResponse;
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

export const listStudentPlacements = async (): Promise<StudentPlacementResponse[]> => {
  const response = await api.get('/student/placements');
  return response.data;
};

export const getStudentPlacement = async (id: number): Promise<StudentPlacementResponse> => {
  const response = await api.get(`/student/placements/${id}`);
  return response.data;
};
