import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { statusBadgeClasses } from '@/lib/status-styles';

export function StatusBadge({ status }: { status: string }) {
  return (
    <Badge variant="outline" className={cn('font-medium', statusBadgeClasses[status] || statusBadgeClasses['Active'])}>
      {status}
    </Badge>
  );
}
