import { useState, useMemo, useEffect } from 'react';
import {
  Sparkles,
  Search,
  Plus,
  X,
  TrendingUp,
  Circle,
  CircleDot,
  CircleCheckBig,
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { PageHeader, PageContainer, LoadingSkeleton } from '@/components/common/PageHeader';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
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
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import { EmptyState } from '@/components/common/EmptyState';
import { cn } from '@/lib/utils';
import toast from 'react-hot-toast';
import { initialSkills } from '../data/profile-skills-resume';
import type { Skill, Proficiency, SkillCategory } from '../types';

const proficiencyConfig: Record<Proficiency, { value: number; color: string; icon: React.ElementType }> = {
  Beginner: { value: 33, color: 'text-amber-600 dark:text-amber-400', icon: Circle },
  Intermediate: { value: 66, color: 'text-blue-600 dark:text-blue-400', icon: CircleDot },
  Advanced: { value: 100, color: 'text-emerald-600 dark:text-emerald-400', icon: CircleCheckBig },
};

const proficiencyBadge: Record<Proficiency, string> = {
  Beginner: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 border-amber-200 dark:border-amber-800',
  Intermediate: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 border-blue-200 dark:border-blue-800',
  Advanced: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800',
};

const categories: SkillCategory[] = [
  'Programming Languages',
  'Frontend',
  'Backend',
  'Database',
  'Cloud',
  'AI / ML',
  'Tools',
];

export default function StudentSkills() {
  const [loading, setLoading] = useState(true);
  const [skills, setSkills] = useState<Skill[]>(initialSkills);
  const [search, setSearch] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newSkill, setNewSkill] = useState({ name: '', category: 'Frontend' as SkillCategory, proficiency: 'Beginner' as Proficiency });

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 500);
    return () => clearTimeout(timer);
  }, []);

  const stats = useMemo(() => {
    const advanced = skills.filter((s) => s.proficiency === 'Advanced').length;
    const intermediate = skills.filter((s) => s.proficiency === 'Intermediate').length;
    const beginner = skills.filter((s) => s.proficiency === 'Beginner').length;
    return { total: skills.length, advanced, intermediate, beginner };
  }, [skills]);

  const filtered = useMemo(() => {
    if (!search.trim()) return skills;
    const q = search.toLowerCase();
    return skills.filter((s) => s.name.toLowerCase().includes(q) || s.category.toLowerCase().includes(q));
  }, [skills, search]);

  const grouped = useMemo(() => {
    const map = new Map<SkillCategory, Skill[]>();
    for (const cat of categories) {
      const items = filtered.filter((s) => s.category === cat);
      if (items.length > 0) map.set(cat, items);
    }
    return map;
  }, [filtered]);

  const handleRemove = (id: string) => {
    setSkills((prev) => prev.filter((s) => s.id !== id));
    toast.success('The skill has been removed from your profile.');
  };

  const handleAdd = () => {
    if (!newSkill.name.trim()) return;
    const skill: Skill = {
      id: `SKL-${String(skills.length + 1).padStart(3, '0')}`,
      name: newSkill.name.trim(),
      category: newSkill.category,
      proficiency: newSkill.proficiency,
    };
    setSkills((prev) => [...prev, skill]);
    setNewSkill({ name: '', category: 'Frontend', proficiency: 'Beginner' });
    setDialogOpen(false);
    toast.success(`${skill.name} has been added to your profile.`);
  };

  const statCards = [
    { label: 'Total Skills', value: stats.total, icon: Sparkles, color: 'text-primary', bg: 'bg-primary/10' },
    { label: 'Advanced', value: stats.advanced, icon: CircleCheckBig, color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-100 dark:bg-emerald-900/30' },
    { label: 'Intermediate', value: stats.intermediate, icon: CircleDot, color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-100 dark:bg-blue-900/30' },
    { label: 'Beginner', value: stats.beginner, icon: Circle, color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-100 dark:bg-amber-900/30' },
  ];

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
          title="My Skills"
          description="Track and manage your technical skills and proficiency levels."
          action={
            <Button onClick={() => setDialogOpen(true)}>
              <Plus className="mr-1.5 h-4 w-4" />
              Add Skill
            </Button>
          }
        />

        {/* Stats grid */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {statCards.map((stat) => (
            <Card key={stat.label} className="transition-all hover:shadow-md hover:-translate-y-0.5">
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">{stat.label}</p>
                    <p className="text-3xl font-bold tracking-tight">{stat.value}</p>
                  </div>
                  <div className={cn('flex h-11 w-11 items-center justify-center rounded-xl', stat.bg)}>
                    <stat.icon className={cn('h-5 w-5', stat.color)} />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Overall proficiency bar */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle>Proficiency Breakdown</CardTitle>
              <CardDescription>Distribution of your skill levels</CardDescription>
            </div>
            <TrendingUp className="h-5 w-5 text-muted-foreground" />
          </CardHeader>
          <CardContent className="space-y-4">
            {(['Advanced', 'Intermediate', 'Beginner'] as Proficiency[]).map((level) => {
              const config = proficiencyConfig[level];
              const count = stats[level.toLowerCase() as 'advanced' | 'intermediate' | 'beginner'];
              const pct = stats.total > 0 ? Math.round((count / stats.total) * 100) : 0;
              return (
                <div key={level} className="space-y-1.5">
                  <div className="flex items-center justify-between text-sm">
                    <span className="flex items-center gap-2 font-medium">
                      <config.icon className={cn('h-4 w-4', config.color)} />
                      {level}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      <span className="font-semibold text-foreground">{count}</span> skills ({pct}%)
                    </span>
                  </div>
                  <Progress value={pct} className="h-2" />
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Search */}
        <div className="relative w-full sm:max-w-sm">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search skills or categories..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
            aria-label="Search skills"
          />
        </div>

        {/* Skills by category */}
        {filtered.length === 0 ? (
          <Card>
            <CardContent>
              <EmptyState
                icon={Sparkles}
                title={search ? 'No skills found' : 'No skills yet'}
                description={search ? 'Try a different search term.' : 'Add your first skill to start building your profile.'}
                actionLabel={search ? undefined : 'Add Skill'}
                onAction={search ? undefined : () => setDialogOpen(true)}
              />
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {[...grouped.entries()].map(([category, items]) => (
              <Card key={category}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0">
                  <CardTitle className="text-base">{category}</CardTitle>
                  <Badge variant="secondary" className="text-xs">{items.length}</Badge>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {items.map((skill) => {
                      const config = proficiencyConfig[skill.proficiency];
                      return (
                        <div
                          key={skill.id}
                          className="group flex items-center gap-3 rounded-lg border p-3 transition-all hover:border-primary/30 hover:shadow-sm"
                        >
                          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-secondary">
                            <config.icon className={cn('h-5 w-5', config.color)} />
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="truncate text-sm font-semibold">{skill.name}</p>
                            <Badge variant="outline" className={cn('mt-1 text-[10px] font-medium', proficiencyBadge[skill.proficiency])}>
                              {skill.proficiency}
                            </Badge>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 shrink-0 text-muted-foreground opacity-0 transition-opacity hover:text-destructive group-hover:opacity-100"
                            onClick={() => handleRemove(skill.id)}
                            aria-label={`Remove ${skill.name}`}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </PageContainer>

      {/* Add skill dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Add New Skill</DialogTitle>
            <DialogDescription>Add a technical skill with its category and proficiency level.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="skill-name">Skill Name</Label>
              <Input
                id="skill-name"
                placeholder="e.g., Rust, Kubernetes, GraphQL"
                value={newSkill.name}
                onChange={(e) => setNewSkill((p) => ({ ...p, name: e.target.value }))}
                onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="skill-category">Category</Label>
              <Select value={newSkill.category} onValueChange={(v) => setNewSkill((p) => ({ ...p, category: v as SkillCategory }))}>
                <SelectTrigger id="skill-category">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((cat) => (
                    <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="skill-proficiency">Proficiency</Label>
              <Select value={newSkill.proficiency} onValueChange={(v) => setNewSkill((p) => ({ ...p, proficiency: v as Proficiency }))}>
                <SelectTrigger id="skill-proficiency">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Beginner">Beginner</SelectItem>
                  <SelectItem value="Intermediate">Intermediate</SelectItem>
                  <SelectItem value="Advanced">Advanced</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleAdd} disabled={!newSkill.name.trim()}>
              <Plus className="mr-1.5 h-4 w-4" />
              Add Skill
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppLayout>
  );
}
