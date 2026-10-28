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
  | 'outline'
  | 'lilac'
  | 'obsidian';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: 'sm' | 'md' | 'lg';
  dot?: boolean;
  bracket?: boolean;
  mono?: boolean;
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  (
    {
      children,
      variant = 'default',
      size = 'md',
      dot = false,
      bracket = false,
      mono = false,
      className = '',
      ...props
    },
    ref
  ) => {
    const sizeStyles = {
      sm: 'px-1.5 py-0.5 text-[10px] gap-1 font-semibold',
      md: 'px-2 py-0.5 text-[11px] gap-1.5 font-bold',
      lg: 'px-2.5 py-1 text-xs gap-2 font-bold',
    };

    const variantStyles: Record<BadgeVariant, { container: string; dot: string }> = {
      default: {
        container: 'bg-[#f4f5f8] text-slate-800 border border-slate-300',
        dot: 'bg-slate-500',
      },
      neutral: {
        container: 'bg-[#f4f5f8] text-slate-700 border border-slate-300',
        dot: 'bg-slate-400',
      },
      primary: {
        container: 'bg-[#f6f3fc] text-[#4b3679] border border-[#c1aeee]',
        dot: 'bg-[#9b86d9]',
      },
      lilac: {
        container: 'bg-[#9b86d9] text-[#07080b] border border-[#07080b] shadow-[1px_1px_0px_#07080b]',
        dot: 'bg-[#07080b]',
      },
      obsidian: {
        container: 'bg-[#0b0c10] text-slate-100 border border-[#1f202b]',
        dot: 'bg-[#10b981]',
      },
      secondary: {
        container: 'bg-slate-900 text-white border border-slate-800',
        dot: 'bg-slate-300',
      },
      success: {
        container: 'bg-[#ecfdf5] text-[#065f46] border border-[#a7f3d0]',
        dot: 'bg-[#10b981]',
      },
      warning: {
        container: 'bg-[#fffbeb] text-[#92400e] border border-[#fde68a]',
        dot: 'bg-[#f59e0b]',
      },
      danger: {
        container: 'bg-[#fff1f2] text-[#9f1239] border border-[#fecdd3]',
        dot: 'bg-[#e11d48]',
      },
      info: {
        container: 'bg-[#f6f3fc] text-[#4b3679] border border-[#ddd0f5]',
        dot: 'bg-[#9b86d9]',
      },
      outline: {
        container: 'bg-white text-slate-700 border border-slate-300',
        dot: 'bg-slate-400',
      },
    };

    const currentVariant = variantStyles[variant] || variantStyles.default;
    const fontClass = mono ? 'font-mono uppercase tracking-wider' : 'font-sans tracking-tight';

    return (
      <span
        ref={ref}
        className={`inline-flex items-center rounded-sm transition-colors ${fontClass} ${sizeStyles[size]} ${currentVariant.container} ${className}`}
        {...props}
      >
        {bracket && <span className="text-slate-400 select-none font-mono mr-0.5">[</span>}
        {dot && (
          <span
            className={`h-1.5 w-1.5 rounded-full shrink-0 ${currentVariant.dot}`}
            aria-hidden="true"
          />
        )}
        <span>{children}</span>
        {bracket && <span className="text-slate-400 select-none font-mono ml-0.5">]</span>}
      </span>
    );
  }
);
Badge.displayName = 'Badge';

/**
 * StatusBadge maps domain status strings to appropriate semantic badges with technical HUD styling.
 */
export interface StatusBadgeProps extends Omit<BadgeProps, 'variant'> {
  status?: string | null;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status = 'ACTIVE', mono = true, bracket = false, ...props }) => {
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
    <Badge variant={variant} dot mono={mono} bracket={bracket} {...props}>
      {safeStatus}
    </Badge>
  );
};
