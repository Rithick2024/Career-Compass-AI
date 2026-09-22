import {
  LayoutDashboard,
  User,
  Sparkles,
  FileText,
  Briefcase,
  ClipboardList,
  Gauge,
  Users,
  Building2,
  GraduationCap,
  Award,
  CheckSquare,
  type LucideIcon,
} from 'lucide-react';

export type NavItem = {
  label: string;
  to: string;
  icon: LucideIcon;
  badge?: string;
};

export type NavSection = {
  title: string;
  items: NavItem[];
};

export const studentNav: NavSection[] = [
  {
    title: 'Main',
    items: [
      { label: 'Dashboard', to: '/student/dashboard', icon: LayoutDashboard },
      { label: 'My Profile', to: '/student/profile', icon: User },
      { label: 'Skills', to: '/student/skills', icon: Sparkles, badge: 'AI' },
      {
        label: 'Resume Management',
        to: '/student/resume',
        icon: FileText,
      },
    ],
  },
  {
    title: 'Opportunities',
    items: [
      { label: 'Available Jobs', to: '/student/jobs', icon: Briefcase },
      {
        label: 'My Applications',
        to: '/student/applications',
        icon: ClipboardList,
      },
      {
        label: 'Placement Readiness',
        to: '/student/readiness',
        icon: Gauge,
      },
    ],
  },
];

export const staffNav: NavSection[] = [
  {
    title: 'Overview',
    items: [
      { label: 'Dashboard', to: '/staff/dashboard', icon: LayoutDashboard },
    ],
  },
  {
    title: 'Platform Master Data',
    items: [
      { label: 'Students', to: '/staff/students', icon: Users },
      { label: 'Departments', to: '/staff/departments', icon: GraduationCap },
      { label: 'Skills Catalog', to: '/staff/skills', icon: Sparkles },
      { label: 'Companies', to: '/staff/companies', icon: Building2 },
      { label: 'Job Postings', to: '/staff/jobs', icon: Briefcase },
    ],
  },
  {
    title: 'Placement Operations',
    items: [
      { label: 'Applications', to: '/staff/applications', icon: CheckSquare },
      { label: 'Placements', to: '/staff/placements', icon: Award },
    ],
  },
];
