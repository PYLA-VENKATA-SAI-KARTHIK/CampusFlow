import React from 'react';
import type { StageFunnelItem } from '../../types/analytics';

interface StageConversionCardProps {
  stage: StageFunnelItem;
  stepIndex: number;
}

export const StageConversionCard: React.FC<StageConversionCardProps> = ({
  stage,
  stepIndex,
}) => {
  const conversionRate = stage.appeared_count > 0
    ? (stage.selected_count / stage.appeared_count) * 100
    : stage.assigned_count > 0
    ? (stage.selected_count / stage.assigned_count) * 100
    : 0;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-800 text-xs font-bold">
            {stepIndex + 1}
          </span>
          <h4 className="text-sm font-bold text-gray-900">{stage.name}</h4>
          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded font-medium">
            {stage.stage_type}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          {!stage.is_published && (
            <span className="bg-amber-100 text-amber-800 text-[10px] px-2 py-0.5 rounded font-semibold">
              Unpublished
            </span>
          )}
          <span className="text-xs font-bold text-primary-600">
            {conversionRate.toFixed(1)}% Conversion
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
        <div className="bg-gray-50 p-2.5 rounded-lg border border-gray-100">
          <span className="text-[11px] text-gray-500 font-medium block">Assigned</span>
          <span className="text-sm font-bold text-gray-800">{stage.assigned_count}</span>
        </div>
        <div className="bg-blue-50 p-2.5 rounded-lg border border-blue-100">
          <span className="text-[11px] text-blue-600 font-medium block">Appeared</span>
          <span className="text-sm font-bold text-blue-900">{stage.appeared_count}</span>
        </div>
        <div className="bg-emerald-50 p-2.5 rounded-lg border border-emerald-100">
          <span className="text-[11px] text-emerald-600 font-medium block">Selected</span>
          <span className="text-sm font-bold text-emerald-900">{stage.selected_count}</span>
        </div>
        <div className="bg-rose-50 p-2.5 rounded-lg border border-rose-100">
          <span className="text-[11px] text-rose-600 font-medium block">Rejected</span>
          <span className="text-sm font-bold text-rose-900">{stage.rejected_count}</span>
        </div>
      </div>
    </div>
  );
};
