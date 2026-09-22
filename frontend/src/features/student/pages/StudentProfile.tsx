import { useState, useEffect } from 'react';
import {
  User,
  Mail,
  Phone,
  Building2,
  GraduationCap,
  Award,
  CalendarDays,
  MapPin,
  Linkedin,
  Github,
  Pencil,
  Save,
  X,
  Loader2,
  CheckCircle2,
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { PageHeader, PageContainer, LoadingSkeleton } from '@/components/common/PageHeader';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import toast from 'react-hot-toast';
import { FormField, ReadOnlyField } from '../components/FormField';
import { profileData as mockProfileData } from '../data/profile-skills-resume';
import type { ProfileData } from '../types';
import { studentService } from '../services/student.service';
import { StudentProfileUpdateRequest } from '../types/api';
import { useAuth } from '@/features/auth/context/AuthContext';

import { departmentService, Department } from '@/features/staff/services/department.service';

type Errors = Partial<Record<keyof ProfileData, string>>;

function validate(data: ProfileData): Errors {
  const errors: Errors = {};
  if (!data.fullName.trim()) errors.fullName = 'Full name is required';
  if (!data.email.trim()) errors.email = 'Email is required';
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) errors.email = 'Invalid email address';
  if (!data.phone.trim()) errors.phone = 'Phone number is required';
  if (!data.department.trim()) errors.department = 'Department is required';
  if (!data.graduationYear.trim()) errors.graduationYear = 'Graduation year is required';
  else if (!/^\d{4}$/.test(data.graduationYear)) errors.graduationYear = 'Enter a valid 4-digit year';
  if (!data.cgpa.trim()) errors.cgpa = 'CGPA is required';
  else if (parseFloat(data.cgpa) < 0 || parseFloat(data.cgpa) > 10) errors.cgpa = 'CGPA must be between 0 and 10';
  return errors;
}

