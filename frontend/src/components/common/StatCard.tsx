import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { ArrowUpRight, ArrowDownRight, Minus, Briefcase, ClipboardList, Gauge, Users } from 'lucide-react';

type StatCardProps = {
  label: string;
  value: string;
  change: string;
  trend: 'up' | 'down' | 'neutral';
  icon: 'briefcase' | 'clipboard' | 'gauge' | 'users';
};

const iconMap = {
  briefcase: Briefcase,
  clipboard: ClipboardList,
  gauge: Gauge,
  users: Users,
};

const trendConfig = {
  up: { icon: ArrowUpRight, className: 'text-emerald-600 dark:text-emerald-400' },
  down: { icon: ArrowDownRight, className: 'text-rose-600 dark:text-rose-400' },
  neutral: { icon: Minus, className: 'text-muted-foreground' },
};

export function StatCard({ label, value, change, trend, icon }: StatCardProps) {
  const Icon = iconMap[icon];
  const TrendIcon = trendConfig[trend].icon;

  return (
    <Card className="overflow-hidden transition-all hover:shadow-md hover:-translate-y-0.5">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">{label}</p>
            <p className="text-3xl font-bold tracking-tight">{value}</p>
          </div>
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <Icon className="h-5 w-5" />
          </div>
        </div>
        <div className={cn('mt-3 flex items-center gap-1 text-xs font-medium', trendConfig[trend].className)}>
          <TrendIcon className="h-3.5 w-3.5" />
          <span>{change}</span>
        </div>
      </CardContent>
    </Card>
  );
}
