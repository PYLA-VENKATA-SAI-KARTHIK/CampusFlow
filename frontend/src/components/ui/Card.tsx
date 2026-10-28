import React, { forwardRef } from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'subtle' | 'outline' | 'terminal' | 'hud' | 'lilac';
  hoverable?: boolean;
  terminalTitle?: string;
  terminalBadge?: string;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      children,
      variant = 'default',
      hoverable = false,
      terminalTitle = 'VALIDATION_RUN.LOG',
      terminalBadge,
      className = '',
      ...props
    },
    ref
  ) => {
    const variantStyles = {
      default: 'bg-white border border-slate-200/90 shadow-[0_1px_3px_rgba(0,0,0,0.03)]',
      elevated: 'bg-white border border-slate-300 shadow-[3px_3px_0px_rgba(10,11,16,0.08)]',
      subtle: 'bg-[#f8f9fc] border border-slate-200/80',
      outline: 'bg-transparent border border-slate-300',
      terminal: 'bg-[#eceef2] border border-[#14151d] shadow-[4px_4px_0px_rgba(10,11,16,0.9)]',
      hud: 'bg-white border border-slate-300 shadow-[3px_3px_0px_rgba(10,11,16,0.05)] hover:border-slate-800',
      lilac: 'bg-white border-2 border-[#9b86d9] shadow-[3px_3px_0px_#9b86d9]',
    };

    const hoverStyle = hoverable
      ? 'transition-all duration-150 hover:-translate-y-0.5 hover:shadow-[4px_4px_0px_rgba(10,11,16,0.12)]'
      : '';

    return (
      <div
        ref={ref}
        className={`rounded-md overflow-hidden ${variantStyles[variant]} ${hoverStyle} ${className}`}
        {...props}
      >
        {variant === 'terminal' && (
          <div className="bg-[#0b0c10] px-4 py-2 border-b border-[#14151d] flex items-center justify-between text-white select-none">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
              <span className="font-mono text-[11px] font-bold tracking-wider text-slate-100">
                {terminalTitle}
              </span>
            </div>
            {terminalBadge && (
              <span className="font-mono text-[10px] text-slate-400 uppercase tracking-widest">
                {terminalBadge}
              </span>
            )}
          </div>
        )}
        {children}
      </div>
    );
  }
);
Card.displayName = 'Card';

export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  action?: React.ReactNode;
}

export const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ children, action, className = '', ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={`px-5 py-4 border-b border-slate-100 flex items-center justify-between gap-3 ${className}`}
        {...props}
      >
        <div className="space-y-0.5 min-w-0">{children}</div>
        {action && <div className="shrink-0">{action}</div>}
      </div>
    );
  }
);
CardHeader.displayName = 'CardHeader';

export const CardTitle = forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ children, className = '', ...props }, ref) => {
    return (
      <h3
        ref={ref}
        className={`text-base font-bold text-slate-900 tracking-tight leading-snug truncate font-display ${className}`}
        {...props}
      >
        {children}
      </h3>
    );
  }
);
CardTitle.displayName = 'CardTitle';

export const CardDescription = forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ children, className = '', ...props }, ref) => {
    return (
      <p
        ref={ref}
        className={`text-xs text-slate-500 leading-relaxed ${className}`}
        {...props}
      >
        {children}
      </p>
    );
  }
);
CardDescription.displayName = 'CardDescription';

export const CardContent = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ children, className = '', ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={`p-5 ${className}`}
        {...props}
      >
        {children}
      </div>
    );
  }
);
CardContent.displayName = 'CardContent';

export const CardFooter = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ children, className = '', ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={`px-5 py-3.5 bg-slate-50/70 border-t border-slate-100 flex items-center justify-between gap-3 text-xs text-slate-500 font-mono ${className}`}
        {...props}
      >
        {children}
      </div>
    );
  }
);
CardFooter.displayName = 'CardFooter';
