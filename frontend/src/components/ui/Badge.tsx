import { LucideIcon } from 'lucide-react';

interface BadgeProps {
  label: string;
  variant?: 'default' | 'critical' | 'high' | 'verified' | 'low' | 'info';
  icon?: LucideIcon;
  size?: 'xs' | 'sm' | 'md';
}

const variantClasses: Record<NonNullable<BadgeProps['variant']>, string> = {
  default: 'bg-ink-border text-gray-300',
  critical: 'severity-pill critical',
  high: 'severity-pill high',
  verified: 'severity-pill verified',
  low: 'severity-pill low',
  info: 'bg-brand/20 text-brand border border-brand/30',
};

const sizeClasses: Record<NonNullable<BadgeProps['size']>, string> = {
  xs: 'text-[10px] px-2 py-0.5',
  sm: 'text-xs px-2.5 py-1',
  md: 'text-xs px-3 py-1.5',
};

export default function Badge({ 
  label, 
  variant = 'default',
  icon: Icon,
  size = 'sm'
}: BadgeProps) {
  return (
    <span className={`status-badge inline-flex items-center gap-1.5 rounded-full font-semibold tracking-wide ${variantClasses[variant]} ${sizeClasses[size]}`}>
      {Icon && <Icon size={size === 'xs' ? 12 : size === 'sm' ? 14 : 16} />}
      {label}
    </span>
  );
}