export default function StudentProfile() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [data, setData] = useState<ProfileData>(mockProfileData);
  const [draft, setDraft] = useState<ProfileData>(mockProfileData);
  const [errors, setErrors] = useState<Errors>({});

  // Dynamic departments state from API
  const [departments, setDepartments] = useState<Department[]>([]);
  const [deptLoading, setDeptLoading] = useState(true);
  const [deptError, setDeptError] = useState<string | null>(null);

  const fetchDepartments = async () => {
    setDeptLoading(true);
    setDeptError(null);
    try {
      const activeDepts = await departmentService.getActiveDepartments();
      setDepartments(activeDepts);
    } catch {
      setDeptError('Failed to load active departments from server.');
    } finally {
      setDeptLoading(false);
    }
  };

  useEffect(() => {
    fetchDepartments();

    const fetchProfile = async () => {
      try {
        const response = await studentService.getMyProfile();
        const mappedData: ProfileData = {
          fullName: response.full_name || '',
          email: user?.email || '',
          phone: response.phone || '',
          department: response.department?.name || '',
          graduationYear: response.graduation_year?.toString() || '',
          cgpa: response.cgpa?.toString() || '',
          dateOfBirth: response.date_of_birth || '',
          address: response.address || '',
          linkedin: response.linkedin_url || '',
          github: response.github_url || '',
          avatarText: (response.full_name || 'ST').substring(0, 2).toUpperCase(),
        };
        setData(mappedData);
        setDraft(mappedData);
      } catch {
        toast.error('Could not load your profile data.');
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [user]);

  // Combine active departments with current student's saved department if it was deactivated
  const displayDepartments = (() => {
    const list = [...departments];
    if (data.department && !list.some((d) => d.name === data.department)) {
      list.unshift({ id: -1, name: data.department, is_active: false });
    }
    return list;
  })();

  const handleEdit = () => {
    setDraft(data);
    setErrors({});
    setEditing(true);
  };

  const handleCancel = () => {
    setEditing(false);
    setErrors({});
  };

  const handleSave = async () => {
    const validationErrors = validate(draft);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    setSaving(true);
    
    // Find department ID from displayDepartments
    const selectedDept = displayDepartments.find((d) => d.name === draft.department);

    const payload: StudentProfileUpdateRequest = {
      full_name: draft.fullName,
      phone: draft.phone,
      department_id: selectedDept && selectedDept.id > 0 ? selectedDept.id : undefined,
      graduation_year: draft.graduationYear ? parseInt(draft.graduationYear, 10) : null,
      cgpa: draft.cgpa ? parseFloat(draft.cgpa) : null,
      date_of_birth: draft.dateOfBirth || null,
      address: draft.address,
      linkedin_url: draft.linkedin || null,
      github_url: draft.github || null,
    };

    try {
      const response = await studentService.updateMyProfile(payload);
      const mappedData: ProfileData = {
        ...draft,
        department: response.department?.name || '',
        avatarText: (response.full_name || 'ST').substring(0, 2).toUpperCase(),
      };
      setData(mappedData);
      setEditing(false);
      setErrors({});
      toast.success('Profile updated successfully. Your changes have been saved.');
    } catch {
      toast.error('Failed to save changes. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const updateDraft = (field: keyof ProfileData) => (value: string) => {
    setDraft((prev) => ({ ...prev, [field]: value }));
  };

  if (loading) {
    return (
      <AppLayout role="student" userName={data.fullName} userRole="Student" avatarText={data.avatarText}>
        <LoadingSkeleton />
      </AppLayout>
    );
  }

  return (
    <AppLayout role="student" userName={data.fullName} userRole="Student" avatarText={data.avatarText}>
      <PageContainer>
        <PageHeader
          title="My Profile"
          description="View and manage your personal and academic information."
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
            ) : (
              <Button onClick={handleEdit}>
                <Pencil className="mr-1.5 h-4 w-4" />
                Edit Profile
              </Button>
            )
          }
        />

        {/* Profile header card */}
        <Card>
          <CardContent className="p-6">
            <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-start">
              <Avatar className="h-20 w-20 border-2 border-primary/20 shadow-sm">
                <AvatarFallback className="bg-primary/10 text-2xl font-bold text-primary">
                  {data.avatarText}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 text-center sm:text-left">
                <h2 className="text-xl font-bold tracking-tight">{data.fullName}</h2>
                <p className="mt-0.5 text-sm text-muted-foreground">{data.email}</p>
                <div className="mt-3 flex flex-wrap justify-center gap-2 sm:justify-start">
                  <span className="inline-flex items-center gap-1 rounded-md bg-secondary px-2.5 py-1 text-xs font-medium">
                    <GraduationCap className="h-3.5 w-3.5 text-muted-foreground" />
                    {data.department}
                  </span>
                  <span className="inline-flex items-center gap-1 rounded-md bg-secondary px-2.5 py-1 text-xs font-medium">
                    <CalendarDays className="h-3.5 w-3.5 text-muted-foreground" />
                    Class of {data.graduationYear}
                  </span>
                  <span className="inline-flex items-center gap-1 rounded-md bg-secondary px-2.5 py-1 text-xs font-medium">
                    <Award className="h-3.5 w-3.5 text-muted-foreground" />
                    CGPA: {data.cgpa}
                  </span>
                </div>
              </div>
              {!editing && (
                <div className="hidden items-center gap-1.5 rounded-lg bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400 sm:flex">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Profile Complete
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Personal information */}
        <Card>
          <CardHeader>
            <CardTitle>Personal Information</CardTitle>
            <CardDescription>Your basic personal details</CardDescription>
          </CardHeader>
          <CardContent>
            {editing ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField id="fullName" label="Full Name" value={draft.fullName} onChange={updateDraft('fullName')} icon={User} error={errors.fullName} />
                <FormField id="email" label="Email" type="email" value={draft.email} onChange={updateDraft('email')} icon={Mail} error={errors.email} />
                <FormField id="phone" label="Phone" type="tel" value={draft.phone} onChange={updateDraft('phone')} icon={Phone} error={errors.phone} />
                <FormField id="dob" label="Date of Birth" type="date" value={draft.dateOfBirth} onChange={updateDraft('dateOfBirth')} icon={CalendarDays} />
                <FormField id="address" label="Address" value={draft.address} onChange={updateDraft('address')} icon={MapPin} className="sm:col-span-2" />
              </div>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2">
                <ReadOnlyField label="Full Name" value={data.fullName} icon={User} />
                <ReadOnlyField label="Email" value={data.email} icon={Mail} />
                <ReadOnlyField label="Phone" value={data.phone} icon={Phone} />
                <ReadOnlyField label="Date of Birth" value={data.dateOfBirth ? new Date(data.dateOfBirth).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : ''} icon={CalendarDays} />
                <ReadOnlyField label="Address" value={data.address} icon={MapPin} className="sm:col-span-2" />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Academic information */}
        <Card>
          <CardHeader>
            <CardTitle>Academic Information</CardTitle>
            <CardDescription>Your academic and university details</CardDescription>
          </CardHeader>
          <CardContent>
            {editing ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-medium leading-none">Department</label>
                  <div className="relative">
                    <Building2 className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground z-10" />
                    {deptLoading ? (
                      <div className="flex h-10 w-full items-center rounded-md border border-input bg-background pl-9 pr-3 text-sm text-muted-foreground">
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Loading departments...
                      </div>
                    ) : deptError ? (
                      <div className="flex flex-col gap-1">
                        <div className="flex h-10 w-full items-center justify-between rounded-md border border-destructive bg-destructive/5 pl-9 pr-3 text-xs text-destructive">
                          <span>{deptError}</span>
                          <button
                            type="button"
                            onClick={fetchDepartments}
                            className="underline font-semibold hover:text-destructive/80"
                          >
                            Retry
                          </button>
                        </div>
                      </div>
                    ) : (
                      <Select
                        value={draft.department}
                        onValueChange={updateDraft('department')}
                      >
                        <SelectTrigger className="pl-9">
                          <SelectValue placeholder="Select Department" />
                        </SelectTrigger>
                        <SelectContent>
                          {displayDepartments.map((dept) => (
                            <SelectItem key={dept.id} value={dept.name}>
                              {dept.name} {!dept.is_active ? '(Inactive)' : ''}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  </div>
                  {errors.department && <p className="text-xs text-destructive">{errors.department}</p>}
                </div>
                <FormField id="gradYear" label="Graduation Year" type="number" value={draft.graduationYear} onChange={updateDraft('graduationYear')} icon={GraduationCap} error={errors.graduationYear} placeholder="2027" />
                <FormField id="cgpa" label="CGPA" type="number" value={draft.cgpa} onChange={updateDraft('cgpa')} icon={Award} error={errors.cgpa} placeholder="8.5" />
              </div>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2">
                <ReadOnlyField label="Department" value={data.department} icon={Building2} />
                <ReadOnlyField label="Graduation Year" value={data.graduationYear} icon={GraduationCap} />
                <ReadOnlyField label="CGPA" value={data.cgpa} icon={Award} />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Social links */}
        <Card>
          <CardHeader>
            <CardTitle>Social & Professional Links</CardTitle>
            <CardDescription>Your online presence and portfolios</CardDescription>
          </CardHeader>
          <CardContent>
            {editing ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField id="linkedin" label="LinkedIn" type="url" value={draft.linkedin} onChange={updateDraft('linkedin')} icon={Linkedin} placeholder="linkedin.com/in/username" />
                <FormField id="github" label="GitHub" type="url" value={draft.github} onChange={updateDraft('github')} icon={Github} placeholder="github.com/username" />
              </div>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2">
                <ReadOnlyField label="LinkedIn" value={data.linkedin} icon={Linkedin} />
                <ReadOnlyField label="GitHub" value={data.github} icon={Github} />
              </div>
            )}
          </CardContent>
        </Card>

        {editing && (
          <div className="flex items-center justify-end gap-2">
            <Button variant="outline" onClick={handleCancel} disabled={saving}>
              <X className="mr-1.5 h-4 w-4" />
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <Save className="mr-1.5 h-4 w-4" />}
              Save Changes
            </Button>
          </div>
        )}

        <Separator />
      </PageContainer>
    </AppLayout>
  );
}
