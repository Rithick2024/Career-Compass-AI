export type Stat = {
  label: string;
  value: string;
  change: string;
  trend: 'up' | 'down' | 'neutral';
  icon: 'briefcase' | 'clipboard' | 'gauge' | 'users';
};

export const dashboardStats: Stat[] = [
  {
    label: 'Active Applications',
    value: '12',
    change: '+3 this week',
    trend: 'up',
    icon: 'clipboard',
  },
  {
    label: 'Available Jobs',
    value: '48',
    change: '+8 new',
    trend: 'up',
    icon: 'briefcase',
  },
  {
    label: 'Readiness Score',
    value: '78%',
    change: '+5% vs last month',
    trend: 'up',
    icon: 'gauge',
  },
  {
    label: 'Profile Views',
    value: '23',
    change: '-2 this week',
    trend: 'down',
    icon: 'users',
  },
];

export type Application = {
  id: string;
  company: string;
  role: string;
  status: 'Pending' | 'Reviewing' | 'Interview' | 'Offered' | 'Rejected';
  appliedDate: string;
  logo: string;
};

export const recentApplications: Application[] = [
  {
    id: 'APP-001',
    company: 'Google',
    role: 'Software Engineer Intern',
    status: 'Interview',
    appliedDate: '2026-08-02',
    logo: 'G',
  },
  {
    id: 'APP-002',
    company: 'Microsoft',
    role: 'Frontend Developer',
    status: 'Reviewing',
    appliedDate: '2026-08-01',
    logo: 'M',
  },
  {
    id: 'APP-003',
    company: 'Amazon',
    role: 'SDE I',
    status: 'Pending',
    appliedDate: '2026-07-28',
    logo: 'A',
  },
  {
    id: 'APP-004',
    company: 'Netflix',
    role: 'UI Engineer',
    status: 'Offered',
    appliedDate: '2026-07-25',
    logo: 'N',
  },
  {
    id: 'APP-005',
    company: 'Stripe',
    role: 'Backend Intern',
    status: 'Rejected',
    appliedDate: '2026-07-20',
    logo: 'S',
  },
];

export type SkillGap = {
  skill: string;
  have: number;
  need: number;
};

export const skillGaps: SkillGap[] = [
  { skill: 'React', have: 85, need: 90 },
  { skill: 'TypeScript', have: 70, need: 85 },
  { skill: 'System Design', have: 45, need: 75 },
  { skill: 'DSA', have: 60, need: 80 },
  { skill: 'AWS', have: 30, need: 60 },
];

export type TimelineEvent = {
  date: string;
  title: string;
  description: string;
  type: 'interview' | 'application' | 'offer' | 'deadline';
};

export const upcomingEvents: TimelineEvent[] = [
  {
    date: '2026-08-10',
    title: 'Google Technical Interview',
    description: 'Round 2 — Data Structures & Algorithms',
    type: 'interview',
  },
  {
    date: '2026-08-12',
    title: 'Microsoft HR Round',
    description: 'Final cultural fit discussion',
    type: 'interview',
  },
  {
    date: '2026-08-15',
    title: 'Netflix Offer Deadline',
    description: 'Respond to UI Engineer offer',
    type: 'deadline',
  },
  {
    date: '2026-08-18',
    title: 'Amazon OA Submission',
    description: 'Online assessment for SDE I',
    type: 'deadline',
  },
];

export type TrendPoint = { month: string; applications: number; interviews: number };

export const applicationTrend: TrendPoint[] = [
  { month: 'Jan', applications: 5, interviews: 1 },
  { month: 'Feb', applications: 8, interviews: 2 },
  { month: 'Mar', applications: 6, interviews: 3 },
  { month: 'Apr', applications: 10, interviews: 4 },
  { month: 'May', applications: 12, interviews: 5 },
  { month: 'Jun', applications: 9, interviews: 6 },
  { month: 'Jul', applications: 14, interviews: 7 },
  { month: 'Aug', applications: 12, interviews: 8 },
];

export type JobRecommendation = {
  id: string;
  company: string;
  role: string;
  location: string;
  match: number;
  salary: string;
  tags: string[];
};

export const jobRecommendations: JobRecommendation[] = [
  {
    id: 'JOB-101',
    company: 'Figma',
    role: 'Frontend Engineer',
    location: 'Remote',
    match: 94,
    salary: '$120k-$140k',
    tags: ['React', 'TypeScript', 'Canvas API'],
  },
  {
    id: 'JOB-102',
    company: 'Vercel',
    role: 'DX Engineer',
    location: 'San Francisco, CA',
    match: 89,
    salary: '$110k-$130k',
    tags: ['Next.js', 'Edge Functions', 'DevOps'],
  },
  {
    id: 'JOB-103',
    company: 'Linear',
    role: 'Full Stack Engineer',
    location: 'Remote',
    match: 82,
    salary: '$100k-$125k',
    tags: ['React', 'Node', 'GraphQL'],
  },
];
