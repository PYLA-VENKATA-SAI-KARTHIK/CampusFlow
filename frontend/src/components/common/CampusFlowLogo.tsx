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
    md: { icon: 'w-8 h-8', text: 'text-lg', sub: 'text-[10px]' },
    lg: { icon: 'w-10 h-10', text: 'text-2xl', sub: 'text-xs' },
    xl: { icon: 'w-12 h-12', text: 'text-3xl', sub: 'text-sm' },
  };

  const currentSize = sizeMap[size];

  const textColor =
    variant === 'light'
      ? 'text-white'
      : 'text-slate-950';

  const subColor =
    variant === 'light'
      ? 'text-[#c1aeee]'
      : 'text-slate-500';

  return (
    <div className={`flex items-center space-x-2.5 ${className}`}>
      {/* Official KARE Logo Glyph */}
      <div className={`relative flex items-center justify-center rounded-md bg-white p-0.5 shadow-[2px_2px_0px_#9b86d9] flex-shrink-0 ${currentSize.icon} overflow-hidden border border-slate-900`}>
        <img
          src="/assets/images/kare_logo.png"
          alt="KARE Logo"
          className="w-full h-full object-contain"
        />
      </div>

      <div className="flex flex-col select-none">
        <span className={`font-black tracking-tighter font-display leading-none ${textColor} ${currentSize.text}`}>
          Campus<span className="text-[#9b86d9]">Flow</span>
        </span>
        {showTagline && (
          <span className={`font-mono tracking-widest uppercase mt-0.5 ${subColor} ${currentSize.sub}`}>
            Career Intelligence
          </span>
        )}
      </div>
    </div>
  );
};
