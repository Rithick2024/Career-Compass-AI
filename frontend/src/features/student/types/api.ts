export interface DepartmentOut {
  id: number;
  name: string;
}

export interface StudentProfileResponse {
  id: number;
  user_id: number;
  full_name: string | null;
  phone: string | null;
  department: DepartmentOut | null;
  graduation_year: number | null;
  cgpa: number | null;
  date_of_birth: string | null;
  address: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface StudentProfileUpdateRequest {
  full_name?: string | null;
  phone?: string | null;
  department_id?: number | null;
  graduation_year?: number | null;
  cgpa?: number | null;
  date_of_birth?: string | null;
  address?: string | null;
  linkedin_url?: string | null;
  github_url?: string | null;
}

export type BackendProficiency = 'beginner' | 'intermediate' | 'advanced';

export interface SkillOut {
  id: number;
  name: string;
  category: string | null;
}

export interface StudentSkillResponse {
  id: number;
  student_id: number;
  skill: SkillOut;
  proficiency: BackendProficiency;
  created_at: string;
  updated_at: string;
}

export interface AddStudentSkillRequest {
  skill_id: number;
  proficiency: BackendProficiency;
}

export interface UpdateStudentSkillProficiencyRequest {
  proficiency: BackendProficiency;
}
