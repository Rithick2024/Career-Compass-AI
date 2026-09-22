import { useState, useEffect, useMemo } from 'react';
import {
  GraduationCap,
  Plus,
  Search,
  Pencil,
  Power,
  RefreshCw,
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
import { useAuth } from '@/features/auth/context/AuthContext';
import { AxiosError } from 'axios';
import { departmentService, Department } from '../services/department.service';

export default function StaffDepartmentsPage() {
  const { user } = useAuth();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');

  // Add modal state
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [addName, setAddName] = useState('');
  const [isSubmittingAdd, setIsSubmittingAdd] = useState(false);

  // Edit modal state
  const [editingDept, setEditingDept] = useState<Department | null>(null);
  const [editName, setEditName] = useState('');
  const [isSubmittingEdit, setIsSubmittingEdit] = useState(false);

  // Toggle status state
  const [toggleDept, setToggleDept] = useState<Department | null>(null);
  const [isSubmittingToggle, setIsSubmittingToggle] = useState(false);

  const fetchDepartments = async () => {
    setLoading(true);
    try {
      const data = await departmentService.getStaffDepartments();
      setDepartments(data);
    } catch (err: unknown) {
      const msg = err instanceof AxiosError ? err.response?.data?.detail : 'Failed to load departments';
      toast.error(msg || 'Failed to load departments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDepartments();
  }, []);

  const filteredDepartments = useMemo(() => {
    return departments.filter((dept) => {
      const matchesSearch = dept.name.toLowerCase().includes(search.toLowerCase());
      const matchesStatus =
        statusFilter === 'all'
          ? true
          : statusFilter === 'active'
          ? dept.is_active
          : !dept.is_active;
      return matchesSearch && matchesStatus;
    });
  }, [departments, search, statusFilter]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!addName.trim()) {
      toast.error('Department name is required');
      return;
    }

    setIsSubmittingAdd(true);
    try {
      const newDept = await departmentService.createDepartment({ name: addName.trim() });
      toast.success(`Department "${newDept.name}" created successfully.`);
      setAddName('');
      setIsAddOpen(false);
      fetchDepartments();
    } catch (err: unknown) {
      const msg = err instanceof AxiosError ? (err.response?.data?.message || err.response?.data?.detail) : 'Failed to create department';
      toast.error(msg || 'Failed to create department');
    } finally {
      setIsSubmittingAdd(false);
    }
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingDept || !editName.trim()) {
      toast.error('Department name is required');
      return;
    }

    setIsSubmittingEdit(true);
    try {
      const updated = await departmentService.updateDepartment(editingDept.id, { name: editName.trim() });
      toast.success(`Department updated to "${updated.name}".`);
      setEditingDept(null);
      setEditName('');
      fetchDepartments();
    } catch (err: unknown) {
      const msg = err instanceof AxiosError ? (err.response?.data?.message || err.response?.data?.detail) : 'Failed to update department';
      toast.error(msg || 'Failed to update department');
    } finally {
      setIsSubmittingEdit(false);
    }
  };

  const handleToggleStatus = async () => {
    if (!toggleDept) return;
    setIsSubmittingToggle(true);
    try {
      const updated = await departmentService.updateDepartmentStatus(
        toggleDept.id,
        !toggleDept.is_active
      );
      toast.success(
        `Department "${updated.name}" is now ${updated.is_active ? 'active' : 'inactive'}.`
      );
      setToggleDept(null);
      fetchDepartments();
    } catch (err: unknown) {
      const msg = err instanceof AxiosError ? (err.response?.data?.message || err.response?.data?.detail) : 'Failed to update status';
      toast.error(msg || 'Failed to update status');
    } finally {
      setIsSubmittingToggle(false);
    }
  };

  const userEmail = user?.email || 'Staff Member';
  const avatarText = userEmail.substring(0, 2).toUpperCase();

  return (
    <AppLayout role="staff" userName={userEmail} userRole="Staff" avatarText={avatarText}>
      <PageContainer>
        <PageHeader
          title="Department Management"
          description="Manage academic departments across the institution."
          action={
            <Button onClick={() => setIsAddOpen(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              Add Department
            </Button>
          }
        />

        {/* Filter bar */}
        <Card className="mb-6">
          <CardContent className="pt-6 flex flex-col md:flex-row gap-4 justify-between items-center">
            <div className="relative w-full md:w-80">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search departments..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>

            <div className="flex items-center gap-2 w-full md:w-auto">
              <span className="text-sm font-medium text-muted-foreground">Status:</span>
              <div className="flex bg-muted p-1 rounded-lg">
                {(['all', 'active', 'inactive'] as const).map((st) => (
                  <button
                    key={st}
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

              <Button variant="ghost" size="icon" onClick={fetchDepartments} title="Refresh Data">
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Table view */}
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-12 text-center text-muted-foreground">
                <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2" />
                Loading departments...
              </div>
            ) : filteredDepartments.length === 0 ? (
              <div className="p-12 text-center text-muted-foreground">
                <GraduationCap className="h-8 w-8 mx-auto mb-2 opacity-50" />
                No departments found.
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-16">ID</TableHead>
                    <TableHead>Department Name</TableHead>
                    <TableHead className="w-32">Status</TableHead>
                    <TableHead className="w-36 text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredDepartments.map((dept) => (
                    <TableRow key={dept.id}>
                      <TableCell className="font-mono text-xs text-muted-foreground">
                        #{dept.id}
                      </TableCell>
                      <TableCell className="font-medium">{dept.name}</TableCell>
                      <TableCell>
                        {dept.is_active ? (
                          <Badge variant="default" className="bg-emerald-500/15 text-emerald-600 hover:bg-emerald-500/25 border-emerald-500/30">
                            Active
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="bg-slate-100 text-slate-600 border-slate-200">
                            Inactive
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => {
                              setEditingDept(dept);
                              setEditName(dept.name);
                            }}
                            title="Edit Name"
                          >
                            <Pencil className="h-4 w-4 text-muted-foreground hover:text-foreground" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setToggleDept(dept)}
                            title={dept.is_active ? 'Deactivate' : 'Reactivate'}
                          >
                            <Power
                              className={`h-4 w-4 ${
                                dept.is_active
                                  ? 'text-red-500 hover:text-red-600'
                                  : 'text-emerald-500 hover:text-emerald-600'
                              }`}
                            />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Add Modal */}
        <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add New Department</DialogTitle>
              <DialogDescription>
                Enter the official academic department name.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreate}>
              <div className="py-4 space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="add-name">Department Name</Label>
                  <Input
                    id="add-name"
                    placeholder="e.g. Artificial Intelligence & Data Science"
                    value={addName}
                    onChange={(e) => setAddName(e.target.value)}
                    required
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" type="button" onClick={() => setIsAddOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={isSubmittingAdd}>
                  {isSubmittingAdd ? 'Saving...' : 'Add Department'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Edit Modal */}
        <Dialog open={!!editingDept} onOpenChange={(open) => !open && setEditingDept(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Edit Department</DialogTitle>
              <DialogDescription>
                Update the department title. References on existing student profiles will reflect the new name.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleEdit}>
              <div className="py-4 space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="edit-name">Department Name</Label>
                  <Input
                    id="edit-name"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    required
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" type="button" onClick={() => setEditingDept(null)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={isSubmittingEdit}>
                  {isSubmittingEdit ? 'Updating...' : 'Save Changes'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Status Confirmation Modal */}
        <Dialog open={!!toggleDept} onOpenChange={(open) => !open && setToggleDept(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {toggleDept?.is_active ? 'Deactivate Department?' : 'Reactivate Department?'}
              </DialogTitle>
              <DialogDescription>
                {toggleDept?.is_active
                  ? `Deactivating "${toggleDept?.name}" will hide it from new student selection. Existing students assigned to this department will retain their profile reference.`
                  : `Reactivating "${toggleDept?.name}" will make it selectable again for new student registrations and profile updates.`}
              </DialogDescription>
            </DialogHeader>
            <DialogFooter className="mt-4">
              <Button variant="outline" onClick={() => setToggleDept(null)}>
                Cancel
              </Button>
              <Button
                variant={toggleDept?.is_active ? 'destructive' : 'default'}
                onClick={handleToggleStatus}
                disabled={isSubmittingToggle}
              >
                {isSubmittingToggle
                  ? 'Updating...'
                  : toggleDept?.is_active
                  ? 'Deactivate'
                  : 'Reactivate'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </PageContainer>
    </AppLayout>
  );
}
