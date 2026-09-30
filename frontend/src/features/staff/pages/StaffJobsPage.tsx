import { useState, useEffect, useCallback } from 'react';
import {
  Briefcase,
  Plus,
  Search,
  Pencil,
  Power,
  RefreshCw,
  Eye,
  MapPin,
  Calendar,
  Building,
  GraduationCap,
  Award,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Trash2,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { AxiosError } from 'axios';

import { AppLayout } from '@/components/layout/AppLayout';
import { PageHeader, PageContainer } from '@/components/common/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

import { useAuth } from '@/features/auth/context/AuthContext';
import {
  jobService,
  JobListItem,
  JobDetail,
  JobStatusFilter,
} from '../services/job.service';
import { companyService, Company } from '../services/company.service';
import { departmentService, Department } from '../services/department.service';
import { staffSkillService, StaffSkill } from '../services/staff-skills.service';
import { JobRecruitmentWorkflowEditor } from '../components/JobRecruitmentWorkflowEditor';

interface RequiredSkillFormItem {
  skill_id: number;
  min_proficiency?: 'beginner' | 'intermediate' | 'advanced' | null;
}

export default function StaffJobsPage() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Master Data state for filters and dropdowns
  const [companies, setCompanies] = useState<Company[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [skills, setSkills] = useState<StaffSkill[]>([]);

  // Filter state
  const [search, setSearch] = useState('');
  const [companyFilter, setCompanyFilter] = useState<string>('all');
  const [departmentFilter, setDepartmentFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<JobStatusFilter>('all');

  // Modal states
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [isStatusOpen, setIsStatusOpen] = useState(false);

  // Selected entities
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [jobDetail, setJobDetail] = useState<JobDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Create Form state
  const [createCompanyId, setCreateCompanyId] = useState<string>('');
  const [createTitle, setCreateTitle] = useState('');
  const [createRoleCategory, setCreateRoleCategory] = useState('');
  const [createDescription, setCreateDescription] = useState('');
  const [createLocation, setCreateLocation] = useState('');
  const [createEmploymentType, setCreateEmploymentType] = useState('Full-time');
  const [createCtc, setCreateCtc] = useState('');
  const [createMinCgpa, setCreateMinCgpa] = useState('');
  const [createDeadline, setCreateDeadline] = useState('');
  const [createEligibleDepts, setCreateEligibleDepts] = useState<number[]>([]);
  const [createSkills, setCreateSkills] = useState<RequiredSkillFormItem[]>([]);
  const [isSubmittingCreate, setIsSubmittingCreate] = useState(false);

  // Edit Form state
  const [editCompanyId, setEditCompanyId] = useState<string>('');
  const [editTitle, setEditTitle] = useState('');
  const [editRoleCategory, setEditRoleCategory] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editLocation, setEditLocation] = useState('');
  const [editEmploymentType, setEditEmploymentType] = useState('Full-time');
  const [editCtc, setEditCtc] = useState('');
  const [editMinCgpa, setEditMinCgpa] = useState('');
  const [editDeadline, setEditDeadline] = useState('');
  const [editEligibleDepts, setEditEligibleDepts] = useState<number[]>([]);
  const [editSkills, setEditSkills] = useState<RequiredSkillFormItem[]>([]);
  const [isSubmittingEdit, setIsSubmittingEdit] = useState(false);

  // Status Toggle state
  const [toggleJob, setToggleJob] = useState<JobListItem | null>(null);
  const [isSubmittingStatus, setIsSubmittingStatus] = useState(false);

  // Fetch Jobs list
  const fetchJobs = useCallback(async () => {
    setLoading(true);
    try {
      const companyIdNum = companyFilter !== 'all' ? parseInt(companyFilter, 10) : undefined;
      const deptIdNum = departmentFilter !== 'all' ? parseInt(departmentFilter, 10) : undefined;
      const data = await jobService.getStaffJobs(search, companyIdNum, deptIdNum, statusFilter);
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
  }, [search, companyFilter, departmentFilter, statusFilter]);

  // Load master data once on mount
  useEffect(() => {
    const loadMasterData = async () => {
      try {
        const [compData, deptData, skillData] = await Promise.all([
          companyService.getStaffCompanies(),
          departmentService.getStaffDepartments(),
          staffSkillService.getStaffSkills(),
        ]);
        setCompanies(compData);
        setDepartments(deptData);
        setSkills(skillData);
      } catch (err: unknown) {
        console.error('Failed to load master data for jobs filter:', err);
      }
    };
    loadMasterData();
  }, []);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  // Handlers for View Detail
  const handleViewDetail = async (jobId: number) => {
    setSelectedJobId(jobId);
    setIsDetailOpen(true);
    setLoadingDetail(true);
    try {
      const detail = await jobService.getJobDetail(jobId);
      setJobDetail(detail);
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.detail || err.response?.data?.message
          : 'Failed to load job details';
      toast.error(msg || 'Failed to load job details');
      setIsDetailOpen(false);
    } finally {
      setLoadingDetail(false);
    }
  };

  // Open Create Dialog
  const handleOpenCreate = () => {
    setCreateCompanyId('');
    setCreateTitle('');
    setCreateRoleCategory('');
    setCreateDescription('');
    setCreateLocation('');
    setCreateEmploymentType('Full-time');
    setCreateCtc('');
    setCreateMinCgpa('');
    setCreateDeadline('');
    setCreateEligibleDepts([]);
    setCreateSkills([]);
    setIsCreateOpen(true);
  };

  // Create Submit
  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createCompanyId) {
      toast.error('Please select a company');
      return;
    }
    if (!createTitle.trim()) {
      toast.error('Job title is required');
      return;
    }

    setIsSubmittingCreate(true);
    try {
      await jobService.createJob({
        company_id: parseInt(createCompanyId, 10),
        title: createTitle.trim(),
        role_category: createRoleCategory.trim() || undefined,
        description: createDescription.trim() || undefined,
        location: createLocation.trim() || undefined,
        employment_type: createEmploymentType.trim() || 'Full-time',
        ctc_lpa: createCtc !== '' ? parseFloat(createCtc) : undefined,
        min_cgpa: createMinCgpa !== '' ? parseFloat(createMinCgpa) : undefined,
        deadline: createDeadline ? new Date(createDeadline).toISOString() : undefined,
        eligible_department_ids: createEligibleDepts,
        required_skills: createSkills.map((s) => ({
          skill_id: s.skill_id,
          min_proficiency: s.min_proficiency || undefined,
        })),
      });

      toast.success('Job posting created successfully!');
      setIsCreateOpen(false);
      fetchJobs();
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.detail || err.response?.data?.message
          : 'Failed to create job';
      toast.error(msg || 'Failed to create job');
    } finally {
      setIsSubmittingCreate(false);
    }
  };

  // Open Edit Dialog
  const handleOpenEdit = async (job: JobListItem) => {
    setSelectedJobId(job.id);
    setIsEditOpen(true);
    try {
      const detail = await jobService.getJobDetail(job.id);
      setEditCompanyId(detail.company_id.toString());
      setEditTitle(detail.title);
      setEditRoleCategory(detail.role_category || '');
      setEditDescription(detail.description || '');
      setEditLocation(detail.location || '');
      setEditEmploymentType(detail.employment_type || 'Full-time');
      setEditCtc(detail.ctc_lpa !== null && detail.ctc_lpa !== undefined ? detail.ctc_lpa.toString() : '');
      setEditMinCgpa(detail.min_cgpa !== null && detail.min_cgpa !== undefined ? detail.min_cgpa.toString() : '');
      
      if (detail.deadline) {
        const d = new Date(detail.deadline);
        const isoLocal = new Date(d.getTime() - d.getTimezoneOffset() * 60000)
          .toISOString()
          .slice(0, 16);
        setEditDeadline(isoLocal);
      } else {
        setEditDeadline('');
      }

      setEditEligibleDepts(detail.eligible_departments.map((d) => d.department_id));
      setEditSkills(
        detail.required_skills.map((s) => ({
          skill_id: s.skill_id,
          min_proficiency: s.min_proficiency || null,
        }))
      );
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.detail || err.response?.data?.message
          : 'Failed to load job for editing';
      toast.error(msg || 'Failed to load job for editing');
      setIsEditOpen(false);
    }
  };

  // Edit Submit
  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedJobId) return;
    if (!editCompanyId) {
      toast.error('Please select a company');
      return;
    }
    if (!editTitle.trim()) {
      toast.error('Job title is required');
      return;
    }

    setIsSubmittingEdit(true);
    try {
      await jobService.updateJob(selectedJobId, {
        company_id: parseInt(editCompanyId, 10),
        title: editTitle.trim(),
        role_category: editRoleCategory.trim() || undefined,
        description: editDescription.trim() || undefined,
        location: editLocation.trim() || undefined,
        employment_type: editEmploymentType.trim() || 'Full-time',
        ctc_lpa: editCtc !== '' ? parseFloat(editCtc) : undefined,
        min_cgpa: editMinCgpa !== '' ? parseFloat(editMinCgpa) : undefined,
        deadline: editDeadline ? new Date(editDeadline).toISOString() : null,
        eligible_department_ids: editEligibleDepts,
        required_skills: editSkills.map((s) => ({
          skill_id: s.skill_id,
          min_proficiency: s.min_proficiency || undefined,
        })),
      });

      toast.success('Job posting updated successfully!');
      setIsEditOpen(false);
      fetchJobs();
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.detail || err.response?.data?.message
          : 'Failed to update job';
      toast.error(msg || 'Failed to update job');
    } finally {
      setIsSubmittingEdit(false);
    }
  };

  // Open Status Confirmation
  const handleOpenStatus = (job: JobListItem) => {
    setToggleJob(job);
    setIsStatusOpen(true);
  };

  // Confirm Status Toggle
  const handleConfirmStatusToggle = async () => {
    if (!toggleJob) return;
    setIsSubmittingStatus(true);
    try {
      const updated = await jobService.updateJobStatus(toggleJob.id, !toggleJob.is_active);
      toast.success(
        `Job "${updated.title}" ${updated.is_active ? 'activated' : 'deactivated'} successfully`
      );
      setIsStatusOpen(false);
      setToggleJob(null);
      fetchJobs();
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.detail || err.response?.data?.message
          : 'Failed to update job status';
      toast.error(msg || 'Failed to update job status');
    } finally {
      setIsSubmittingStatus(false);
    }
  };

  // Helper functions for skill management in form
  const addSkillRow = (skillsList: RequiredSkillFormItem[], setSkillsList: (s: RequiredSkillFormItem[]) => void) => {
    const availableSkills = skills.filter((s) => s.is_active && !skillsList.some((item) => item.skill_id === s.id));
    if (availableSkills.length === 0) {
      toast.error('No additional active skills available to add');
      return;
    }
    setSkillsList([...skillsList, { skill_id: availableSkills[0].id, min_proficiency: null }]);
  };

  const removeSkillRow = (
    index: number,
    skillsList: RequiredSkillFormItem[],
    setSkillsList: (s: RequiredSkillFormItem[]) => void
  ) => {
    const updated = [...skillsList];
    updated.splice(index, 1);
    setSkillsList(updated);
  };

  const updateSkillRow = (
    index: number,
    field: keyof RequiredSkillFormItem,
    val: number | 'beginner' | 'intermediate' | 'advanced' | null,
    skillsList: RequiredSkillFormItem[],
    setSkillsList: (s: RequiredSkillFormItem[]) => void
  ) => {
    const updated = [...skillsList];
    updated[index] = { ...updated[index], [field]: val };
    setSkillsList(updated);
  };

  // Helper function for department selection in form
  const toggleDeptSelection = (
    deptId: number,
    deptList: number[],
    setDeptList: (d: number[]) => void
  ) => {
    if (deptList.includes(deptId)) {
      setDeptList(deptList.filter((id) => id !== deptId));
    } else {
      setDeptList([...deptList, deptId]);
    }
  };

  // Utility date formatter
  const formatDate = (dateStr?: string | null) => {
    if (!dateStr) return 'No deadline';
    const date = new Date(dateStr);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  // Helper to determine derived status badge
  const renderStatusBadge = (job: { is_active: boolean; deadline?: string | null }) => {
    const now = new Date();
    const isExpired = job.deadline ? new Date(job.deadline) < now : false;

    if (!job.is_active) {
      return (
        <Badge variant="secondary" className="bg-muted text-muted-foreground border-border font-medium">
          <XCircle className="w-3 h-3 mr-1" /> Inactive
        </Badge>
      );
    }
    if (isExpired) {
      return (
        <Badge variant="outline" className="bg-amber-500/15 text-amber-600 dark:text-amber-400 hover:bg-amber-500/25 border-amber-500/30 font-medium">
          <Clock className="w-3 h-3 mr-1" /> Expired
        </Badge>
      );
    }
    return (
      <Badge variant="default" className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/25 border-emerald-500/30 font-medium">
        <CheckCircle2 className="w-3 h-3 mr-1" /> Active
      </Badge>
    );
  };

  const userEmail = user?.email || 'Staff Member';
  const avatarText = userEmail.substring(0, 2).toUpperCase();

  return (
    <AppLayout role="staff" userName={userEmail} userRole="Staff" avatarText={avatarText}>
      <PageContainer>
        <PageHeader
          title="Job Postings & Recruitment Drives"
          description="Manage job opportunities and placement drives across partner companies."
          action={
            <Button onClick={handleOpenCreate} className="gap-2">
              <Plus className="h-4 w-4" />
              Post New Job
            </Button>
          }
        />

        {/* Filter Bar */}
        <Card className="mb-6">
          <CardContent className="pt-6 flex flex-col md:flex-row gap-4 justify-between items-center">
            <div className="relative w-full md:w-80">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search title, company, location..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>

            <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
              {/* Company Filter */}
              <div className="w-full md:w-44">
                <Select value={companyFilter} onValueChange={setCompanyFilter}>
                  <SelectTrigger className="h-9 text-xs">
                    <SelectValue placeholder="All Companies" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Companies</SelectItem>
                    {companies.map((c) => (
                      <SelectItem key={c.id} value={c.id.toString()}>
                        {c.name} {!c.is_active ? '(Inactive)' : ''}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Department Filter */}
              <div className="w-full md:w-44">
                <Select value={departmentFilter} onValueChange={setDepartmentFilter}>
                  <SelectTrigger className="h-9 text-xs">
                    <SelectValue placeholder="All Departments" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Departments</SelectItem>
                    {departments.map((d) => (
                      <SelectItem key={d.id} value={d.id.toString()}>
                        {d.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Status Filter Tab Switcher */}
              <div className="flex bg-muted p-1 rounded-lg">
                {(['all', 'active', 'inactive', 'expired'] as const).map((st) => (
                  <button
                    key={st}
                    type="button"
                    onClick={() => setStatusFilter(st)}
                    className={`px-3 py-1 text-xs font-medium rounded-md capitalize transition-colors ${
                      statusFilter === st
                        ? 'bg-background text-foreground shadow-sm'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>

              {/* Refresh Button */}
              <Button variant="ghost" size="icon" onClick={fetchJobs} title="Refresh Job Postings">
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Jobs Table */}
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-12 text-center text-muted-foreground">
                <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-primary" />
                Loading job postings...
              </div>
            ) : jobs.length === 0 ? (
              <div className="p-12 text-center text-muted-foreground">
                <Briefcase className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-base font-medium text-foreground">No job postings found</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Try adjusting your search criteria or create a new job posting.
                </p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Job Title & Company</TableHead>
                    <TableHead>Location & Type</TableHead>
                    <TableHead>CTC</TableHead>
                    <TableHead>Eligible Depts</TableHead>
                    <TableHead>Required Skills</TableHead>
                    <TableHead>Deadline</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jobs.map((job) => {
                    const now = new Date();
                    const isExpired = job.deadline ? new Date(job.deadline) < now : false;

                    return (
                      <TableRow key={job.id}>
                        {/* Title & Company */}
                        <TableCell>
                          <div>
                            <span className="font-medium text-foreground text-sm block">
                              {job.title}
                            </span>
                            <span className="text-xs text-muted-foreground flex items-center mt-0.5">
                              <Building className="w-3 h-3 mr-1 text-muted-foreground inline" />
                              {job.company?.name || 'Unknown Company'}
                              {!job.company?.is_active && (
                                <Badge
                                  variant="outline"
                                  className="ml-1 text-[10px] px-1 py-0 bg-muted text-muted-foreground border-border"
                                >
                                  Inactive Company
                                </Badge>
                              )}
                            </span>
                          </div>
                        </TableCell>

                        {/* Location & Employment Type */}
                        <TableCell>
                          <div className="text-sm">
                            {job.location ? (
                              <span className="flex items-center text-xs text-muted-foreground mb-1">
                                <MapPin className="w-3 h-3 mr-1 text-muted-foreground inline" />
                                {job.location}
                              </span>
                            ) : (
                              <span className="text-xs text-muted-foreground italic">Remote / Flexible</span>
                            )}
                            <Badge variant="secondary" className="text-[11px] font-normal">
                              {job.employment_type}
                            </Badge>
                          </div>
                        </TableCell>

                        {/* CTC */}
                        <TableCell>
                          <div className="text-sm">
                            {job.ctc_lpa !== null && job.ctc_lpa !== undefined ? (
                              <span className="font-medium text-emerald-600 dark:text-emerald-400">
                                ₹{job.ctc_lpa.toFixed(2)} LPA
                              </span>
                            ) : (
                              <span className="text-xs text-muted-foreground italic">Not specified</span>
                            )}
                          </div>
                        </TableCell>

                        {/* Eligible Departments */}
                        <TableCell>
                          <div className="flex flex-wrap gap-1 max-w-[200px]">
                            {job.eligible_departments && job.eligible_departments.length > 0 ? (
                              <>
                                {job.eligible_departments.slice(0, 2).map((d) => (
                                  <Badge
                                    key={d.id}
                                    variant="outline"
                                    className="text-[10px] bg-primary/10 text-primary border-primary/20"
                                  >
                                    {d.department?.code || d.department?.name || d.department_name}
                                  </Badge>
                                ))}
                                {job.eligible_departments.length > 2 && (
                                  <Badge
                                    variant="outline"
                                    className="text-[10px] bg-muted text-muted-foreground border-border"
                                  >
                                    +{job.eligible_departments.length - 2} more
                                  </Badge>
                                )}
                              </>
                            ) : (
                              <span className="text-xs text-muted-foreground italic">All Depts</span>
                            )}
                          </div>
                        </TableCell>

                        {/* Required Skills */}
                        <TableCell>
                          <div className="flex flex-wrap gap-1 max-w-[200px]">
                            {job.required_skills && job.required_skills.length > 0 ? (
                              <>
                                {job.required_skills.slice(0, 2).map((s) => (
                                  <Badge
                                    key={s.id}
                                    variant="outline"
                                    className="text-[10px] bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20"
                                  >
                                    {s.skill?.name || s.skill_name}
                                  </Badge>
                                ))}
                                {job.required_skills.length > 2 && (
                                  <Badge
                                    variant="outline"
                                    className="text-[10px] bg-muted text-muted-foreground border-border"
                                  >
                                    +{job.required_skills.length - 2} more
                                  </Badge>
                                )}
                              </>
                            ) : (
                              <span className="text-xs text-muted-foreground italic">None specified</span>
                            )}
                          </div>
                        </TableCell>

                        {/* Deadline */}
                        <TableCell>
                          <div className="text-xs text-muted-foreground">
                            {job.deadline ? (
                              <span
                                className={`flex items-center ${
                                  isExpired ? 'text-amber-600 dark:text-amber-400 font-medium' : 'text-foreground'
                                }`}
                              >
                                <Calendar className="w-3 h-3 mr-1 text-muted-foreground inline" />
                                {formatDate(job.deadline)}
                              </span>
                            ) : (
                              <span className="text-muted-foreground italic">No deadline</span>
                            )}
                          </div>
                        </TableCell>

                        {/* Status */}
                        <TableCell>{renderStatusBadge(job)}</TableCell>

                        {/* Actions */}
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-1">
                            {/* View */}
                            <Button
                              variant="ghost"
                              size="icon"
                              title="View Details"
                              onClick={() => handleViewDetail(job.id)}
                            >
                              <Eye className="h-4 w-4 text-muted-foreground" />
                            </Button>

                            {/* Edit */}
                            <Button
                              variant="ghost"
                              size="icon"
                              title="Edit Job"
                              onClick={() => handleOpenEdit(job)}
                            >
                              <Pencil className="h-4 w-4 text-primary" />
                            </Button>

                            {/* Activate / Deactivate */}
                            <Button
                              variant="ghost"
                              size="icon"
                              title={job.is_active ? 'Deactivate Job' : 'Activate Job'}
                              onClick={() => handleOpenStatus(job)}
                            >
                              <Power
                                className={`h-4 w-4 ${
                                  job.is_active ? 'text-destructive' : 'text-emerald-600 dark:text-emerald-400'
                                }`}
                              />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* ========================================================
            CREATE JOB DIALOG
           ======================================================== */}
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-xl font-bold text-foreground">
                Post New Job Opportunity
              </DialogTitle>
              <DialogDescription>
                Fill out the job details, eligibility criteria, and required skills for students.
              </DialogDescription>
            </DialogHeader>

            <form onSubmit={handleCreateSubmit} className="space-y-6 py-2">
              {/* Section 1: Basic Information */}
              <div className="space-y-4">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider border-b border-border pb-1">
                  1. Basic Information
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Company */}
                  <div>
                    <Label className="text-sm font-medium">Company *</Label>
                    <Select value={createCompanyId} onValueChange={setCreateCompanyId}>
                      <SelectTrigger className="mt-1">
                        <SelectValue placeholder="Select active company" />
                      </SelectTrigger>
                      <SelectContent>
                        {companies
                          .filter((c) => c.is_active)
                          .map((c) => (
                            <SelectItem key={c.id} value={c.id.toString()}>
                              {c.name} ({c.industry || 'General'})
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Job Title */}
                  <div>
                    <Label className="text-sm font-medium">Job Title *</Label>
                    <Input
                      placeholder="e.g. Software Engineer Trainee"
                      value={createTitle}
                      onChange={(e) => setCreateTitle(e.target.value)}
                      className="mt-1"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Role Category */}
                  <div>
                    <Label className="text-sm font-medium">Role Category</Label>
                    <Input
                      placeholder="e.g. Full-Stack Development"
                      value={createRoleCategory}
                      onChange={(e) => setCreateRoleCategory(e.target.value)}
                      className="mt-1"
                    />
                  </div>

                  {/* Location */}
                  <div>
                    <Label className="text-sm font-medium">Location</Label>
                    <Input
                      placeholder="e.g. Chennai, TN"
                      value={createLocation}
                      onChange={(e) => setCreateLocation(e.target.value)}
                      className="mt-1"
                    />
                  </div>
                </div>

                {/* Description */}
                <div>
                  <Label className="text-sm font-medium">Job Description</Label>
                  <Textarea
                    placeholder="Provide detailed description of roles, responsibilities, and benefits..."
                    value={createDescription}
                    onChange={(e) => setCreateDescription(e.target.value)}
                    className="mt-1"
                    rows={3}
                  />
                </div>
              </div>

              {/* Section 2: Job Details */}
              <div className="space-y-4">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider border-b border-border pb-1">
                  2. Compensation & Requirements
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Employment Type */}
                  <div>
                    <Label className="text-sm font-medium">Employment Type *</Label>
                    <Select value={createEmploymentType} onValueChange={setCreateEmploymentType}>
                      <SelectTrigger className="mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Full-time">Full-time</SelectItem>
                        <SelectItem value="Part-time">Part-time</SelectItem>
                        <SelectItem value="Internship">Internship</SelectItem>
                        <SelectItem value="Contract">Contract</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* CTC LPA */}
                  <div>
                    <Label className="text-sm font-medium">CTC (LPA)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="e.g. 6.5"
                      value={createCtc}
                      onChange={(e) => setCreateCtc(e.target.value)}
                      className="mt-1"
                    />
                  </div>

                  {/* Min CGPA */}
                  <div>
                    <Label className="text-sm font-medium">Min CGPA (0 - 10)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      max="10"
                      placeholder="e.g. 7.5"
                      value={createMinCgpa}
                      onChange={(e) => setCreateMinCgpa(e.target.value)}
                      className="mt-1"
                    />
                  </div>
                </div>

                {/* Deadline */}
                <div>
                  <Label className="text-sm font-medium">Application Deadline</Label>
                  <Input
                    type="datetime-local"
                    value={createDeadline}
                    onChange={(e) => setCreateDeadline(e.target.value)}
                    className="mt-1"
                  />
                </div>
              </div>

              {/* Section 3: Eligible Departments */}
              <div className="space-y-3">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider border-b border-border pb-1">
                  3. Eligible Departments
                </h3>
                <p className="text-xs text-muted-foreground">
                  Select which departments are eligible to apply (leave empty if all departments are eligible).
                </p>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-36 overflow-y-auto p-2 border border-border rounded-md bg-muted/20">
                  {departments
                    .filter((d) => d.is_active)
                    .map((dept) => {
                      const isSelected = createEligibleDepts.includes(dept.id);
                      return (
                        <label
                          key={dept.id}
                          className={`flex items-center space-x-2 p-2 rounded cursor-pointer text-xs border transition-colors ${
                            isSelected
                              ? 'bg-primary/10 border-primary text-primary font-medium'
                              : 'bg-card border-border text-foreground hover:bg-accent'
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() =>
                              toggleDeptSelection(dept.id, createEligibleDepts, setCreateEligibleDepts)
                            }
                            className="rounded border-input text-primary focus:ring-primary"
                          />
                          <span className="truncate">{dept.name}</span>
                        </label>
                      );
                    })}
                </div>
              </div>

              {/* Section 4: Required Skills */}
              <div className="space-y-3">
                <div className="flex items-center justify-between border-b border-border pb-1">
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    4. Required Skills
                  </h3>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => addSkillRow(createSkills, setCreateSkills)}
                    className="text-xs"
                  >
                    <Plus className="h-3 w-3 mr-1" /> Add Skill
                  </Button>
                </div>

                {createSkills.length === 0 ? (
                  <p className="text-xs text-muted-foreground italic">No specific skills required.</p>
                ) : (
                  <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                    {createSkills.map((row, idx) => (
                      <div key={idx} className="flex items-center space-x-2 bg-muted/40 p-2 rounded-md border border-border">
                        {/* Skill Select */}
                        <div className="flex-1">
                          <Select
                            value={row.skill_id.toString()}
                            onValueChange={(val) =>
                              updateSkillRow(idx, 'skill_id', parseInt(val, 10), createSkills, setCreateSkills)
                            }
                          >
                            <SelectTrigger className="text-xs bg-background">
                              <SelectValue placeholder="Select skill" />
                            </SelectTrigger>
                            <SelectContent>
                              {skills
                                .filter((s) => s.is_active)
                                .map((s) => (
                                  <SelectItem key={s.id} value={s.id.toString()}>
                                    {s.name} ({s.category || 'General'})
                                  </SelectItem>
                                ))}
                            </SelectContent>
                          </Select>
                        </div>

                        {/* Minimum Proficiency Select */}
                        <div className="w-40">
                          <Select
                            value={row.min_proficiency || 'none'}
                            onValueChange={(val) =>
                              updateSkillRow(
                                idx,
                                'min_proficiency',
                                val === 'none' ? null : (val as 'beginner' | 'intermediate' | 'advanced'),
                                createSkills,
                                setCreateSkills
                              )
                            }
                          >
                            <SelectTrigger className="text-xs bg-background">
                              <SelectValue placeholder="Proficiency (Opt)" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="none">Any Proficiency</SelectItem>
                              <SelectItem value="beginner">Beginner</SelectItem>
                              <SelectItem value="intermediate">Intermediate</SelectItem>
                              <SelectItem value="advanced">Advanced</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>

                        {/* Remove */}
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => removeSkillRow(idx, createSkills, setCreateSkills)}
                          className="text-destructive hover:text-destructive hover:bg-destructive/10 h-8 w-8"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <DialogFooter className="pt-4 border-t border-border">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsCreateOpen(false)}
                  disabled={isSubmittingCreate}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isSubmittingCreate}
                >
                  {isSubmittingCreate ? 'Posting Job...' : 'Create Job Posting'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* ========================================================
            EDIT JOB DIALOG
           ======================================================== */}
        <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-xl font-bold text-foreground">
                Edit Job Opportunity
              </DialogTitle>
              <DialogDescription>
                Update job details, eligibility criteria, and required skills.
              </DialogDescription>
            </DialogHeader>

            <form onSubmit={handleEditSubmit} className="space-y-6 py-2">
              {/* Section 1: Basic Information */}
              <div className="space-y-4">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider border-b border-border pb-1">
                  1. Basic Information
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Company */}
                  <div>
                    <Label className="text-sm font-medium">Company *</Label>
                    <Select value={editCompanyId} onValueChange={setEditCompanyId}>
                      <SelectTrigger className="mt-1">
                        <SelectValue placeholder="Select company" />
                      </SelectTrigger>
                      <SelectContent>
                        {companies.map((c) => (
                          <SelectItem key={c.id} value={c.id.toString()}>
                            {c.name} {!c.is_active ? '(Inactive)' : ''}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Job Title */}
                  <div>
                    <Label className="text-sm font-medium">Job Title *</Label>
                    <Input
                      placeholder="e.g. Software Engineer Trainee"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      className="mt-1"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Role Category */}
                  <div>
                    <Label className="text-sm font-medium">Role Category</Label>
                    <Input
                      placeholder="e.g. Full-Stack Development"
                      value={editRoleCategory}
                      onChange={(e) => setEditRoleCategory(e.target.value)}
                      className="mt-1"
                    />
                  </div>

                  {/* Location */}
                  <div>
                    <Label className="text-sm font-medium">Location</Label>
                    <Input
                      placeholder="e.g. Chennai, TN"
                      value={editLocation}
                      onChange={(e) => setEditLocation(e.target.value)}
                      className="mt-1"
                    />
                  </div>
                </div>

                {/* Description */}
                <div>
                  <Label className="text-sm font-medium">Job Description</Label>
                  <Textarea
                    placeholder="Provide detailed description..."
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                    className="mt-1"
                    rows={3}
                  />
                </div>
              </div>

              {/* Section 2: Job Details */}
              <div className="space-y-4">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider border-b border-border pb-1">
                  2. Compensation & Requirements
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Employment Type */}
                  <div>
                    <Label className="text-sm font-medium">Employment Type *</Label>
                    <Select value={editEmploymentType} onValueChange={setEditEmploymentType}>
                      <SelectTrigger className="mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Full-time">Full-time</SelectItem>
                        <SelectItem value="Part-time">Part-time</SelectItem>
                        <SelectItem value="Internship">Internship</SelectItem>
                        <SelectItem value="Contract">Contract</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* CTC LPA */}
                  <div>
                    <Label className="text-sm font-medium">CTC (LPA)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="e.g. 6.5"
                      value={editCtc}
                      onChange={(e) => setEditCtc(e.target.value)}
                      className="mt-1"
                    />
                  </div>

                  {/* Min CGPA */}
                  <div>
                    <Label className="text-sm font-medium">Min CGPA (0 - 10)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      max="10"
                      placeholder="e.g. 7.5"
                      value={editMinCgpa}
                      onChange={(e) => setEditMinCgpa(e.target.value)}
                      className="mt-1"
                    />
                  </div>
                </div>

                {/* Deadline */}
                <div>
                  <Label className="text-sm font-medium">Application Deadline</Label>
                  <Input
                    type="datetime-local"
                    value={editDeadline}
                    onChange={(e) => setEditDeadline(e.target.value)}
                    className="mt-1"
                  />
                </div>
              </div>

              {/* Section 3: Eligible Departments */}
              <div className="space-y-3">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider border-b border-border pb-1">
                  3. Eligible Departments
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-36 overflow-y-auto p-2 border border-border rounded-md bg-muted/20">
                  {departments.map((dept) => {
                    const isSelected = editEligibleDepts.includes(dept.id);
                    return (
                      <label
                        key={dept.id}
                        className={`flex items-center space-x-2 p-2 rounded cursor-pointer text-xs border transition-colors ${
                          isSelected
                            ? 'bg-primary/10 border-primary text-primary font-medium'
                            : 'bg-card border-border text-foreground hover:bg-accent'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() =>
                            toggleDeptSelection(dept.id, editEligibleDepts, setEditEligibleDepts)
                          }
                          className="rounded border-input text-primary focus:ring-primary"
                        />
                        <span className="truncate">
                          {dept.name} {!dept.is_active ? '(Inactive)' : ''}
                        </span>
                      </label>
                    );
                  })}
                </div>
              </div>

              {/* Section 4: Required Skills */}
              <div className="space-y-3">
                <div className="flex items-center justify-between border-b border-border pb-1">
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    4. Required Skills
                  </h3>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => addSkillRow(editSkills, setEditSkills)}
                    className="text-xs"
                  >
                    <Plus className="h-3 w-3 mr-1" /> Add Skill
                  </Button>
                </div>

                {editSkills.length === 0 ? (
                  <p className="text-xs text-muted-foreground italic">No specific skills required.</p>
                ) : (
                  <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                    {editSkills.map((row, idx) => (
                      <div key={idx} className="flex items-center space-x-2 bg-muted/40 p-2 rounded-md border border-border">
                        {/* Skill Select */}
                        <div className="flex-1">
                          <Select
                            value={row.skill_id.toString()}
                            onValueChange={(val) =>
                              updateSkillRow(idx, 'skill_id', parseInt(val, 10), editSkills, setEditSkills)
                            }
                          >
                            <SelectTrigger className="text-xs bg-background">
                              <SelectValue placeholder="Select skill" />
                            </SelectTrigger>
                            <SelectContent>
                              {skills.map((s) => (
                                <SelectItem key={s.id} value={s.id.toString()}>
                                  {s.name} {!s.is_active ? '(Inactive)' : ''}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>

                        {/* Minimum Proficiency Select */}
                        <div className="w-40">
                          <Select
                            value={row.min_proficiency || 'none'}
                            onValueChange={(val) =>
                              updateSkillRow(
                                idx,
                                'min_proficiency',
                                val === 'none' ? null : (val as 'beginner' | 'intermediate' | 'advanced'),
                                editSkills,
                                setEditSkills
                              )
                            }
                          >
                            <SelectTrigger className="text-xs bg-background">
                              <SelectValue placeholder="Proficiency (Opt)" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="none">Any Proficiency</SelectItem>
                              <SelectItem value="beginner">Beginner</SelectItem>
                              <SelectItem value="intermediate">Intermediate</SelectItem>
                              <SelectItem value="advanced">Advanced</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>

                        {/* Remove */}
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => removeSkillRow(idx, editSkills, setEditSkills)}
                          className="text-destructive hover:text-destructive hover:bg-destructive/10 h-8 w-8"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <DialogFooter className="pt-4 border-t border-border">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsEditOpen(false)}
                  disabled={isSubmittingEdit}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isSubmittingEdit}
                >
                  {isSubmittingEdit ? 'Saving Changes...' : 'Save Job Changes'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* ========================================================
            JOB DETAIL VIEW DIALOG
           ======================================================== */}
        <Dialog open={isDetailOpen} onOpenChange={setIsDetailOpen}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-xl font-bold text-foreground flex items-center">
                <Briefcase className="h-5 w-5 text-primary mr-2" />
                Job Posting Details
              </DialogTitle>
            </DialogHeader>

            {loadingDetail || !jobDetail ? (
              <div className="p-8 text-center text-muted-foreground">
                <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-primary" />
                Loading job details...
              </div>
            ) : (
              <div className="space-y-6 py-2">
                {/* Header Card */}
                <div className="bg-muted/40 p-4 rounded-lg border border-border">
                  <div className="flex items-start justify-between">
                    <div>
                      <h2 className="text-lg font-bold text-foreground">{jobDetail.title}</h2>
                      <div className="text-sm font-medium text-primary flex items-center mt-1">
                        <Building className="h-4 w-4 mr-1 text-primary" />
                        {jobDetail.company?.name}
                      </div>
                    </div>
                    {renderStatusBadge(jobDetail)}
                  </div>

                  {jobDetail.role_category && (
                    <div className="mt-2 text-xs text-muted-foreground">
                      Category: <span className="font-medium text-foreground">{jobDetail.role_category}</span>
                    </div>
                  )}
                </div>

                {/* Key Overview Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 border border-border rounded-lg bg-card">
                  <div>
                    <span className="text-xs text-muted-foreground block uppercase tracking-wider">Location</span>
                    <span className="text-sm font-medium text-foreground flex items-center mt-1">
                      <MapPin className="h-3.5 w-3.5 mr-1 text-muted-foreground" />
                      {jobDetail.location || 'Remote'}
                    </span>
                  </div>

                  <div>
                    <span className="text-xs text-muted-foreground block uppercase tracking-wider">Employment</span>
                    <span className="text-sm font-medium text-foreground mt-1 block">
                      {jobDetail.employment_type}
                    </span>
                  </div>

                  <div>
                    <span className="text-xs text-muted-foreground block uppercase tracking-wider">Compensation</span>
                    <span className="text-sm font-semibold text-emerald-600 dark:text-emerald-400 mt-1 block">
                      {jobDetail.ctc_lpa ? `₹${jobDetail.ctc_lpa.toFixed(2)} LPA` : 'Not specified'}
                    </span>
                  </div>

                  <div>
                    <span className="text-xs text-muted-foreground block uppercase tracking-wider">Min CGPA</span>
                    <span className="text-sm font-medium text-foreground mt-1 block">
                      {jobDetail.min_cgpa ? `${jobDetail.min_cgpa.toFixed(2)} / 10` : 'No CGPA limit'}
                    </span>
                  </div>
                </div>

                {/* Deadline & Timestamps */}
                <div className="flex flex-wrap items-center justify-between text-xs text-muted-foreground border-t border-b border-border py-2 px-1">
                  <div className="flex items-center">
                    <Calendar className="h-4 w-4 mr-1.5 text-muted-foreground" />
                    <span>Application Deadline: </span>
                    <span className="font-medium text-foreground ml-1">
                      {formatDate(jobDetail.deadline)}
                    </span>
                  </div>

                  <div>
                    Created: {new Date(jobDetail.created_at).toLocaleDateString()}
                  </div>
                </div>

                {/* Description */}
                {jobDetail.description && (
                  <div>
                    <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                      Description & Scope
                    </h3>
                    <p className="text-sm text-foreground whitespace-pre-line leading-relaxed bg-muted/30 p-3 rounded-md border border-border">
                      {jobDetail.description}
                    </p>
                  </div>
                )}

                {/* Eligible Departments */}
                <div>
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center">
                    <GraduationCap className="h-4 w-4 mr-1 text-muted-foreground" />
                    Eligible Departments
                  </h3>
                  {jobDetail.eligible_departments && jobDetail.eligible_departments.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {jobDetail.eligible_departments.map((d) => (
                        <Badge
                          key={d.id}
                          variant="outline"
                          className="bg-primary/10 text-primary border-primary/20 text-xs py-1 px-2"
                        >
                          {d.department?.name || d.department_name} {d.department?.code ? `(${d.department.code})` : ''}
                        </Badge>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground italic">Open to students from all departments.</p>
                  )}
                </div>

                {/* Required Skills */}
                <div>
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center">
                    <Award className="h-4 w-4 mr-1 text-muted-foreground" />
                    Required Skills & Min Proficiency
                  </h3>
                  {jobDetail.required_skills && jobDetail.required_skills.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {jobDetail.required_skills.map((s) => (
                        <div
                          key={s.id}
                          className="flex items-center justify-between p-2 rounded-md border border-border bg-muted/30 text-xs"
                        >
                          <span className="font-medium text-foreground">{s.skill?.name || s.skill_name}</span>
                          {s.min_proficiency ? (
                            <Badge
                              variant="outline"
                              className="bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20 capitalize text-[10px]"
                            >
                              Min: {s.min_proficiency}
                            </Badge>
                          ) : (
                            <span className="text-muted-foreground text-[10px]">Any proficiency</span>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground italic">No specific skill prerequisites specified.</p>
                  )}
                </div>

                {/* Recruitment Workflow Section */}
                <JobRecruitmentWorkflowEditor
                  jobId={jobDetail.id}
                  initialRounds={jobDetail.rounds}
                />

                <DialogFooter className="pt-4 border-t border-border">
                  <Button variant="outline" onClick={() => setIsDetailOpen(false)}>
                    Close
                  </Button>
                </DialogFooter>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* ========================================================
            STATUS TOGGLE CONFIRMATION DIALOG
           ======================================================== */}
        <Dialog open={isStatusOpen} onOpenChange={setIsStatusOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="text-lg font-bold text-foreground flex items-center">
                <AlertCircle className="h-5 w-5 text-amber-500 mr-2" />
                Confirm Job Status Change
              </DialogTitle>
              <DialogDescription className="pt-2">
                {toggleJob && (
                  <span>
                    Are you sure you want to{' '}
                    <strong className="text-foreground">
                      {toggleJob.is_active ? 'deactivate' : 'activate'}
                    </strong>{' '}
                    the job posting &quot;{toggleJob.title}&quot; for{' '}
                    <strong className="text-foreground">{toggleJob.company?.name}</strong>?
                  </span>
                )}
              </DialogDescription>
            </DialogHeader>

            <div className="text-xs text-muted-foreground bg-amber-500/10 p-3 rounded-md border border-amber-500/20 mt-2">
              <p className="font-medium text-amber-600 dark:text-amber-400 mb-1">Note:</p>
              <ul className="list-disc pl-4 space-y-1 text-amber-700 dark:text-amber-300">
                <li>Deactivating a job posting does NOT delete historical data or requirements.</li>
                <li>Inactive job postings are hidden from student visibility.</li>
                {toggleJob?.deadline && new Date(toggleJob.deadline) < new Date() && (
                  <li>
                    This job has an expired deadline ({formatDate(toggleJob.deadline)}). Activating it will not change its expired deadline status.
                  </li>
                )}
              </ul>
            </div>

            <DialogFooter className="pt-4 border-t border-border">
              <Button
                variant="outline"
                onClick={() => setIsStatusOpen(false)}
                disabled={isSubmittingStatus}
              >
                Cancel
              </Button>
              <Button
                onClick={handleConfirmStatusToggle}
                variant={toggleJob?.is_active ? 'destructive' : 'default'}
                disabled={isSubmittingStatus}
              >
                {isSubmittingStatus
                  ? 'Updating...'
                  : toggleJob?.is_active
                  ? 'Deactivate Job'
                  : 'Activate Job'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </PageContainer>
    </AppLayout>
  );
}
