import { useState, useEffect, useCallback } from 'react';
import {
  Briefcase,
  MapPin,
  Search,
  Building,
  GraduationCap,
  Award,
  Clock,
  CheckCircle2,
  XCircle,
  Banknote,
  Send,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { AxiosError } from 'axios';

import { AppLayout } from '@/components/layout/AppLayout';
import { PageHeader, PageContainer } from '@/components/common/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

import { useAuth } from '@/features/auth/context/AuthContext';
import { studentJobService, StudentJob } from '../services/job.service';
import { studentApplicationService } from '../services/application.service';
import { resumeService } from '../services/resume.service';
import { intelligenceService } from '../services/intelligence.service';
import { JobMatchResponse } from '../types/intelligence.types';
import { ResumeResponse } from '../types/api';
import { Progress } from '@/components/ui/progress';

export default function StudentJobsPage() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<StudentJob[]>([]);
  const [loading, setLoading] = useState(true);

  // Filter state
  const [search, setSearch] = useState('');
  const [companyFilter, setCompanyFilter] = useState<string>('all');
  const [employmentTypeFilter, setEmploymentTypeFilter] = useState<string>('all');
  const [eligibleOnly, setEligibleOnly] = useState(false);

  // Dialog state
  const [selectedJob, setSelectedJob] = useState<StudentJob | null>(null);
  const [jobMatch, setJobMatch] = useState<JobMatchResponse | null>(null);

  useEffect(() => {
    if (selectedJob) {
      intelligenceService.getJobMatch(selectedJob.id)
        .then(setJobMatch)
        .catch(() => setJobMatch(null));
    } else {
      setJobMatch(null);
    }
  }, [selectedJob]);

  // Application state
  const [resumes, setResumes] = useState<ResumeResponse[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<string>('');
  const [isApplying, setIsApplying] = useState(false);
  const [showApplyForm, setShowApplyForm] = useState(false);

  const fetchResumes = useCallback(async () => {
    try {
      const data = await resumeService.getResumes();
      setResumes(data);
      const defaultResume = data.find((r) => r.is_default);
      if (defaultResume) {
        setSelectedResumeId(defaultResume.id.toString());
      } else if (data.length > 0) {
        setSelectedResumeId(data[0].id.toString());
      }
    } catch (err) {
      console.error('Failed to fetch resumes', err);
    }
  }, []);

  useEffect(() => {
    fetchResumes();
  }, [fetchResumes]);

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    try {
      const companyIdNum = companyFilter !== 'all' ? parseInt(companyFilter, 10) : undefined;
      const empType = employmentTypeFilter !== 'all' ? employmentTypeFilter : undefined;
      
      const data = await studentJobService.getJobs({
        search,
        company_id: companyIdNum,
        employment_type: empType,
        eligible_only: eligibleOnly,
      });
      setJobs(data);
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.detail || err.response?.data?.message
          : 'Failed to fetch jobs';
      toast.error(msg || 'Failed to fetch jobs');
    } finally {
      setLoading(false);
    }
  }, [search, companyFilter, employmentTypeFilter, eligibleOnly]);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  // Extract unique companies from jobs for the filter dropdown
  // A better approach would be fetching active companies from an endpoint, but this works for MVP
  const uniqueCompanies = Array.from(new Set(jobs.map(j => j.company.id))).map(id => {
    return jobs.find(j => j.company.id === id)!.company;
  });

  return (
    <AppLayout role="student" userName={user?.email || 'Student'} userRole="Student" avatarText="ST">
      <PageContainer>
        <PageHeader
          title="Job Discovery"
          description="Find and explore job opportunities that match your profile."
        />

        {/* Filters */}
        <Card className="mb-6 border-none bg-muted/40 shadow-none">
          <CardContent className="p-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by title, company, role..."
                  className="pl-9 bg-background"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>

              <Select value={companyFilter} onValueChange={setCompanyFilter}>
                <SelectTrigger className="bg-background">
                  <SelectValue placeholder="Filter by Company" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Companies</SelectItem>
                  {uniqueCompanies.map((c) => (
                    <SelectItem key={c.id} value={c.id.toString()}>
                      {c.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={employmentTypeFilter} onValueChange={setEmploymentTypeFilter}>
                <SelectTrigger className="bg-background">
                  <SelectValue placeholder="Employment Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="Full-time">Full-time</SelectItem>
                  <SelectItem value="Part-time">Part-time</SelectItem>
                  <SelectItem value="Contract">Contract</SelectItem>
                  <SelectItem value="Internship">Internship</SelectItem>
                </SelectContent>
              </Select>

              <div className="flex items-center space-x-2">
                <Button
                  variant={eligibleOnly ? "default" : "outline"}
                  className="w-full"
                  onClick={() => setEligibleOnly(!eligibleOnly)}
                >
                  {eligibleOnly ? (
                    <><CheckCircle2 className="mr-2 h-4 w-4" /> Eligible Only</>
                  ) : (
                    "Show All Jobs"
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center p-8">
            <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-primary"></div>
          </div>
        )}

        {/* Empty State */}
        {!loading && jobs.length === 0 && (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12 text-center">
              <Briefcase className="h-12 w-12 text-muted-foreground mb-4 opacity-50" />
              <p className="text-lg font-medium">No jobs found</p>
              <p className="text-sm text-muted-foreground mt-1 max-w-sm">
                Try adjusting your search or filter criteria to find more opportunities.
              </p>
              {(search || companyFilter !== 'all' || employmentTypeFilter !== 'all' || eligibleOnly) && (
                <Button
                  variant="outline"
                  className="mt-4"
                  onClick={() => {
                    setSearch('');
                    setCompanyFilter('all');
                    setEmploymentTypeFilter('all');
                    setEligibleOnly(false);
                  }}
                >
                  Clear all filters
                </Button>
              )}
            </CardContent>
          </Card>
        )}

        {/* Job Grid */}
        {!loading && jobs.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {jobs.map((job) => (
              <Card 
                key={job.id} 
                className="group cursor-pointer hover:border-primary/50 transition-colors focus-within:ring-2 focus-within:ring-ring"
                onClick={() => setSelectedJob(job)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setSelectedJob(job);
                  }
                }}
              >
                <CardHeader className="pb-3">
                  <div className="flex justify-between items-start gap-4">
                    <div>
                      <CardTitle className="text-base line-clamp-1 group-hover:text-primary transition-colors">
                        {job.title}
                      </CardTitle>
                      <div className="flex items-center gap-1.5 mt-1 text-sm text-muted-foreground">
                        <Building className="h-3.5 w-3.5 shrink-0" />
                        <span className="truncate">{job.company.name}</span>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                      {job.location && (
                        <div className="flex items-center gap-1 bg-muted/50 px-2 py-1 rounded-md">
                          <MapPin className="h-3 w-3" />
                          {job.location}
                        </div>
                      )}
                      <div className="flex items-center gap-1 bg-muted/50 px-2 py-1 rounded-md">
                        <Briefcase className="h-3 w-3" />
                        {job.employment_type}
                      </div>
                      {job.ctc_lpa && (
                        <div className="flex items-center gap-1 bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 px-2 py-1 rounded-md">
                          <Banknote className="h-3 w-3" />
                          {job.ctc_lpa} LPA
                        </div>
                      )}
                    </div>
                    
                    {/* Eligibility Badge Preview */}
                    <div className="pt-2 border-t">
                      {job.is_fully_eligible ? (
                        <div className="flex items-center gap-1.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                          <CheckCircle2 className="h-4 w-4" />
                          Eligible
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5 text-xs font-medium text-amber-600 dark:text-amber-400">
                          <XCircle className="h-4 w-4" />
                          Not Eligible
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Job Detail Dialog */}
        <Dialog open={!!selectedJob} onOpenChange={(open) => !open && setSelectedJob(null)}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            {selectedJob && (
              <>
                <DialogHeader>
                  <DialogTitle className="text-xl leading-tight">
                    {selectedJob.title}
                  </DialogTitle>
                  <DialogDescription className="flex items-center gap-2 mt-1.5 text-base">
                    <Building className="h-4 w-4" />
                    {selectedJob.company.name}
                  </DialogDescription>
                </DialogHeader>

                <div className="space-y-6 py-4">
                  {/* Quick Info Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 bg-muted/30 rounded-lg border">
                    <div className="space-y-1">
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <MapPin className="h-3 w-3" /> Location
                      </span>
                      <p className="text-sm font-medium">{selectedJob.location || 'Not specified'}</p>
                    </div>
                    <div className="space-y-1">
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Briefcase className="h-3 w-3" /> Type
                      </span>
                      <p className="text-sm font-medium">{selectedJob.employment_type}</p>
                    </div>
                    <div className="space-y-1">
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Banknote className="h-3 w-3" /> Salary (CTC)
                      </span>
                      <p className="text-sm font-medium">{selectedJob.ctc_lpa ? `${selectedJob.ctc_lpa} LPA` : 'Not specified'}</p>
                    </div>
                    <div className="space-y-1">
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3" /> Deadline
                      </span>
                      <p className="text-sm font-medium">
                        {selectedJob.deadline 
                          ? new Date(selectedJob.deadline).toLocaleDateString() 
                          : 'No deadline'}
                      </p>
                    </div>
                  </div>

                  {/* Eligibility Section */}
                  <div className="space-y-3">
                    <h3 className="text-sm font-semibold flex items-center gap-2">
                      <Award className="h-4 w-4 text-primary" />
                      Your Eligibility
                    </h3>
                    <div className="space-y-2 p-4 rounded-lg border bg-card">
                      <div className="flex items-start gap-3">
                        {selectedJob.is_department_eligible ? (
                          <CheckCircle2 className="h-5 w-5 text-emerald-500 mt-0.5 shrink-0" />
                        ) : (
                          <XCircle className="h-5 w-5 text-destructive mt-0.5 shrink-0" />
                        )}
                        <div>
                          <p className="text-sm font-medium">
                            {selectedJob.is_department_eligible ? 'Department Eligible' : 'Department Not Eligible'}
                          </p>
                          <p className="text-xs text-muted-foreground mt-0.5">
                            {selectedJob.eligible_departments.length === 0 
                              ? '✓ Open to all departments' 
                              : `This job is limited to: ${selectedJob.eligible_departments.map(d => d.department_name).join(', ')}`}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-start gap-3 mt-4">
                        {selectedJob.is_cgpa_eligible ? (
                          <CheckCircle2 className="h-5 w-5 text-emerald-500 mt-0.5 shrink-0" />
                        ) : (
                          <XCircle className="h-5 w-5 text-destructive mt-0.5 shrink-0" />
                        )}
                        <div>
                          <p className="text-sm font-medium">
                            {selectedJob.is_cgpa_eligible ? 'CGPA Requirement Met' : 'CGPA Requirement Not Met'}
                          </p>
                          <p className="text-xs text-muted-foreground mt-0.5">
                            {selectedJob.min_cgpa === null 
                              ? '✓ No minimum CGPA requirement' 
                              : `Required: ${selectedJob.min_cgpa}`}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Description */}
                  {selectedJob.description && (
                    <div className="space-y-2">
                      <h3 className="text-sm font-semibold">Description</h3>
                      <div className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
                        {selectedJob.description}
                      </div>
                    </div>
                  )}

                  {/* Skill Match Intelligence Section */}
                  {jobMatch && (
                    <div className="space-y-3 pt-2">
                      <div className="flex items-center justify-between">
                        <h3 className="text-sm font-semibold flex items-center gap-2">
                          <GraduationCap className="h-4 w-4 text-primary" />
                          Skill Match Analysis
                        </h3>
                        <Badge variant="outline" className="font-semibold text-xs bg-primary/5 text-primary border-primary/20">
                          {jobMatch.skill_match_percentage}% Match
                        </Badge>
                      </div>
                      
                      <div className="p-4 rounded-lg border bg-card space-y-3">
                        <div className="space-y-1">
                          <div className="flex justify-between text-xs font-semibold text-muted-foreground">
                            <span>Match Ratio</span>
                            <span>{jobMatch.skill_match_percentage}%</span>
                          </div>
                          <Progress value={jobMatch.skill_match_percentage} className="h-2" />
                          <p className="text-xs text-muted-foreground mt-1">{jobMatch.skill_match_explanation}</p>
                        </div>

                        {jobMatch.total_required_skills > 0 && (
                          <div className="space-y-2 pt-2 border-t">
                            {jobMatch.strong_matches.length > 0 && (
                              <div>
                                <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">Strong Matches:</span>
                                <div className="flex flex-wrap gap-1.5 mt-1">
                                  {jobMatch.strong_matches.map(s => (
                                    <Badge key={s.skill_id} variant="outline" className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-200 text-xs">
                                      ✓ {s.skill_name} ({s.student_proficiency})
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}

                            {jobMatch.matched_skills.length > 0 && (
                              <div>
                                <span className="text-xs font-semibold text-blue-600 dark:text-blue-400">Exact Matches:</span>
                                <div className="flex flex-wrap gap-1.5 mt-1">
                                  {jobMatch.matched_skills.map(s => (
                                    <Badge key={s.skill_id} variant="outline" className="bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-200 text-xs">
                                      ✓ {s.skill_name} ({s.student_proficiency})
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}

                            {jobMatch.insufficient_proficiency.length > 0 && (
                              <div>
                                <span className="text-xs font-semibold text-amber-600 dark:text-amber-400">Needs Higher Proficiency:</span>
                                <div className="flex flex-wrap gap-1.5 mt-1">
                                  {jobMatch.insufficient_proficiency.map(s => (
                                    <Badge key={s.skill_id} variant="outline" className="bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-200 text-xs">
                                      ! {s.skill_name} (Have {s.student_proficiency}, Need {s.min_proficiency})
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}

                            {jobMatch.missing_skills.length > 0 && (
                              <div>
                                <span className="text-xs font-semibold text-red-600 dark:text-red-400">Missing Skills:</span>
                                <div className="flex flex-wrap gap-1.5 mt-1">
                                  {jobMatch.missing_skills.map(s => (
                                    <Badge key={s.skill_id} variant="outline" className="bg-red-500/10 text-red-700 dark:text-red-400 border-red-200 text-xs">
                                      ✕ {s.skill_name} (Need {s.min_proficiency})
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Skills */}
                  {selectedJob.required_skills.length > 0 && !jobMatch && (
                    <div className="space-y-2">
                      <h3 className="text-sm font-semibold flex items-center gap-2">
                        <GraduationCap className="h-4 w-4" />
                        Required Skills
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {selectedJob.required_skills.map((skill) => (
                          <Badge key={skill.id} variant="secondary" className="font-normal">
                            {skill.skill_name}
                            {skill.min_proficiency && (
                              <span className="ml-1 text-muted-foreground">
                                ({skill.min_proficiency})
                              </span>
                            )}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex justify-end pt-4 border-t mt-4 gap-2">
                  {!showApplyForm ? (
                    <Button 
                      className="w-full sm:w-auto" 
                      disabled={!selectedJob.is_fully_eligible}
                      onClick={() => setShowApplyForm(true)}
                    >
                      <Send className="h-4 w-4 mr-2" />
                      Apply for Job
                    </Button>
                  ) : (
                    <div className="flex flex-col sm:flex-row items-end gap-2 w-full sm:w-auto">
                      <div className="w-full sm:w-64">
                        <Select value={selectedResumeId} onValueChange={setSelectedResumeId}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select Resume" />
                          </SelectTrigger>
                          <SelectContent>
                            {resumes.map((r: ResumeResponse) => (
                              <SelectItem key={r.id} value={r.id.toString()}>
                                {r.title} {r.is_default && '(Default)'}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="flex gap-2 w-full sm:w-auto mt-2 sm:mt-0">
                        <Button 
                          variant="outline" 
                          onClick={() => setShowApplyForm(false)}
                          disabled={isApplying}
                        >
                          Cancel
                        </Button>
                        <Button 
                          onClick={async () => {
                            if (!selectedResumeId) {
                              toast.error('Please select a resume');
                              return;
                            }
                            setIsApplying(true);
                            try {
                              await studentApplicationService.submitApplication({
                                job_id: selectedJob.id,
                                resume_id: parseInt(selectedResumeId, 10),
                              });
                              toast.success('Successfully applied for the job!');
                              setSelectedJob(null);
                              setShowApplyForm(false);
                            } catch (err: unknown) {
                              const msg = err instanceof AxiosError 
                                ? err.response?.data?.detail || err.response?.data?.message 
                                : 'Failed to apply';
                              toast.error(msg || 'Failed to apply');
                            } finally {
                              setIsApplying(false);
                            }
                          }}
                          disabled={isApplying || !selectedResumeId}
                        >
                          {isApplying ? 'Submitting...' : 'Confirm Apply'}
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
          </DialogContent>
        </Dialog>

      </PageContainer>
    </AppLayout>
  );
}
