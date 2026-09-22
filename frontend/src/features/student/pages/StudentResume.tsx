import { useState, useEffect, useRef } from 'react';
import {
  FileText,
  Pencil,
  Save,
  X,
  Loader2,
  Trash2,
  AlignLeft,
  Target,
  Upload,
  Download,
  Paperclip
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { PageHeader, PageContainer, LoadingSkeleton } from '@/components/common/PageHeader';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
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

type FormState = {
  professionalSummary: string;
  careerObjective: string;
};

export default function StudentResume() {
  const [loading, setLoading] = useState(true);
  const [resume, setResume] = useState<ResumeResponse | null>(null);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  // Resume File States
  const [uploadingFile, setUploadingFile] = useState(false);
  const [downloadingFile, setDownloadingFile] = useState(false);
  const [deletingFile, setDeletingFile] = useState(false);
  const [showDeleteFileDialog, setShowDeleteFileDialog] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [formState, setFormState] = useState<FormState>({
    professionalSummary: '',
    careerObjective: ''
  });

  const fetchResume = async () => {
    try {
      const data = await resumeService.getResume();
      setResume(data);
      setFormState({
        professionalSummary: data.professional_summary || '',
        careerObjective: data.career_objective || ''
      });
    } catch (err: unknown) {
      if (err instanceof AxiosError && err.response?.status === 404) {
        // Normal state: No resume yet
        setResume(null);
      } else {
        toast.error('Could not load resume data.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResume();
  }, []);

  const formatFileSize = (bytes?: number | null) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleEdit = () => {
    setFormState({
      professionalSummary: resume?.professional_summary || '',
      careerObjective: resume?.career_objective || ''
    });
    setEditing(true);
  };

  const handleCancel = () => {
    setEditing(false);
  };

  const handleSave = async () => {
    // Validation
    if (formState.professionalSummary.length > 2000) {
      toast.error('Professional summary must be under 2000 characters.');
      return;
    }
    if (formState.careerObjective.length > 1000) {
      toast.error('Career objective must be under 1000 characters.');
      return;
    }

    setSaving(true);
    
    try {
      if (resume) {
        // Update existing
        const data = await resumeService.updateResume({
          professional_summary: formState.professionalSummary || null,
          career_objective: formState.careerObjective || null
        });
        setResume(data);
        toast.success('Resume updated successfully.');
      } else {
        // Create new
        const data = await resumeService.createResume({
          professional_summary: formState.professionalSummary || null,
          career_objective: formState.careerObjective || null
        });
        setResume(data);
        toast.success('Resume created successfully.');
      }
      setEditing(false);
    } catch (err: unknown) {
      if (err instanceof AxiosError && err.response?.status === 422) {
        toast.error('Validation error. Please check your inputs.');
      } else {
        toast.error('Failed to save resume. Please try again.');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await resumeService.deleteResume();
      setResume(null);
      setShowDeleteDialog(false);
      setFormState({ professionalSummary: '', careerObjective: '' });
      toast.success('Resume deleted successfully.');
    } catch (err: unknown) {
      if (err instanceof AxiosError && err.response?.status === 404) {
        toast.error('Resume not found.');
      } else {
        toast.error('Failed to delete resume.');
      }
    } finally {
      setDeleting(false);
    }
  };

  // Resume File Handlers
  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    // Validate extension (.pdf, .doc, .docx)
    const validExtensions = ['.pdf', '.doc', '.docx'];
    const fileExt = selectedFile.name.substring(selectedFile.name.lastIndexOf('.')).toLowerCase();
    if (!validExtensions.includes(fileExt)) {
      toast.error('Invalid file format. Only PDF, DOC, and DOCX files are allowed.');
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    // Validate maximum 5MB (5 * 1024 * 1024 bytes)
    const MAX_FILE_SIZE = 5 * 1024 * 1024;
    if (selectedFile.size > MAX_FILE_SIZE) {
      toast.error('File size exceeds the 5 MB limit.');
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    setUploadingFile(true);
    try {
      // If no resume profile exists yet, create an empty resume record first
      if (!resume) {
        await resumeService.createResume({
          professional_summary: null,
          career_objective: null,
        });
      }
      const updated = await resumeService.uploadResumeFile(selectedFile);
      setResume(updated);
      toast.success('Resume file uploaded successfully.');
    } catch (err: unknown) {
      if (err instanceof AxiosError && err.response?.status === 404) {
        toast.error('Resume profile not found.');
      } else if (err instanceof AxiosError && err.response?.status === 422) {
        toast.error('Invalid file format or file corrupt.');
      } else {
        toast.error('Failed to upload resume file.');
      }
    } finally {
      setUploadingFile(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDownloadFile = async () => {
    if (!resume?.file_name) {
      toast.error('No resume file available to download.');
      return;
    }

    setDownloadingFile(true);
    try {
      const blob = await resumeService.downloadResumeFile();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = resume.file_name || 'resume.pdf';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: unknown) {
      if (err instanceof AxiosError && err.response?.status === 404) {
        toast.error('Resume file not found on server.');
      } else {
        toast.error('Failed to download resume file.');
      }
    } finally {
      setDownloadingFile(false);
    }
  };

  const handleDeleteFile = async () => {
    setDeletingFile(true);
    try {
      const updated = await resumeService.deleteResumeFile();
      setResume(updated);
      setShowDeleteFileDialog(false);
      toast.success('Resume file deleted successfully.');
    } catch (err: unknown) {
      if (err instanceof AxiosError && err.response?.status === 404) {
        toast.error('Resume file not found.');
      } else {
        toast.error('Failed to delete resume file.');
      }
    } finally {
      setDeletingFile(false);
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
        {/* Hidden File Input shared by all upload triggers */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          accept=".pdf,.doc,.docx"
          className="hidden"
        />

        <PageHeader
          title="Resume Profile"
          description="Manage your professional summary, career objective, and resume document."
          action={
            editing ? (
              <div className="flex items-center gap-2">
                <Button variant="outline" onClick={handleCancel} disabled={saving}>
                  <X className="mr-1.5 h-4 w-4" />
                  Cancel
                </Button>
                <Button onClick={handleSave} disabled={saving}>
                  {saving ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <Save className="mr-1.5 h-4 w-4" />}
                  Save Changes
                </Button>
              </div>
            ) : resume ? (
              <div className="flex items-center gap-2">
                <Button variant="outline" className="text-destructive hover:bg-destructive/10 hover:text-destructive" onClick={() => setShowDeleteDialog(true)} disabled={deleting}>
                  <Trash2 className="mr-1.5 h-4 w-4" />
                  Delete
                </Button>
                <Button onClick={handleEdit}>
                  <Pencil className="mr-1.5 h-4 w-4" />
                  Edit Resume Profile
                </Button>
              </div>
            ) : null
          }
        />

        {!resume && !editing ? (
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                  <FileText className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="mt-4 text-lg font-semibold">No resume profile yet</h3>
                <p className="mt-1 max-w-sm text-sm text-muted-foreground">
                  Upload your resume file or create your professional summary and career objective to get started.
                </p>
                <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
                  <Button onClick={() => fileInputRef.current?.click()} disabled={uploadingFile}>
                    {uploadingFile ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <Upload className="mr-1.5 h-4 w-4" />}
                    Upload Resume File
                  </Button>
                  <Button variant="outline" onClick={() => setEditing(true)}>
                    <Pencil className="mr-1.5 h-4 w-4" />
                    Create Summary & Objective
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            {/* Resume File Document Card */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Paperclip className="h-5 w-5 text-primary" />
                  Resume Document File
                </CardTitle>
                <CardDescription>
                  Upload, download, or update your resume document (PDF, DOC, DOCX up to 5 MB).
                </CardDescription>
              </CardHeader>
              <CardContent>
                {resume?.file_name || resume?.has_file ? (
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-lg border bg-secondary/30 p-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2.5 rounded-md bg-primary/10 text-primary">
                        <FileText className="h-6 w-6" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-foreground">{resume.file_name}</p>
                        <p className="text-xs text-muted-foreground">
                          {resume.file_type || 'Document'} • {formatFileSize(resume.file_size)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleDownloadFile}
                        disabled={downloadingFile || uploadingFile || deletingFile}
                      >
                        {downloadingFile ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <Download className="mr-1.5 h-4 w-4" />}
                        Download
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={uploadingFile || downloadingFile || deletingFile}
                      >
                        {uploadingFile ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <Upload className="mr-1.5 h-4 w-4" />}
                        Replace
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                        onClick={() => setShowDeleteFileDialog(true)}
                        disabled={deletingFile || uploadingFile || downloadingFile}
                      >
                        <Trash2 className="mr-1.5 h-4 w-4" />
                        Delete File
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-6 text-center">
                    <Upload className="h-8 w-8 text-muted-foreground mb-2" />
                    <p className="text-sm font-medium">No resume document uploaded</p>
                    <p className="text-xs text-muted-foreground mb-4">Supported formats: PDF, DOC, DOCX (Max 5 MB)</p>
                    <Button
                      size="sm"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploadingFile}
                    >
                      {uploadingFile ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <Upload className="mr-1.5 h-4 w-4" />}
                      Upload Resume File
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlignLeft className="h-5 w-5 text-primary" />
                  Professional Summary
                </CardTitle>
                <CardDescription>A brief overview of your professional background and key skills.</CardDescription>
              </CardHeader>
              <CardContent>
                {editing ? (
                  <div className="space-y-2">
                    <Label htmlFor="professionalSummary">Summary (max 2000 chars)</Label>
                    <Textarea
                      id="professionalSummary"
                      placeholder="e.g. Highly motivated software engineering student..."
                      value={formState.professionalSummary}
                      onChange={(e) => setFormState(prev => ({ ...prev, professionalSummary: e.target.value }))}
                      className="min-h-[150px]"
                      maxLength={2000}
                    />
                    <p className="text-xs text-muted-foreground text-right">
                      {formState.professionalSummary.length} / 2000
                    </p>
                  </div>
                ) : (
                  <div className="rounded-lg border bg-secondary/30 p-4">
                    <p className="text-sm whitespace-pre-wrap">
                      {resume?.professional_summary || <span className="text-muted-foreground italic">No professional summary provided.</span>}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5 text-primary" />
                  Career Objective
                </CardTitle>
                <CardDescription>Your short-term and long-term career goals.</CardDescription>
              </CardHeader>
              <CardContent>
                {editing ? (
                  <div className="space-y-2">
                    <Label htmlFor="careerObjective">Objective (max 1000 chars)</Label>
                    <Textarea
                      id="careerObjective"
                      placeholder="e.g. Seeking a challenging role as a backend developer..."
                      value={formState.careerObjective}
                      onChange={(e) => setFormState(prev => ({ ...prev, careerObjective: e.target.value }))}
                      className="min-h-[120px]"
                      maxLength={1000}
                    />
                    <p className="text-xs text-muted-foreground text-right">
                      {formState.careerObjective.length} / 1000
                    </p>
                  </div>
                ) : (
                  <div className="rounded-lg border bg-secondary/30 p-4">
                    <p className="text-sm whitespace-pre-wrap">
                      {resume?.career_objective || <span className="text-muted-foreground italic">No career objective provided.</span>}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
            
            {editing && (
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={handleCancel} disabled={saving}>
                  Cancel
                </Button>
                <Button onClick={handleSave} disabled={saving}>
                  {saving ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <Save className="mr-1.5 h-4 w-4" />}
                  Save Resume Profile
                </Button>
              </div>
            )}
          </div>
        )}

      </PageContainer>

      {/* Delete File confirmation dialog */}
      <AlertDialog open={showDeleteFileDialog} onOpenChange={setShowDeleteFileDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Resume File?</AlertDialogTitle>
            <AlertDialogDescription>
              This will remove your uploaded file ({resume?.file_name}). Your professional summary and career objective will remain intact.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deletingFile}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteFile}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={deletingFile}
            >
              {deletingFile ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <Trash2 className="mr-1.5 h-4 w-4" />}
              Delete File
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete Resume Profile confirmation dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Resume Profile?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete your professional summary and career objective. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={deleting}
            >
              {deleting ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <Trash2 className="mr-1.5 h-4 w-4" />}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </AppLayout>
  );
}
