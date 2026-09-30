import React, { useState, useEffect } from 'react';
import {
  Clock,
  Plus,
  Pencil,
  Trash2,
  ArrowUp,
  ArrowDown,
  Link,
  FileText,
  Video,
  AlertCircle,
  CheckCircle2,
  Calendar,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

import {
  jobRoundService,
  JobRound,
  RoundType,
  ScheduleType,
  CreateJobRoundPayload,
  UpdateJobRoundPayload,
} from '../services/job-round.service';

interface Props {
  jobId: number;
  initialRounds?: JobRound[];
  onRoundsChange?: () => void;
}

const ROUND_TYPES: RoundType[] = [
  'Online Assessment',
  'Coding Test',
  'Aptitude Test',
  'Technical Interview',
  'Managerial Interview',
  'HR Interview',
  'Group Discussion',
  'Other',
];

export const JobRecruitmentWorkflowEditor: React.FC<Props> = ({
  jobId,
  initialRounds = [],
  onRoundsChange,
}) => {
  const [rounds, setRounds] = useState<JobRound[]>(initialRounds);
  const [loading, setLoading] = useState(false);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingRound, setEditingRound] = useState<JobRound | null>(null);

  // Form State
  const [roundNumber, setRoundNumber] = useState<number>(1);
  const [roundType, setRoundType] = useState<RoundType>('Technical Interview');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [scheduleType, setScheduleType] = useState<ScheduleType>('FIXED_TIME');
  const [availableFrom, setAvailableFrom] = useState('');
  const [availableUntil, setAvailableUntil] = useState('');
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [meetingLink, setMeetingLink] = useState('');
  const [testLink, setTestLink] = useState('');
  const [instructions, setInstructions] = useState('');
  const [isRequired, setIsRequired] = useState(true);
  const [isActive, setIsActive] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const fetchRounds = async () => {
    setLoading(true);
    try {
      const data = await jobRoundService.getJobRounds(jobId);
      setRounds(data);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to load job recruitment rounds');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (jobId) {
      fetchRounds();
    }
  }, [jobId]);

  const openCreateModal = () => {
    setEditingRound(null);
    setRoundNumber(rounds.length + 1);
    setRoundType('Technical Interview');
    setTitle('');
    setDescription('');
    setScheduleType('FIXED_TIME');
    setAvailableFrom('');
    setAvailableUntil('');
    setDurationMinutes(60);
    setMeetingLink('');
    setTestLink('');
    setInstructions('');
    setIsRequired(true);
    setIsActive(true);
    setIsDialogOpen(true);
  };

  const openEditModal = (round: JobRound) => {
    setEditingRound(round);
    setRoundNumber(round.round_number);
    setRoundType(round.round_type);
    setTitle(round.title || '');
    setDescription(round.description || '');
    setScheduleType(round.schedule_type || 'FIXED_TIME');
    setAvailableFrom(round.available_from ? new Date(round.available_from).toISOString().slice(0, 16) : '');
    setAvailableUntil(round.available_until ? new Date(round.available_until).toISOString().slice(0, 16) : '');
    setDurationMinutes(round.duration_minutes || 60);
    setMeetingLink(round.meeting_link || '');
    setTestLink(round.test_link || '');
    setInstructions(round.instructions || '');
    setIsRequired(round.is_required);
    setIsActive(round.is_active);
    setIsDialogOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!availableFrom) {
      toast.error('Start date / Available from is required');
      return;
    }
    if (scheduleType === 'AVAILABILITY_WINDOW' && !availableUntil) {
      toast.error('End date / Available until is required for Availability Window');
      return;
    }

    setSubmitting(true);
    try {
      const payload: CreateJobRoundPayload | UpdateJobRoundPayload = {
        round_number: roundNumber,
        round_type: roundType,
        title: title.trim() || undefined,
        description: description.trim() || undefined,
        schedule_type: scheduleType,
        available_from: availableFrom ? new Date(availableFrom).toISOString() : undefined,
        available_until: scheduleType === 'AVAILABILITY_WINDOW' && availableUntil ? new Date(availableUntil).toISOString() : null,
        duration_minutes: Number(durationMinutes),
        meeting_link: meetingLink.trim() || undefined,
        test_link: testLink.trim() || undefined,
        instructions: instructions.trim() || undefined,
        is_required: isRequired,
        is_active: isActive,
      };

      if (editingRound) {
        await jobRoundService.updateJobRound(jobId, editingRound.id, payload);
        toast.success(`Round ${roundNumber} updated`);
      } else {
        await jobRoundService.createJobRound(jobId, payload as CreateJobRoundPayload);
        toast.success(`Round ${roundNumber} created`);
      }

      setIsDialogOpen(false);
      await fetchRounds();
      if (onRoundsChange) onRoundsChange();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to save round configuration');
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleActive = async (round: JobRound) => {
    try {
      await jobRoundService.updateJobRound(jobId, round.id, { is_active: !round.is_active });
      toast.success(`Round ${round.round_number} ${!round.is_active ? 'activated' : 'deactivated'}`);
      await fetchRounds();
      if (onRoundsChange) onRoundsChange();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to update round status');
    }
  };

  const handleMoveRound = async (index: number, direction: 'up' | 'down') => {
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= rounds.length) return;

    const roundA = rounds[index];
    const roundB = rounds[targetIndex];

    try {
      // Swap round numbers
      await jobRoundService.updateJobRound(jobId, roundA.id, { round_number: 9999 }); // temp offset
      await jobRoundService.updateJobRound(jobId, roundB.id, { round_number: roundA.round_number });
      await jobRoundService.updateJobRound(jobId, roundA.id, { round_number: roundB.round_number });

      toast.success('Rounds reordered');
      await fetchRounds();
      if (onRoundsChange) onRoundsChange();
    } catch (err: any) {
      toast.error('Failed to reorder rounds');
    }
  };

  const formatDateString = (isoStr?: string | null) => {
    if (!isoStr) return 'Not set';
    return new Date(isoStr).toLocaleString([], {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  };

  return (
    <div className="space-y-4 border-t pt-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-foreground flex items-center gap-2">
            <Clock className="h-5 w-5 text-primary" />
            Recruitment Workflow ({rounds.length} Rounds)
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Rounds configured here will automatically snapshot when a student applies.
          </p>
        </div>
        <Button size="sm" onClick={openCreateModal} className="h-8 gap-1">
          <Plus className="h-3.5 w-3.5" /> Add Round
        </Button>
      </div>

      {rounds.length === 0 ? (
        <div className="p-6 text-center border rounded-lg bg-muted/20 text-muted-foreground">
          <AlertCircle className="h-8 w-8 mx-auto mb-2 text-amber-500 opacity-80" />
          <p className="text-sm font-medium">No recruitment rounds configured for this job.</p>
          <p className="text-xs mt-1">Students can still apply, but no automated interview rounds will be attached.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {rounds.map((r, idx) => (
            <Card
              key={r.id}
              className={`border transition-all ${
                !r.is_active ? 'opacity-50 bg-muted/40 border-dashed' : 'bg-card border-border'
              }`}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start gap-3">
                    <div className="h-8 w-8 rounded-full bg-primary/10 text-primary font-bold flex items-center justify-center text-sm shrink-0 mt-0.5">
                      {r.round_number}
                    </div>
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold text-sm text-foreground">
                          {r.title || r.round_type}
                        </span>
                        <Badge variant="outline" className="text-xs">
                          {r.round_type}
                        </Badge>
                        <Badge
                          variant={r.schedule_type === 'AVAILABILITY_WINDOW' ? 'secondary' : 'default'}
                          className="text-[10px]"
                        >
                          {r.schedule_type === 'AVAILABILITY_WINDOW' ? 'Window' : 'Fixed Time'}
                        </Badge>
                        {!r.is_active && <Badge variant="destructive" className="text-[10px]">Inactive</Badge>}
                      </div>

                      {r.description && (
                        <p className="text-xs text-muted-foreground mt-1">{r.description}</p>
                      )}

                      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground flex-wrap">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3.5 w-3.5 text-primary" />
                          {r.schedule_type === 'AVAILABILITY_WINDOW' ? (
                            <>
                              Window: {formatDateString(r.available_from)} → {formatDateString(r.available_until)}
                            </>
                          ) : (
                            <>Scheduled: {formatDateString(r.available_from)}</>
                          )}
                        </span>
                        <span className="font-medium text-foreground">
                          Duration: {r.duration_minutes} mins
                        </span>
                      </div>

                      {(r.test_link || r.meeting_link) && (
                        <div className="flex items-center gap-3 mt-2 text-xs">
                          {r.test_link && (
                            <a
                              href={r.test_link}
                              target="_blank"
                              rel="noreferrer"
                              className="text-primary hover:underline flex items-center gap-1 font-medium"
                            >
                              <FileText className="h-3 w-3" /> Test Link
                            </a>
                          )}
                          {r.meeting_link && (
                            <a
                              href={r.meeting_link}
                              target="_blank"
                              rel="noreferrer"
                              className="text-primary hover:underline flex items-center gap-1 font-medium"
                            >
                              <Video className="h-3 w-3" /> Meeting Link
                            </a>
                          )}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-1 shrink-0">
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-7 w-7 text-muted-foreground"
                      disabled={idx === 0}
                      onClick={() => handleMoveRound(idx, 'up')}
                      title="Move Up"
                    >
                      <ArrowUp className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-7 w-7 text-muted-foreground"
                      disabled={idx === rounds.length - 1}
                      onClick={() => handleMoveRound(idx, 'down')}
                      title="Move Down"
                    >
                      <ArrowDown className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      size="icon"
                      variant="outline"
                      className="h-7 w-7"
                      onClick={() => openEditModal(r)}
                      title="Edit Round"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      size="sm"
                      variant={r.is_active ? 'ghost' : 'outline'}
                      className={`h-7 px-2 text-xs ${!r.is_active ? 'text-emerald-600' : 'text-muted-foreground'}`}
                      onClick={() => handleToggleActive(r)}
                    >
                      {r.is_active ? 'Deactivate' : 'Activate'}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create / Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-md max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingRound ? `Edit Round ${editingRound.round_number}` : 'Add Recruitment Round'}
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4 py-2">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-xs font-semibold">Round Number</Label>
                <Input
                  type="number"
                  min={1}
                  value={roundNumber}
                  onChange={(e) => setRoundNumber(Number(e.target.value))}
                  required
                />
              </div>

              <div>
                <Label className="text-xs font-semibold">Round Type</Label>
                <Select
                  value={roundType}
                  onValueChange={(val) => setRoundType(val as RoundType)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ROUND_TYPES.map((rt) => (
                      <SelectItem key={rt} value={rt}>
                        {rt}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label className="text-xs font-semibold">Title</Label>
              <Input
                placeholder="e.g. Technical Screening"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>

            <div>
              <Label className="text-xs font-semibold">Schedule Type</Label>
              <Select
                value={scheduleType}
                onValueChange={(val) => setScheduleType(val as ScheduleType)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="FIXED_TIME">Fixed Time</SelectItem>
                  <SelectItem value="AVAILABILITY_WINDOW">Availability Window</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-xs font-semibold">
                  {scheduleType === 'AVAILABILITY_WINDOW' ? 'Available From' : 'Scheduled Start'}
                </Label>
                <Input
                  type="datetime-local"
                  value={availableFrom}
                  onChange={(e) => setAvailableFrom(e.target.value)}
                  required
                />
              </div>

              {scheduleType === 'AVAILABILITY_WINDOW' ? (
                <div>
                  <Label className="text-xs font-semibold">Available Until</Label>
                  <Input
                    type="datetime-local"
                    value={availableUntil}
                    onChange={(e) => setAvailableUntil(e.target.value)}
                    required
                  />
                </div>
              ) : (
                <div>
                  <Label className="text-xs font-semibold">Duration (Minutes)</Label>
                  <Input
                    type="number"
                    min={15}
                    value={durationMinutes}
                    onChange={(e) => setDurationMinutes(Number(e.target.value))}
                    required
                  />
                </div>
              )}
            </div>

            {scheduleType === 'AVAILABILITY_WINDOW' && (
              <div>
                <Label className="text-xs font-semibold">Duration per Student (Minutes)</Label>
                <Input
                  type="number"
                  min={15}
                  value={durationMinutes}
                  onChange={(e) => setDurationMinutes(Number(e.target.value))}
                  required
                />
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-xs font-semibold">Test Link (Optional)</Label>
                <Input
                  placeholder="https://..."
                  value={testLink}
                  onChange={(e) => setTestLink(e.target.value)}
                />
              </div>
              <div>
                <Label className="text-xs font-semibold">Meeting Link (Optional)</Label>
                <Input
                  placeholder="https://..."
                  value={meetingLink}
                  onChange={(e) => setMeetingLink(e.target.value)}
                />
              </div>
            </div>

            <div>
              <Label className="text-xs font-semibold">Instructions / Description</Label>
              <Textarea
                placeholder="Specific instructions for candidates..."
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                rows={2}
              />
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? 'Saving...' : editingRound ? 'Update Round' : 'Create Round'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};
