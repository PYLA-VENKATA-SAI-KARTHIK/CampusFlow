import React from 'react';

export interface PageHeaderProps {
  eyebrow?: string;
  title: React.ReactNode;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  badge?: React.ReactNode;
  className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  eyebrow,
  title,
  description,
  actions,
  badge,
  className = '',
}) => {
  return (
    <header className={`mb-8 border-b border-slate-200/80 pb-6 ${className}`}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1 min-w-0">
          {eyebrow && (
            <p className="text-[11px] font-bold uppercase tracking-wider text-indigo-600">
              {eyebrow}
            </p>
          )}
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-black text-slate-900 tracking-tight sm:text-3xl">
              {title}
            </h1>
            {badge && <div>{badge}</div>}
          </div>
          {description && (
            <p className="text-sm text-slate-500 max-w-3xl leading-relaxed">
              {description}
            </p>
          )}
        </div>
        {actions && (
          <div className="flex flex-wrap items-center gap-2.5 shrink-0 sm:self-center">
            {actions}
          </div>
        )}
      </div>
    </header>
  );
};
