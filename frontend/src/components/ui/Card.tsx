import React, { forwardRef } from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'subtle' | 'outline';
  hoverable?: boolean;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ children, variant = 'default', hoverable = false, className = '', ...props }, ref) => {
    const variantStyles = {
      default: 'bg-white border border-slate-200/80 shadow-xs',
      elevated: 'bg-white border border-slate-200/80 shadow-sm hover:shadow-md',
      subtle: 'bg-slate-50/70 border border-slate-200/60',
      outline: 'bg-transparent border border-slate-200',
    };

    const hoverStyle = hoverable ? 'transition-all duration-200 hover:-translate-y-0.5 hover:border-slate-300' : '';

    return (
      <div
        ref={ref}
        className={`rounded-xl overflow-hidden ${variantStyles[variant]} ${hoverStyle} ${className}`}
        {...props}
      >
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
        className={`text-base font-bold text-slate-900 tracking-tight leading-snug truncate ${className}`}
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
        className={`px-5 py-3.5 bg-slate-50/50 border-t border-slate-100 flex items-center justify-between gap-3 text-xs text-slate-500 ${className}`}
        {...props}
      >
        {children}
      </div>
    );
  }
);
CardFooter.displayName = 'CardFooter';
