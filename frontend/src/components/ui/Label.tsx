import React, { forwardRef } from 'react';

export interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
  required?: boolean;
}

export const Label = forwardRef<HTMLLabelElement, LabelProps>(
  ({ children, required = false, className = '', ...props }, ref) => {
    return (
      <label
        ref={ref}
        className={`block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 ${className}`}
        {...props}
      >
        {children}
        {required && <span className="text-rose-500 ml-1" aria-hidden="true">*</span>}
      </label>
    );
  }
);
Label.displayName = 'Label';
