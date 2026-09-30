import { useState, useEffect, useCallback } from 'react';
import {
  Briefcase,
  Calendar,
  AlertCircle,
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  Users,
  ExternalLink,
  Star
} from 'lucide-react';
import toast from 'react-hot-toast';
import { AxiosError } from 'axios';
import { format } from 'date-fns';

import { AppLayout } from '@/components/layout/AppLayout';
import { PageHeader, PageContainer } from '@/components/common/PageHeader';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';

import { useAuth } from '@/features/auth/context/AuthContext';
import { studentApplicationService, StudentApplication, ApplicationStatus } from '../services/application.service';
import { studentApplicationRoundService, ApplicationRoundResponse, RoundStatus, RoundResult } from '../services/application-round.service';

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
      return <Clock className="h-4 w-4 mr-1" />;
    case 'Reviewing':
      return <Users className="h-4 w-4 mr-1" />;
    case 'Interview':
      return <Star className="h-4 w-4 mr-1" />;
    case 'Offered':
      return <CheckCircle2 className="h-4 w-4 mr-1" />;
    case 'Rejected':
      return <XCircle className="h-4 w-4 mr-1" />;
    case 'Withdrawn':
      return <AlertCircle className="h-4 w-4 mr-1" />;
    default:
      return null;
  }
};

