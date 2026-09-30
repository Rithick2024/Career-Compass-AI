import { useEffect, useState } from 'react';
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
  ShieldCheck,
  TrendingUp,
  Clock,
  CheckCircle2,
  XCircle
} from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { AppLayout } from '@/components/layout/AppLayout';
import { PageHeader, PageContainer } from '@/components/common/PageHeader';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/features/auth/context/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { analyticsService, StaffAnalyticsOverview } from '@/features/analytics/services/analytics.service';
import { Skeleton } from '@/components/ui/skeleton';

const STATUS_COLORS: Record<string, string> = {
  Pending: '#eab308',
  Reviewing: '#3b82f6',
  Interview: '#8b5cf6',
  Offered: '#10b981',
  Rejected: '#ef4444',
  Withdrawn: '#6b7280',
};

export default function StaffDashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();
  
  const [data, setData] = useState<StaffAnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await analyticsService.getStaffOverview();
      setData(res);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load analytics overview.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const modules = [
    { title: 'Student Directory', icon: Users, path: '/staff/students', badge: 'Core Directory' },
    { title: 'Department Management', icon: GraduationCap, path: '/staff/departments', badge: 'Master Data' },
    { title: 'Skills Catalog', icon: Sparkles, path: '/staff/skills', badge: 'Master Data' },
    { title: 'Company Partners', icon: Building2, path: '/staff/companies', badge: 'Recruitment' },
    { title: 'Job Postings & Drives', icon: Briefcase, path: '/staff/jobs', badge: 'Recruitment' },
    { title: 'Applications Review', icon: CheckSquare, path: '/staff/applications', badge: 'Operations' },
    { title: 'Placements & Offers', icon: Award, path: '/staff/placements', badge: 'Operations' },
  ];

  const userEmail = user?.email || 'Staff Member';
  const avatarText = userEmail.substring(0, 2).toUpperCase();

  const renderStats = () => {
    if (loading) {
      return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5 mb-8">
          {[1,2,3,4,5].map(i => <Skeleton key={i} className="h-28 rounded-xl" />)}
        </div>
      );
    }
    
    if (!data) return null;

    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Students</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.total_students}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Jobs</CardTitle>
            <Briefcase className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.active_jobs}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Pending Apps</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.pending_applications}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Placements</CardTitle>
            <Award className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.accepted_placements}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Avg Package</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${data.average_package.toLocaleString(undefined, {maximumFractionDigits:0})}</div>
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderCharts = () => {
    if (loading || !data) return null;

    const hasApps = data.applications_by_status.some(s => s.count > 0);
    const hasPlacements = data.placements_by_department.length > 0;

    return (
      <div className="grid gap-6 md:grid-cols-2 mb-8">
        <Card>
          <CardHeader>
            <CardTitle>Applications by Status</CardTitle>
          </CardHeader>
          <CardContent className="h-[300px]">
            {hasApps ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.applications_by_status}
                    dataKey="count"
                    nameKey="status"
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    label
                  >
                    {data.applications_by_status.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={STATUS_COLORS[entry.status] || '#cbd5e1'} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground text-sm">No application data</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Placements by Department</CardTitle>
          </CardHeader>
          <CardContent className="h-[300px]">
            {hasPlacements ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.placements_by_department} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" />
                  <YAxis dataKey="department" type="category" width={100} fontSize={12} />
                  <RechartsTooltip />
                  <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground text-sm">No placement data</div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderRecruitmentSummary = () => {
    if (loading || !data) return null;
    const { recruitment_summary } = data;

    return (
      <div className="mb-10">
        <h3 className="text-lg font-semibold mb-4 tracking-tight">Recruitment Pipeline Overview</h3>
        <div className="grid gap-4 md:grid-cols-4 lg:grid-cols-6 mb-4">
          <Card className="bg-muted/30">
            <CardContent className="p-4 text-center">
              <p className="text-sm text-muted-foreground mb-1">Total Rounds</p>
              <p className="text-xl font-bold">{recruitment_summary.total_rounds}</p>
            </CardContent>
          </Card>
          <Card className="bg-muted/30">
            <CardContent className="p-4 text-center">
              <p className="text-sm text-muted-foreground mb-1">Scheduled</p>
              <p className="text-xl font-bold">{recruitment_summary.scheduled_rounds}</p>
            </CardContent>
          </Card>
          <Card className="bg-muted/30">
            <CardContent className="p-4 text-center">
              <p className="text-sm text-muted-foreground mb-1">Completed</p>
              <p className="text-xl font-bold">{recruitment_summary.completed_rounds}</p>
            </CardContent>
          </Card>
          <Card className="bg-emerald-50/50 dark:bg-emerald-950/20 border-emerald-100 dark:border-emerald-900">
            <CardContent className="p-4 text-center">
              <p className="text-sm text-emerald-600 dark:text-emerald-400 mb-1">Passed</p>
              <p className="text-xl font-bold text-emerald-700 dark:text-emerald-500">{recruitment_summary.passed_rounds}</p>
            </CardContent>
          </Card>
          <Card className="bg-red-50/50 dark:bg-red-950/20 border-red-100 dark:border-red-900">
            <CardContent className="p-4 text-center">
              <p className="text-sm text-red-600 dark:text-red-400 mb-1">Failed</p>
              <p className="text-xl font-bold text-red-700 dark:text-red-500">{recruitment_summary.failed_rounds}</p>
            </CardContent>
          </Card>
          <Card className="bg-primary/5 border-primary/20">
            <CardContent className="p-4 text-center">
              <p className="text-sm text-primary mb-1">Pass Rate</p>
              <p className="text-xl font-bold text-primary">{recruitment_summary.pass_rate.toFixed(1)}%</p>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  };

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

        {renderStats()}
        {renderCharts()}
        {renderRecruitmentSummary()}

        <h3 className="text-lg font-semibold mb-4 tracking-tight">Navigation</h3>
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3 pb-10">
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
              </CardHeader>
            </Card>
          ))}
        </div>
      </PageContainer>
    </AppLayout>
  );
}
