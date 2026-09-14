import React from 'react';

/* -------------------------------------------------------------------------- */
/*                               LoadingSpinner                               */
/* -------------------------------------------------------------------------- */

export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  label,
  className = '',
}) => {
  const sizeStyles = {
    sm: 'h-4 w-4 border-2',
    md: 'h-8 w-8 border-2.5',
    lg: 'h-12 w-12 border-3',
  };

  return (
    <div className={`flex flex-col items-center justify-center gap-3 p-4 ${className}`} role="status">
      <div
        className={`animate-spin rounded-full border-indigo-600 border-t-transparent ${sizeStyles[size]}`}
      />
      {label && <span className="text-xs font-semibold text-slate-500">{label}</span>}
      <span className="sr-only">Loading...</span>
    </div>
  );
};

/* -------------------------------------------------------------------------- */
/*                                  Skeleton                                  */
/* -------------------------------------------------------------------------- */

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'rectangular' | 'circular';
}

export const Skeleton: React.FC<SkeletonProps> = ({
  variant = 'rectangular',
  className = '',
  ...props
}) => {
  const variantStyles = {
    text: 'h-4 w-full rounded-md',
    rectangular: 'h-24 w-full rounded-xl',
    circular: 'h-10 w-10 rounded-full',
  };

  return (
    <div
      className={`animate-pulse bg-slate-200/70 ${variantStyles[variant]} ${className}`}
      aria-hidden="true"
      {...props}
    />
  );
};

/* -------------------------------------------------------------------------- */
/*                                 EmptyState                                 */
/* -------------------------------------------------------------------------- */

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className = '',
}) => {
  return (
    <div className={`flex flex-col items-center justify-center p-8 text-center rounded-2xl border border-dashed border-slate-200 bg-slate-50/50 ${className}`}>
      {icon ? (
        <div className="mb-3 text-slate-400">{icon}</div>
      ) : (
        <div className="w-12 h-12 mb-3 rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
          <svg
            className="w-6 h-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="1.5"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
            />
          </svg>
        </div>
      )}
      <h3 className="text-sm font-bold text-slate-800 tracking-tight">{title}</h3>
      {description && (
        <p className="mt-1 text-xs text-slate-500 max-w-sm leading-relaxed">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
};

/* -------------------------------------------------------------------------- */
/*                                    Alert                                   */
/* -------------------------------------------------------------------------- */

export type AlertVariant = 'info' | 'success' | 'warning' | 'danger';

export interface AlertProps {
  variant?: AlertVariant;
  title?: string;
  children: React.ReactNode;
  icon?: React.ReactNode;
  onClose?: () => void;
  className?: string;
}

export const Alert: React.FC<AlertProps> = ({
  variant = 'info',
  title,
  children,
  icon,
  onClose,
  className = '',
}) => {
  const variantStyles: Record<AlertVariant, { container: string; icon: string; title: string }> = {
    info: {
      container: 'bg-sky-50 border-sky-200 text-sky-800',
      icon: 'text-sky-500',
      title: 'text-sky-900',
    },
    success: {
      container: 'bg-emerald-50 border-emerald-200 text-emerald-800',
      icon: 'text-emerald-500',
      title: 'text-emerald-900',
    },
    warning: {
      container: 'bg-amber-50 border-amber-200 text-amber-800',
      icon: 'text-amber-500',
      title: 'text-amber-900',
    },
    danger: {
      container: 'bg-rose-50 border-rose-200 text-rose-800',
      icon: 'text-rose-500',
      title: 'text-rose-900',
    },
  };

  const currentVariant = variantStyles[variant];

  return (
    <div
      role="alert"
      className={`relative rounded-xl border p-4 text-xs transition-all ${currentVariant.container} ${className}`}
    >
      <div className="flex items-start gap-3">
        {icon && <div className={`shrink-0 mt-0.5 ${currentVariant.icon}`}>{icon}</div>}
        <div className="flex-1 min-w-0">
          {title && <h4 className={`font-bold mb-0.5 text-xs ${currentVariant.title}`}>{title}</h4>}
          <div className="leading-relaxed">{children}</div>
        </div>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            aria-label="Dismiss alert"
            className="shrink-0 rounded-md p-1 text-slate-400 hover:text-slate-600 focus:outline-none"
          >
            <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};

/* -------------------------------------------------------------------------- */
/*                                  StatCard                                  */
/* -------------------------------------------------------------------------- */

export interface StatCardProps {
  label: string;
  value: React.ReactNode;
  subtext?: string;
  icon?: React.ReactNode;
  badge?: React.ReactNode;
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  subtext,
  icon,
  badge,
  className = '',
}) => {
  return (
    <div className={`p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex flex-col justify-between ${className}`}>
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">{label}</span>
        {icon && <div className="text-slate-400">{icon}</div>}
      </div>
      <div className="mt-3 flex items-baseline justify-between gap-2">
        <div className="text-2xl font-black text-slate-900 tracking-tight">{value}</div>
        {badge && <div>{badge}</div>}
      </div>
      {subtext && <div className="mt-1 text-[11px] text-slate-400">{subtext}</div>}
    </div>
  );
};
