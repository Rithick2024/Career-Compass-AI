import api from '@/api/axios';

export interface ApplicationStatusCount {
  status: string;
  count: number;
}

export interface DepartmentPlacementCount {
  department: string;
  count: number;
}

export interface RoundTypeCount {
  round_type: string;
  count: number;
}

export interface StaffRecruitmentSummary {
  total_rounds: number;
  scheduled_rounds: number;
  completed_rounds: number;
  passed_rounds: number;
  failed_rounds: number;
  pass_rate: number;
  rounds_by_type: RoundTypeCount[];
}

export interface StaffAnalyticsOverview {
  total_students: number;
  active_jobs: number;
  pending_applications: number;
  accepted_placements: number;
  average_package: number;
  applications_by_status: ApplicationStatusCount[];
  placements_by_department: DepartmentPlacementCount[];
  recruitment_summary: StaffRecruitmentSummary;
}

export interface UpcomingRound {
  id: number;
  round_type: string;
  job_title: string;
  company_name: string;
  scheduled_at: string;
  status: string;
}

export interface RecentApplication {
  id: number;
  job_title: string;
  company_name: string;
  status: string;
  applied_at: string;
}

export interface StudentRecruitmentSummary {
  total_rounds: number;
  scheduled_rounds: number;
  completed_rounds: number;
  passed_rounds: number;
  failed_rounds: number;
}

export interface PlacementSummary {
  has_accepted_placement: boolean;
  accepted_placement_count: number;
  latest_accepted_placement_company: string | null;
  latest_accepted_placement_package: number | null;
  latest_accepted_placement_date: string | null;
}

export interface StudentAnalyticsOverview {
  active_applications: number;
  total_offers: number;
  application_status_summary: ApplicationStatusCount[];
  upcoming_rounds: UpcomingRound[];
  recent_applications: RecentApplication[];
  recruitment_summary: StudentRecruitmentSummary;
  placement_summary: PlacementSummary;
}

export const analyticsService = {
  async getStaffOverview(): Promise<StaffAnalyticsOverview> {
    const res = await api.get<StaffAnalyticsOverview>('/staff/analytics/overview');
    return res.data;
  },

  async getStudentOverview(): Promise<StudentAnalyticsOverview> {
    const res = await api.get<StudentAnalyticsOverview>('/student/analytics/overview');
    return res.data;
  }
};
