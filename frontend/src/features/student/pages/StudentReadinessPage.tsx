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
  Bot,
  Target,
  Sparkles,
  RefreshCw,
  HelpCircle,
  Clock,
  CheckCircle,
  Circle,
  Send,
  MessageSquare,
  AlertCircle,
  Building2,
  ShieldCheck,
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { PageHeader, PageContainer } from '@/components/common/PageHeader';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/features/auth/context/AuthContext';
import { studentJobService, StudentJob } from '@/features/student/services/job.service';
import { intelligenceService } from '@/features/student/services/intelligence.service';
import {
  ReadinessResponse,
  MarketSkillGapResponse,
  JobReadinessAssessmentResponse,
  ImprovementPlanResponse,
  JobMentorAdviceResponse,
} from '@/features/student/types/intelligence.types';

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

const READINESS_BAND_COLORS: Record<string, string> = {
  'High Match': 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-300',
  'Moderate Match': 'bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-300',
  'Developing': 'bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-300',
  'Action Required': 'bg-red-500/15 text-red-700 dark:text-red-400 border-red-300',
  'High Readiness': 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-300',
  'Moderate Readiness': 'bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-300',
  'Low Readiness': 'bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-300',
  'Critical Gaps': 'bg-red-500/15 text-red-700 dark:text-red-400 border-red-300',
};

