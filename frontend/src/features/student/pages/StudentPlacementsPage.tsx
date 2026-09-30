import { useState, useEffect, useCallback } from 'react';
import {
  Calendar,
  Building,
  CheckCircle2,
  XCircle,
  Trophy,
  DollarSign
} from 'lucide-react';
import toast from 'react-hot-toast';
import { AxiosError } from 'axios';
import { format } from 'date-fns';

import { AppLayout } from '@/components/layout/AppLayout';
import { PageHeader, PageContainer } from '@/components/common/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/features/auth/context/AuthContext';
import { listStudentPlacements, StudentPlacementResponse } from '../services/placement.service';

export default function StudentPlacementsPage() {
  const { user } = useAuth();
  const [placements, setPlacements] = useState<StudentPlacementResponse[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPlacements = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listStudentPlacements();
      setPlacements(data);
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.detail || err.response?.data?.message
          : 'Failed to fetch placements';
      toast.error(msg || 'Failed to fetch placements');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPlacements();
  }, [fetchPlacements]);

  return (
    <AppLayout role="student" userName={user?.email || 'Student'} userRole="Student" avatarText="ST">
      <PageContainer>
        <PageHeader
          title="My Placements"
          description="View your confirmed job placements and offers."
        />

        {loading && (
          <div className="flex justify-center p-8">
            <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-primary"></div>
          </div>
        )}

        {!loading && placements.length === 0 && (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12 text-center">
              <Trophy className="h-12 w-12 text-muted-foreground mb-4 opacity-50" />
              <p className="text-lg font-medium">No placements yet</p>
              <p className="text-sm text-muted-foreground mt-1 max-w-sm">
                You don't have any recorded placements. Keep applying and interviewing!
              </p>
            </CardContent>
          </Card>
        )}

        {!loading && placements.length > 0 && (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {placements.map(({ placement, job, company }) => (
              <Card key={placement.id} className={`flex flex-col relative overflow-hidden group ${placement.offer_accepted ? 'border-green-200 bg-green-50/30 dark:border-green-900/30 dark:bg-green-900/10' : ''}`}>
                {placement.offer_accepted && (
                  <div className="absolute top-0 right-0 w-16 h-16 pointer-events-none overflow-hidden">
                    <div className="absolute top-0 right-0 w-[141%] h-8 origin-bottom-left rotate-45 bg-green-500/20 flex items-center justify-center">
                      <Trophy className="h-4 w-4 text-green-600" />
                    </div>
                  </div>
                )}
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg mb-1">{job.title}</CardTitle>
                      <div className="flex items-center text-muted-foreground text-sm font-medium">
                        <Building className="h-4 w-4 mr-1" />
                        {company.name}
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pb-4 flex-1">
                  <div className="space-y-3 mt-2 text-sm">
                    <div className="flex items-center text-muted-foreground">
                      <DollarSign className="h-4 w-4 mr-2 text-green-600" />
                      <span className="font-medium text-foreground mr-1">CTC:</span>
                      {placement.final_package_ctc} LPA
                    </div>
                    <div className="flex items-center text-muted-foreground">
                      <Calendar className="h-4 w-4 mr-2" />
                      <span className="font-medium text-foreground mr-1">Placed On:</span>
                      {format(new Date(placement.placement_date), 'MMM d, yyyy')}
                    </div>
                    <div className="flex items-center text-muted-foreground pt-2">
                       <span className="mr-2 font-medium">Status:</span>
                       {placement.offer_accepted ? (
                         <Badge variant="default" className="bg-green-100 text-green-800 hover:bg-green-100 dark:bg-green-900/30 dark:text-green-400">
                           <CheckCircle2 className="h-3 w-3 mr-1" /> Offer Accepted
                         </Badge>
                       ) : (
                         <Badge variant="secondary" className="bg-amber-100 text-amber-800 hover:bg-amber-100 dark:bg-amber-900/30 dark:text-amber-400">
                           <XCircle className="h-3 w-3 mr-1" /> Offer Pending
                         </Badge>
                       )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </PageContainer>
    </AppLayout>
  );
}
