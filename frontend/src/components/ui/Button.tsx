import React, { forwardRef } from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'lilac';
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
    // Base styling with expert UI designer tactile feedback
    const baseStyles =
      'inline-flex items-center justify-center font-bold font-sans transition duration-150 ease-in-out select-none cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50';

    // Size variants
    const sizeStyles = {
      sm: 'text-xs px-3 py-1.5 rounded-sm gap-1.5',
      md: 'text-xs px-4 py-2.5 rounded-md gap-2 tracking-tight',
      lg: 'text-sm px-6 py-3 rounded-md gap-2.5 tracking-tight',
    };

    // Variant styling
    const variantStyles = {
      primary:
        'bg-[#0a0b10] hover:bg-[#1f202b] text-white shadow-[2px_2px_0px_#9b86d9] hover:border-[#9b86d9] active:translate-x-[1px] active:translate-y-[1px] active:shadow-none focus-visible:ring-[#9b86d9] border border-[#0a0b10]',
      lilac:
        'bg-[#9b86d9] hover:bg-[#886ee0] text-[#07080b] font-extrabold border border-[#07080b] shadow-[2px_2px_0px_#07080b] active:translate-x-[1px] active:translate-y-[1px] active:shadow-none focus-visible:ring-[#9b86d9]',
      secondary:
        'bg-[#12131b] hover:bg-[#1d1f2b] text-white border border-[#272a3a] shadow-[2px_2px_0px_rgba(10,11,16,0.3)] active:translate-x-[1px] active:translate-y-[1px] active:shadow-none focus-visible:ring-[#9b86d9]',
      outline:
        'bg-white hover:bg-[#f6f3fc] text-slate-800 border border-slate-300 shadow-[1px_1px_0px_rgba(10,11,16,0.08)] hover:border-slate-800 hover:text-[#4b3679] active:translate-x-[1px] active:translate-y-[1px] focus-visible:ring-[#9b86d9]',
      ghost:
        'bg-transparent hover:bg-[#f6f3fc] text-slate-700 hover:text-[#5a4195] border border-transparent',
      danger:
        'bg-[#e11d48] hover:bg-[#be123c] text-white border border-[#9f1239] shadow-[2px_2px_0px_#881337] active:translate-x-[1px] active:translate-y-[1px] active:shadow-none focus-visible:ring-rose-500',
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
