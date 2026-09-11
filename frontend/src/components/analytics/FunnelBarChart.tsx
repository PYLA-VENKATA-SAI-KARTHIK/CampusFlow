import React from 'react';

export interface FunnelStep {
  label: string;
  count: number;
  sublabel?: string;
  rate?: number;
  isPublished?: boolean;
}

interface FunnelBarChartProps {
  steps: FunnelStep[];
  title?: string;
  subtitle?: string;
}

export const FunnelBarChart: React.FC<FunnelBarChartProps> = ({
  steps,
  title,
  subtitle,
}) => {
  const maxCount = Math.max(...steps.map((s) => s.count), 1);

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      {(title || subtitle) && (
        <div className="mb-6">
          {title && <h3 className="text-base font-bold text-gray-900">{title}</h3>}
          {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
        </div>
      )}

      <div className="space-y-4">
        {steps.map((step, idx) => {
          const widthPercent = Math.max((step.count / maxCount) * 100, step.count > 0 ? 4 : 0);
          const prevStep = idx > 0 ? steps[idx - 1] : null;
          const dropOffRate = prevStep && prevStep.count > 0
            ? (((prevStep.count - step.count) / prevStep.count) * 100).toFixed(1)
            : null;

          return (
            <div key={`${step.label}-${idx}`} className="group">
              <div className="flex items-center justify-between text-xs mb-1.5 font-medium text-gray-700">
                <div className="flex items-center space-x-2">
                  <span className="font-semibold text-gray-900">{step.label}</span>
                  {step.isPublished === false && (
                    <span className="bg-amber-100 text-amber-800 text-[10px] px-1.5 py-0.5 rounded font-medium">
                      Unpublished
                    </span>
                  )}
                  {step.sublabel && (
                    <span className="text-gray-400 font-normal text-[11px]">({step.sublabel})</span>
                  )}
                </div>
                <div className="flex items-center space-x-3">
                  {dropOffRate !== null && Number(dropOffRate) > 0 && (
                    <span className="text-rose-500 text-[11px] font-medium hidden sm:inline">
                      ↓ {dropOffRate}% drop
                    </span>
                  )}
                  {step.rate !== undefined && (
                    <span className="text-primary-600 font-semibold">{step.rate.toFixed(1)}%</span>
                  )}
                  <span className="font-bold text-gray-900 text-sm">{step.count}</span>
                </div>
              </div>

              <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full transition-all duration-500 group-hover:from-blue-600 group-hover:to-indigo-700"
                  style={{ width: `${widthPercent}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
