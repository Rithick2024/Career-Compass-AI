import { useState, useEffect, useCallback } from 'react';
import {
  Search,
  Eye,
  Building,
  GraduationCap,
  Trophy,
  CheckCircle2,
  XCircle
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
import { Label } from '@/components/ui/label';

import { useAuth } from '@/features/auth/context/AuthContext';
import {
  listStaffPlacements,
  getStaffPlacement,
  updatePlacement,
  StaffPlacementResponse
} from '../services/placement.service';

export default function StaffPlacementsPage() {
  const { user } = useAuth();
  const [placements, setPlacements] = useState<StaffPlacementResponse[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  
  // Dialog State
  const [selectedPlacement, setSelectedPlacement] = useState<StaffPlacementResponse | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [updateLoading, setUpdateLoading] = useState(false);

  // Form State
  const [ctc, setCtc] = useState<string>('');
  const [placedDate, setPlacedDate] = useState<string>('');

  const fetchPlacements = useCallback(async () => {
    setLoading(true);
    try {
      const offerAccepted = statusFilter === 'accepted' ? true : statusFilter === 'pending' ? false : undefined;
      const data = await listStaffPlacements({
        search,
        offer_accepted: offerAccepted,
      });
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
  }, [search, statusFilter]);

  useEffect(() => {
    fetchPlacements();
  }, [fetchPlacements]);

  const handleViewDetails = async (id: number) => {
    setDetailLoading(true);
    setDialogOpen(true);
    try {
      const data = await getStaffPlacement(id);
      setSelectedPlacement(data);
      setCtc(data.placement.final_package_ctc.toString());
      setPlacedDate(data.placement.placement_date);
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.detail || err.response?.data?.message
          : 'Failed to fetch placement details';
      toast.error(msg || 'Failed to fetch placement details');
      setDialogOpen(false);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleUpdate = async () => {
    if (!selectedPlacement) return;
    setUpdateLoading(true);
    try {
      const data = await updatePlacement(selectedPlacement.placement.id, {
        final_package_ctc: parseFloat(ctc),
        placement_date: placedDate
      });
      setSelectedPlacement(data);
      toast.success('Placement details updated successfully');
      fetchPlacements();
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.detail || err.response?.data?.message
          : 'Failed to update placement details';
      toast.error(msg || 'Failed to update placement details');
    } finally {
      setUpdateLoading(false);
    }
  };

  const handleToggleOffer = async () => {
    if (!selectedPlacement) return;
    setUpdateLoading(true);
    try {
      const newStatus = !selectedPlacement.placement.offer_accepted;
      const data = await updatePlacement(selectedPlacement.placement.id, {
        offer_accepted: newStatus
      });
      setSelectedPlacement(data);
      toast.success(`Offer marked as ${newStatus ? 'Accepted' : 'Pending'}`);
      fetchPlacements();
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.detail || err.response?.data?.message
          : 'Failed to update offer status';
      toast.error(msg || 'Failed to update offer status');
    } finally {
      setUpdateLoading(false);
    }
  };

  return (
    <AppLayout role="staff" userName={user?.email || 'Staff'} userRole="Staff" avatarText="SA">
      <PageContainer>
        <PageHeader
          title="Placements"
          description="Manage student job placements and accepted offers."
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
                  <SelectValue placeholder="Filter by Offer Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Offers</SelectItem>
                  <SelectItem value="accepted">Accepted Offers</SelectItem>
                  <SelectItem value="pending">Pending Offers</SelectItem>
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
                  <TableHead>CTC</TableHead>
                  <TableHead>Placed On</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={6} className="h-32 text-center">
                      <div className="flex items-center justify-center">
                        <div className="h-6 w-6 animate-spin rounded-full border-b-2 border-primary"></div>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : placements.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="h-32 text-center text-muted-foreground">
                      No placements found.
                    </TableCell>
                  </TableRow>
                ) : (
                  placements.map(({ placement, student, job, company }) => (
                    <TableRow key={placement.id}>
                      <TableCell>
                        <div className="font-medium">{student.full_name || 'N/A'}</div>
                        <div className="text-xs text-muted-foreground">ID: {student.id}</div>
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">{job.title}</div>
                        <div className="text-xs text-muted-foreground flex items-center">
                          <Building className="h-3 w-3 mr-1" />
                          {company.name}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="font-medium text-green-700 dark:text-green-400">
                          {placement.final_package_ctc} LPA
                        </div>
                      </TableCell>
                      <TableCell className="text-muted-foreground text-sm">
                        {format(new Date(placement.placement_date), 'MMM d, yyyy')}
                      </TableCell>
                      <TableCell>
                        {placement.offer_accepted ? (
                           <Badge variant="default" className="bg-green-100 text-green-800 hover:bg-green-100 dark:bg-green-900/30 dark:text-green-400 border-none">
                             <CheckCircle2 className="h-3 w-3 mr-1" /> Accepted
                           </Badge>
                         ) : (
                           <Badge variant="secondary" className="bg-amber-100 text-amber-800 hover:bg-amber-100 dark:bg-amber-900/30 dark:text-amber-400 border-none">
                             <XCircle className="h-3 w-3 mr-1" /> Pending
                           </Badge>
                         )}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleViewDetails(placement.id)}
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

      {/* Placement Details Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Placement Details</DialogTitle>
            <DialogDescription>
              Review or update the placement details.
            </DialogDescription>
          </DialogHeader>

          {detailLoading || !selectedPlacement ? (
            <div className="flex justify-center p-8">
              <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-primary"></div>
            </div>
          ) : (
            <div className="space-y-6 mt-4">
              <div className="p-4 bg-muted/50 rounded-lg border flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-lg">{selectedPlacement.student.full_name}</h3>
                  <p className="text-sm text-muted-foreground flex items-center mt-1">
                    <GraduationCap className="h-4 w-4 mr-1" />
                    Dept ID: {selectedPlacement.student.department_id || 'N/A'} • CGPA: {selectedPlacement.student.cgpa || 'N/A'}
                  </p>
                </div>
                {selectedPlacement.placement.offer_accepted && (
                  <Trophy className="h-8 w-8 text-green-500 opacity-80" />
                )}
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Job Title</span>
                  <p className="font-medium">{selectedPlacement.job.title}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Company</span>
                  <p className="font-medium">{selectedPlacement.company.name}</p>
                </div>
              </div>

              <div className="space-y-4 pt-4 border-t">
                <div className="grid gap-2">
                  <Label htmlFor="ctc">Final CTC (LPA)</Label>
                  <Input
                    id="ctc"
                    type="number"
                    step="0.01"
                    value={ctc}
                    onChange={(e) => setCtc(e.target.value)}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="placed_date">Placed Date</Label>
                  <Input
                    id="placed_date"
                    type="date"
                    value={placedDate}
                    onChange={(e) => setPlacedDate(e.target.value)}
                  />
                </div>
                <div className="flex items-center justify-between pt-2">
                  <Button variant="outline" onClick={handleToggleOffer} disabled={updateLoading}>
                    {selectedPlacement.placement.offer_accepted ? 'Mark as Pending' : 'Mark as Accepted'}
                  </Button>
                  <Button onClick={handleUpdate} disabled={updateLoading}>
                    {updateLoading ? 'Saving...' : 'Save Changes'}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </AppLayout>
  );
}
