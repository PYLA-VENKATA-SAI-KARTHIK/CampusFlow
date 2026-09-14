import React, { forwardRef, useId } from 'react';

export interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: React.ReactNode;
  description?: React.ReactNode;
  error?: string;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ label, description, error, id, className = '', disabled, ...props }, ref) => {
    const generatedId = useId();
    const checkboxId = id || generatedId;
    const errorId = `${checkboxId}-error`;

    return (
      <div className={`flex items-start ${className}`}>
        <div className="flex items-center h-5">
          <input
            ref={ref}
            id={checkboxId}
            type="checkbox"
            disabled={disabled}
            aria-invalid={error ? 'true' : 'false'}
            aria-describedby={error ? errorId : undefined}
            className="h-4 w-4 rounded-md text-indigo-600 border-slate-300 focus:ring-indigo-500/20 focus:ring-2 transition duration-150 ease-in-out cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
            {...props}
          />
        </div>
        {(label || description) && (
          <div className="ml-3 text-xs leading-5">
            {label && (
              <label
                htmlFor={checkboxId}
                className={`font-semibold select-none cursor-pointer ${
                  disabled ? 'text-slate-400 cursor-not-allowed' : 'text-slate-700 hover:text-slate-900'
                }`}
              >
                {label}
              </label>
            )}
            {description && (
              <p className="text-slate-500 select-none">{description}</p>
            )}
            {error && (
              <p id={errorId} className="mt-1 text-rose-600 font-semibold animate-fade-in" role="alert">
                {error}
              </p>
            )}
          </div>
        )}
      </div>
    );
  }
);
Checkbox.displayName = 'Checkbox';
