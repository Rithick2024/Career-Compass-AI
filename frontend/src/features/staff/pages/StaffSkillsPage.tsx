import { useState, useEffect, useMemo } from 'react';
import {
  Sparkles,
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
import { staffSkillService, StaffSkill } from '../services/staff-skills.service';

export default function StaffSkillsPage() {
  const { user } = useAuth();
  const [skills, setSkills] = useState<StaffSkill[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');

  // Add modal state
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [addName, setAddName] = useState('');
  const [addCategory, setAddCategory] = useState('');
  const [isSubmittingAdd, setIsSubmittingAdd] = useState(false);

  // Edit modal state
  const [editingSkill, setEditingSkill] = useState<StaffSkill | null>(null);
  const [editName, setEditName] = useState('');
  const [editCategory, setEditCategory] = useState('');
  const [isSubmittingEdit, setIsSubmittingEdit] = useState(false);

  // Toggle status state
  const [toggleSkill, setToggleSkill] = useState<StaffSkill | null>(null);
  const [isSubmittingToggle, setIsSubmittingToggle] = useState(false);

  const fetchSkills = async () => {
    setLoading(true);
    try {
      const data = await staffSkillService.getStaffSkills();
      setSkills(data);
    } catch (err: unknown) {
      const msg = err instanceof AxiosError ? err.response?.data?.detail : 'Failed to load skills';
      toast.error(msg || 'Failed to load skills');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSkills();
  }, []);

  const categories = useMemo(() => {
    const cats = new Set<string>();
    skills.forEach((s) => {
      if (s.category) cats.add(s.category);
    });
    return Array.from(cats);
  }, [skills]);

  const filteredSkills = useMemo(() => {
    return skills.filter((skill) => {
      const matchesSearch =
        skill.name.toLowerCase().includes(search.toLowerCase()) ||
        (skill.category && skill.category.toLowerCase().includes(search.toLowerCase()));
      const matchesStatus =
        statusFilter === 'all'
          ? true
          : statusFilter === 'active'
          ? skill.is_active
          : !skill.is_active;
      const matchesCategory =
        categoryFilter === 'all' ? true : skill.category === categoryFilter;
      return matchesSearch && matchesStatus && matchesCategory;
    });
  }, [skills, search, statusFilter, categoryFilter]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!addName.trim()) {
      toast.error('Skill name is required');
      return;
    }

    setIsSubmittingAdd(true);
    try {
      const newSkill = await staffSkillService.createSkill({
        name: addName.trim(),
        category: addCategory.trim() || null,
      });
      toast.success(`Skill "${newSkill.name}" created successfully.`);
      setAddName('');
      setAddCategory('');
      setIsAddOpen(false);
      fetchSkills();
    } catch (err: unknown) {
      const msg = err instanceof AxiosError ? (err.response?.data?.message || err.response?.data?.detail) : 'Failed to create skill';
      toast.error(msg || 'Failed to create skill');
    } finally {
      setIsSubmittingAdd(false);
    }
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingSkill || !editName.trim()) {
      toast.error('Skill name is required');
      return;
    }

    setIsSubmittingEdit(true);
    try {
      const updated = await staffSkillService.updateSkill(editingSkill.id, {
        name: editName.trim(),
        category: editCategory.trim() || null,
      });
      toast.success(`Skill updated to "${updated.name}".`);
      setEditingSkill(null);
      setEditName('');
      setEditCategory('');
      fetchSkills();
    } catch (err: unknown) {
      const msg = err instanceof AxiosError ? (err.response?.data?.message || err.response?.data?.detail) : 'Failed to update skill';
      toast.error(msg || 'Failed to update skill');
    } finally {
      setIsSubmittingEdit(false);
    }
  };

  const handleToggleStatus = async () => {
    if (!toggleSkill) return;
    setIsSubmittingToggle(true);
    try {
      const updated = await staffSkillService.updateSkillStatus(
        toggleSkill.id,
        !toggleSkill.is_active
      );
      toast.success(
        `Skill "${updated.name}" is now ${updated.is_active ? 'active' : 'inactive'}.`
      );
      setToggleSkill(null);
      fetchSkills();
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
          title="Skills Catalog Management"
          description="Manage master skill taxonomy and categories for student profiles."
          action={
            <Button onClick={() => setIsAddOpen(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              Add Skill
            </Button>
          }
        />

        {/* Filter Bar */}
        <Card className="mb-6">
          <CardContent className="pt-6 flex flex-col md:flex-row gap-4 justify-between items-center">
            <div className="relative w-full md:w-80">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search skills or categories..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>

            <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
              {categories.length > 0 && (
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="h-9 px-3 py-1 text-xs border border-input bg-background rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="all">All Categories</option>
                  {categories.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              )}

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

              <Button variant="ghost" size="icon" onClick={fetchSkills} title="Refresh Catalog">
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Table View */}
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-12 text-center text-muted-foreground">
                <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2" />
                Loading skill catalog...
              </div>
            ) : filteredSkills.length === 0 ? (
              <div className="p-12 text-center text-muted-foreground">
                <Sparkles className="h-8 w-8 mx-auto mb-2 opacity-50" />
                No skills found matching your filters.
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-16">ID</TableHead>
                    <TableHead>Skill Name</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead className="w-32">Status</TableHead>
                    <TableHead className="w-36 text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredSkills.map((skill) => (
                    <TableRow key={skill.id}>
                      <TableCell className="font-mono text-xs text-muted-foreground">
                        #{skill.id}
                      </TableCell>
                      <TableCell className="font-medium">{skill.name}</TableCell>
                      <TableCell>
                        {skill.category ? (
                          <Badge variant="outline" className="font-normal text-xs">
                            {skill.category}
                          </Badge>
                        ) : (
                          <span className="text-xs text-muted-foreground italic">Uncategorized</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {skill.is_active ? (
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
                              setEditingSkill(skill);
                              setEditName(skill.name);
                              setEditCategory(skill.category || '');
                            }}
                            title="Edit Skill"
                          >
                            <Pencil className="h-4 w-4 text-muted-foreground hover:text-foreground" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setToggleSkill(skill)}
                            title={skill.is_active ? 'Deactivate' : 'Reactivate'}
                          >
                            <Power
                              className={`h-4 w-4 ${
                                skill.is_active
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
              <DialogTitle>Add New Skill</DialogTitle>
              <DialogDescription>
                Add a skill to the master catalog for student proficiency selection.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreate}>
              <div className="py-4 space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="skill-name">Skill Name</Label>
                  <Input
                    id="skill-name"
                    placeholder="e.g. PyTorch"
                    value={addName}
                    onChange={(e) => setAddName(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="skill-category">Category (Optional)</Label>
                  <Input
                    id="skill-category"
                    placeholder="e.g. Machine Learning, Web Development"
                    value={addCategory}
                    onChange={(e) => setAddCategory(e.target.value)}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" type="button" onClick={() => setIsAddOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={isSubmittingAdd}>
                  {isSubmittingAdd ? 'Saving...' : 'Add Skill'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Edit Modal */}
        <Dialog open={!!editingSkill} onOpenChange={(open) => !open && setEditingSkill(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Edit Skill</DialogTitle>
              <DialogDescription>
                Update skill name or category in the master catalog.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleEdit}>
              <div className="py-4 space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="edit-skill-name">Skill Name</Label>
                  <Input
                    id="edit-skill-name"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="edit-skill-category">Category (Optional)</Label>
                  <Input
                    id="edit-skill-category"
                    value={editCategory}
                    onChange={(e) => setEditCategory(e.target.value)}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" type="button" onClick={() => setEditingSkill(null)}>
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
        <Dialog open={!!toggleSkill} onOpenChange={(open) => !open && setToggleSkill(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {toggleSkill?.is_active ? 'Deactivate Skill?' : 'Reactivate Skill?'}
              </DialogTitle>
              <DialogDescription>
                {toggleSkill?.is_active
                  ? `Deactivating "${toggleSkill?.name}" will prevent students from adding it as a NEW skill. Existing students who already have this skill on their profile will retain it.`
                  : `Reactivating "${toggleSkill?.name}" will make it available for new student selections again.`}
              </DialogDescription>
            </DialogHeader>
            <DialogFooter className="mt-4">
              <Button variant="outline" onClick={() => setToggleSkill(null)}>
                Cancel
              </Button>
              <Button
                variant={toggleSkill?.is_active ? 'destructive' : 'default'}
                onClick={handleToggleStatus}
                disabled={isSubmittingToggle}
              >
                {isSubmittingToggle
                  ? 'Updating...'
                  : toggleSkill?.is_active
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
