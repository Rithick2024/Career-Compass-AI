import { useState, useEffect, useCallback } from 'react';
import {
  Building2,
  Plus,
  Search,
  Pencil,
  Power,
  RefreshCw,
  Globe,
  MapPin,
  ExternalLink,
} from 'lucide-react';
import toast from 'react-hot-toast';

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
import { useAuth } from '@/features/auth/context/AuthContext';
import { AxiosError } from 'axios';
import { companyService, Company } from '../services/company.service';

export default function StaffCompaniesPage() {
  const { user } = useAuth();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');

  // Add modal state
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [addName, setAddName] = useState('');
  const [addIndustry, setAddIndustry] = useState('');
  const [addLocation, setAddLocation] = useState('');
  const [addWebsite, setAddWebsite] = useState('');
  const [addDescription, setAddDescription] = useState('');
  const [isSubmittingAdd, setIsSubmittingAdd] = useState(false);

  // Edit modal state
  const [editingCompany, setEditingCompany] = useState<Company | null>(null);
  const [editName, setEditName] = useState('');
  const [editIndustry, setEditIndustry] = useState('');
  const [editLocation, setEditLocation] = useState('');
  const [editWebsite, setEditWebsite] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [isSubmittingEdit, setIsSubmittingEdit] = useState(false);

  // Toggle status state
  const [toggleCompany, setToggleCompany] = useState<Company | null>(null);
  const [isSubmittingToggle, setIsSubmittingToggle] = useState(false);

  const fetchCompanies = useCallback(async () => {
    setLoading(true);
    try {
      const data = await companyService.getStaffCompanies(search, statusFilter);
      setCompanies(data);
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.detail || err.response?.data?.message
          : 'Failed to load companies';
      toast.error(msg || 'Failed to load companies');
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter]);

  useEffect(() => {
    fetchCompanies();
  }, [fetchCompanies]);

  const formatWebsiteUrl = (url: string): string => {
    const trimmed = url.trim();
    if (!trimmed) return '';
    if (!/^https?:\/\//i.test(trimmed)) {
      return `https://${trimmed}`;
    }
    return trimmed;
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!addName.trim()) {
      toast.error('Company name is required');
      return;
    }

    const websiteUrl = addWebsite.trim() ? formatWebsiteUrl(addWebsite) : undefined;

    setIsSubmittingAdd(true);
    try {
      const newCompany = await companyService.createCompany({
        name: addName.trim(),
        industry: addIndustry.trim() || undefined,
        location: addLocation.trim() || undefined,
        website: websiteUrl,
        description: addDescription.trim() || undefined,
      });
      toast.success(`Company "${newCompany.name}" created successfully.`);
      setAddName('');
      setAddIndustry('');
      setAddLocation('');
      setAddWebsite('');
      setAddDescription('');
      setIsAddOpen(false);
      fetchCompanies();
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.message || err.response?.data?.detail
          : 'Failed to create company';
      toast.error(msg || 'Failed to create company');
    } finally {
      setIsSubmittingAdd(false);
    }
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingCompany || !editName.trim()) {
      toast.error('Company name is required');
      return;
    }

    const websiteUrl = editWebsite.trim() ? formatWebsiteUrl(editWebsite) : undefined;

    setIsSubmittingEdit(true);
    try {
      const updated = await companyService.updateCompany(editingCompany.id, {
        name: editName.trim(),
        industry: editIndustry.trim() || undefined,
        location: editLocation.trim() || undefined,
        website: websiteUrl,
        description: editDescription.trim() || undefined,
      });
      toast.success(`Company "${updated.name}" updated successfully.`);
      setEditingCompany(null);
      fetchCompanies();
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.message || err.response?.data?.detail
          : 'Failed to update company';
      toast.error(msg || 'Failed to update company');
    } finally {
      setIsSubmittingEdit(false);
    }
  };

  const handleToggleStatus = async () => {
    if (!toggleCompany) return;
    setIsSubmittingToggle(true);
    try {
      const updated = await companyService.updateCompanyStatus(
        toggleCompany.id,
        !toggleCompany.is_active
      );
      toast.success(
        `Company "${updated.name}" is now ${updated.is_active ? 'active' : 'inactive'}.`
      );
      setToggleCompany(null);
      fetchCompanies();
    } catch (err: unknown) {
      const msg =
        err instanceof AxiosError
          ? err.response?.data?.message || err.response?.data?.detail
          : 'Failed to update company status';
      toast.error(msg || 'Failed to update company status');
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
          title="Company Management"
          description="Manage companies and hiring organizations used by the placement platform."
          action={
            <Button onClick={() => setIsAddOpen(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              Add Company
            </Button>
          }
        />

        {/* Filter Bar */}
        <Card className="mb-6">
          <CardContent className="pt-6 flex flex-col md:flex-row gap-4 justify-between items-center">
            <div className="relative w-full md:w-80">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by name, industry, location..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>

            <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
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

              <Button variant="ghost" size="icon" onClick={fetchCompanies} title="Refresh Data">
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
                Loading companies...
              </div>
            ) : companies.length === 0 ? (
              <div className="p-12 text-center text-muted-foreground">
                <Building2 className="h-8 w-8 mx-auto mb-2 opacity-50" />
                No companies found matching your filters.
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-16">ID</TableHead>
                    <TableHead>Company</TableHead>
                    <TableHead>Industry</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead className="w-32">Status</TableHead>
                    <TableHead className="w-36 text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {companies.map((comp) => (
                    <TableRow key={comp.id}>
                      <TableCell className="font-mono text-xs text-muted-foreground">
                        #{comp.id}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium text-foreground">{comp.name}</span>
                          {comp.website && (
                            <a
                              href={comp.website}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-1 text-xs text-primary hover:underline mt-0.5"
                            >
                              <Globe className="h-3 w-3" />
                              {comp.website.replace(/^https?:\/\//i, '')}
                              <ExternalLink className="h-2.5 w-2.5 opacity-70" />
                            </a>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        {comp.industry ? (
                          <Badge variant="outline" className="font-normal text-xs">
                            {comp.industry}
                          </Badge>
                        ) : (
                          <span className="text-xs text-muted-foreground italic">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {comp.location ? (
                          <div className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                            <MapPin className="h-3 w-3 shrink-0 text-muted-foreground" />
                            {comp.location}
                          </div>
                        ) : (
                          <span className="text-xs text-muted-foreground italic">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {comp.is_active ? (
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
                              setEditingCompany(comp);
                              setEditName(comp.name);
                              setEditIndustry(comp.industry || '');
                              setEditLocation(comp.location || '');
                              setEditWebsite(comp.website || '');
                              setEditDescription(comp.description || '');
                            }}
                            title="Edit Company"
                          >
                            <Pencil className="h-4 w-4 text-muted-foreground hover:text-foreground" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setToggleCompany(comp)}
                            title={comp.is_active ? 'Deactivate' : 'Reactivate'}
                          >
                            <Power
                              className={`h-4 w-4 ${
                                comp.is_active
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
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>Add New Company</DialogTitle>
              <DialogDescription>
                Enter hiring organization details for placement management.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreate}>
              <div className="py-4 space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="add-company-name">Company Name *</Label>
                  <Input
                    id="add-company-name"
                    placeholder="e.g. Acme Technologies"
                    value={addName}
                    onChange={(e) => setAddName(e.target.value)}
                    required
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="add-company-industry">Industry</Label>
                    <Input
                      id="add-company-industry"
                      placeholder="e.g. IT Services, FinTech"
                      value={addIndustry}
                      onChange={(e) => setAddIndustry(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="add-company-location">Location</Label>
                    <Input
                      id="add-company-location"
                      placeholder="e.g. Bangalore / Remote"
                      value={addLocation}
                      onChange={(e) => setAddLocation(e.target.value)}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="add-company-website">Website URL</Label>
                  <Input
                    id="add-company-website"
                    type="url"
                    placeholder="e.g. https://acme.example.com"
                    value={addWebsite}
                    onChange={(e) => setAddWebsite(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="add-company-description">Description</Label>
                  <Textarea
                    id="add-company-description"
                    placeholder="Brief overview of company focus, culture, or hiring history..."
                    value={addDescription}
                    onChange={(e) => setAddDescription(e.target.value)}
                    rows={3}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" type="button" onClick={() => setIsAddOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={isSubmittingAdd}>
                  {isSubmittingAdd ? 'Saving...' : 'Add Company'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Edit Modal */}
        <Dialog open={!!editingCompany} onOpenChange={(open) => !open && setEditingCompany(null)}>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>Edit Company</DialogTitle>
              <DialogDescription>
                Update company information in the master record.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleEdit}>
              <div className="py-4 space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="edit-company-name">Company Name *</Label>
                  <Input
                    id="edit-company-name"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    required
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="edit-company-industry">Industry</Label>
                    <Input
                      id="edit-company-industry"
                      value={editIndustry}
                      onChange={(e) => setEditIndustry(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="edit-company-location">Location</Label>
                    <Input
                      id="edit-company-location"
                      value={editLocation}
                      onChange={(e) => setEditLocation(e.target.value)}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="edit-company-website">Website URL</Label>
                  <Input
                    id="edit-company-website"
                    type="url"
                    value={editWebsite}
                    onChange={(e) => setEditWebsite(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="edit-company-description">Description</Label>
                  <Textarea
                    id="edit-company-description"
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                    rows={3}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" type="button" onClick={() => setEditingCompany(null)}>
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
        <Dialog open={!!toggleCompany} onOpenChange={(open) => !open && setToggleCompany(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {toggleCompany?.is_active ? 'Deactivate Company?' : 'Reactivate Company?'}
              </DialogTitle>
              <DialogDescription>
                {toggleCompany?.is_active
                  ? `Deactivating "${toggleCompany?.name}" will mark it as inactive. Existing job postings or historical records referencing this company will remain preserved.`
                  : `Reactivating "${toggleCompany?.name}" will make it active and selectable for new job postings.`}
              </DialogDescription>
            </DialogHeader>
            <DialogFooter className="mt-4">
              <Button variant="outline" onClick={() => setToggleCompany(null)}>
                Cancel
              </Button>
              <Button
                variant={toggleCompany?.is_active ? 'destructive' : 'default'}
                onClick={handleToggleStatus}
                disabled={isSubmittingToggle}
              >
                {isSubmittingToggle
                  ? 'Updating...'
                  : toggleCompany?.is_active
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
