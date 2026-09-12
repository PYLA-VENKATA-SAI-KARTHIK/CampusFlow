import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../services/apiClient';
import type { DriveAnalyticsResponse } from '../types/analytics';
import { KpiStatCard } from '../components/analytics/KpiStatCard';
import { FunnelBarChart } from '../components/analytics/FunnelBarChart';
import type { FunnelStep } from '../components/analytics/FunnelBarChart';
import { BranchBreakdownTable } from '../components/analytics/BranchBreakdownTable';
import { StageConversionCard } from '../components/analytics/StageConversionCard';

export const DriveAnalyticsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<DriveAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDriveAnalytics = async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.get<DriveAnalyticsResponse>(`/drives/${id}/analytics`);
      setData(res.data);
    } catch (err: any) {
      if (err?.response?.status === 404) {
        setError('Placement drive not found.');
      } else if (err?.response?.status === 403) {
        setError('You are not authorized to view analytics for this drive.');
      } else {
        setError(err?.response?.data?.detail || 'Failed to load drive analytics.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDriveAnalytics();
  }, [id]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
        <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-semibold text-slate-500">Loading drive recruitment funnel...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-2xl p-8 text-center max-w-lg mx-auto my-8 shadow-sm">
        <svg className="w-12 h-12 text-red-500 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <h3 className="text-base font-bold text-red-800">Drive Analytics Unavailable</h3>
        <p className="text-xs text-red-600 mt-1">{error || 'Unknown error occurred.'}</p>
        <div className="mt-4 flex items-center justify-center space-x-3">
          <button
            onClick={() => navigate('/analytics')}
            className="px-4 py-2 bg-slate-200 text-slate-800 text-xs font-semibold rounded-xl hover:bg-slate-300 transition"
          >
            ← Back to Overview
          </button>
          <button
            onClick={fetchDriveAnalytics}
            className="px-4 py-2 bg-red-600 text-white text-xs font-semibold rounded-xl hover:bg-red-700 transition"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const { title, company_name, job_role, status, summary, stage_funnel, branch_breakdown } = data;

  // Assemble visual funnel steps
  const funnelSteps: FunnelStep[] = [
    {
      label: 'Eligible Students',
      count: summary.eligible_count,
      sublabel: 'Criteria Matched',
      rate: 100,
    },
    {
      label: 'Registered Candidates',
      count: summary.registered_count,
      sublabel: 'Applications Received',
      rate: summary.registration_rate_percentage,
    },
    ...stage_funnel.map((s) => {
      const stageRate = s.appeared_count > 0
        ? (s.selected_count / s.appeared_count) * 100
        : s.assigned_count > 0
        ? (s.selected_count / s.assigned_count) * 100
        : 0;

      return {
        label: `${s.name} (${s.stage_type})`,
        count: s.selected_count,
        sublabel: `${s.appeared_count} appeared`,
        rate: stageRate,
        isPublished: s.is_published,
      };
    }),
    {
      label: 'Total Selected / Offered',
      count: summary.total_selected_count,
      sublabel: 'Overall Final Offers',
      rate: summary.overall_conversion_percentage,
    },
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Top Header & Breadcrumb */}
      <div>
        <button
          onClick={() => navigate('/analytics')}
          className="text-xs text-indigo-600 hover:text-indigo-800 font-bold inline-flex items-center space-x-1 mb-3 transition"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" />
          </svg>
          <span>Back to Institutional Overview</span>
        </button>

        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-6 border-b border-slate-200">
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">{title}</h1>
              <span className={`inline-flex items-center px-3 py-0.5 rounded-full text-xs font-bold ${
                status === 'COMPLETED'
                  ? 'bg-emerald-100 text-emerald-800'
                  : status === 'ACTIVE' || status === 'PUBLISHED'
                  ? 'bg-blue-100 text-blue-800'
                  : 'bg-slate-100 text-slate-800'
              }`}>
                {status}
              </span>
            </div>
            <p className="text-sm text-slate-500 mt-1">
              <span className="font-bold text-slate-700">{company_name}</span> &bull; {job_role}
            </p>
          </div>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <KpiStatCard
          title="Eligible Students"
          value={summary.eligible_count}
          subtitle="Batch & CGPA criteria verified"
          color="blue"
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          }
        />
        <KpiStatCard
          title="Registered"
          value={summary.registered_count}
          subtitle={`${summary.registration_rate_percentage.toFixed(1)}% registration rate`}
          color="purple"
          badge={`${summary.registration_rate_percentage.toFixed(0)}%`}
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          }
        />
        <KpiStatCard
          title="Shortlisted"
          value={summary.total_shortlisted_count}
          subtitle="Unique candidates in evaluation stages"
          color="amber"
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <KpiStatCard
          title="Final Selections"
          value={summary.total_selected_count}
          subtitle={`${summary.overall_conversion_percentage.toFixed(1)}% overall conversion`}
          color="emerald"
          badge={`${summary.overall_conversion_percentage.toFixed(0)}%`}
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
            </svg>
          }
        />
      </div>

      {/* Recruitment Funnel Chart */}
      <FunnelBarChart
        steps={funnelSteps}
        title="Recruitment Conversion Funnel"
        subtitle="End-to-end candidate progression from eligibility through final offer"
      />

      {/* Stage Breakdown Cards */}
      {stage_funnel.length > 0 && (
        <div className="space-y-4">
          <div>
            <h3 className="text-base font-bold text-slate-900">Evaluation Stages Breakdown</h3>
            <p className="text-xs text-slate-500">Performance metrics per assessment and interview stage</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {stage_funnel.map((stage, idx) => (
              <StageConversionCard
                key={stage.stage_id}
                stage={stage}
                stepIndex={idx}
              />
            ))}
          </div>
        </div>
      )}

      {/* Branch Breakdown Table */}
      <BranchBreakdownTable
        driveData={branch_breakdown}
        title="Branch-wise Candidate Distribution"
        subtitle="Candidate performance breakdown across academic departments"
      />
    </div>
  );
};
