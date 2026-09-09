import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  Calendar,
  CalendarClock,
  MapPin,
  Sparkles,
  ArrowRight,
  Plus,
  TrendingUp,
  Video,
  FileText,
  Award,
  AlertCircle,
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { PageHeader, PageContainer } from '@/components/common/PageHeader';
import { StatCard } from '@/components/common/StatCard';
import { StatusBadge } from '@/components/common/StatusBadge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import {
  dashboardStats,
  recentApplications,
  skillGaps,
  upcomingEvents,
  applicationTrend,
  jobRecommendations,
} from '@/features/student/data/mock-data';
import { studentService } from '@/features/student/services/student.service';
import { useAuth } from '@/features/auth/context/AuthContext';

const eventTypeConfig = {
  interview: { icon: Video, color: 'text-violet-600 dark:text-violet-400', bg: 'bg-violet-100 dark:bg-violet-900/30' },
  application: { icon: FileText, color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-100 dark:bg-blue-900/30' },
  offer: { icon: Award, color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-100 dark:bg-emerald-900/30' },
  deadline: { icon: AlertCircle, color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-100 dark:bg-amber-900/30' },
} as const;

export default function StudentDashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [firstName, setFirstName] = useState('');
  const readinessScore = 78;

  useEffect(() => {
    studentService.getMyProfile()
      .then((p) => {
        const name = p.full_name || user?.email || 'Student';
        setFirstName(name.split(' ')[0]);
      })
      .catch(console.error);
  }, [user]);

  const greeting = (() => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  })();

  return (
    <AppLayout role="student" userName="Aarav Sharma" userRole="Student" avatarText="AS">
      <PageContainer>
        <PageHeader
          title={`${greeting}, ${firstName || 'Student'}`}
          description="Here's what's happening with your placement journey today."
          action={
            <Button onClick={() => navigate('/student/jobs')}>
              <Plus className="mr-1.5 h-4 w-4" />
              Find Jobs
            </Button>
          }
        />

        {/* Stats grid */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {dashboardStats.map((stat) => (
            <StatCard key={stat.label} {...stat} />
          ))}
        </div>

        {/* Charts row */}
        <div className="grid gap-4 lg:grid-cols-3">
          {/* Application trend chart */}
          <Card className="lg:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <div className="space-y-1">
                <CardTitle>Application Activity</CardTitle>
                <CardDescription>Applications vs interviews over the last 8 months</CardDescription>
              </div>
              <div className="flex items-center gap-4 text-xs">
                <span className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-primary" />
                  Applications
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-chart-2" />
                  Interviews
                </span>
              </div>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={applicationTrend} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="gradApplications" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="gradInterviews" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--chart-2))" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(var(--chart-2))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                  <XAxis
                    dataKey="month"
                    stroke="hsl(var(--muted-foreground))"
                    fontSize={12}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    stroke="hsl(var(--muted-foreground))"
                    fontSize={12}
                    tickLine={false}
                    axisLine={false}
                  />
                  <RechartsTooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="applications"
                    stroke="hsl(var(--primary))"
                    strokeWidth={2}
                    fill="url(#gradApplications)"
                  />
                  <Area
                    type="monotone"
                    dataKey="interviews"
                    stroke="hsl(var(--chart-2))"
                    strokeWidth={2}
                    fill="url(#gradInterviews)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Readiness score gauge */}
          <Card>
            <CardHeader>
              <CardTitle>Placement Readiness</CardTitle>
              <CardDescription>Your overall readiness score</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col items-center justify-center pt-2">
              <div className="relative flex h-40 w-40 items-center justify-center">
                <svg className="h-full w-full -rotate-90" viewBox="0 0 120 120">
                  <circle
                    cx="60"
                    cy="60"
                    r="52"
                    fill="none"
                    stroke="hsl(var(--muted))"
                    strokeWidth="10"
                  />
                  <circle
                    cx="60"
                    cy="60"
                    r="52"
                    fill="none"
                    stroke="hsl(var(--primary))"
                    strokeWidth="10"
                    strokeLinecap="round"
                    strokeDasharray={`${(readinessScore / 100) * 327} 327`}
                    className="transition-all duration-1000"
                  />
                </svg>
                <div className="absolute flex flex-col items-center">
                  <span className="text-4xl font-bold">{readinessScore}%</span>
                  <span className="text-xs text-muted-foreground">Ready</span>
                </div>
              </div>
              <div className="mt-4 flex w-full items-center justify-center gap-1.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                <TrendingUp className="h-3.5 w-3.5" />
                <span>+5% from last month</span>
              </div>
              <Button variant="outline" size="sm" className="mt-4 w-full" onClick={() => navigate('/student/readiness')}>
                View Details
                <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Recent applications + Upcoming events */}
        <div className="grid gap-4 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <div>
                <CardTitle>Recent Applications</CardTitle>
                <CardDescription>Track the status of your latest applications</CardDescription>
              </div>
              <Button variant="ghost" size="sm" onClick={() => navigate('/student/applications')}>
                View All
                <ArrowRight className="ml-1 h-3.5 w-3.5" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-1">
              {recentApplications.map((app, idx) => (
                <div key={app.id}>
                  <div className="flex items-center gap-3 rounded-lg p-2.5 transition-colors hover:bg-secondary/60">
                    <Avatar className="h-10 w-10 border">
                      <AvatarFallback className="bg-primary/10 text-sm font-semibold text-primary">
                        {app.logo}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{app.role}</p>
                      <p className="text-xs text-muted-foreground">{app.company}</p>
                    </div>
                    <div className="hidden sm:block">
                      <StatusBadge status={app.status} />
                    </div>
                    <span className="hidden text-xs text-muted-foreground md:block">
                      {new Date(app.appliedDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </span>
                  </div>
                  {idx < recentApplications.length - 1 && <Separator className="my-0.5" />}
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Upcoming events */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <div>
                <CardTitle>Upcoming</CardTitle>
                <CardDescription>Next 2 weeks</CardDescription>
              </div>
              <CalendarClock className="h-5 w-5 text-muted-foreground" />
            </CardHeader>
            <CardContent className="space-y-3">
              {upcomingEvents.map((event) => {
                const config = eventTypeConfig[event.type];
                return (
                  <div key={event.title} className="flex gap-3">
                    <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${config.bg}`}>
                      <config.icon className={`h-4 w-4 ${config.color}`} />
                    </div>
                    <div className="flex-1 space-y-0.5">
                      <p className="text-sm font-medium leading-tight">{event.title}</p>
                      <p className="text-xs text-muted-foreground">{event.description}</p>
                      <p className="flex items-center gap-1 text-[11px] font-medium text-muted-foreground">
                        <Calendar className="h-3 w-3" />
                        {new Date(event.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                      </p>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </div>

        {/* Skill gaps + Job recommendations */}
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <div>
                <CardTitle>Skill Gap Analysis</CardTitle>
                <CardDescription>AI-identified areas to improve</CardDescription>
              </div>
              <Badge variant="secondary" className="gap-1">
                <Sparkles className="h-3 w-3" />
                AI
              </Badge>
            </CardHeader>
            <CardContent className="space-y-4">
              {skillGaps.map((skill) => (
                <div key={skill.skill} className="space-y-1.5">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{skill.skill}</span>
                    <span className="text-xs text-muted-foreground">
                      <span className="font-semibold text-foreground">{skill.have}%</span> / {skill.need}%
                    </span>
                  </div>
                  <div className="relative">
                    <Progress value={skill.have} className="h-2" />
                    <div
                      className="absolute top-0 h-2 w-0.5 bg-foreground/40"
                      style={{ left: `${skill.need}%` }}
                    />
                  </div>
                </div>
              ))}
              <Button variant="outline" size="sm" className="w-full" onClick={() => navigate('/student/skills')}>
                Improve Skills
                <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <div>
                <CardTitle>Recommended Jobs</CardTitle>
                <CardDescription>AI-matched based on your profile</CardDescription>
              </div>
              <Badge variant="secondary" className="gap-1">
                <Sparkles className="h-3 w-3" />
                AI
              </Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              {jobRecommendations.map((job) => (
                <div
                  key={job.id}
                  role="button"
                  tabIndex={0}
                  className="rounded-lg border p-3.5 transition-all hover:border-primary/30 hover:shadow-sm cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  onClick={() => navigate('/student/jobs')}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      navigate('/student/jobs');
                    }
                  }}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="space-y-0.5">
                      <p className="text-sm font-semibold">{job.role}</p>
                      <p className="text-xs text-muted-foreground">{job.company}</p>
                    </div>
                    <Badge className="bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 border-0">
                      {job.match}% match
                    </Badge>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {job.tags.slice(0, 3).map((tag) => (
                      <Badge key={tag} variant="outline" className="text-[10px] font-medium">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                  <div className="mt-2.5 flex items-center justify-between text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      {job.location}
                    </span>
                    <span className="font-medium text-foreground">{job.salary}</span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </PageContainer>
    </AppLayout>
  );
}
