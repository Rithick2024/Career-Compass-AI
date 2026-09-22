import { useNavigate } from 'react-router-dom';
import {
  Users,
  GraduationCap,
  Sparkles,
  Building2,
  Briefcase,
  CheckSquare,
  Award,
  ArrowRight,
  ShieldCheck
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { PageHeader, PageContainer } from '@/components/common/PageHeader';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/features/auth/context/AuthContext';

export default function StaffDashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const modules = [
    {
      title: 'Student Directory',
      description: 'View student profiles, academic departments, CGPA, and resume documents.',
      icon: Users,
      path: '/staff/students',
      badge: 'Core Directory',
    },
    {
      title: 'Department Management',
      description: 'Manage academic departments and degree programs across the institution.',
      icon: GraduationCap,
      path: '/staff/departments',
      badge: 'Master Data',
    },
    {
      title: 'Skills Catalog',
      description: 'Manage the master skill catalog and technical domain categories.',
      icon: Sparkles,
      path: '/staff/skills',
      badge: 'Master Data',
    },
    {
      title: 'Company Partners',
      description: 'Manage partner recruiting companies, industry sectors, and contacts.',
      icon: Building2,
      path: '/staff/companies',
      badge: 'Recruitment',
    },
    {
      title: 'Job Postings & Drives',
      description: 'Create and manage placement drive openings and role requirements.',
      icon: Briefcase,
      path: '/staff/jobs',
      badge: 'Recruitment',
    },
    {
      title: 'Applications Review',
      description: 'Track and process student job applications for active recruitment drives.',
      icon: CheckSquare,
      path: '/staff/applications',
      badge: 'Operations',
    },
    {
      title: 'Placements & Offers',
      description: 'Record confirmed job placement offers and track placement statistics.',
      icon: Award,
      path: '/staff/placements',
      badge: 'Operations',
    },
  ];

  const userEmail = user?.email || 'Staff Member';
  const avatarText = userEmail.substring(0, 2).toUpperCase();

  return (
    <AppLayout role="staff" userName={userEmail} userRole="Staff" avatarText={avatarText}>
      <PageContainer>
        <PageHeader
          title="Staff Workspace"
          description="Manage platform master data, student records, and placement operations."
          action={
            <Badge variant="outline" className="gap-1.5 px-3 py-1 bg-primary/10 border-primary/30 text-primary">
              <ShieldCheck className="h-4 w-4" />
              Staff Authorized
            </Badge>
          }
        />

        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {modules.map((mod) => (
            <Card
              key={mod.title}
              className="flex flex-col justify-between transition-all duration-200 hover:shadow-md hover:border-primary/40 cursor-pointer group"
              onClick={() => navigate(mod.path)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="p-2.5 rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                    <mod.icon className="h-6 w-6" />
                  </div>
                  <Badge variant="secondary" className="text-[11px] font-medium">
                    {mod.badge}
                  </Badge>
                </div>
                <CardTitle className="text-lg font-bold group-hover:text-primary transition-colors">
                  {mod.title}
                </CardTitle>
                <CardDescription className="text-sm mt-1 text-muted-foreground leading-relaxed">
                  {mod.description}
                </CardDescription>
              </CardHeader>

              <CardContent className="pt-0">
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-between group-hover:bg-primary/5 group-hover:text-primary"
                >
                  <span>Access Module</span>
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </PageContainer>
    </AppLayout>
  );
}
