import { useState, useEffect, useRef } from 'react';
import {
  FileText,
  Pencil,
  Plus,
  Loader2,
  Trash2,
  Download,
  CheckCircle2,
  Upload,
  Star,
  Eye,
  ExternalLink,
  Calendar,
  HardDrive
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { PageHeader, PageContainer, LoadingSkeleton } from '@/components/common/PageHeader';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import toast from 'react-hot-toast';
import { resumeService } from '../services/resume.service';
import type { ResumeResponse } from '../types/api';
import { AxiosError } from 'axios';

export default function StudentResume() {
  const [loading, setLoading] = useState(true);
  const [resumes, setResumes] = useState<ResumeResponse[]>([]);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [editingResume, setEditingResume] = useState<ResumeResponse | null>(null);
  const [deletingResume, setDeletingResume] = useState<ResumeResponse | null>(null);

  // Preview States
  const [previewingResume, setPreviewingResume] = useState<ResumeResponse | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [downloadingId, setDownloadingId] = useState<number | null>(null);
  const [settingDefaultId, setSettingDefaultId] = useState<number | null>(null);

  // Add Form State
  const [addTitle, setAddTitle] = useState('');
  const [addDescription, setAddDescription] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Edit Form State
  const [editTitle, setEditTitle] = useState('');
  const [editDescription, setEditDescription] = useState('');

  const fetchResumes = async () => {
    try {
      const data = await resumeService.getResumes();
      setResumes(data);
    } catch {
      toast.error('Could not load resumes.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResumes();
  }, []);

  const formatFileSize = (bytes?: number | null) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  const handleOpenAdd = () => {
    setAddTitle('');
    setAddDescription('');
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    setShowAddDialog(true);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) {
      setSelectedFile(null);
      return;
    }

    const validExtensions = ['.pdf', '.doc', '.docx'];
    const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!validExtensions.includes(fileExt)) {
      toast.error('Invalid file format. Only PDF, DOC, and DOCX files are allowed.');
      if (fileInputRef.current) fileInputRef.current.value = '';
      setSelectedFile(null);
      return;
    }

    const MAX_FILE_SIZE = 5 * 1024 * 1024;
    if (file.size > MAX_FILE_SIZE) {
      toast.error('File size exceeds the 5 MB limit.');
      if (fileInputRef.current) fileInputRef.current.value = '';
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!addTitle.trim()) {
      toast.error('Title is required.');
      return;
    }
    if (!selectedFile) {
      toast.error('Please select a resume file.');
      return;
    }

    setSubmitting(true);
    try {
      await resumeService.createResume({
        title: addTitle.trim(),
        description: addDescription.trim() || undefined,
        file: selectedFile,
      });
      toast.success('Resume added successfully.');
      setShowAddDialog(false);
      await fetchResumes();
    } catch (err: unknown) {
      if (err instanceof AxiosError && err.response?.data?.message) {
        toast.error(err.response.data.message);
      } else {
        toast.error('Failed to add resume.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleOpenEdit = (resume: ResumeResponse) => {
    setEditingResume(resume);
    setEditTitle(resume.title);
    setEditDescription(resume.description || '');
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingResume) return;
    if (!editTitle.trim()) {
      toast.error('Title is required.');
      return;
    }

    setSubmitting(true);
    try {
      await resumeService.updateResume(editingResume.id, {
        title: editTitle.trim(),
        description: editDescription.trim() || null,
      });
      toast.success('Resume updated successfully.');
      setEditingResume(null);
      await fetchResumes();
    } catch (err: unknown) {
      if (err instanceof AxiosError && err.response?.data?.message) {
        toast.error(err.response.data.message);
      } else {
        toast.error('Failed to update resume.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleSetDefault = async (id: number) => {
    setSettingDefaultId(id);
    try {
      await resumeService.setDefaultResume(id);
      toast.success('Set as default resume.');
      await fetchResumes();
    } catch {
      toast.error('Failed to set default resume.');
    } finally {
      setSettingDefaultId(null);
    }
  };

  const handleDownload = async (resume: ResumeResponse) => {
    setDownloadingId(resume.id);
    try {
      const blob = await resumeService.downloadResumeFile(resume.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = resume.file_name || 'resume.pdf';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      toast.error('Failed to download resume file.');
    } finally {
      setDownloadingId(null);
    }
  };

  // Preview Handlers
  const handleOpenPreview = async (resume: ResumeResponse) => {
    setPreviewingResume(resume);
    setLoadingPreview(true);
    try {
      const blob = await resumeService.downloadResumeFile(resume.id);
      const url = window.URL.createObjectURL(blob);
      setPreviewUrl(url);
    } catch {
      toast.error('Failed to load resume preview.');
      setPreviewingResume(null);
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleClosePreview = () => {
    if (previewUrl) {
      window.URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    setPreviewingResume(null);
  };

  const handleDeleteSubmit = async () => {
    if (!deletingResume) return;
    setSubmitting(true);
    try {
      await resumeService.deleteResume(deletingResume.id);
      toast.success('Resume deleted successfully.');
      setDeletingResume(null);
      await fetchResumes();
    } catch {
      toast.error('Failed to delete resume.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <AppLayout role="student" userName="Student" userRole="Student" avatarText="ST">
        <LoadingSkeleton />
      </AppLayout>
    );
  }

  return (
    <AppLayout role="student" userName="Student" userRole="Student" avatarText="ST">
      <PageContainer>
        <PageHeader
          title="My Resumes"
          description="Manage different resumes for different job opportunities."
          action={
            <Button onClick={handleOpenAdd}>
              <Plus className="mr-1.5 h-4 w-4" />
              Add Resume
            </Button>
          }
        />

        {resumes.length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted mb-4">
                  <FileText className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="text-lg font-semibold">No resumes yet</h3>
                <p className="mt-1 max-w-sm text-sm text-muted-foreground mb-6">
                  Upload different versions of your resume for different job opportunities.
                </p>
                <Button onClick={handleOpenAdd}>
                  <Plus className="mr-1.5 h-4 w-4" />
                  Add Resume
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-5">
            {resumes.map((resume) => (
              <Card
                key={resume.id}
                className={`transition-all duration-200 hover:shadow-md ${resume.is_default ? 'border-primary/60 shadow-sm bg-card' : ''
                  }`}
              >
                <CardHeader className="pt-5 pb-3 px-6">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <h3 className="text-xl font-bold tracking-tight text-foreground">{resume.title}</h3>
                      {resume.is_default && (
                        <Badge variant="default" className="gap-1 bg-primary/15 text-primary border border-primary/30 hover:bg-primary/20 px-2.5 py-0.5 font-medium text-xs">
                          <Star className="h-3 w-3 fill-primary" />
                          Default Resume
                        </Badge>
                      )}
                    </div>
                  </div>

                  {resume.description && (
                    <div className="mt-2.5 rounded-lg bg-secondary/50 border border-secondary px-3.5 py-2.5 text-sm text-foreground/90 leading-relaxed font-normal">
                      {resume.description}
                    </div>
                  )}
                </CardHeader>

                <CardContent className="pb-5 px-6">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-lg border bg-muted/20 p-4">
                    <div className="flex items-center gap-3.5">
                      <div className="p-3 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
                        <FileText className="h-6 w-6" />
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm font-semibold text-foreground">{resume.file_name}</p>
                        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                          <span className="uppercase font-semibold text-[10px] bg-secondary border px-1.5 py-0.5 rounded text-secondary-foreground">
                            {resume.file_name.split('.').pop() || 'FILE'}
                          </span>
                          <span>•</span>
                          <span className="flex items-center gap-1">
                            <HardDrive className="h-3 w-3" />
                            {formatFileSize(resume.file_size)}
                          </span>
                          <span>•</span>
                          <span className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            Uploaded {formatDate(resume.created_at)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
                      <Button
                        variant="default"
                        size="sm"
                        onClick={() => handleOpenPreview(resume)}
                        className="shadow-sm"
                      >
                        <Eye className="mr-1.5 h-4 w-4" />
                        Preview
                      </Button>

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownload(resume)}
                        disabled={downloadingId === resume.id}
                      >
                        {downloadingId === resume.id ? (
                          <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                        ) : (
                          <Download className="mr-1.5 h-4 w-4" />
                        )}
                        Download
                      </Button>

                      {!resume.is_default && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleSetDefault(resume.id)}
                          disabled={settingDefaultId === resume.id}
                        >
                          {settingDefaultId === resume.id ? (
                            <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                          ) : (
                            <CheckCircle2 className="mr-1.5 h-4 w-4 text-primary" />
                          )}
                          Set as Default
                        </Button>
                      )}

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleOpenEdit(resume)}
                      >
                        <Pencil className="mr-1.5 h-4 w-4" />
                        Edit
                      </Button>

                      <Button
                        variant="outline"
                        size="sm"
                        className="text-destructive hover:bg-destructive/10 hover:text-destructive border-destructive/30"
                        onClick={() => setDeletingResume(resume)}
                      >
                        <Trash2 className="mr-1.5 h-4 w-4" />
                        Delete
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </PageContainer>

      {/* Resume Preview Modal */}
      <Dialog open={!!previewingResume} onOpenChange={(open) => !open && handleClosePreview()}>
        <DialogContent className="sm:max-w-[900px] max-h-[92vh] flex flex-col p-6 gap-4">
          <DialogHeader className="space-y-3 pb-3 border-b border-border/60">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <DialogTitle className="text-2xl font-bold tracking-tight text-foreground">
                  {previewingResume?.title}
                </DialogTitle>
                {previewingResume?.is_default && (
                  <Badge variant="default" className="gap-1 bg-primary/15 text-primary border border-primary/30 px-2.5 py-0.5 font-medium text-xs">
                    <Star className="h-3.5 w-3.5 fill-primary" />
                    Default Resume
                  </Badge>
                )}
              </div>
              {/* <Badge variant="outline" className="uppercase text-xs tracking-wider px-2.5 py-1">
                {previewingResume?.file_name.split('.').pop() || 'DOCUMENT'}
              </Badge> */}
            </div>

            {previewingResume?.description && (
              <div className="rounded-lg bg-muted/60 border border-border/60 px-4 py-2.5 text-sm text-foreground/80 leading-relaxed font-normal">
                <span className="font-semibold text-xs text-muted-foreground uppercase tracking-wider block mb-1">
                  Description
                </span>
                {previewingResume.description}
              </div>
            )}

            <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground pt-1">
              <span className="inline-flex items-center gap-1.5 bg-background border px-2.5 py-1 rounded-md font-mono font-medium text-foreground">
                <FileText className="h-3.5 w-3.5 text-primary" />
                {previewingResume?.file_name}
              </span>
              <span className="inline-flex items-center gap-1 bg-background border px-2.5 py-1 rounded-md font-medium text-muted-foreground">
                <HardDrive className="h-3.5 w-3.5" />
                {formatFileSize(previewingResume?.file_size)}
              </span>
              <span className="inline-flex items-center gap-1 bg-background border px-2.5 py-1 rounded-md font-medium text-muted-foreground">
                <Calendar className="h-3.5 w-3.5" />
                Uploaded {previewingResume ? formatDate(previewingResume.created_at) : ''}
              </span>
            </div>
          </DialogHeader>

          <div className="flex-1 my-1 overflow-hidden rounded-xl border bg-muted/20 min-h-[450px] flex items-center justify-center shadow-inner">
            {loadingPreview ? (
              <div className="flex flex-col items-center gap-2 p-8">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <p className="text-sm font-medium text-muted-foreground">Loading document preview...</p>
              </div>
            ) : previewUrl && (previewingResume?.file_name.toLowerCase().endsWith('.pdf') || previewingResume?.file_type.includes('pdf')) ? (
              <iframe
                src={previewUrl}
                className="w-full h-[62vh] rounded-lg border-0"
                title={previewingResume?.title || 'Resume Preview'}
              />
            ) : (
              <div className="flex flex-col items-center justify-center p-8 text-center max-w-md">
                <div className="p-4 rounded-full bg-primary/10 text-primary mb-4">
                  <FileText className="h-12 w-12" />
                </div>
                <h4 className="text-base font-bold text-foreground">{previewingResume?.file_name}</h4>
                <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
                  Interactive preview is optimized for PDF files. Microsoft Word documents (.doc/.docx) can be downloaded or opened directly.
                </p>
                {previewUrl && (
                  <Button
                    className="mt-5 gap-2"
                    onClick={() => window.open(previewUrl, '_blank')}
                  >
                    <ExternalLink className="h-4 w-4" />
                    Open Document in New Tab
                  </Button>
                )}
              </div>
            )}
          </div>

          <DialogFooter className="flex flex-col sm:flex-row gap-2 justify-between items-center pt-2 border-t">
            {previewUrl && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open(previewUrl, '_blank')}
                className="gap-1.5"
              >
                <ExternalLink className="h-4 w-4" />
                Open in New Tab
              </Button>
            )}

            <div className="flex items-center gap-2 ml-auto">
              <Button
                variant="outline"
                size="sm"
                onClick={() => previewingResume && handleDownload(previewingResume)}
                className="gap-1.5"
              >
                <Download className="h-4 w-4" />
                Download
              </Button>
              <Button size="sm" onClick={handleClosePreview}>
                Close
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Resume Dialog */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <form onSubmit={handleAddSubmit}>
            <DialogHeader>
              <DialogTitle>Add New Resume</DialogTitle>
              <DialogDescription>
                Upload a resume document tailored for a specific role or career focus.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="add-title">
                  Title <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="add-title"
                  placeholder="e.g. Frontend Developer Resume, Data Analyst Resume"
                  value={addTitle}
                  onChange={(e) => setAddTitle(e.target.value)}
                  maxLength={100}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="add-description">Description (Optional)</Label>
                <Textarea
                  id="add-description"
                  placeholder="e.g. Tailored for React and TypeScript roles"
                  value={addDescription}
                  onChange={(e) => setAddDescription(e.target.value)}
                  maxLength={500}
                  className="min-h-[80px]"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="add-file">
                  Resume File <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="add-file"
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept=".pdf,.doc,.docx"
                  required
                />
                <p className="text-xs text-muted-foreground">
                  Accepted formats: PDF, DOC, DOCX (Max 5 MB)
                </p>
              </div>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowAddDialog(false)}
                disabled={submitting}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? (
                  <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                ) : (
                  <Upload className="mr-1.5 h-4 w-4" />
                )}
                Upload Resume
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Resume Dialog */}
      <Dialog open={!!editingResume} onOpenChange={(open) => !open && setEditingResume(null)}>
        <DialogContent className="sm:max-w-[500px]">
          <form onSubmit={handleEditSubmit}>
            <DialogHeader>
              <DialogTitle>Edit Resume Details</DialogTitle>
              <DialogDescription>
                Update the title and description for this resume.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="edit-title">
                  Title <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="edit-title"
                  placeholder="e.g. Senior Frontend Engineer Resume"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  maxLength={100}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit-description">Description (Optional)</Label>
                <Textarea
                  id="edit-description"
                  placeholder="e.g. Updated with recent internship experience"
                  value={editDescription}
                  onChange={(e) => setEditDescription(e.target.value)}
                  maxLength={500}
                  className="min-h-[80px]"
                />
              </div>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setEditingResume(null)}
                disabled={submitting}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
                Save Changes
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Resume Confirmation Dialog */}
      <AlertDialog open={!!deletingResume} onOpenChange={(open) => !open && setDeletingResume(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Resume Document?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete &quot;{deletingResume?.title}&quot;? This will permanently remove the resume record and physical file.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={submitting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteSubmit}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={submitting}
            >
              {submitting ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <Trash2 className="mr-1.5 h-4 w-4" />}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </AppLayout>
  );
}
