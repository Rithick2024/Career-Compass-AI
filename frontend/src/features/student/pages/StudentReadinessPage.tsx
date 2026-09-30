import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Gauge,
  Award,
  CheckCircle2,
  AlertTriangle,
  BookOpen,
  Zap,
  FileText,
  Briefcase,
  ArrowRight,
  TrendingUp,
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { PageHeader, PageContainer } from '@/components/common/PageHeader';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/features/auth/context/AuthContext';
import { intelligenceService } from '@/features/student/services/intelligence.service';
import { ReadinessResponse, MarketSkillGapResponse } from '@/features/student/types/intelligence.types';

const CATEGORY_COLORS: Record<string, string> = {
  'Needs Improvement': 'bg-red-500/15 text-red-700 dark:text-red-400 border-red-200 dark:border-red-900',
  'Developing': 'bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-900',
  'Good': 'bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-900',
  'Strong': 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-900',
};

const PILLAR_ICONS: Record<string, any> = {
  'Academic Readiness': BookOpen,
  'Skill Profile': Zap,
  'Profile & Resume': FileText,
  'Market Eligibility': Briefcase,
};

export default function StudentReadinessPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();

  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [skillGaps, setSkillGaps] = useState<MarketSkillGapResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [rRes, gRes] = await Promise.all([
        intelligenceService.getReadiness(),
        intelligenceService.getSkillGaps(),
      ]);
      setReadiness(rRes);
      setSkillGaps(gRes);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load intelligence data.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const renderHeader = () => (
    <PageHeader
      title="Placement Readiness & Skill Gaps"
      description="Rule-based preparation and platform eligibility indicator."
      action={
        <Button variant="outline" onClick={() => navigate('/student/skills')}>
          <Zap className="mr-1.5 h-4 w-4" />
          Manage My Skills
        </Button>
      }
    />
  );

  if (loading) {
    return (
      <AppLayout role="student" userName={user?.email || 'Student'} userRole="Student" avatarText="ST">
        <PageContainer>
          {renderHeader()}
          <div className="space-y-6">
            <Skeleton className="h-44 w-full rounded-xl" />
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-36 rounded-xl" />
              ))}
            </div>
            <Skeleton className="h-64 w-full rounded-xl" />
          </div>
        </PageContainer>
      </AppLayout>
    );
  }

  return (
    <AppLayout role="student" userName={user?.email || 'Student'} userRole="Student" avatarText="ST">
      <PageContainer>
        {renderHeader()}

        {readiness && (
          <>
            {/* Overall Score Banner */}
            <Card className="mb-6 bg-gradient-to-r from-primary/5 via-primary/10 to-transparent border-primary/20">
              <CardContent className="p-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className={CATEGORY_COLORS[readiness.status_category] || ''}>
                        {readiness.status_category}
                      </Badge>
                      {readiness.is_placed && (
                        <Badge variant="outline" className="bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-300">
                          <Award className="mr-1 h-3.5 w-3.5" />
                          Placed
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-4xl font-extrabold tracking-tight">{readiness.readiness_score}</span>
                      <span className="text-lg text-muted-foreground font-medium">/ 100</span>
                    </div>
                    <p className="text-sm text-muted-foreground max-w-xl">
                      Calculated dynamically based on your academic profile, active technical skills, default resume availability, and active job market eligibility.
                    </p>
                  </div>
                  <div className="w-full md:w-64 space-y-2">
                    <div className="flex justify-between text-xs font-semibold text-muted-foreground">
                      <span>Overall Progress</span>
                      <span>{readiness.readiness_score}%</span>
                    </div>
                    <Progress value={readiness.readiness_score} className="h-3" />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Pillar Breakdown Cards */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
              {readiness.components.map((comp) => {
                const IconComp = PILLAR_ICONS[comp.name] || Gauge;
                const pct = Math.round((comp.score / comp.max_score) * 100);
                return (
                  <Card key={comp.name}>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-sm font-medium">{comp.name}</CardTitle>
                      <IconComp className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="flex items-baseline justify-between">
                        <span className="text-2xl font-bold">{comp.score}</span>
                        <span className="text-xs text-muted-foreground">/ {comp.max_score} pts</span>
                      </div>
                      <Progress value={pct} className="h-2" />
                      <p className="text-xs text-muted-foreground leading-relaxed">{comp.explanation}</p>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {/* Actionable Recommendations */}
            {readiness.actionable_recommendations.length > 0 && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                    Actionable Recommendations to Improve Readiness
                  </CardTitle>
                  <CardDescription>Deterministic steps based on your current profile gaps</CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2.5">
                    {readiness.actionable_recommendations.map((rec, idx) => (
                      <li key={idx} className="flex items-start gap-2.5 text-sm p-2.5 rounded-lg bg-muted/40 border">
                        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary mt-0.5">
                          {idx + 1}
                        </span>
                        <span className="text-foreground leading-relaxed">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </>
        )}

        {/* Market Skill Gap Analysis */}
        {skillGaps && (
          <Card className="mb-8">
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-primary" />
                  Relevant Market Skill Gaps
                </CardTitle>
                <CardDescription>
                  {skillGaps.explanation} ({skillGaps.total_active_jobs_evaluated} active visible jobs evaluated)
                </CardDescription>
              </div>
              <Button variant="ghost" size="sm" onClick={() => navigate('/student/skills')}>
                Add Skills
                <ArrowRight className="ml-1 h-3.5 w-3.5" />
              </Button>
            </CardHeader>
            <CardContent>
              {skillGaps.gaps.length === 0 ? (
                <div className="py-8 text-center text-sm text-muted-foreground">
                  No skill gaps identified for your profile against active jobs!
                </div>
              ) : (
                <div className="space-y-3">
                  {skillGaps.gaps.map((gap) => (
                    <div
                      key={gap.skill_id}
                      className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-lg border bg-card hover:bg-muted/30 transition-colors"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-sm">{gap.skill_name}</span>
                          {gap.category && (
                            <Badge variant="outline" className="text-[11px] font-normal">
                              {gap.category}
                            </Badge>
                          )}
                          <Badge
                            variant="secondary"
                            className={
                              gap.gap_type === 'MISSING'
                                ? 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-200'
                                : 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-200'
                            }
                          >
                            {gap.gap_type === 'MISSING' ? 'Missing Skill' : 'Insufficient Proficiency'}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span>
                            Required: <strong className="capitalize text-foreground">{gap.required_proficiency}</strong>
                          </span>
                          <span>•</span>
                          <span>
                            Your Level: <strong className="capitalize text-foreground">{gap.student_proficiency || 'None'}</strong>
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 self-start sm:self-center">
                        <Badge variant="outline" className="bg-primary/5 text-primary text-xs">
                          {gap.jobs_requiring_skill} active job{gap.jobs_requiring_skill > 1 ? 's' : ''} requiring
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </PageContainer>
    </AppLayout>
  );
}
