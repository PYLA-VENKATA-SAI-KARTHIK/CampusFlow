import React from 'react';
import type { DriveBranchBreakdownItem, BranchPlacementStat } from '../../types/analytics';

interface BranchBreakdownTableProps {
  driveData?: DriveBranchBreakdownItem[];
  overviewData?: BranchPlacementStat[];
  title?: string;
  subtitle?: string;
}

export const BranchBreakdownTable: React.FC<BranchBreakdownTableProps> = ({
  driveData,
  overviewData,
  title = 'Branch-wise Breakdown',
  subtitle,
}) => {
  const isDriveMode = !!driveData;

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <div className="p-5 border-b border-gray-200">
        <h3 className="text-base font-bold text-gray-900">{title}</h3>
        {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-left text-xs">
          <thead className="bg-gray-50 text-gray-600 font-semibold uppercase tracking-wider">
            {isDriveMode ? (
              <tr>
                <th scope="col" className="px-5 py-3">Branch</th>
                <th scope="col" className="px-5 py-3 text-right">Eligible</th>
                <th scope="col" className="px-5 py-3 text-right">Registered</th>
                <th scope="col" className="px-5 py-3 text-right">Shortlisted</th>
                <th scope="col" className="px-5 py-3 text-right">Selected</th>
                <th scope="col" className="px-5 py-3 text-right">Reg Rate</th>
              </tr>
            ) : (
              <tr>
                <th scope="col" className="px-5 py-3">Branch</th>
                <th scope="col" className="px-5 py-3 text-right">Total Students</th>
                <th scope="col" className="px-5 py-3 text-right">Placed</th>
                <th scope="col" className="px-5 py-3 text-right">Placement Rate</th>
                <th scope="col" className="px-5 py-3">Progress</th>
              </tr>
            )}
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {isDriveMode && driveData && driveData.length > 0 ? (
              driveData.map((row) => {
                const regRate = row.eligible_count > 0
                  ? ((row.registered_count / row.eligible_count) * 100).toFixed(1)
                  : '0.0';

                return (
                  <tr key={row.branch_code} className="hover:bg-gray-50 transition-colors">
                    <td className="px-5 py-3 font-medium text-gray-900 whitespace-nowrap">
                      <span className="font-bold text-blue-600">{row.branch_code}</span>
                      <span className="text-gray-500 font-normal ml-2">{row.branch_name}</span>
                    </td>
                    <td className="px-5 py-3 text-right text-gray-700">{row.eligible_count}</td>
                    <td className="px-5 py-3 text-right font-medium text-gray-900">{row.registered_count}</td>
                    <td className="px-5 py-3 text-right text-amber-600 font-medium">{row.shortlisted_count}</td>
                    <td className="px-5 py-3 text-right text-emerald-600 font-bold">{row.selected_count}</td>
                    <td className="px-5 py-3 text-right text-gray-600 font-medium">{regRate}%</td>
                  </tr>
                );
              })
            ) : null}

            {!isDriveMode && overviewData && overviewData.length > 0 ? (
              overviewData.map((row) => (
                <tr key={row.branch_code} className="hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-3 font-medium text-gray-900 whitespace-nowrap">
                    <span className="font-bold text-blue-600">{row.branch_code}</span>
                    <span className="text-gray-500 font-normal ml-2">{row.branch_name}</span>
                  </td>
                  <td className="px-5 py-3 text-right text-gray-700">{row.total_students}</td>
                  <td className="px-5 py-3 text-right font-semibold text-emerald-600">{row.placed_students}</td>
                  <td className="px-5 py-3 text-right font-bold text-gray-900">
                    {row.placement_percentage.toFixed(1)}%
                  </td>
                  <td className="px-5 py-3 w-36">
                    <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 rounded-full"
                        style={{ width: `${Math.min(row.placement_percentage, 100)}%` }}
                      />
                    </div>
                  </td>
                </tr>
              ))
            ) : null}

            {((isDriveMode && (!driveData || driveData.length === 0)) ||
              (!isDriveMode && (!overviewData || overviewData.length === 0))) && (
              <tr>
                <td colSpan={6} className="px-5 py-6 text-center text-gray-400 font-medium">
                  No branch data available.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
