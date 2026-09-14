import React, { forwardRef } from 'react';

export type BadgeVariant =
  | 'default'
  | 'primary'
  | 'secondary'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'neutral'
  | 'outline';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: 'sm' | 'md' | 'lg';
  dot?: boolean;
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ children, variant = 'default', size = 'md', dot = false, className = '', ...props }, ref) => {
    const sizeStyles = {
      sm: 'px-2 py-0.5 text-[10px] gap-1 font-semibold',
      md: 'px-2.5 py-1 text-xs gap-1.5 font-bold',
      lg: 'px-3 py-1.5 text-xs gap-2 font-bold',
    };

    const variantStyles: Record<BadgeVariant, { container: string; dot: string }> = {
      default: {
        container: 'bg-slate-100 text-slate-700 border border-slate-200/80',
        dot: 'bg-slate-400',
      },
      neutral: {
        container: 'bg-slate-100 text-slate-700 border border-slate-200/80',
        dot: 'bg-slate-400',
      },
      primary: {
        container: 'bg-indigo-50 text-indigo-700 border border-indigo-200/80',
        dot: 'bg-indigo-500',
      },
      secondary: {
        container: 'bg-slate-800 text-white border border-slate-700',
        dot: 'bg-slate-300',
      },
      success: {
        container: 'bg-emerald-50 text-emerald-700 border border-emerald-200/80',
        dot: 'bg-emerald-500',
      },
      warning: {
        container: 'bg-amber-50 text-amber-800 border border-amber-200/80',
        dot: 'bg-amber-500',
      },
      danger: {
        container: 'bg-rose-50 text-rose-700 border border-rose-200/80',
        dot: 'bg-rose-500',
      },
      info: {
        container: 'bg-sky-50 text-sky-700 border border-sky-200/80',
        dot: 'bg-sky-500',
      },
      outline: {
        container: 'bg-white text-slate-600 border border-slate-300',
        dot: 'bg-slate-400',
      },
    };

    const currentVariant = variantStyles[variant] || variantStyles.default;

    return (
      <span
        ref={ref}
        className={`inline-flex items-center rounded-full tracking-wide transition-colors ${sizeStyles[size]} ${currentVariant.container} ${className}`}
        {...props}
      >
        {dot && (
          <span
            className={`h-1.5 w-1.5 rounded-full shrink-0 ${currentVariant.dot}`}
            aria-hidden="true"
          />
        )}
        <span>{children}</span>
      </span>
    );
  }
);
Badge.displayName = 'Badge';

/**
 * StatusBadge maps domain status strings to appropriate semantic badges.
 */
export interface StatusBadgeProps extends Omit<BadgeProps, 'variant'> {
  status?: string | null;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status = 'ACTIVE', ...props }) => {
  const safeStatus = status || 'ACTIVE';
  const normalized = safeStatus.toUpperCase().trim();

  let variant: BadgeVariant = 'neutral';

  switch (normalized) {
    case 'PUBLISHED':
    case 'ACTIVE':
    case 'REGISTERED':
    case 'PASSED':
    case 'OFFERED':
    case 'COMPLETED':
    case 'SUCCESS':
    case 'RESOLVED':
    case 'VERIFIED':
    case 'EASY':
      variant = 'success';
      break;

    case 'SHORTLISTED':
    case 'INTERVIEW_SCHEDULED':
    case 'IN_PROGRESS':
    case 'PENDING':
    case 'UNDER_REVIEW':
    case 'MEDIUM':
    case 'DRAFT':
      variant = 'warning';
      break;

    case 'REJECTED':
    case 'FAILED':
    case 'EXPIRED':
    case 'CANCELLED':
    case 'SUSPENDED':
    case 'HARD':
    case 'DISQUALIFIED':
      variant = 'danger';
      break;

    case 'PRIMARY':
    case 'APPLIED':
    case 'INFO':
    case 'CODING':
      variant = 'primary';
      break;

    case 'ARCHIVED':
    case 'OPTIONAL':
    case 'MCQ':
    case 'DEBUGGING':
    default:
      variant = 'neutral';
      break;
  }

  return (
    <Badge variant={variant} dot {...props}>
      {safeStatus}
    </Badge>
  );
};
