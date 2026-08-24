import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

type FormFieldProps = {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: 'text' | 'email' | 'tel' | 'date' | 'number' | 'url';
  placeholder?: string;
  error?: string;
  icon?: React.ElementType;
  disabled?: boolean;
  className?: string;
};

export function FormField({
  id,
  label,
  value,
  onChange,
  type = 'text',
  placeholder,
  error,
  icon: Icon,
  disabled,
  className,
}: FormFieldProps) {
  return (
    <div className={cn('space-y-2', className)}>
      <Label htmlFor={id} className={cn(error && 'text-destructive')}>
        {label}
      </Label>
      <div className="relative">
        {Icon && (
          <Icon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        )}
        <Input
          id={id}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          aria-invalid={!!error}
          aria-describedby={error ? `${id}-error` : undefined}
          className={cn(
            Icon && 'pl-9',
            error && 'border-destructive focus-visible:ring-destructive'
          )}
        />
      </div>
      {error && (
        <p id={`${id}-error`} className="text-xs font-medium text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}

type ReadOnlyFieldProps = {
  label: string;
  value: string;
  icon?: React.ElementType;
  className?: string;
};

export function ReadOnlyField({ label, value, icon: Icon, className }: ReadOnlyFieldProps) {
  return (
    <div className={cn('space-y-1.5', className)}>
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <div className="flex items-center gap-2 rounded-lg border bg-secondary/30 px-3 py-2.5">
        {Icon && <Icon className="h-4 w-4 shrink-0 text-muted-foreground" />}
        <span className="text-sm font-medium">{value || '—'}</span>
      </div>
    </div>
  );
}
