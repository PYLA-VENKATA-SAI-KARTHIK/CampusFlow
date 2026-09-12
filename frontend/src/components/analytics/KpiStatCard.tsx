import React from 'react';

interface KpiStatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  color?: 'blue' | 'green' | 'purple' | 'amber' | 'indigo' | 'emerald';
  badge?: string;
}

const colorMap = {
  blue: {
    bg: 'bg-sky-50 text-sky-600',
    border: 'border-sky-100',
    badge: 'bg-sky-50 text-sky-700 border-sky-200',
  },
  green: {
    bg: 'bg-emerald-50 text-emerald-600',
    border: 'border-emerald-100',
    badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  },
  emerald: {
    bg: 'bg-emerald-50 text-emerald-600',
    border: 'border-emerald-100',
    badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  },
  purple: {
    bg: 'bg-purple-50 text-purple-600',
    border: 'border-purple-100',
    badge: 'bg-purple-50 text-purple-700 border-purple-200',
  },
  amber: {
    bg: 'bg-amber-50 text-amber-600',
    border: 'border-amber-100',
    badge: 'bg-amber-50 text-amber-700 border-amber-200',
  },
  indigo: {
    bg: 'bg-indigo-50 text-indigo-600',
    border: 'border-indigo-100',
    badge: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  },
};

export const KpiStatCard: React.FC<KpiStatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  color = 'blue',
  badge,
}) => {
  const styles = colorMap[color] || colorMap.blue;

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-all group">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
          {title}
        </span>
        {icon && (
          <div className={`p-2.5 rounded-xl ${styles.bg} transition-transform group-hover:scale-105`}>
            {icon}
          </div>
        )}
      </div>
      <div className="mt-4 flex items-baseline justify-between">
        <span className="text-3xl font-extrabold text-slate-900 tracking-tight font-sans">
          {value}
        </span>
        {badge && (
          <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${styles.badge}`}>
            {badge}
          </span>
        )}
      </div>
      {subtitle && (
        <p className="mt-1.5 text-xs text-slate-500 font-medium leading-relaxed">
          {subtitle}
        </p>
      )}
    </div>
  );
};
