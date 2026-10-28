import React from 'react';

export interface PageHeaderProps {
  eyebrow?: string;
  sectionNumber?: string;
  coordinates?: string;
  readout?: string;
  title: React.ReactNode;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  badge?: React.ReactNode;
  className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  eyebrow,
  sectionNumber,
  coordinates,
  readout,
  title,
  description,
  actions,
  badge,
  className = '',
}) => {
  return (
    <header className={`mb-8 border-b border-slate-200 pb-6 ${className}`}>
      {/* Top Technical Metadata Bar (Coordinates & Section Tags) */}
      {(coordinates || eyebrow) && (
        <div className="flex items-center justify-between font-mono text-[11px] text-slate-500 mb-2 select-none tracking-wider">
          <div className="flex items-center space-x-2">
            {eyebrow && (
              <span className="font-bold text-[#6d50b4] uppercase">
                {eyebrow.startsWith('[') ? eyebrow : `[${eyebrow}]`}
              </span>
            )}
          </div>
          {coordinates && (
            <span className="text-slate-400 font-mono text-[10px] tracking-widest uppercase">
              {coordinates}
            </span>
          )}
        </div>
      )}

      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1.5 min-w-0">
          <div className="flex items-baseline gap-3.5">
            {sectionNumber && (
              <span className="font-display font-black text-3xl sm:text-4xl text-[#9b86d9] select-none tracking-tighter">
                {sectionNumber}
              </span>
            )}
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl sm:text-3xl font-black text-slate-950 tracking-tighter font-display">
                {title}
              </h1>
              {badge && <div>{badge}</div>}
            </div>
          </div>

          {readout && (
            <div className="font-mono text-[10px] font-bold text-slate-500 uppercase tracking-widest pt-0.5">
              {readout}
            </div>
          )}

          {description && (
            <p className="text-xs sm:text-sm text-slate-600 max-w-3xl leading-relaxed pt-0.5">
              {description}
            </p>
          )}
        </div>

        {actions && (
          <div className="flex flex-wrap items-center gap-2 shrink-0 sm:self-center">
            {actions}
          </div>
        )}
      </div>
    </header>
  );
};
