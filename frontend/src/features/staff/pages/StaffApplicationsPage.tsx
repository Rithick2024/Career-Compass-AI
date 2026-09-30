import { useState, useEffect, useCallback } from 'react';
import {
  Search,
  Eye,
  Building,
  GraduationCap,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Users,
  Star,
  FileText,
  Plus,
  ExternalLink,
  Edit,
  Calendar
} from 'lucide-react';
import toast from 'react-hot-toast';
import { AxiosError } from 'axios';
import { format } from 'date-fns';

import { AppLayout } from '@/components/layout/AppLayout';
import { PageHeader, PageContainer } from '@/components/common/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

import { useAuth } from '@/features/auth/context/AuthContext';
import {
  staffApplicationService,
  StaffApplicationListResponse,
  StaffApplicationDetailResponse,
  ApplicationStatus
} from '../services/application.service';
import {
  staffApplicationRoundService,
  ApplicationRoundResponse,
  ApplicationRoundCreate,
  ApplicationRoundUpdate,
  RoundStatus,
  RoundResult,
  RoundType
} from '../services/application-round.service';

const getStatusBadgeVariant = (status: ApplicationStatus) => {
  switch (status) {
    case 'Pending':
      return 'secondary';
    case 'Reviewing':
      return 'default';
    case 'Interview':
      return 'secondary';
    case 'Offered':
      return 'default';
    case 'Rejected':
      return 'destructive';
    case 'Withdrawn':
      return 'outline';
    default:
      return 'secondary';
  }
};

const getStatusIcon = (status: ApplicationStatus) => {
  switch (status) {
    case 'Pending':
      return <Clock className="h-3 w-3 mr-1" />;
    case 'Reviewing':
      return <Users className="h-3 w-3 mr-1" />;
    case 'Interview':
      return <Star className="h-3 w-3 mr-1" />;
    case 'Offered':
      return <CheckCircle2 className="h-3 w-3 mr-1" />;
    case 'Rejected':
      return <XCircle className="h-3 w-3 mr-1" />;
    case 'Withdrawn':
      return <AlertCircle className="h-3 w-3 mr-1" />;
    default:
      return null;
  }
};

const getRoundStatusBadge = (status: RoundStatus, result: RoundResult | null) => {
  if (status === 'Completed') {
    if (result === 'Passed') return <Badge variant="default" className="bg-green-600">Passed</Badge>;
    if (result === 'Failed') return <Badge variant="destructive">Failed</Badge>;
    if (result === 'Not Attended') return <Badge variant="secondary">Not Attended</Badge>;
  }
  if (status === 'Cancelled') return <Badge variant="destructive">Cancelled</Badge>;
  if (status === 'Scheduled') return <Badge variant="default" className="bg-blue-600">Scheduled</Badge>;
  return <Badge variant="secondary">{status}</Badge>;
};

const roundSchema = z.object({
  round_number: z.coerce.number().min(1, 'Required'),
  round_type: z.string().min(1, 'Required'),
  title: z.string().optional(),
  status: z.string().optional(),
  result: z.string().optional(),
  scheduled_at: z.string().optional(),
  external_link: z.string().url().optional().or(z.literal('')),
  notes: z.string().optional(),
});

