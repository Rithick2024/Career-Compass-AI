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
  BarChart3,
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

export const adminNav: NavSection[] = [
  {
    title: 'Overview',
    items: [
      { label: 'Dashboard', to: '/admin/dashboard', icon: LayoutDashboard },
      {
        label: 'Placement Analytics',
        to: '/admin/analytics',
        icon: BarChart3,
      },
    ],
  },
  {
    title: 'Management',
    items: [
      {
        label: 'Student Management',
        to: '/admin/students',
        icon: Users,
      },
      {
        label: 'Company Management',
        to: '/admin/companies',
        icon: Building2,
      },
      { label: 'Job Management', to: '/admin/jobs', icon: Briefcase },
    ],
  },
];