export default function StudentReadinessPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();

  // General Readiness State
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [skillGaps, setSkillGaps] = useState<MarketSkillGapResponse | null>(null);
  const [loadingGeneral, setLoadingGeneral] = useState(true);

  // Job-Specific Readiness & Improvement Plan State
  const [jobs, setJobs] = useState<StudentJob[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [jobReadiness, setJobReadiness] = useState<JobReadinessAssessmentResponse | null>(null);
  const [improvementPlan, setImprovementPlan] = useState<ImprovementPlanResponse | null>(null);
  const [loadingJobAssessment, setLoadingJobAssessment] = useState(false);
  const [generatingPlan, setGeneratingPlan] = useState(false);
  const [updatingActionId, setUpdatingActionId] = useState<number | null>(null);

  // AI Mentor Advice State
  const [mentorQuery, setMentorQuery] = useState('');
  const [mentorAdvice, setMentorAdvice] = useState<JobMentorAdviceResponse | null>(null);
  const [loadingMentorAdvice, setLoadingMentorAdvice] = useState(false);

  // Derived Skill Breakdown & Pillar Points from Job Readiness
  const demonstratedSkills =
    jobReadiness?.skills_breakdown?.filter((s) => s.status === 'DEMONSTRATED') || [];
  const partialSkills =
    jobReadiness?.skills_breakdown?.filter((s) => s.status === 'PARTIAL_EVIDENCE') || [];
  const missingSkills =
    jobReadiness?.skills_breakdown?.filter((s) => s.status === 'UNVERIFIED_OR_MISSING') || [];
  const academicScore = jobReadiness?.score_breakdown?.academic_points ?? 0;
  const skillScore = jobReadiness?.score_breakdown?.skill_points ?? 0;
  const prepScore = jobReadiness?.score_breakdown?.preparation_points ?? 0;


  useEffect(() => {
    loadGeneralData();
    loadJobs();
  }, []);

  const loadGeneralData = async () => {
    try {
      setLoadingGeneral(true);
      const [rRes, gRes] = await Promise.all([
        intelligenceService.getReadiness(),
        intelligenceService.getSkillGaps(),
      ]);
      setReadiness(rRes);
      setSkillGaps(gRes);
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to load general intelligence data.',
        variant: 'destructive',
      });
    } finally {
      setLoadingGeneral(false);
    }
  };

  const loadJobs = async () => {
    try {
      const activeJobs = await studentJobService.getJobs();
      setJobs(activeJobs);
      if (activeJobs.length > 0) {
        const firstId = String(activeJobs[0].id);
        setSelectedJobId(firstId);
        loadJobAssessmentAndPlan(activeJobs[0].id);
      }
    } catch {
      // Jobs fetch error handled silently or with fallback
    }
  };

  const loadJobAssessmentAndPlan = async (jobId: number) => {
    try {
      setLoadingJobAssessment(true);
      setMentorAdvice(null);
      const [assessRes, planRes] = await Promise.all([
        intelligenceService.getJobReadiness(jobId),
        intelligenceService.getJobPlan(jobId).catch(() => null),
      ]);
      setJobReadiness(assessRes);
      setImprovementPlan(planRes);
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to assess target job readiness.',
        variant: 'destructive',
      });
    } finally {
      setLoadingJobAssessment(false);
    }
  };

  const handleSelectJob = (jobIdStr: string) => {
    setSelectedJobId(jobIdStr);
    const jId = parseInt(jobIdStr, 10);
    if (!isNaN(jId)) {
      loadJobAssessmentAndPlan(jId);
    }
  };

  const handleGeneratePlan = async () => {
    if (!selectedJobId) return;
    const jId = parseInt(selectedJobId, 10);
    try {
      setGeneratingPlan(true);
      const newPlan = await intelligenceService.generateJobPlan(jId);
      setImprovementPlan(newPlan);
      toast({
        title: 'Improvement Plan Ready',
        description: `Generated ${newPlan.actions.length} prioritized action items.`,
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Could not generate improvement plan.',
        variant: 'destructive',
      });
    } finally {
      setGeneratingPlan(false);
    }
  };

  const handleToggleActionStatus = async (
    actionId: number,
    currentStatus: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED'
  ) => {
    const nextStatus: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' =
      currentStatus === 'PENDING'
        ? 'IN_PROGRESS'
        : currentStatus === 'IN_PROGRESS'
        ? 'COMPLETED'
        : 'PENDING';

    try {
      setUpdatingActionId(actionId);
      const updated = await intelligenceService.updateActionStatus(actionId, nextStatus);

      if (improvementPlan) {
        const updatedActions = improvementPlan.actions.map((a) =>
          a.id === actionId ? updated : a
        );
        const total = updatedActions.length;
        const completed = updatedActions.filter((a) => a.status === 'COMPLETED').length;
        const progress = total > 0 ? Math.round((completed / total) * 100) : 0;

        setImprovementPlan({
          ...improvementPlan,
          actions: updatedActions,
          completed_actions: completed,
          progress_percentage: progress,
        });
      }

      toast({
        title: 'Action Status Updated',
        description: `Action set to ${nextStatus.replace('_', ' ')}.`,
      });

      if (selectedJobId) {
        const jId = parseInt(selectedJobId, 10);
        try {
          const updatedReadiness = await intelligenceService.getJobReadiness(jId);
          setJobReadiness(updatedReadiness);
        } catch {
          // non-critical if readiness refresh fails
        }
      }
    } catch {
      toast({
        title: 'Update Failed',
        description: 'Could not update action status.',
        variant: 'destructive',
      });
    } finally {
      setUpdatingActionId(null);
    }
  };

  const handleAskJobMentor = async () => {
    if (!selectedJobId) return;
    const jId = parseInt(selectedJobId, 10);
    try {
      setLoadingMentorAdvice(true);
      const res = await intelligenceService.askJobMentorAdvice(jId, {
        question: mentorQuery.trim() || undefined,
      });
      setMentorAdvice(res);
    } catch {
      toast({
        title: 'Advisor Unavailable',
        description: 'Could not retrieve AI advisor guidance right now.',
        variant: 'destructive',
      });
    } finally {
      setLoadingMentorAdvice(false);
    }
  };

  const renderHeader = () => (
    <PageHeader
      title="Career Readiness & Growth Engine"
      description="Connected, job-specific readiness assessment, skill gap diagnostics, and personalized improvement plans."
      action={
        <div className="flex gap-2">
          <Button variant="outline" className="gap-1.5" onClick={() => navigate('/student/mentor')}>
            <Bot className="h-4 w-4 text-primary" />
            AI Career Mentor
          </Button>
          <Button variant="outline" onClick={() => navigate('/student/skills')}>
            <Zap className="mr-1.5 h-4 w-4" />
            Manage My Skills
          </Button>
        </div>
      }
    />
  );

  return (
    <AppLayout role="student" userName={user?.email || 'Student'} userRole="Student" avatarText="ST">
      <PageContainer>
        {renderHeader()}

        <Tabs defaultValue="target-job" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2 max-w-md">
            <TabsTrigger value="target-job" className="gap-2">
              <Target className="h-4 w-4" />
              Target Job Readiness & Plan
            </TabsTrigger>
            <TabsTrigger value="campus-overview" className="gap-2">
              <TrendingUp className="h-4 w-4" />
              Campus Readiness & Gaps
            </TabsTrigger>
          </TabsList>

          {/* TAB 1: Target Job Readiness & Growth Engine */}
          <TabsContent value="target-job" className="space-y-6">
            {/* Job Selection Card */}
            <Card className="border-primary/20 bg-muted/20">
              <CardContent className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Briefcase className="h-4 w-4 text-primary" />
                    <span className="font-semibold text-sm">Select Target Placement Opportunity</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Evaluate your profile against real job requirements and generate a personalized improvement plan.
                  </p>
                </div>
                <div className="w-full md:w-80">
                  <Select value={selectedJobId} onValueChange={handleSelectJob}>
                    <SelectTrigger className="w-full bg-background">
                      <SelectValue placeholder="Choose a campus drive..." />
                    </SelectTrigger>
                    <SelectContent>
                      {jobs.map((j) => (
                        <SelectItem key={j.id} value={String(j.id)}>
                          {j.title} · {j.company?.name || 'Company'}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            {loadingJobAssessment ? (
              <div className="space-y-4">
                <Skeleton className="h-44 w-full rounded-xl" />
                <div className="grid gap-4 md:grid-cols-3">
                  <Skeleton className="h-32 rounded-xl" />
                  <Skeleton className="h-32 rounded-xl" />
                  <Skeleton className="h-32 rounded-xl" />
                </div>
                <Skeleton className="h-64 w-full rounded-xl" />
              </div>
            ) : jobReadiness ? (
              <>
                {/* Explainable Job Readiness Banner */}
                <Card className="bg-gradient-to-r from-primary/5 via-primary/10 to-transparent border-primary/30">
                  <CardContent className="p-6">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                      <div className="space-y-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-lg font-bold tracking-tight">
                            {jobReadiness.job_title}
                          </span>
                          <span className="text-sm text-muted-foreground">at</span>
                          <span className="text-sm font-semibold text-foreground">
                            {jobReadiness.company_name}
                          </span>
                          <Badge
                            variant="outline"
                            className={READINESS_BAND_COLORS[jobReadiness.readiness_tier] || ''}
                          >
                            {jobReadiness.readiness_tier}
                          </Badge>
                          <Badge
                            variant={jobReadiness.is_eligible ? 'default' : 'destructive'}
                            className="gap-1 text-xs"
                          >
                            {jobReadiness.is_eligible ? (
                              <>
                                <CheckCircle2 className="h-3 w-3" />
                                Eligible to Apply
                              </>
                            ) : (
                              <>
                                <AlertTriangle className="h-3 w-3" />
                                Eligibility Restrictions
                              </>
                            )}
                          </Badge>
                        </div>

                        <div className="flex items-baseline gap-2 pt-1">
                          <span className="text-5xl font-extrabold tracking-tight">
                            {jobReadiness.readiness_score}
                          </span>
                          <span className="text-lg text-muted-foreground font-medium">/ 100</span>
                        </div>

                        <p className="text-xs text-muted-foreground max-w-2xl leading-relaxed">
                          {jobReadiness.scoring_explanation}
                        </p>

                        {/* Eligibility reasons / warnings */}
                        <div className="pt-2 space-y-1">
                          {jobReadiness.eligibility_reasons.map((reason, idx) => (
                            <div key={idx} className="flex items-center gap-1.5 text-xs text-muted-foreground">
                              {jobReadiness.is_eligible ? (
                                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                              ) : (
                                <AlertCircle className="h-3.5 w-3.5 text-amber-500 shrink-0" />
                              )}
                              <span>{reason}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Component breakdown meters */}
                      <div className="w-full md:w-72 space-y-3 bg-card/60 p-4 rounded-xl border">
                        <div className="space-y-1">
                          <div className="flex justify-between text-xs font-medium">
                            <span>Academic Criteria</span>
                            <span className="font-bold">{academicScore} / 30 pts</span>
                          </div>
                          <Progress
                            value={Math.round((academicScore / 30) * 100)}
                            className="h-2"
                          />
                        </div>
                        <div className="space-y-1">
                          <div className="flex justify-between text-xs font-medium">
                            <span>Demonstrated Skills</span>
                            <span className="font-bold">{skillScore} / 50 pts</span>
                          </div>
                          <Progress
                            value={Math.round((skillScore / 50) * 100)}
                            className="h-2"
                          />
                        </div>
                        <div className="space-y-1">
                          <div className="flex justify-between text-xs font-medium">
                            <span>Preparation & Resume</span>
                            <span className="font-bold">{prepScore} / 20 pts</span>
                          </div>
                          <Progress
                            value={Math.round((prepScore / 20) * 100)}
                            className="h-2"
                          />
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Skill-by-Skill Evidence Analysis */}
                <div className="grid gap-6 md:grid-cols-3">
                  {/* Demonstrated Skills */}
                  <Card className="border-emerald-500/20 bg-emerald-500/[0.02]">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-semibold flex items-center justify-between text-emerald-700 dark:text-emerald-400">
                        <span className="flex items-center gap-2">
                          <CheckCircle2 className="h-4 w-4" />
                          Demonstrated Skills
                        </span>
                        <Badge variant="outline" className="border-emerald-300 text-emerald-700 dark:text-emerald-400">
                          {demonstratedSkills.length}
                        </Badge>
                      </CardTitle>
                      <CardDescription className="text-xs">
                        Skills verified or meeting target requirements.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-2.5">
                      {demonstratedSkills.length === 0 ? (
                        <p className="text-xs text-muted-foreground italic py-3 text-center">
                          No fully demonstrated skills recorded yet.
                        </p>
                      ) : (
                        demonstratedSkills.map((s) => (
                          <div key={s.skill_id} className="p-2.5 rounded-lg border bg-card text-xs space-y-1.5">
                            <div className="flex items-center justify-between font-semibold gap-1">
                              <span className="flex items-center gap-1.5">
                                {s.skill_name}
                                {s.is_verified ? (
                                  <Badge variant="outline" className="text-[10px] bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-300 gap-1 py-0 h-4">
                                    <ShieldCheck className="h-2.5 w-2.5" />
                                    Verified
                                  </Badge>
                                ) : (
                                  <Badge variant="outline" className="text-[10px] text-muted-foreground border-muted py-0 h-4">
                                    Self-Reported
                                  </Badge>
                                )}
                              </span>
                              <Badge variant="secondary" className="text-[10px] bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 shrink-0">
                                {s.student_proficiency || 'Proficient'}
                              </Badge>
                            </div>
                            <p className="text-muted-foreground text-[11px] leading-relaxed">{s.evidence_summary}</p>
                            {s.evidence_reference && (
                              <p className="text-[10px] text-emerald-800 dark:text-emerald-300 font-mono truncate">
                                Provenance: {s.evidence_reference}
                              </p>
                            )}
                          </div>
                        ))
                      )}
                    </CardContent>
                  </Card>

                  {/* Partially Supported Skills */}
                  <Card className="border-amber-500/20 bg-amber-500/[0.02]">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-semibold flex items-center justify-between text-amber-700 dark:text-amber-400">
                        <span className="flex items-center gap-2">
                          <AlertTriangle className="h-4 w-4" />
                          Partially Supported
                        </span>
                        <Badge variant="outline" className="border-amber-300 text-amber-700 dark:text-amber-400">
                          {partialSkills.length}
                        </Badge>
                      </CardTitle>
                      <CardDescription className="text-xs">
                        Self-reported or below required proficiency level.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-2.5">
                      {partialSkills.length === 0 ? (
                        <p className="text-xs text-muted-foreground italic py-3 text-center">
                          No partially supported skills for this role.
                        </p>
                      ) : (
                        partialSkills.map((s) => (
                          <div key={s.skill_id} className="p-2.5 rounded-lg border bg-card text-xs space-y-1.5">
                            <div className="flex items-center justify-between font-semibold gap-1">
                              <span className="flex items-center gap-1.5">
                                {s.skill_name}
                                {s.evidence_source === 'PRACTICE_COMPLETED' ? (
                                  <Badge variant="outline" className="text-[10px] bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-300 py-0 h-4">
                                    Practice Done
                                  </Badge>
                                ) : (
                                  <Badge variant="outline" className="text-[10px] text-muted-foreground border-muted py-0 h-4">
                                    Self-Reported
                                  </Badge>
                                )}
                              </span>
                              <Badge variant="secondary" className="text-[10px] bg-amber-500/10 text-amber-700 dark:text-amber-400 shrink-0">
                                {s.student_proficiency || 'Basic'} / Req: {s.required_proficiency || 'Intermediate'}
                              </Badge>
                            </div>
                            <p className="text-muted-foreground text-[11px] leading-relaxed">{s.evidence_summary}</p>
                            {s.evidence_reference && (
                              <p className="text-[10px] text-amber-800 dark:text-amber-300 font-mono truncate">
                                Provenance: {s.evidence_reference}
                              </p>
                            )}
                          </div>
                        ))
                      )}
                    </CardContent>
                  </Card>

                  {/* Missing Evidence / Identified Gaps */}
                  <Card className="border-rose-500/20 bg-rose-500/[0.02]">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-semibold flex items-center justify-between text-rose-700 dark:text-rose-400">
                        <span className="flex items-center gap-2">
                          <AlertCircle className="h-4 w-4" />
                          Missing Platform Evidence
                        </span>
                        <Badge variant="outline" className="border-rose-300 text-rose-700 dark:text-rose-400">
                          {missingSkills.length}
                        </Badge>
                      </CardTitle>
                      <CardDescription className="text-xs">
                        Not recorded on platform. May exist outside system.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-2.5">
                      {missingSkills.length === 0 ? (
                        <p className="text-xs text-muted-foreground italic py-3 text-center">
                          Zero missing skill evidence for this job!
                        </p>
                      ) : (
                        missingSkills.map((s) => (
                          <div key={s.skill_id} className="p-2.5 rounded-lg border bg-card text-xs space-y-1.5">
                            <div className="flex items-center justify-between font-semibold gap-1">
                              <span className="flex items-center gap-1.5">
                                {s.skill_name}
                                {s.practice_completed && (
                                  <Badge variant="outline" className="text-[10px] bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-300 py-0 h-4">
                                    Practice Done
                                  </Badge>
                                )}
                              </span>
                              <Badge variant="outline" className="text-[10px] text-rose-600 border-rose-200 shrink-0">
                                Req: {s.required_proficiency || 'Required'}
                              </Badge>
                            </div>
                            <p className="text-muted-foreground text-[11px] leading-relaxed">{s.evidence_summary}</p>
                            {s.evidence_reference && (
                              <p className="text-[10px] text-muted-foreground font-mono truncate">
                                Ref: {s.evidence_reference}
                              </p>
                            )}
                          </div>
                        ))
                      )}
                    </CardContent>
                  </Card>
                </div>


                {/* Personalized Improvement Plan (Growth Engine) */}
                <Card className="border-primary/20">
                  <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                      <CardTitle className="flex items-center gap-2 text-base">
                        <Sparkles className="h-5 w-5 text-primary" />
                        Personalized Improvement Plan
                      </CardTitle>
                      <CardDescription>
                        Concrete, prioritized practice tasks targeting identified gaps for {jobReadiness.job_title}.
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-3">
                      {improvementPlan && (
                        <div className="flex items-center gap-2 text-xs font-semibold">
                          <span className="text-muted-foreground">Progress:</span>
                          <span className="text-primary">{improvementPlan.progress_percentage}%</span>
                          <span className="text-muted-foreground">
                            ({improvementPlan.completed_actions}/{improvementPlan.total_actions})
                          </span>
                        </div>
                      )}
                      <Button
                        size="sm"
                        variant={improvementPlan ? 'outline' : 'default'}
                        onClick={handleGeneratePlan}
                        disabled={generatingPlan}
                        className="gap-1.5"
                      >
                        <RefreshCw className={`h-3.5 w-3.5 ${generatingPlan ? 'animate-spin' : ''}`} />
                        {improvementPlan ? 'Regenerate Plan' : 'Generate Improvement Plan'}
                      </Button>
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-4">
                    {!improvementPlan || improvementPlan.actions.length === 0 ? (
                      <div className="text-center py-8 space-y-3 bg-muted/20 rounded-xl border border-dashed">
                        <Sparkles className="h-8 w-8 text-primary mx-auto opacity-70" />
                        <div className="space-y-1">
                          <p className="text-sm font-semibold">No Active Improvement Plan Generated</p>
                          <p className="text-xs text-muted-foreground max-w-md mx-auto">
                            Click &quot;Generate Improvement Plan&quot; to transform skill and evidence gaps into prioritized practice actions.
                          </p>
                        </div>
                        <Button size="sm" onClick={handleGeneratePlan} disabled={generatingPlan}>
                          Generate Plan Now
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {improvementPlan.actions.map((act) => {
                          const isCompleted = act.status === 'COMPLETED';
                          const isInProgress = act.status === 'IN_PROGRESS';
                          const priorityColor =
                            act.priority === 'HIGH'
                              ? 'bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-200'
                              : act.priority === 'MEDIUM'
                              ? 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-200'
                              : 'bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-200';

                          return (
                            <div
                              key={act.id}
                              className={`p-4 rounded-xl border transition-all ${
                                isCompleted
                                  ? 'bg-muted/30 border-muted opacity-80'
                                  : 'bg-card border-border hover:border-primary/40'
                              }`}
                            >
                              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-2">
                                <div className="space-y-1">
                                  <div className="flex flex-wrap items-center gap-2">
                                    <span
                                      className={`font-semibold text-sm ${
                                        isCompleted ? 'line-through text-muted-foreground' : 'text-foreground'
                                      }`}
                                    >
                                      {act.skill_name}
                                    </span>
                                    <Badge variant="outline" className={`text-[10px] ${priorityColor}`}>
                                      {act.priority} Priority
                                    </Badge>
                                    <Badge variant="secondary" className="text-[10px]">
                                      Target: {act.target_proficiency}
                                    </Badge>
                                  </div>
                                  <p className="text-xs text-muted-foreground italic">{act.reason}</p>
                                </div>

                                <Button
                                  size="sm"
                                  variant={isCompleted ? 'secondary' : isInProgress ? 'default' : 'outline'}
                                  onClick={() => handleToggleActionStatus(act.id, act.status)}
                                  disabled={updatingActionId === act.id}
                                  className="h-8 gap-1.5 self-start sm:self-auto shrink-0 text-xs"
                                >
                                  {isCompleted ? (
                                    <>
                                      <CheckCircle className="h-3.5 w-3.5 text-emerald-500" />
                                      Completed
                                    </>
                                  ) : isInProgress ? (
                                    <>
                                      <Clock className="h-3.5 w-3.5 animate-pulse" />
                                      In Progress
                                    </>
                                  ) : (
                                    <>
                                      <Circle className="h-3.5 w-3.5 text-muted-foreground" />
                                      Start Action
                                    </>
                                  )}
                                </Button>
                              </div>

                              <div className="grid gap-2 sm:grid-cols-2 text-xs pt-2 border-t mt-3">
                                <div className="space-y-0.5">
                                  <span className="font-semibold text-foreground">Suggested Activity:</span>
                                  <p className="text-muted-foreground leading-relaxed">{act.suggested_activity}</p>
                                </div>
                                <div className="space-y-0.5">
                                  <span className="font-semibold text-foreground">Completion Criteria:</span>
                                  <p className="text-muted-foreground leading-relaxed">{act.completion_criteria}</p>
                                </div>
                              </div>

                              {act.evidence_reference && (
                                <div className="text-[11px] text-muted-foreground pt-2 border-t mt-2 flex items-center gap-1.5 font-mono">
                                  <CheckCircle className="h-3 w-3 text-emerald-500 shrink-0" />
                                  <span>Recorded Evidence: {act.evidence_reference} ({act.evidence_source})</span>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* AI Career Mentor Strategy Connection */}
                <Card className="border-primary/30 bg-gradient-to-br from-primary/5 via-card to-card">
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <Bot className="h-5 w-5 text-primary" />
                      Consult AI Mentor on this Job & Plan
                    </CardTitle>
                    <CardDescription>
                      Get contextual strategy advice on how to tackle these improvement actions for {jobReadiness.job_title}.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex gap-2">
                      <Input
                        placeholder="e.g., Which of these actions should I focus on first for my upcoming interview?"
                        value={mentorQuery}
                        onChange={(e) => setMentorQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleAskJobMentor()}
                        className="text-sm"
                      />
                      <Button
                        onClick={handleAskJobMentor}
                        disabled={loadingMentorAdvice}
                        className="gap-1.5 shrink-0"
                      >
                        <Send className="h-4 w-4" />
                        {loadingMentorAdvice ? 'Analyzing...' : 'Ask Mentor'}
                      </Button>
                    </div>

                    {mentorAdvice && (
                      <div className="p-4 rounded-xl border bg-card space-y-3">
                        <div className="flex items-center justify-between text-xs text-muted-foreground border-b pb-2">
                          <span className="font-medium text-foreground">
                            Guidance for {mentorAdvice.grounded_job_title} at {mentorAdvice.grounded_company}
                          </span>
                          <Badge variant="outline" className="text-[10px]">
                            Model: {mentorAdvice.model_used}
                          </Badge>
                        </div>
                        <p className="text-sm leading-relaxed text-foreground whitespace-pre-wrap">
                          {mentorAdvice.advice}
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card>
                <CardContent className="py-12 text-center text-sm text-muted-foreground">
                  Select a job above to view readiness diagnostic and generate an improvement plan.
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* TAB 2: Campus-Wide Overview (Existing General Placement Readiness) */}
          <TabsContent value="campus-overview" className="space-y-6">
            {loadingGeneral ? (
              <div className="space-y-4">
                <Skeleton className="h-44 w-full rounded-xl" />
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  {[1, 2, 3, 4].map((i) => (
                    <Skeleton key={i} className="h-36 rounded-xl" />
                  ))}
                </div>
              </div>
            ) : readiness ? (
              <>
                {/* Overall Score Banner */}
                <Card className="bg-gradient-to-r from-primary/5 via-primary/10 to-transparent border-primary/20">
                  <CardContent className="p-6">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className={CATEGORY_COLORS[readiness.status_category] || ''}>
                            {readiness.status_category}
                          </Badge>
                          {readiness.is_placed && (
                            <Badge
                              variant="outline"
                              className="bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-300"
                            >
                              <Award className="mr-1 h-3.5 w-3.5" />
                              Placed
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-baseline gap-2">
                          <span className="text-4xl font-extrabold tracking-tight">
                            {readiness.readiness_score}
                          </span>
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
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
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

                {/* Market Skill Gap Analysis */}
                {skillGaps && (
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0">
                      <div>
                        <CardTitle className="flex items-center gap-2">
                          <TrendingUp className="h-5 w-5 text-primary" />
                          Campus-Wide Market Skill Gaps
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
              </>
            ) : null}
          </TabsContent>
        </Tabs>
      </PageContainer>
    </AppLayout>
  );
}
