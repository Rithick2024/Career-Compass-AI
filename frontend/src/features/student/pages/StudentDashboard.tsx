import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  Calendar,
  CalendarClock,
  ArrowRight,
  TrendingUp,
  FileText,
  Award,
  AlertCircle,
  Briefcase,
  CheckCircle2,
  Clock,
  Video
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { PageHeader, PageContainer } from '@/components/common/PageHeader';
import { StatusBadge } from '@/components/common/StatusBadge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import { studentService } from '@/features/student/services/student.service';
import { analyticsService, StudentAnalyticsOverview } from '@/features/analytics/services/analytics.service';
import { intelligenceService } from '@/features/student/services/intelligence.service';
import { ReadinessResponse } from '@/features/student/types/intelligence.types';
import { Gauge } from 'lucide-react';
import { useAuth } from '@/features/auth/context/AuthContext';
import { MagnifyingGlassIcon } from '@radix-ui/react-icons';
import { useToast } from '@/hooks/use-toast';
import { Skeleton } from '@/components/ui/skeleton';

const STATUS_COLORS: Record<string, string> = {
  Pending: '#eab308',
  Reviewing: '#3b82f6',
  Interview: '#8b5cf6',
  Offered: '#10b981',
  Rejected: '#ef4444',
  Withdrawn: '#6b7280',
};

const ROUND_ICONS: Record<string, any> = {
  'Technical Interview': Video,
  'HR Interview': Video,
  'Online Assessment': FileText,
  'Coding Test': FileText,
  'Aptitude Test': FileText,
  'Managerial Interview': Video,
  'Group Discussion': AlertCircle,
  'Other': AlertCircle
};

