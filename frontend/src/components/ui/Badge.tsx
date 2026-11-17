import { LucideIcon } from 'lucide-react';

interface BadgeProps {
  label: string;
  variant?: 'default' | 'critical' | 'high' | 'verified' | 'low' | 'info';
  icon?: LucideIcon;
  size?: 'xs' | 'sm' | 'md';
}

const variantClasses: Record<NonNullable<BadgeProps['variant']>, string> = {
  default: 'bg-[#F4F5FB] text-[#73758B] border border-[#E6E5F0]',
  critical: 'bg-[#FDF2F2] text-[#DC4545] border border-[#FAD8D8]',
  high: 'bg-[#FFF8EC] text-[#E9A12A] border border-[#FFE8BF]',
  verified: 'bg-[#EBF9F1] text-[#159B55] border border-[#D1F2DE]',
  low: 'bg-[#EBF9F1] text-[#159B55] border border-[#D1F2DE]',
  info: 'bg-[#F0EBFF] text-[#7045E8] border border-[#DDD5F9]',
};

const sizeClasses: Record<NonNullable<BadgeProps['size']>, string> = {
  xs: 'text-[10px] px-2 py-0.5 font-medium',
  sm: 'text-xs px-2.5 py-1 font-semibold',
  md: 'text-xs px-3 py-1.5 font-bold',
};

export default function Badge({ 
  label, 
  variant = 'default',
  icon: Icon,
  size = 'sm'
}: BadgeProps) {
  return (
    <span className={`status-badge inline-flex items-center gap-1.5 rounded-full ${variantClasses[variant]} ${sizeClasses[size]}`}>
      {Icon && <Icon size={size === 'xs' ? 12 : size === 'sm' ? 14 : 16} />}
      {label}
    </span>
  );
}
