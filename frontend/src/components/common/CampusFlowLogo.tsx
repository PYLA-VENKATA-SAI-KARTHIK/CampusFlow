import React from 'react';

interface CampusFlowLogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showTagline?: boolean;
  variant?: 'light' | 'dark' | 'color';
}

export const CampusFlowLogo: React.FC<CampusFlowLogoProps> = ({
  className = '',
  size = 'md',
  showTagline = false,
  variant = 'color',
}) => {
  const sizeMap = {
    sm: { icon: 'w-6 h-6', text: 'text-base', sub: 'text-[9px]' },
    md: { icon: 'w-8 h-8', text: 'text-xl', sub: 'text-[10px]' },
    lg: { icon: 'w-10 h-10', text: 'text-2xl', sub: 'text-xs' },
    xl: { icon: 'w-12 h-12', text: 'text-3xl', sub: 'text-sm' },
  };

  const currentSize = sizeMap[size];

  const textColor =
    variant === 'light'
      ? 'text-white'
      : variant === 'dark'
      ? 'text-slate-900'
      : 'text-slate-900';

  const subColor =
    variant === 'light'
      ? 'text-indigo-200'
      : 'text-slate-500';

  return (
    <div className={`flex items-center space-x-2.5 ${className}`}>
      {/* Abstract Modern Logo Glyph */}
      <div className={`relative flex items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-700 via-indigo-600 to-sky-500 shadow-md shadow-indigo-500/20 text-white flex-shrink-0 ${currentSize.icon}`}>
        <svg
          viewBox="0 0 24 24"
          fill="none"
          className="w-3/5 h-3/5"
          stroke="currentColor"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          {/* Flowing Chevron & Opportunity Path */}
          <path d="M4 14l8-8 8 8" />
          <path d="M4 19l8-8 8 8" opacity="0.65" />
          <circle cx="12" cy="6" r="1.5" fill="currentColor" />
        </svg>
      </div>

      <div className="flex flex-col">
        <span className={`font-extrabold tracking-tight font-sans leading-none ${textColor} ${currentSize.text}`}>
          Campus<span className="text-indigo-600">Flow</span>
        </span>
        {showTagline && (
          <span className={`font-medium tracking-wide mt-0.5 ${subColor} ${currentSize.sub}`}>
            One flow for every opportunity.
          </span>
        )}
      </div>
    </div>
  );
};