export default function StudentDashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();
  
  const [firstName, setFirstName] = useState('');
  const [data, setData] = useState<StudentAnalyticsOverview | null>(null);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    studentService.getMyProfile()
      .then((p) => {
        const name = p.full_name || user?.email || 'Student';
        setFirstName(name.split(' ')[0]);
      })
      .catch(console.error);

    loadData();
  }, [user]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [res, rRes] = await Promise.all([
        analyticsService.getStudentOverview(),
        intelligenceService.getReadiness().catch(() => null),
      ]);
      setData(res);
      setReadiness(rRes);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load dashboard data.',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const renderReadinessCard = () => {
    if (loading || !readiness) return null;

    return (
      <Card className="mb-6 cursor-pointer hover:border-primary/50 transition-colors bg-card" onClick={() => navigate('/student/readiness')}>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <div>
            <CardTitle className="flex items-center gap-2 text-base font-semibold">
              <Gauge className="h-5 w-5 text-primary" />
              Placement Readiness
            </CardTitle>
            <CardDescription className="text-xs">
              Rule-based preparation & platform eligibility score
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs font-semibold">
              {readiness.status_category}
            </Badge>
            {readiness.is_placed && (
              <Badge variant="outline" className="bg-emerald-500/10 text-emerald-600 border-emerald-200 text-xs">
                Placed
              </Badge>
            )}
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight">{readiness.readiness_score}</span>
            <span className="text-sm text-muted-foreground font-medium">/ 100</span>
          </div>
          {readiness.actionable_recommendations.length > 0 && (
            <div className="space-y-1.5 pt-2 border-t">
              <span className="text-xs font-semibold text-muted-foreground">Top Recommendations:</span>
              <div className="grid gap-1">
                {readiness.actionable_recommendations.slice(0, 2).map((rec, i) => (
                  <p key={i} className="text-xs text-foreground flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
                    <span className="truncate">{rec}</span>
                  </p>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  const greeting = (() => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  })();

  const renderKPIs = () => {
    if (loading) {
      return (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          {[1,2,3,4].map(i => <Skeleton key={i} className="h-28 rounded-xl" />)}
        </div>
      );
    }

    if (!data) return null;

    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Applications</CardTitle>
            <Briefcase className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.active_applications}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Offers</CardTitle>
            <Award className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.total_offers}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Upcoming Rounds</CardTitle>
            <CalendarClock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.upcoming_rounds.length}</div>
          </CardContent>
        </Card>

        <Card className={data.placement_summary.has_accepted_placement ? "bg-emerald-50/50 dark:bg-emerald-950/20" : ""}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Accepted Placement</CardTitle>
            <TrendingUp className={`h-4 w-4 ${data.placement_summary.has_accepted_placement ? "text-emerald-500" : "text-muted-foreground"}`} />
          </CardHeader>
          <CardContent>
            {data.placement_summary.has_accepted_placement ? (
              <>
                <div className="text-xl font-bold truncate" title={data.placement_summary.latest_accepted_placement_company || ''}>
                  {data.placement_summary.latest_accepted_placement_company}
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  ${data.placement_summary.latest_accepted_placement_package?.toLocaleString()} Package
                </div>
              </>
            ) : (
              <div className="text-lg font-medium text-muted-foreground mt-1">
                No placement yet
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderStatusChart = () => {
    if (loading || !data) return null;

    const hasApps = data.application_status_summary.some(s => s.count > 0);

    return (
      <Card className="lg:col-span-1">
        <CardHeader>
          <CardTitle>Application Pipeline</CardTitle>
          <CardDescription>Current status of all applications</CardDescription>
        </CardHeader>
        <CardContent className="h-[280px]">
          {hasApps ? (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.application_status_summary}
                  dataKey="count"
                  nameKey="status"
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  label
                >
                  {data.application_status_summary.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={STATUS_COLORS[entry.status] || '#cbd5e1'} />
                  ))}
                </Pie>
                <RechartsTooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-muted-foreground text-sm">No applications yet</div>
          )}
        </CardContent>
      </Card>
    );
  };

  const renderRecruitmentSummary = () => {
    if (loading || !data) return null;
    const { recruitment_summary } = data;

    return (
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Recruitment Summary</CardTitle>
          <CardDescription>Your performance across all recruitment rounds</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-2">
            <div className="flex flex-col items-center justify-center p-4 bg-muted/30 rounded-lg">
              <span className="text-3xl font-bold">{recruitment_summary.total_rounds}</span>
              <span className="text-xs text-muted-foreground mt-1 uppercase tracking-wider font-semibold">Total Rounds</span>
            </div>
            <div className="flex flex-col items-center justify-center p-4 bg-muted/30 rounded-lg">
              <span className="text-3xl font-bold">{recruitment_summary.completed_rounds}</span>
              <span className="text-xs text-muted-foreground mt-1 uppercase tracking-wider font-semibold">Completed</span>
            </div>
            <div className="flex flex-col items-center justify-center p-4 bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900 rounded-lg">
              <span className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">{recruitment_summary.passed_rounds}</span>
              <span className="text-xs text-emerald-600/80 dark:text-emerald-400/80 mt-1 uppercase tracking-wider font-semibold">Passed</span>
            </div>
            <div className="flex flex-col items-center justify-center p-4 bg-red-50/50 dark:bg-red-950/20 border border-red-100 dark:border-red-900 rounded-lg">
              <span className="text-3xl font-bold text-red-600 dark:text-red-400">{recruitment_summary.failed_rounds}</span>
              <span className="text-xs text-red-600/80 dark:text-red-400/80 mt-1 uppercase tracking-wider font-semibold">Failed</span>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderRecentApps = () => {
    if (loading || !data) return null;

    return (
      <Card className="lg:col-span-2">
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle>Recent Applications</CardTitle>
            <CardDescription>Latest tracked jobs</CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={() => navigate('/student/applications')}>
            View All
            <ArrowRight className="ml-1 h-3.5 w-3.5" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-1">
          {data.recent_applications.length === 0 ? (
            <div className="py-8 text-center text-sm text-muted-foreground">
              You haven't applied to any jobs yet.
            </div>
          ) : (
            data.recent_applications.map((app, idx) => (
              <div key={app.id}>
                <div className="flex items-center gap-3 rounded-lg p-2.5 transition-colors hover:bg-secondary/60 cursor-pointer" onClick={() => navigate('/student/applications')}>
                  <Avatar className="h-10 w-10 border">
                    <AvatarFallback className="bg-primary/10 text-sm font-semibold text-primary">
                      {app.company_name.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{app.job_title}</p>
                    <p className="text-xs text-muted-foreground truncate">{app.company_name}</p>
                  </div>
                  <div className="hidden sm:block">
                    <StatusBadge status={app.status as any} />
                  </div>
                  <span className="hidden text-xs text-muted-foreground md:block">
                    {new Date(app.applied_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </span>
                </div>
                {idx < data.recent_applications.length - 1 && <Separator className="my-0.5" />}
              </div>
            ))
          )}
        </CardContent>
      </Card>
    );
  };

  const renderUpcomingRounds = () => {
    if (loading || !data) return null;

    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle>Upcoming Rounds</CardTitle>
            <CardDescription>Scheduled interviews and tests</CardDescription>
          </div>
          <CalendarClock className="h-5 w-5 text-muted-foreground" />
        </CardHeader>
        <CardContent className="space-y-3">
          {data.upcoming_rounds.length === 0 ? (
            <div className="py-8 text-center text-sm text-muted-foreground">
              No upcoming rounds scheduled.
            </div>
          ) : (
            data.upcoming_rounds.map((event) => {
              const IconComp = ROUND_ICONS[event.round_type] || CalendarClock;
              return (
                <div key={event.id} className="flex gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
                    <IconComp className="h-4 w-4" />
                  </div>
                  <div className="flex-1 space-y-0.5 min-w-0">
                    <p className="text-sm font-medium leading-tight truncate" title={`${event.round_type} - ${event.company_name}`}>
                      {event.round_type}
                    </p>
                    <p className="text-xs text-muted-foreground truncate">{event.job_title} at {event.company_name}</p>
                    <p className="flex items-center gap-1 text-[11px] font-medium text-muted-foreground">
                      <Calendar className="h-3 w-3" />
                      {new Date(event.scheduled_at).toLocaleString('en-US', { weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              );
            })
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <AppLayout role="student" userName={user?.email || firstName || 'Student'} userRole="Student" avatarText={firstName.substring(0,2).toUpperCase() || 'ST'}>
      <PageContainer>
        <PageHeader
          title={`${greeting}, ${firstName || 'Student'}`}
          description="Here's what's happening with your placement journey."
          action={
            <Button onClick={() => navigate('/student/jobs')}>
              <MagnifyingGlassIcon className="mr-1.5 h-4 w-4" />
              Find Jobs
            </Button>
          }
        />

        {renderReadinessCard()}
        {renderKPIs()}

        <div className="grid gap-6 lg:grid-cols-3 mb-6">
          {renderStatusChart()}
          {renderRecruitmentSummary()}
        </div>

        <div className="grid gap-6 lg:grid-cols-3 pb-10">
          {renderRecentApps()}
          {renderUpcomingRounds()}
        </div>
      </PageContainer>
    </AppLayout>
  );
}