export default function StaffApplicationsPage() {
  const { user } = useAuth();
  const [applications, setApplications] = useState<StaffApplicationListResponse[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  
  // Dialog State
  const [selectedApp, setSelectedApp] = useState<StaffApplicationDetailResponse | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [updateLoading, setUpdateLoading] = useState(false);

  // Rounds State
  const [rounds, setRounds] = useState<ApplicationRoundResponse[]>([]);
  const [roundsLoading, setRoundsLoading] = useState(false);
  const [roundActionLoading, setRoundActionLoading] = useState(false);
  const [showRoundForm, setShowRoundForm] = useState(false);
  const [editingRoundId, setEditingRoundId] = useState<number | null>(null);

  const roundForm = useForm<z.infer<typeof roundSchema>>({
    resolver: zodResolver(roundSchema),
    defaultValues: {
      round_number: 1,
      round_type: 'Technical Interview',
      title: '',
      status: 'Scheduled',
      result: 'Pending',
      scheduled_at: '',
      external_link: '',
      notes: '',
    },
  });

  const fetchApplications = useCallback(async () => {
    setLoading(true);
    try {
      const data = await staffApplicationService.listApplications({
        search,
        status: statusFilter !== 'all' ? statusFilter : undefined,
      });
      setApplications(data);
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.detail || err.response?.data?.message
          : 'Failed to fetch applications';
      toast.error(msg || 'Failed to fetch applications');
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter]);

  useEffect(() => {
    fetchApplications();
  }, [fetchApplications]);

  const fetchRounds = async (appId: number) => {
    setRoundsLoading(true);
    try {
      const data = await staffApplicationRoundService.listRounds(appId);
      setRounds(data);
    } catch (err: unknown) {
      console.error(err);
      toast.error('Failed to fetch rounds');
    } finally {
      setRoundsLoading(false);
    }
  };

  const handleViewDetails = async (appId: number) => {
    setDetailLoading(true);
    setDialogOpen(true);
    setShowRoundForm(false);
    setEditingRoundId(null);
    try {
      const data = await staffApplicationService.getApplication(appId);
      setSelectedApp(data);
      await fetchRounds(appId);
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.detail || err.response?.data?.message
          : 'Failed to fetch application details';
      toast.error(msg || 'Failed to fetch application details');
      setDialogOpen(false);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleUpdateStatus = async (newStatus: ApplicationStatus) => {
    if (!selectedApp) return;
    setUpdateLoading(true);
    try {
      const data = await staffApplicationService.updateStatus(selectedApp.id, newStatus);
      setSelectedApp(data);
      toast.success('Status updated successfully');
      fetchApplications();
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.detail || err.response?.data?.message
          : 'Failed to update status';
      toast.error(msg || 'Failed to update status');
    } finally {
      setUpdateLoading(false);
    }
  };

  const onSubmitRound = async (values: z.infer<typeof roundSchema>) => {
    if (!selectedApp) return;
    setRoundActionLoading(true);
    try {
      const payload = {
        ...values,
        round_type: values.round_type as RoundType,
        status: values.status as RoundStatus | undefined,
        result: values.result as RoundResult | undefined,
        title: values.title || undefined,
        external_link: values.external_link || undefined,
        notes: values.notes || undefined,
        scheduled_at: values.scheduled_at ? new Date(values.scheduled_at).toISOString() : undefined,
      };

      if (editingRoundId) {
        // update
        await staffApplicationRoundService.updateRound(selectedApp.id, editingRoundId, payload as ApplicationRoundUpdate);
        toast.success('Round updated');
      } else {
        // create
        await staffApplicationRoundService.createRound(selectedApp.id, payload as ApplicationRoundCreate);
        toast.success('Round created');
      }
      setShowRoundForm(false);
      setEditingRoundId(null);
      roundForm.reset();
      await fetchRounds(selectedApp.id);
    } catch (err: unknown) {
      const msg = err instanceof AxiosError ? err.response?.data?.detail : 'Failed to save round';
      toast.error(msg || 'Failed to save round');
    } finally {
      setRoundActionLoading(false);
    }
  };

  const handleEditRound = (round: ApplicationRoundResponse) => {
    setEditingRoundId(round.id);
    setShowRoundForm(true);
    roundForm.reset({
      round_number: round.round_number,
      round_type: round.round_type,
      title: round.title || '',
      status: round.status,
      result: round.result || 'Pending',
      scheduled_at: round.scheduled_at ? round.scheduled_at.substring(0, 16) : '',
      external_link: round.external_link || '',
      notes: round.notes || '',
    });
  };

  return (
    <AppLayout role="staff" userName={user?.email || 'Staff'} userRole="Staff" avatarText="SA">
      <PageContainer>
        <PageHeader
          title="Job Applications"
          description="Manage and review student job applications."
        />

        {/* Filters */}
        <Card className="mb-6 border-none bg-muted/40 shadow-none">
          <CardContent className="p-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search student, job, company..."
                  className="pl-9 bg-background"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>

              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="bg-background">
                  <SelectValue placeholder="Filter by Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="Pending">Pending</SelectItem>
                  <SelectItem value="Reviewing">Reviewing</SelectItem>
                  <SelectItem value="Interview">Interview</SelectItem>
                  <SelectItem value="Offered">Offered</SelectItem>
                  <SelectItem value="Rejected">Rejected</SelectItem>
                  <SelectItem value="Withdrawn">Withdrawn</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Data Table */}
        <Card>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Student</TableHead>
                  <TableHead>Job & Company</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead>CGPA</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Applied At</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={7} className="h-32 text-center">
                      <div className="flex items-center justify-center">
                        <div className="h-6 w-6 animate-spin rounded-full border-b-2 border-primary"></div>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : applications.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="h-32 text-center text-muted-foreground">
                      No applications found.
                    </TableCell>
                  </TableRow>
                ) : (
                  applications.map((app) => (
                    <TableRow key={app.id}>
                      <TableCell>
                        <div className="font-medium">{app.student_name}</div>
                        <div className="text-xs text-muted-foreground">{app.student_email}</div>
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">{app.job_title}</div>
                        <div className="text-xs text-muted-foreground flex items-center">
                          <Building className="h-3 w-3 mr-1" />
                          {app.company_name}
                        </div>
                      </TableCell>
                      <TableCell>
                        {app.department ? (
                          <div className="flex items-center">
                            <GraduationCap className="h-3 w-3 mr-1 text-muted-foreground" />
                            {app.department}
                          </div>
                        ) : (
                          <span className="text-muted-foreground text-sm">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {app.cgpa ? app.cgpa.toFixed(2) : '-'}
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusBadgeVariant(app.status)} className="flex w-max items-center">
                          {getStatusIcon(app.status)}
                          {app.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground text-sm">
                        {format(new Date(app.applied_at), 'MMM d, yyyy')}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleViewDetails(app.id)}
                          title="View Details"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </Card>
      </PageContainer>

      {/* Application Details Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Application Details</DialogTitle>
            <DialogDescription>
              Review application and update status.
            </DialogDescription>
          </DialogHeader>

          {detailLoading || !selectedApp ? (
            <div className="flex justify-center p-8">
              <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-primary"></div>
            </div>
          ) : (
            <div className="space-y-6 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-1">Student</h4>
                  <p className="font-medium">{selectedApp.student_name}</p>
                  <p className="text-sm text-muted-foreground">{selectedApp.student_email}</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Dept: {selectedApp.department || 'N/A'} • CGPA: {selectedApp.cgpa ? selectedApp.cgpa.toFixed(2) : 'N/A'}
                  </p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-1">Job</h4>
                  <p className="font-medium">{selectedApp.job_title}</p>
                  <p className="text-sm text-muted-foreground">{selectedApp.company_name}</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {selectedApp.employment_type} • {selectedApp.location || 'Remote'}
                  </p>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">Resume Submitted</h4>
                <div className="flex items-center p-3 bg-muted rounded-md border border-border/50">
                  <FileText className="h-5 w-5 text-primary mr-3" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{selectedApp.resume_title}</p>
                    <p className="text-xs text-muted-foreground truncate">{selectedApp.resume_file_name}</p>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">Current Status</h4>
                <div className="flex items-center gap-2">
                  <Badge variant={getStatusBadgeVariant(selectedApp.status)} className="text-sm py-1">
                    {getStatusIcon(selectedApp.status)}
                    {selectedApp.status}
                  </Badge>
                  <span className="text-xs text-muted-foreground ml-2">
                    Applied: {format(new Date(selectedApp.applied_at), 'PP p')}
                  </span>
                </div>
              </div>

              <div className="pt-4 border-t">
                <h4 className="text-sm font-medium mb-3">Update Status</h4>
                <div className="flex flex-wrap gap-2">
                  {['Pending', 'Reviewing', 'Interview', 'Offered', 'Rejected'].map((status) => (
                    <Button
                      key={status}
                      variant={selectedApp.status === status ? "default" : "outline"}
                      size="sm"
                      disabled={updateLoading || selectedApp.status === 'Withdrawn'}
                      onClick={() => handleUpdateStatus(status as ApplicationStatus)}
                    >
                      {status}
                    </Button>
                  ))}
                  {selectedApp.status === 'Withdrawn' && (
                    <p className="text-sm text-destructive w-full mt-2">
                      This application has been withdrawn by the student.
                    </p>
                  )}
                </div>
              </div>

              {/* Rounds Section */}
              <div className="pt-6 border-t mt-6">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-lg font-semibold flex items-center gap-2">
                    <Clock className="h-5 w-5 text-primary" />
                    Recruitment Timeline
                  </h4>
                  {!showRoundForm && (
                    <Button size="sm" onClick={() => {
                      setShowRoundForm(true);
                      setEditingRoundId(null);
                      roundForm.reset({ round_number: rounds.length + 1, round_type: 'Technical Interview', status: 'Scheduled', result: 'Pending' });
                    }}>
                      <Plus className="h-4 w-4 mr-1" /> Add Round
                    </Button>
                  )}
                </div>

                {showRoundForm ? (
                  <Card className="mb-6 border-primary/20 bg-muted/20">
                    <CardContent className="p-4 pt-6">
                      <Form {...roundForm}>
                        <form onSubmit={roundForm.handleSubmit(onSubmitRound)} className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <FormField
                              control={roundForm.control}
                              name="round_number"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Round #</FormLabel>
                                  <FormControl>
                                    <Input type="number" disabled={!!editingRoundId} {...field} />
                                  </FormControl>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                            <FormField
                              control={roundForm.control}
                              name="round_type"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Type</FormLabel>
                                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                                    <FormControl>
                                      <SelectTrigger>
                                        <SelectValue placeholder="Select type" />
                                      </SelectTrigger>
                                    </FormControl>
                                    <SelectContent>
                                      <SelectItem value="Online Assessment">Online Assessment</SelectItem>
                                      <SelectItem value="Coding Test">Coding Test</SelectItem>
                                      <SelectItem value="Aptitude Test">Aptitude Test</SelectItem>
                                      <SelectItem value="Technical Interview">Technical Interview</SelectItem>
                                      <SelectItem value="Managerial Interview">Managerial Interview</SelectItem>
                                      <SelectItem value="HR Interview">HR Interview</SelectItem>
                                      <SelectItem value="Group Discussion">Group Discussion</SelectItem>
                                      <SelectItem value="Other">Other</SelectItem>
                                    </SelectContent>
                                  </Select>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                            <FormField
                              control={roundForm.control}
                              name="title"
                              render={({ field }) => (
                                <FormItem className="col-span-2">
                                  <FormLabel>Title (Optional)</FormLabel>
                                  <FormControl>
                                    <Input placeholder="e.g. System Design Interview" {...field} />
                                  </FormControl>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                            <FormField
                              control={roundForm.control}
                              name="status"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Status</FormLabel>
                                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                                    <FormControl>
                                      <SelectTrigger>
                                        <SelectValue placeholder="Select status" />
                                      </SelectTrigger>
                                    </FormControl>
                                    <SelectContent>
                                      <SelectItem value="Not Started">Not Started</SelectItem>
                                      <SelectItem value="Scheduled">Scheduled</SelectItem>
                                      <SelectItem value="In Progress">In Progress</SelectItem>
                                      <SelectItem value="Completed">Completed</SelectItem>
                                      <SelectItem value="Cancelled">Cancelled</SelectItem>
                                    </SelectContent>
                                  </Select>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                            <FormField
                              control={roundForm.control}
                              name="result"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Result</FormLabel>
                                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                                    <FormControl>
                                      <SelectTrigger>
                                        <SelectValue placeholder="Select result" />
                                      </SelectTrigger>
                                    </FormControl>
                                    <SelectContent>
                                      <SelectItem value="Pending">Pending</SelectItem>
                                      <SelectItem value="Passed">Passed</SelectItem>
                                      <SelectItem value="Failed">Failed</SelectItem>
                                      <SelectItem value="Not Attended">Not Attended</SelectItem>
                                    </SelectContent>
                                  </Select>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                            <FormField
                              control={roundForm.control}
                              name="scheduled_at"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Scheduled At (Optional)</FormLabel>
                                  <FormControl>
                                    <Input type="datetime-local" {...field} />
                                  </FormControl>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                            <FormField
                              control={roundForm.control}
                              name="external_link"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Link (Optional)</FormLabel>
                                  <FormControl>
                                    <Input placeholder="https://meet.google.com/..." {...field} />
                                  </FormControl>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                          </div>
                          
                          <div className="flex justify-end gap-2 pt-2">
                            <Button variant="outline" size="sm" type="button" onClick={() => setShowRoundForm(false)}>
                              Cancel
                            </Button>
                            <Button size="sm" type="submit" disabled={roundActionLoading}>
                              {roundActionLoading ? 'Saving...' : 'Save Round'}
                            </Button>
                          </div>
                        </form>
                      </Form>
                    </CardContent>
                  </Card>
                ) : roundsLoading ? (
                  <div className="flex justify-center p-4">
                    <div className="h-5 w-5 animate-spin rounded-full border-b-2 border-primary"></div>
                  </div>
                ) : rounds.length === 0 ? (
                  <div className="text-center py-6 bg-muted/20 rounded-lg border border-dashed">
                    <p className="text-sm text-muted-foreground">No rounds have been added yet.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {rounds.map((round) => (
                      <div key={round.id} className="relative pl-6 border-l-2 border-muted pb-4 last:border-0 last:pb-0">
                        <div className="absolute w-3 h-3 bg-background border-2 border-primary rounded-full -left-[7px] top-1.5"></div>
                        
                        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 bg-card border rounded-lg p-4 shadow-sm group">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-sm text-muted-foreground">Round {round.round_number}</span>
                              <h4 className="font-medium text-base">{round.title || round.round_type}</h4>
                            </div>
                            <p className="text-sm text-muted-foreground flex items-center">
                              <Calendar className="h-3 w-3 mr-1" />
                              {round.scheduled_at 
                                ? format(new Date(round.scheduled_at), 'MMM d, yyyy · h:mm a') 
                                : 'To be scheduled'}
                            </p>
                          </div>
                          
                          <div className="flex flex-col items-start sm:items-end gap-2">
                            <div className="flex items-center gap-2">
                              {getRoundStatusBadge(round.status, round.result)}
                              <Button 
                                variant="ghost" 
                                size="icon" 
                                className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                                onClick={() => handleEditRound(round)}
                              >
                                <Edit className="h-3 w-3" />
                              </Button>
                            </div>
                            
                            {round.external_link && (
                              <Button variant="outline" size="sm" className="h-7 text-xs" asChild>
                                <a href={round.external_link} target="_blank" rel="noopener noreferrer">
                                  <ExternalLink className="h-3 w-3 mr-1" /> Open Link
                                </a>
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </AppLayout>
  );
}