export default function StudentApplicationsPage() {
  const { user } = useAuth();
  const [applications, setApplications] = useState<StudentApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const [appToWithdraw, setAppToWithdraw] = useState<StudentApplication | null>(null);
  const [withdrawDialogOpen, setWithdrawDialogOpen] = useState(false);

  // Detail Dialog State
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [selectedApp, setSelectedApp] = useState<StudentApplication | null>(null);
  const [rounds, setRounds] = useState<ApplicationRoundResponse[]>([]);
  const [roundsLoading, setRoundsLoading] = useState(false);

  const fetchApplications = useCallback(async () => {
    setLoading(true);
    try {
      const data = await studentApplicationService.listApplications();
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
  }, []);

  useEffect(() => {
    fetchApplications();
  }, [fetchApplications]);

  const handleWithdraw = async () => {
    if (!appToWithdraw) return;
    setActionLoading(true);
    try {
      await studentApplicationService.withdrawApplication(appToWithdraw.id);
      toast.success('Application withdrawn successfully');
      setWithdrawDialogOpen(false);
      setAppToWithdraw(null);
      fetchApplications();
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.detail || err.response?.data?.message
          : 'Failed to withdraw application';
      toast.error(msg || 'Failed to withdraw application');
    } finally {
      setActionLoading(false);
    }
  };

  const handleOpenDetails = async (app: StudentApplication) => {
    setSelectedApp(app);
    setDetailDialogOpen(true);
    setRoundsLoading(true);
    try {
      const data = await studentApplicationRoundService.listRounds(app.id);
      setRounds(data);
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.detail || err.response?.data?.message
          : 'Failed to fetch recruitment timeline';
      toast.error(msg || 'Failed to fetch recruitment timeline');
    } finally {
      setRoundsLoading(false);
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

  return (
    <AppLayout role="student" userName={user?.email || 'Student'} userRole="Student" avatarText="ST">
      <PageContainer>
        <PageHeader
          title="My Applications"
          description="Track the status of your job applications."
        />

        {loading && (
          <div className="flex justify-center p-8">
            <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-primary"></div>
          </div>
        )}

        {!loading && applications.length === 0 && (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12 text-center">
              <FileText className="h-12 w-12 text-muted-foreground mb-4 opacity-50" />
              <p className="text-lg font-medium">No applications found</p>
              <p className="text-sm text-muted-foreground mt-1 max-w-sm">
                You haven't applied to any jobs yet. Check out the Job Discovery page to find opportunities.
              </p>
            </CardContent>
          </Card>
        )}

        {!loading && applications.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {applications.map((app) => (
              <Card key={app.id} className="flex flex-col relative overflow-hidden group">
                {app.status === 'Offered' && (
                  <div className="absolute top-0 right-0 w-16 h-16 pointer-events-none overflow-hidden">
                    <div className="absolute top-0 right-0 w-[141%] h-8 origin-bottom-left rotate-45 bg-green-500/20 flex items-center justify-center">
                      <Star className="h-4 w-4 text-green-600" />
                    </div>
                  </div>
                )}
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg mb-1 flex items-center gap-2">
                        <Briefcase className="h-5 w-5 text-primary" />
                        Job #{app.job_id}
                      </CardTitle>
                    </div>
                    <Badge variant={getStatusBadgeVariant(app.status)} className="flex items-center">
                      {getStatusIcon(app.status)}
                      {app.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="pb-4 flex-1">
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center text-muted-foreground">
                      <FileText className="h-4 w-4 mr-2" />
                      Applied with Resume #{app.resume_id}
                    </div>
                    <div className="flex items-center text-muted-foreground">
                      <Calendar className="h-4 w-4 mr-2" />
                      Applied on: {format(new Date(app.applied_at), 'MMM d, yyyy')}
                    </div>
                  </div>
                </CardContent>
                <CardFooter className="pt-0 flex justify-between">
                  <Button variant="ghost" size="sm" onClick={() => handleOpenDetails(app)}>
                    View Timeline
                  </Button>
                  {(app.status === 'Pending' || app.status === 'Reviewing') && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        setAppToWithdraw(app);
                        setWithdrawDialogOpen(true);
                      }}
                    >
                      Withdraw
                    </Button>
                  )}
                </CardFooter>
              </Card>
            ))}
          </div>
        )}
      </PageContainer>

      {/* Detail Dialog */}
      <Dialog open={detailDialogOpen} onOpenChange={setDetailDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Application Details</DialogTitle>
            <DialogDescription>
              Recruitment timeline for Job #{selectedApp?.job_id}
            </DialogDescription>
          </DialogHeader>
          
          {selectedApp && (
            <div className="space-y-6 mt-4">
              <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Current Status</p>
                  <div className="mt-1 flex items-center gap-2">
                    <Badge variant={getStatusBadgeVariant(selectedApp.status)} className="text-sm py-1">
                      {getStatusIcon(selectedApp.status)}
                      {selectedApp.status}
                    </Badge>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-muted-foreground">Applied On</p>
                  <p className="mt-1 font-medium">{format(new Date(selectedApp.applied_at), 'MMM d, yyyy')}</p>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-4">Recruitment Timeline</h3>
                
                {roundsLoading ? (
                  <div className="flex justify-center p-8">
                    <div className="h-6 w-6 animate-spin rounded-full border-b-2 border-primary"></div>
                  </div>
                ) : rounds.length === 0 ? (
                  <div className="text-center py-8 bg-muted/20 rounded-lg border border-dashed">
                    <Clock className="h-8 w-8 text-muted-foreground mx-auto mb-2 opacity-50" />
                    <p className="text-sm text-muted-foreground">No recruitment rounds have been scheduled for this application yet.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {rounds.map((round, index) => (
                      <div key={round.id} className="relative pl-6 border-l-2 border-muted pb-4 last:border-0 last:pb-0">
                        <div className="absolute w-3 h-3 bg-background border-2 border-primary rounded-full -left-[7px] top-1.5"></div>
                        
                        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 bg-card border rounded-lg p-4 shadow-sm">
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
                            </div>
                            
                            {round.external_link && (round.status === 'Scheduled' || round.status === 'In Progress') && (
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
          
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setDetailDialogOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Withdraw Dialog */}
      <Dialog open={withdrawDialogOpen} onOpenChange={setWithdrawDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Withdraw Application</DialogTitle>
            <DialogDescription>
              Are you sure you want to withdraw your application? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setWithdrawDialogOpen(false)} disabled={actionLoading}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleWithdraw} disabled={actionLoading}>
              {actionLoading ? 'Withdrawing...' : 'Withdraw Application'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppLayout>
  );
}
