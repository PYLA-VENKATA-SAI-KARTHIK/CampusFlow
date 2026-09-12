import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../services/apiClient';

interface ApplicationItem {
  id: string;
  drive_id: string;
  student_id: string;
  status: string;
  created_at: string;
  drive_title?: string;
  company_name?: string;
  role_title?: string;
  current_stage_name?: string | null;
  current_stage_sequence?: number | null;
  is_shortlisted?: boolean;
}

const DEFAULT_STAGES = [
  'Applied',
  'Shortlisted',
  'Online Assessment',
  'Technical Interview',
  'HR Interview',
  'Final Offer',
];

export const MyApplicationsPage: React.FC = () => {
  const navigate = useNavigate();
  const [applications, setApplications] = useState<ApplicationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState('ALL');

  useEffect(() => {
    const fetchApplications = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await apiClient.get('/students/me/applications', {
          params: { page: 1, page_size: 50 },
        });
        setApplications(res.data.items || []);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load applications.');
      } finally {
        setLoading(false);
      }
    };

    fetchApplications();
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'SELECTED':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'SHORTLISTED':
        return 'bg-indigo-100 text-indigo-800 border-indigo-200';
      case 'REJECTED':
        return 'bg-rose-100 text-rose-800 border-rose-200';
      case 'APPLIED':
      default:
        return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  const getActiveStageIndex = (app: ApplicationItem) => {
    if (app.status === 'SELECTED') return DEFAULT_STAGES.length - 1;
    if (app.status === 'REJECTED') return 1;
    if (app.current_stage_name) {
      const matchIdx = DEFAULT_STAGES.findIndex(
        (s) => s.toLowerCase() === app.current_stage_name?.toLowerCase()
      );
      if (matchIdx !== -1) return matchIdx;
    }
    if (app.is_shortlisted || app.status === 'SHORTLISTED') return 1;
    return 0; // Applied
  };

  const filteredApps = applications.filter((app) => {
    if (filter === 'ALL') return true;
    return app.status === filter;
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            My Applications
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Track recruitment funnels, assessment schedules, shortlist announcements, and selection outcomes.
          </p>
        </div>

        <button
          onClick={() => navigate('/drives')}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-sm transition self-start sm:self-auto flex items-center space-x-1.5"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <span>Explore Placement Drives</span>
        </button>
      </div>

      {/* FILTER TABS */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-1">
        {['ALL', 'APPLIED', 'SHORTLISTED', 'SELECTED', 'REJECTED'].map((tab) => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition ${
              filter === tab
                ? 'bg-slate-900 text-white shadow-sm'
                : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100'
            }`}
          >
            {tab.replace('_', ' ')}
            {tab === 'ALL' && ` (${applications.length})`}
          </button>
        ))}
      </div>

      {/* CONTENT LIST */}
      {loading ? (
        <div className="p-12 text-center bg-white rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-indigo-500 border-t-transparent mb-3" />
          <p className="text-xs text-slate-500 font-medium">Loading applications...</p>
        </div>
      ) : error ? (
        <div className="p-6 bg-red-50 border border-red-200 rounded-2xl text-center">
          <p className="text-xs text-red-700 font-semibold">{error}</p>
        </div>
      ) : filteredApps.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-3">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <h3 className="text-sm font-bold text-slate-900">No applications yet</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Explore active placement drives to submit applications and track recruitment rounds.
          </p>
          <button
            onClick={() => navigate('/drives')}
            className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition shadow-sm"
          >
            Explore Drives
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredApps.map((app) => {
            const activeIndex = getActiveStageIndex(app);
            const isRejected = app.status === 'REJECTED';
            const isSelected = app.status === 'SELECTED';

            return (
              <div
                key={app.id}
                className="bg-white border border-slate-200/90 rounded-2xl p-5 sm:p-6 shadow-sm hover:border-slate-300 transition space-y-5"
              >
                {/* Top Row: Company, Role, Status Badge, Submission Date */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-xl bg-slate-900 text-white flex items-center justify-center font-bold text-sm flex-shrink-0">
                      {(app.company_name || app.drive_title || 'C').charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-slate-900">
                        {app.company_name || app.drive_title || 'Placement Drive'}
                      </h3>
                      <p className="text-xs text-slate-500 font-medium">
                        {app.role_title || 'Graduate Engineering Role'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3 self-start sm:self-auto">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${getStatusBadge(
                        app.status
                      )}`}
                    >
                      {app.status}
                    </span>
                    <span className="text-xs text-slate-400 font-medium">
                      Applied on {new Date(app.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                {/* Progress Stepper Timeline */}
                <div>
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3">
                    Recruitment Stage Progression
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-6 gap-2">
                    {DEFAULT_STAGES.map((stageName, idx) => {
                      const isCompleted = idx < activeIndex || (isSelected && idx === activeIndex);
                      const isCurrent = idx === activeIndex && !isSelected && !isRejected;

                      let stepColor = 'bg-slate-50 border-slate-200 text-slate-400';
                      if (isCompleted) {
                        stepColor = 'bg-emerald-50 border-emerald-300 text-emerald-800 font-semibold';
                      } else if (isCurrent) {
                        stepColor = 'bg-indigo-50 border-indigo-400 text-indigo-900 font-bold ring-2 ring-indigo-500/20';
                      } else if (isRejected && idx === activeIndex) {
                        stepColor = 'bg-rose-50 border-rose-300 text-rose-800 font-semibold';
                      }

                      return (
                        <div
                          key={stageName}
                          className={`p-2.5 rounded-xl border text-center transition flex flex-col items-center justify-center ${stepColor}`}
                        >
                          <div className="text-[10px] uppercase font-bold opacity-70 mb-0.5">
                            Step {idx + 1}
                          </div>
                          <div className="text-xs leading-tight">{stageName}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Current Stage Note / Next Action */}
                <div className="bg-slate-50/80 rounded-xl p-3 border border-slate-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs">
                  <div className="flex items-center space-x-2 text-slate-700">
                    <span className="font-semibold text-slate-900">Current Round:</span>
                    <span>{app.current_stage_name || (app.status === 'SELECTED' ? 'Offered' : 'Application Review')}</span>
                  </div>
                  <button
                    onClick={() => navigate('/notifications')}
                    className="text-indigo-600 hover:text-indigo-800 font-semibold text-xs flex items-center space-x-1"
                  >
                    <span>Check Round Notifications</span>
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
