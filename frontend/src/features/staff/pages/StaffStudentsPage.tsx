import { useState, useEffect, useCallback } from 'react';
import {
  Users,
  Search,
  RefreshCw,
  Eye,
  FileText,
  Sparkles,
  GraduationCap,
  Download,
  ExternalLink,
  Linkedin,
  Github,
  Mail,
  Phone,
  Calendar,
  MapPin,
  X,
} from 'lucide-react';
import toast from 'react-hot-toast';

import { AppLayout } from '@/components/layout/AppLayout';
import { PageHeader, PageContainer } from '@/components/common/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useAuth } from '@/features/auth/context/AuthContext';
import { AxiosError } from 'axios';
import { departmentService, Department } from '../services/department.service';
import {
  staffStudentService,
  StaffStudentListItem,
  StaffStudentDetail,
} from '../services/staff-student.service';

export default function StaffStudentsPage() {
  const { user } = useAuth();
  const [students, setStudents] = useState<StaffStudentListItem[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);

  // Filter states
  const [search, setSearch] = useState('');
  const [selectedDeptId, setSelectedDeptId] = useState<string>('all');
  const [selectedGradYear, setSelectedGradYear] = useState<string>('all');

  // Detail Modal states
  const [selectedStudentId, setSelectedStudentId] = useState<number | null>(null);
  const [studentDetail, setStudentDetail] = useState<StaffStudentDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Resume Preview Modal states
  const [previewBlobUrl, setPreviewBlobUrl] = useState<string | null>(null);
  const [previewTitle, setPreviewTitle] = useState<string>('');
  const [loadingPreview, setLoadingPreview] = useState(false);

  // Fetch departments for filter dropdown
  useEffect(() => {
    departmentService
      .getActiveDepartments()
      .then(setDepartments)
      .catch(() => {
        // Fallback or retry silently
      });
  }, []);

  const fetchStudents = useCallback(async () => {
    setLoading(true);
    try {
      const deptId = selectedDeptId === 'all' ? undefined : Number(selectedDeptId);
      const gradYear = selectedGradYear === 'all' ? undefined : Number(selectedGradYear);
      const data = await staffStudentService.getStaffStudents(search, deptId, gradYear);
      setStudents(data);
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.detail || err.response?.data?.message
          : 'Failed to load student directory';
      toast.error(msg || 'Failed to load student directory');
    } finally {
      setLoading(false);
    }
  }, [search, selectedDeptId, selectedGradYear]);

  useEffect(() => {
    fetchStudents();
  }, [fetchStudents]);

  const handleOpenDetail = async (studentId: number) => {
    setSelectedStudentId(studentId);
    setLoadingDetail(true);
    setStudentDetail(null);
    try {
      const data = await staffStudentService.getStaffStudentDetail(studentId);
      setStudentDetail(data);
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.detail || err.response?.data?.message
          : 'Failed to load student profile details';
      toast.error(msg || 'Failed to load student profile details');
      setSelectedStudentId(null);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleDownloadResume = async (studentId: number, resumeId: number, fileName: string) => {
    try {
      await staffStudentService.downloadResumeFile(studentId, resumeId, fileName);
      toast.success(`Downloading ${fileName}...`);
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.detail || err.response?.data?.message
          : 'Failed to download resume document';
      toast.error(msg || 'Failed to download resume document');
    }
  };

  const handlePreviewResume = async (studentId: number, resumeId: number, title: string, fileType: string) => {
    if (!fileType.toLowerCase().includes('pdf')) {
      toast.error('Preview is only available for PDF documents. Downloading file instead...');
      const r = studentDetail?.resumes.find((res) => res.id === resumeId);
      if (r) handleDownloadResume(studentId, resumeId, r.file_name);
      return;
    }

    setLoadingPreview(true);
    setPreviewTitle(title);
    try {
      const blobUrl = await staffStudentService.previewResumeFileBlob(studentId, resumeId);
      setPreviewBlobUrl(blobUrl);
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.detail || err.response?.data?.message
          : 'Failed to preview resume file';
      toast.error(msg || 'Failed to preview resume file');
    } finally {
      setLoadingPreview(false);
    }
  };

  const closePreviewModal = () => {
    if (previewBlobUrl) {
      window.URL.revokeObjectURL(previewBlobUrl);
    }
    setPreviewBlobUrl(null);
    setPreviewTitle('');
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const userEmail = user?.email || 'Staff Member';
  const avatarText = userEmail.substring(0, 2).toUpperCase();

  return (
    <AppLayout role="staff" userName={userEmail} userRole="Staff" avatarText={avatarText}>
      <PageContainer>
        <PageHeader
          title="Student Directory"
          description="View student profiles, academic information, skills, and resumes."
        />

        {/* Filter Bar */}
        <Card className="mb-6">
          <CardContent className="pt-6 flex flex-col lg:flex-row gap-4 justify-between items-center">
            <div className="relative w-full lg:w-80">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by name, email, or phone..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>

            <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-muted-foreground">Department:</span>
                <select
                  value={selectedDeptId}
                  onChange={(e) => setSelectedDeptId(e.target.value)}
                  className="h-9 px-3 py-1 text-xs border border-input bg-background rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="all">All Departments</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-muted-foreground">Graduation Year:</span>
                <select
                  value={selectedGradYear}
                  onChange={(e) => setSelectedGradYear(e.target.value)}
                  className="h-9 px-3 py-1 text-xs border border-input bg-background rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="all">All Batches</option>
                  <option value="2024">2024</option>
                  <option value="2025">2025</option>
                  <option value="2026">2026</option>
                  <option value="2027">2027</option>
                  <option value="2028">2028</option>
                </select>
              </div>

              <Button variant="ghost" size="icon" onClick={fetchStudents} title="Refresh Directory">
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Directory Table */}
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-12 text-center text-muted-foreground">
                <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2" />
                Loading student directory...
              </div>
            ) : students.length === 0 ? (
              <div className="p-12 text-center text-muted-foreground">
                <Users className="h-8 w-8 mx-auto mb-2 opacity-50" />
                No student profiles found matching your filters.
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-16">ID</TableHead>
                    <TableHead>Student</TableHead>
                    <TableHead>Department</TableHead>
                    <TableHead>Batch</TableHead>
                    <TableHead>CGPA</TableHead>
                    <TableHead>Skills</TableHead>
                    <TableHead>Resumes</TableHead>
                    <TableHead className="w-28">Status</TableHead>
                    <TableHead className="w-32 text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {students.map((st) => (
                    <TableRow key={st.id}>
                      <TableCell className="font-mono text-xs text-muted-foreground">
                        #{st.id}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium text-foreground">
                            {st.full_name || (
                              <span className="text-muted-foreground italic font-normal">
                                Profile incomplete
                              </span>
                            )}
                          </span>
                          <span className="text-xs text-muted-foreground">{st.email}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {st.department ? (
                          <Badge variant="outline" className="font-normal text-xs">
                            {st.department.name}
                          </Badge>
                        ) : (
                          <span className="text-xs text-muted-foreground italic">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {st.graduation_year ? (
                          <span className="text-xs font-medium">{st.graduation_year}</span>
                        ) : (
                          <span className="text-xs text-muted-foreground italic">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {st.cgpa !== null && st.cgpa !== undefined ? (
                          <span className="text-xs font-mono font-medium">{st.cgpa.toFixed(2)}</span>
                        ) : (
                          <span className="text-xs text-muted-foreground italic">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="inline-flex items-center gap-1">
                          <Sparkles className="h-3 w-3 text-amber-500" />
                          <span className="text-xs font-medium">{st.skills_count}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="inline-flex items-center gap-1">
                          <FileText className="h-3 w-3 text-blue-500" />
                          <span className="text-xs font-medium">{st.resumes_count}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {st.is_active ? (
                          <Badge variant="default" className="bg-emerald-500/15 text-emerald-600 border-emerald-500/30">
                            Active
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="bg-slate-100 text-slate-600 border-slate-200">
                            Inactive
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleOpenDetail(st.id)}
                          className="gap-1 text-xs"
                        >
                          <Eye className="h-3.5 w-3.5" />
                          View Profile
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Student Profile Detail Modal */}
        <Dialog open={selectedStudentId !== null} onOpenChange={(open) => !open && setSelectedStudentId(null)}>
          <DialogContent className="sm:max-w-3xl max-h-[85vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center justify-between pr-4">
                <span>Student Details</span>
                {studentDetail?.is_active ? (
                  <Badge variant="default" className="bg-emerald-500/15 text-emerald-600 border-emerald-500/30">
                    Active Account
                  </Badge>
                ) : (
                  <Badge variant="secondary">Inactive Account</Badge>
                )}
              </DialogTitle>
              <DialogDescription>
                Comprehensive academic profile, verified skills, and resume documents.
              </DialogDescription>
            </DialogHeader>

            {loadingDetail ? (
              <div className="p-12 text-center text-muted-foreground">
                <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2" />
                Loading profile details...
              </div>
            ) : studentDetail ? (
              <div className="py-2 space-y-6">
                {/* Header Banner */}
                <div className="rounded-xl border bg-muted/30 p-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div>
                    <h3 className="text-lg font-bold text-foreground">
                      {studentDetail.full_name || 'Profile Incomplete'}
                    </h3>
                    <p className="text-xs text-muted-foreground flex items-center gap-1.5 mt-0.5">
                      <Mail className="h-3.5 w-3.5 text-muted-foreground" />
                      {studentDetail.email}
                    </p>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    {studentDetail.department && (
                      <Badge variant="outline" className="bg-background text-xs">
                        <GraduationCap className="h-3 w-3 mr-1 text-primary" />
                        {studentDetail.department.name}
                      </Badge>
                    )}
                    {studentDetail.graduation_year && (
                      <Badge variant="secondary" className="text-xs">
                        Batch of {studentDetail.graduation_year}
                      </Badge>
                    )}
                    {studentDetail.cgpa !== null && studentDetail.cgpa !== undefined && (
                      <Badge className="bg-primary/10 text-primary border-primary/20 text-xs">
                        CGPA: {studentDetail.cgpa.toFixed(2)} / 10.0
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Section 1: Basic Information */}
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
                    Basic Information
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 rounded-xl border p-4 bg-card text-xs">
                    <div>
                      <span className="text-muted-foreground flex items-center gap-1 mb-1">
                        <Phone className="h-3 w-3" /> Phone Number
                      </span>
                      <span className="font-medium">{studentDetail.phone || 'Not provided'}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground flex items-center gap-1 mb-1">
                        <Calendar className="h-3 w-3" /> Date of Birth
                      </span>
                      <span className="font-medium">{studentDetail.date_of_birth || 'Not provided'}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground flex items-center gap-1 mb-1">
                        <MapPin className="h-3 w-3" /> Address
                      </span>
                      <span className="font-medium line-clamp-2">{studentDetail.address || 'Not provided'}</span>
                    </div>
                  </div>
                </div>

                {/* Section 2: External Links */}
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
                    Online Profiles & Links
                  </h4>
                  <div className="flex flex-wrap items-center gap-3">
                    {studentDetail.linkedin_url ? (
                      <a
                        href={studentDetail.linkedin_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium text-blue-600 hover:bg-blue-50 transition-colors"
                      >
                        <Linkedin className="h-3.5 w-3.5" />
                        LinkedIn Profile
                        <ExternalLink className="h-3 w-3 opacity-70" />
                      </a>
                    ) : (
                      <span className="text-xs text-muted-foreground italic border rounded-lg px-3 py-1.5 bg-muted/20">
                        LinkedIn: Not provided
                      </span>
                    )}

                    {studentDetail.github_url ? (
                      <a
                        href={studentDetail.github_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium text-slate-800 hover:bg-slate-100 transition-colors"
                      >
                        <Github className="h-3.5 w-3.5" />
                        GitHub Profile
                        <ExternalLink className="h-3 w-3 opacity-70" />
                      </a>
                    ) : (
                      <span className="text-xs text-muted-foreground italic border rounded-lg px-3 py-1.5 bg-muted/20">
                        GitHub: Not provided
                      </span>
                    )}
                  </div>
                </div>

                {/* Section 3: Skills */}
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 text-amber-500" />
                    Skills & Proficiency ({studentDetail.skills.length})
                  </h4>
                  {studentDetail.skills.length === 0 ? (
                    <p className="text-xs text-muted-foreground italic border rounded-xl p-4 bg-muted/20">
                      No skills added to profile yet.
                    </p>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                      {studentDetail.skills.map((sk) => (
                        <div
                          key={sk.id}
                          className="flex items-center justify-between rounded-lg border p-2.5 bg-card text-xs"
                        >
                          <div>
                            <p className="font-medium text-foreground">{sk.skill_name}</p>
                            {sk.category && (
                              <p className="text-[10px] text-muted-foreground">{sk.category}</p>
                            )}
                          </div>
                          <Badge
                            variant="secondary"
                            className="capitalize text-[10px] font-semibold bg-muted"
                          >
                            {sk.proficiency}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Section 4: Resumes */}
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-1.5">
                    <FileText className="h-3.5 w-3.5 text-blue-500" />
                    Resume Documents ({studentDetail.resumes.length})
                  </h4>
                  {studentDetail.resumes.length === 0 ? (
                    <p className="text-xs text-muted-foreground italic border rounded-xl p-4 bg-muted/20">
                      No resume documents uploaded yet.
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {studentDetail.resumes.map((res) => (
                        <div
                          key={res.id}
                          className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 rounded-xl border p-3 bg-card"
                        >
                          <div className="flex items-start gap-2.5">
                            <FileText className="h-5 w-5 text-blue-500 shrink-0 mt-0.5" />
                            <div>
                              <div className="flex items-center gap-2">
                                <p className="text-xs font-bold text-foreground">{res.title}</p>
                                {res.is_default && (
                                  <Badge className="bg-blue-500/15 text-blue-600 border-blue-500/30 text-[10px]">
                                    Default Resume
                                  </Badge>
                                )}
                              </div>
                              {res.description && (
                                <p className="text-[11px] text-muted-foreground mt-0.5">
                                  {res.description}
                                </p>
                              )}
                              <p className="text-[10px] text-muted-foreground mt-1">
                                {res.file_name} • {formatFileSize(res.file_size)}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                            {res.file_type.toLowerCase().includes('pdf') && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() =>
                                  handlePreviewResume(studentDetail.id, res.id, res.title, res.file_type)
                                }
                                disabled={loadingPreview}
                                className="h-8 text-xs gap-1"
                              >
                                <Eye className="h-3.5 w-3.5" />
                                Preview
                              </Button>
                            )}
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() =>
                                handleDownloadResume(studentDetail.id, res.id, res.file_name)
                              }
                              className="h-8 text-xs gap-1"
                            >
                              <Download className="h-3.5 w-3.5" />
                              Download
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : null}
          </DialogContent>
        </Dialog>

        {/* PDF Document Preview Modal */}
        <Dialog open={!!previewBlobUrl} onOpenChange={(open) => !open && closePreviewModal()}>
          <DialogContent className="sm:max-w-4xl h-[90vh] flex flex-col p-4">
            <DialogHeader className="flex flex-row items-center justify-between pb-2 border-b">
              <div>
                <DialogTitle className="text-sm font-bold">{previewTitle}</DialogTitle>
                <DialogDescription className="text-xs">Document Preview</DialogDescription>
              </div>
              <Button variant="ghost" size="icon" onClick={closePreviewModal}>
                <X className="h-4 w-4" />
              </Button>
            </DialogHeader>

            <div className="flex-1 w-full bg-slate-100 rounded-lg overflow-hidden mt-2">
              {previewBlobUrl && (
                <iframe
                  src={previewBlobUrl}
                  title={previewTitle}
                  className="w-full h-full border-0"
                />
              )}
            </div>
          </DialogContent>
        </Dialog>
      </PageContainer>
    </AppLayout>
  );
}
