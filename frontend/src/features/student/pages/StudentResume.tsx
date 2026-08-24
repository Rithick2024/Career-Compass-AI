import { useState, useEffect, useCallback } from 'react';
import {
  FileText,
  Download,
  Eye,
  Trash2,
  CheckCircle2,
  Loader2,
  FileWarning,
  CloudUpload,
  Star,
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { PageHeader, PageContainer, LoadingSkeleton } from '@/components/common/PageHeader';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
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
import { EmptyState } from '@/components/common/EmptyState';
import { cn } from '@/lib/utils';
import toast from 'react-hot-toast';
import { resumeVersions } from '../data/profile-skills-resume';
import type { ResumeVersion } from '../types';

type UploadState = 'idle' | 'uploading' | 'error';

export default function StudentResume() {
  const [loading, setLoading] = useState(true);
  const [resumes, setResumes] = useState<ResumeVersion[]>(resumeVersions);
  const [uploadState, setUploadState] = useState<UploadState>('idle');
  const [isDragging, setIsDragging] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<ResumeVersion | null>(null);

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 500);
    return () => clearTimeout(timer);
  }, []);

  const simulateUpload = useCallback(() => {
    setUploadState('uploading');
    setTimeout(() => {
      const versionNum = resumes.length + 1;
      const newResume: ResumeVersion = {
        id: `RES-00${versionNum}`,
        fileName: `Aarav_Sharma_Resume_v${versionNum}.pdf`,
        version: `v${versionNum}`,
        uploadDate: new Date().toISOString().split('T')[0],
        fileSize: `${200 + Math.floor(Math.random() * 80)} KB`,
        isActive: false,
      };
      setResumes((prev) => [newResume, ...prev]);
      setUploadState('idle');
      toast.success(`${newResume.fileName} has been uploaded.`);
    }, 1500);
  }, [resumes.length]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    simulateUpload();
  };

  const handleFileSelect = () => {
    simulateUpload();
  };

  const handleSetActive = (id: string) => {
    setResumes((prev) =>
      prev.map((r) => ({ ...r, isActive: r.id === id }))
    );
    const resume = resumes.find((r) => r.id === id);
    toast.success(`${resume?.fileName} is now your active resume.`);
  };

  const handleDelete = () => {
    if (!deleteTarget) return;
    setResumes((prev) => prev.filter((r) => r.id !== deleteTarget.id));
    toast.success(`${deleteTarget.fileName} has been deleted.`);
    setDeleteTarget(null);
  };

  const handleDownload = (resume: ResumeVersion) => {
    toast.success(`${resume.fileName} is being downloaded.`);
  };

  const handlePreview = (resume: ResumeVersion) => {
    toast.success(`${resume.fileName} will open in a new tab.`);
  };

  if (loading) {
    return (
      <AppLayout role="student" userName="Aarav Sharma" userRole="Student" avatarText="AS">
        <LoadingSkeleton />
      </AppLayout>
    );
  }

  return (
    <AppLayout role="student" userName="Aarav Sharma" userRole="Student" avatarText="AS">
      <PageContainer>
        <PageHeader
          title="Resume Management"
          description="Upload, manage, and track different versions of your resume."
        />

        {/* Upload area */}
        <Card>
          <CardHeader>
            <CardTitle>Upload Resume</CardTitle>
            <CardDescription>Drag and drop your resume or click to browse</CardDescription>
          </CardHeader>
          <CardContent>
            <div
              role="button"
              tabIndex={0}
              aria-label="Upload resume"
              onClick={uploadState === 'idle' ? handleFileSelect : undefined}
              onKeyDown={(e) => {
                if ((e.key === 'Enter' || e.key === ' ') && uploadState === 'idle') {
                  e.preventDefault();
                  handleFileSelect();
                }
              }}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={cn(
                'flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 text-center transition-all cursor-pointer',
                isDragging
                  ? 'border-primary bg-primary/5 scale-[1.01]'
                  : 'border-border hover:border-primary/40 hover:bg-secondary/30',
                uploadState === 'uploading' && 'pointer-events-none opacity-70'
              )}
            >
              {uploadState === 'uploading' ? (
                <>
                  <Loader2 className="h-10 w-10 animate-spin text-primary" />
                  <p className="mt-3 text-sm font-medium">Uploading resume...</p>
                  <p className="mt-1 text-xs text-muted-foreground">Please wait a moment</p>
                </>
              ) : uploadState === 'error' ? (
                <>
                  <FileWarning className="h-10 w-10 text-destructive" />
                  <p className="mt-3 text-sm font-medium text-destructive">Upload failed</p>
                  <p className="mt-1 text-xs text-muted-foreground">Please try again</p>
                </>
              ) : (
                <>
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
                    <CloudUpload className="h-7 w-7 text-primary" />
                  </div>
                  <p className="mt-3 text-sm font-medium">
                    <span className="text-primary">Click to upload</span> or drag and drop
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">PDF, DOC, or DOCX (max 5MB)</p>
                </>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Resume list */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle>Uploaded Resumes</CardTitle>
              <CardDescription>Manage your resume versions</CardDescription>
            </div>
            <Badge variant="secondary" className="text-xs">{resumes.length} {resumes.length === 1 ? 'version' : 'versions'}</Badge>
          </CardHeader>
          <CardContent>
            {resumes.length === 0 ? (
              <EmptyState
                icon={FileText}
                title="No resumes uploaded"
                description="Upload your first resume to start applying for jobs."
                actionLabel="Upload Resume"
                onAction={handleFileSelect}
              />
            ) : (
              <div className="space-y-1">
                {resumes.map((resume, idx) => (
                  <div key={resume.id}>
                    <div className="group flex flex-col gap-3 rounded-lg border p-4 transition-all hover:border-primary/30 hover:shadow-sm sm:flex-row sm:items-center sm:justify-between">
                      {/* File info */}
                      <div className="flex items-center gap-3 min-w-0">
                        <div className={cn(
                          'flex h-11 w-11 shrink-0 items-center justify-center rounded-lg',
                          resume.isActive ? 'bg-primary/10' : 'bg-secondary'
                        )}>
                          <FileText className={cn('h-5 w-5', resume.isActive ? 'text-primary' : 'text-muted-foreground')} />
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="truncate text-sm font-semibold">{resume.fileName}</p>
                            {resume.isActive && (
                              <Badge className="gap-1 bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 border-0 text-[10px]">
                                <CheckCircle2 className="h-3 w-3" />
                                Active
                              </Badge>
                            )}
                          </div>
                          <div className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
                            <span className="font-medium">{resume.version}</span>
                            <span>•</span>
                            <span>{new Date(resume.uploadDate).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</span>
                            <span>•</span>
                            <span>{resume.fileSize}</span>
                          </div>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-1 sm:shrink-0">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 px-2 text-muted-foreground hover:text-foreground"
                          onClick={() => handlePreview(resume)}
                        >
                          <Eye className="h-4 w-4" />
                          <span className="ml-1.5 hidden sm:inline">Preview</span>
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 px-2 text-muted-foreground hover:text-foreground"
                          onClick={() => handleDownload(resume)}
                        >
                          <Download className="h-4 w-4" />
                          <span className="ml-1.5 hidden sm:inline">Download</span>
                        </Button>
                        {!resume.isActive && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 px-2 text-muted-foreground hover:text-primary"
                            onClick={() => handleSetActive(resume.id)}
                          >
                            <Star className="h-4 w-4" />
                            <span className="ml-1.5 hidden sm:inline">Set Active</span>
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 px-2 text-muted-foreground hover:text-destructive"
                          onClick={() => setDeleteTarget(resume)}
                          aria-label={`Delete ${resume.fileName}`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    {idx < resumes.length - 1 && <Separator className="my-0.5" />}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </PageContainer>

      {/* Delete confirmation */}
      <AlertDialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this resume?</AlertDialogTitle>
            <AlertDialogDescription>
              {deleteTarget && (
                <>
                  This will permanently delete <strong>{deleteTarget.fileName}</strong>. This action cannot be undone.
                </>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              <Trash2 className="mr-1.5 h-4 w-4" />
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </AppLayout>
  );
}
