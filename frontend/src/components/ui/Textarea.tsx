import React, { forwardRef, useId } from 'react';
import { Label } from './Label';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      label,
      error,
      helperText,
      id,
      required,
      className = '',
      disabled,
      rows = 4,
      ...props
    },
    ref
  ) => {
    const generatedId = useId();
    const textareaId = id || generatedId;
    const errorId = `${textareaId}-error`;
    const helperId = `${textareaId}-helper`;

    const describedBy = error ? errorId : helperText ? helperId : undefined;

    return (
      <div className="w-full">
        {label && (
          <Label htmlFor={textareaId} required={required}>
            {label}
          </Label>
        )}
        <div className="relative">
          <textarea
            ref={ref}
            id={textareaId}
            rows={rows}
            required={required}
            disabled={disabled}
            aria-invalid={error ? 'true' : 'false'}
            aria-describedby={describedBy}
            className={`w-full text-sm font-medium bg-white text-slate-900 placeholder:text-slate-400 border rounded-xl px-3.5 py-2.5 transition duration-150 ease-in-out focus:outline-none focus:ring-2 disabled:bg-slate-50 disabled:text-slate-400 disabled:cursor-not-allowed resize-y ${
              error
                ? 'border-rose-300 focus:border-rose-500 focus:ring-rose-500/20 text-rose-900 placeholder:text-rose-300'
                : 'border-slate-200 hover:border-slate-300 focus:border-indigo-600 focus:ring-indigo-600/20'
            } ${className}`}
            {...props}
          />
        </div>
        {error && (
          <p id={errorId} className="mt-1.5 text-xs font-semibold text-rose-600 animate-fade-in" role="alert">
            {error}
          </p>
        )}
        {!error && helperText && (
          <p id={helperId} className="mt-1.5 text-xs text-slate-500">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);
Textarea.displayName = 'Textarea';
