import React, { forwardRef } from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      className = '',
      disabled,
      type = 'button',
      ...props
    },
    ref
  ) => {
    // Base styling
    const baseStyles =
      'inline-flex items-center justify-center font-bold transition duration-150 ease-in-out select-none cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 active:scale-[0.98]';

    // Size variants
    const sizeStyles = {
      sm: 'text-xs px-3 py-1.5 rounded-lg gap-1.5',
      md: 'text-xs px-4 py-2.5 rounded-xl gap-2',
      lg: 'text-sm px-6 py-3 rounded-xl gap-2.5',
    };

    // Variant styling
    const variantStyles = {
      primary:
        'bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm shadow-indigo-600/20 focus-visible:ring-indigo-500 border border-transparent',
      secondary:
        'bg-slate-900 hover:bg-slate-800 text-white shadow-sm shadow-slate-900/10 focus-visible:ring-slate-700 border border-transparent',
      outline:
        'bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 shadow-xs focus-visible:ring-slate-400 hover:border-slate-300',
      ghost:
        'bg-transparent hover:bg-slate-100/80 text-slate-600 hover:text-slate-900 focus-visible:ring-slate-400 border border-transparent',
      danger:
        'bg-rose-600 hover:bg-rose-700 text-white shadow-sm shadow-rose-600/20 focus-visible:ring-rose-500 border border-transparent',
    };

    return (
      <button
        ref={ref}
        type={type}
        disabled={disabled || isLoading}
        className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
        {...props}
      >
        {isLoading && (
          <svg
            className="animate-spin h-3.5 w-3.5 text-current"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {!isLoading && leftIcon}
        <span>{children}</span>
        {!isLoading && rightIcon}
      </button>
    );
  }
);

Button.displayName = 'Button';
