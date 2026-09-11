import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../services/apiClient';
import type { OverviewAnalyticsResponse, RecentDriveActivity } from '../types/analytics';
import { KpiStatCard } from '../components/analytics/KpiStatCard';
import { BranchBreakdownTable } from '../components/analytics/BranchBreakdownTable';

export const AnalyticsDashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<OverviewAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchDriveId, setSearchDriveId] = useState('');

  const fetchOverview = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.get<OverviewAnalyticsResponse>('/analytics/overview');
      setData(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load institutional analytics overview.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  const handleSearchDrive = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchDriveId.trim()) {
      navigate(`/drives/${searchDriveId.trim()}/analytics`);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
        <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-medium text-gray-500">Loading placement analytics...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center max-w-lg mx-auto my-8">
        <svg className="w-12 h-12 text-red-500 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <h3 className="text-base font-bold text-red-800">Analytics Unavailable</h3>
        <p className="text-xs text-red-600 mt-1">{error || 'Unknown error occurred.'}</p>
        <button
          onClick={fetchOverview}
          className="mt-4 px-4 py-2 bg-red-600 text-white text-xs font-semibold rounded-lg hover:bg-red-700 transition"
        >
          Try Again
        </button>
      </div>
    );
  }

  const { drives_summary, placement_metrics, branch_placement_stats, recent_drives_activity } = data;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Institutional Placement Analytics</h1>
          <p className="text-xs text-gray-500 mt-1">
            Aggregate institutional statistics, placement conversion rates, and drive metrics.
          </p>
        </div>

        {/* Quick Drive Lookup */}
        <form onSubmit={handleSearchDrive} className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Drive UUID..."
            value={searchDriveId}
            onChange={(e) => setSearchDriveId(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-xs focus:ring-2 focus:ring-blue-500 focus:border-blue-500 w-48 sm:w-64"
          />
          <button
            type="submit"
            disabled={!searchDriveId.trim()}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-semibold rounded-lg transition"
          >
            Drive Analytics
          </button>
        </form>
      </div>

      {/* Top Level KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <KpiStatCard
          title="Placement Rate"
          value={`${placement_metrics.overall_placement_percentage.toFixed(1)}%`}
          subtitle={`${placement_metrics.total_placed_students} of ${placement_metrics.total_active_students} students placed`}
          color="emerald"
          badge="Cohort Rate"
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <KpiStatCard
          title="Total Drives"
          value={drives_summary.total_drives}
          subtitle={`${drives_summary.active_drives} active / ${drives_summary.completed_drives} completed`}
          color="blue"
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          }
        />
        <KpiStatCard
          title="Total Applications"
          value={placement_metrics.total_applications_submitted}
          subtitle="Across all campus placement drives"
          color="purple"
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          }
        />
        <KpiStatCard
          title="Placed Students"
          value={placement_metrics.total_placed_students}
          subtitle="Unique candidates with offers"
          color="indigo"
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          }
        />
      </div>

      {/* Branch Breakdown */}
      <BranchBreakdownTable
        overviewData={branch_placement_stats}
        title="Branch-wise Placement Statistics"
        subtitle="Distribution of placed candidates across academic departments"
      />

      {/* Recent Drives Activity Table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-gray-900">Recent Placement Drives</h3>
            <p className="text-xs text-gray-500 mt-0.5">Quick summary of recent drives with registrations & selections</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-left text-xs">
            <thead className="bg-gray-50 text-gray-600 font-semibold uppercase tracking-wider">
              <tr>
                <th scope="col" className="px-5 py-3">Drive Title</th>
                <th scope="col" className="px-5 py-3">Company</th>
                <th scope="col" className="px-5 py-3">Status</th>
                <th scope="col" className="px-5 py-3 text-right">Registrations</th>
                <th scope="col" className="px-5 py-3 text-right">Selected</th>
                <th scope="col" className="px-5 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {recent_drives_activity && recent_drives_activity.length > 0 ? (
                recent_drives_activity.map((drive: RecentDriveActivity) => (
                  <tr key={drive.drive_id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-5 py-3 font-semibold text-gray-900">{drive.title}</td>
                    <td className="px-5 py-3 text-gray-600">{drive.company_name}</td>
                    <td className="px-5 py-3">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold ${
                        drive.status === 'COMPLETED'
                          ? 'bg-green-100 text-green-800'
                          : drive.status === 'PUBLISHED' || drive.status === 'ACTIVE'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {drive.status}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-right font-medium text-gray-800">{drive.registered_count}</td>
                    <td className="px-5 py-3 text-right font-bold text-emerald-600">{drive.selected_count}</td>
                    <td className="px-5 py-3 text-right">
                      <button
                        onClick={() => navigate(`/drives/${drive.drive_id}/analytics`)}
                        className="text-primary-600 hover:text-primary-800 font-semibold text-xs inline-flex items-center space-x-1"
                      >
                        <span>View Funnel</span>
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                        </svg>
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-5 py-6 text-center text-gray-400 font-medium">
                    No drives found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
