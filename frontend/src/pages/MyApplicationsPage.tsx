import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../services/apiClient';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Badge, StatusBadge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { EmptyState, Skeleton, StatCard } from '../components/ui/StatusFeedback';

/* ─────────────────────────────────────────────────────────────────────────────
   Types
───────────────────────────────────────────────────────────────────────────── */

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

/* ─────────────────────────────────────────────────────────────────────────────
   Constants
───────────────────────────────────────────────────────────────────────────── */

const DEFAULT_STAGES = [
  'Applied',
  'Shortlisted',
  'Online Assessment',
  'Technical Interview',
  'HR Interview',
  'Final Offer',
];

const FILTER_TABS = ['ALL', 'APPLIED', 'SHORTLISTED', 'SELECTED', 'REJECTED'] as const;
type FilterTab = typeof FILTER_TABS[number];

/* ─────────────────────────────────────────────────────────────────────────────
   Helpers
───────────────────────────────────────────────────────────────────────────── */

const getActiveStageIndex = (app: ApplicationItem): number => {
  if (app.status === 'SELECTED') return DEFAULT_STAGES.length - 1;
  if (app.status === 'REJECTED') {
    if (app.is_shortlisted) return 1;
    return 0;
  }
  if (app.current_stage_name) {
    const matchIdx = DEFAULT_STAGES.findIndex(
      (s) => s.toLowerCase() === app.current_stage_name?.toLowerCase()
    );
    if (matchIdx !== -1) return matchIdx;
  }
  if (app.is_shortlisted || app.status === 'SHORTLISTED') return 1;
  return 0;
};

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });

const getCompanyInitial = (app: ApplicationItem): string =>
  ((app.company_name || app.drive_title || 'C').charAt(0) || 'C').toUpperCase();

/* ─────────────────────────────────────────────────────────────────────────────
   Journey Stage Stepper — horizontal rail with progress fill
───────────────────────────────────────────────────────────────────────────── */

interface StageStepperProps {
  app: ApplicationItem;
  activeIndex: number;
  isRejected: boolean;
  isSelected: boolean;
}

const StageStepper: React.FC<StageStepperProps> = ({ activeIndex, isRejected, isSelected }) => {
  const progressPct = DEFAULT_STAGES.length > 1
    ? (activeIndex / (DEFAULT_STAGES.length - 1)) * 88
    : 0;

  return (
    <div className="relative" aria-label="Recruitment stage progression">
      {/* Connecting rail */}
      <div className="absolute top-4 left-4 right-4 h-0.5 bg-slate-100 z-0" aria-hidden="true" />
      {/* Progress fill */}
      <div
        className={`absolute top-4 left-4 h-0.5 z-0 transition-all duration-700 ${
          isRejected ? 'bg-rose-300' : isSelected ? 'bg-emerald-400' : 'bg-indigo-400'
        }`}
        style={{ width: `${progressPct}%` }}
        aria-hidden="true"
      />

      {/* Steps */}
      <ol className="relative z-10 flex items-start justify-between gap-1">
        {DEFAULT_STAGES.map((stageName, idx) => {
          const isCompleted = isSelected ? idx <= activeIndex : !isRejected && idx < activeIndex;
          const isCurrent = idx === activeIndex && !isSelected;
          const isRejectedStage = isRejected && idx === activeIndex;

          let nodeColor: string;
          let labelColor: string;

          if (isRejectedStage) {
            nodeColor = 'bg-rose-100 border-rose-300 text-rose-600';
            labelColor = 'text-rose-600 font-semibold';
          } else if (isCompleted) {
            nodeColor = 'bg-emerald-500 border-emerald-500 text-white';
            labelColor = 'text-emerald-700 font-semibold';
          } else if (isCurrent) {
            nodeColor = 'bg-indigo-600 border-indigo-600 text-white ring-4 ring-indigo-100';
            labelColor = 'text-indigo-700 font-bold';
          } else {
            nodeColor = 'bg-white border-slate-200 text-slate-300';
            labelColor = 'text-slate-400';
          }

          return (
            <li key={stageName} className="flex-1 flex flex-col items-center gap-1.5 min-w-0">
              <div
                className={`w-8 h-8 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-all duration-300 ${nodeColor}`}
                aria-current={isCurrent ? 'step' : undefined}
              >
                {isCompleted && !isRejectedStage ? (
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3} aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : isRejectedStage ? (
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                ) : (
                  <span className="text-[10px] font-bold">{idx + 1}</span>
                )}
              </div>
              <span className={`text-[10px] text-center leading-tight px-0.5 truncate w-full ${labelColor}`}>
                {stageName}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
};

/* ─────────────────────────────────────────────────────────────────────────────
   Application Card
───────────────────────────────────────────────────────────────────────────── */

interface ApplicationCardProps {
  app: ApplicationItem;
  onNavigate: (path: string) => void;
}

const ApplicationCard: React.FC<ApplicationCardProps> = ({ app, onNavigate }) => {
  const activeIndex = getActiveStageIndex(app);
  const isRejected = app.status === 'REJECTED';
  const isSelected = app.status === 'SELECTED';

  const currentStageName =
    app.current_stage_name ||
    (isSelected
      ? 'Final Offer'
      : isRejected
      ? `Eliminated at ${DEFAULT_STAGES[activeIndex] ?? 'Stage'}`
      : DEFAULT_STAGES[activeIndex] ?? 'Under Review');

  const borderAccent = isSelected
    ? 'border-l-4 border-l-emerald-400'
    : isRejected
    ? 'border-l-4 border-l-rose-300'
    : app.status === 'SHORTLISTED'
    ? 'border-l-4 border-l-indigo-400'
    : 'border-l-4 border-l-slate-200';

  return (
    <Card variant="elevated" className={`transition-all duration-200 hover:shadow-md ${borderAccent}`}>
      <CardHeader
        action={<StatusBadge status={app.status} size="sm" />}
      >
        <div className="flex items-center gap-3">
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center font-black text-sm flex-shrink-0 ${
              isSelected ? 'bg-emerald-600 text-white' : isRejected ? 'bg-slate-200 text-slate-500' : 'bg-slate-900 text-white'
            }`}
            aria-hidden="true"
          >
            {getCompanyInitial(app)}
          </div>
          <div className="min-w-0">
            <CardTitle className="text-sm">
              {app.company_name || app.drive_title || 'Placement Drive'}
            </CardTitle>
            <CardDescription className="truncate">
              {app.role_title || 'Graduate Engineering Role'}
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-4 pb-3">
        <div className="mb-2 flex items-center justify-between">
          <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
            Recruitment Funnel
          </span>
          <span className="text-[10px] text-slate-400">
            Stage {activeIndex + 1} of {DEFAULT_STAGES.length}
          </span>
        </div>
        <StageStepper
          app={app}
          activeIndex={activeIndex}
          isRejected={isRejected}
          isSelected={isSelected}
        />
      </CardContent>

      <div className="px-5 py-3 bg-slate-50/60 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <div
            className={`w-2 h-2 rounded-full flex-shrink-0 ${
              isSelected ? 'bg-emerald-500' : isRejected ? 'bg-rose-400' : 'bg-indigo-500 animate-pulse'
            }`}
            aria-hidden="true"
          />
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
            Current Round:
          </span>
          <span className="text-[11px] font-semibold text-slate-800 truncate">
            {currentStageName}
          </span>
        </div>

        <div className="flex items-center gap-3 flex-shrink-0">
          <span className="text-[10px] text-slate-400">
            Applied {formatDate(app.created_at)}
          </span>
          <button
            onClick={() => onNavigate('/notifications')}
            className="inline-flex items-center gap-1 text-[11px] font-bold text-indigo-600 hover:text-indigo-800 transition-colors"
            aria-label="Check round notifications"
          >
            Check Round Notifications
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
    </Card>
  );
};

/* ─────────────────────────────────────────────────────────────────────────────
   Skeleton loader for cards
───────────────────────────────────────────────────────────────────────────── */

const ApplicationCardSkeleton: React.FC = () => (
  <Card variant="elevated" className="border-l-4 border-l-slate-100">
    <CardHeader>
      <div className="flex items-center gap-3">
        <Skeleton variant="circular" className="w-10 h-10 flex-shrink-0" />
        <div className="flex-1 space-y-1.5">
          <Skeleton variant="text" className="h-4 w-40" />
          <Skeleton variant="text" className="h-3 w-24" />
        </div>
      </div>
    </CardHeader>
    <CardContent>
      <Skeleton className="h-16 w-full" />
    </CardContent>
    <div className="px-5 py-3 border-t border-slate-100">
      <Skeleton variant="text" className="h-3 w-48" />
    </div>
  </Card>
);

/* ─────────────────────────────────────────────────────────────────────────────
   Summary Stats Bar
───────────────────────────────────────────────────────────────────────────── */

const StatsBar: React.FC<{ applications: ApplicationItem[] }> = ({ applications }) => {
  const total = applications.length;
  const active = applications.filter((a) => !['SELECTED', 'REJECTED'].includes(a.status)).length;
  const selected = applications.filter((a) => a.status === 'SELECTED').length;
  const rejected = applications.filter((a) => a.status === 'REJECTED').length;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <StatCard
        label="Applications"
        value={total}
        subtext="Total submitted"
        icon={
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        }
      />
      <StatCard
        label="In Progress"
        value={active}
        subtext="Active pipelines"
        icon={
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        }
      />
      <StatCard
        label="Offers"
        value={selected}
        subtext="Final selections"
        badge={selected > 0 ? <Badge variant="success" size="sm">🎉</Badge> : undefined}
        icon={
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
          </svg>
        }
      />
      <StatCard
        label="Closed"
        value={rejected}
        subtext="Not progressed"
        icon={
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        }
      />
    </div>
  );
};

/* ─────────────────────────────────────────────────────────────────────────────
   Filter Tabs
───────────────────────────────────────────────────────────────────────────── */

const FilterTabs: React.FC<{
  filter: FilterTab;
  setFilter: (f: FilterTab) => void;
  applications: ApplicationItem[];
}> = ({ filter, setFilter, applications }) => {
  const countFor = (tab: FilterTab) =>
    tab === 'ALL' ? applications.length : applications.filter((a) => a.status === tab).length;

  return (
    <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5" role="tablist" aria-label="Filter applications">
      {FILTER_TABS.map((tab) => {
        const count = countFor(tab);
        const isActive = filter === tab;
        return (
          <button
            key={tab}
            role="tab"
            aria-selected={isActive}
            onClick={() => setFilter(tab)}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-[11px] font-bold whitespace-nowrap transition-all duration-150 flex-shrink-0 ${
              isActive
                ? 'bg-slate-900 text-white shadow-sm'
                : 'bg-white border border-slate-200 text-slate-500 hover:bg-slate-50 hover:text-slate-800'
            }`}
          >
            <span>
              {tab === 'ALL' ? 'All' : tab.charAt(0) + tab.slice(1).toLowerCase()}
            </span>
            <span
              className={`inline-flex items-center justify-center w-4 h-4 rounded-full text-[9px] font-black ${
                isActive ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-600'
              }`}
            >
              {count}
            </span>
          </button>
        );
      })}
    </div>
  );
};

/* ─────────────────────────────────────────────────────────────────────────────
   Page
───────────────────────────────────────────────────────────────────────────── */

export const MyApplicationsPage: React.FC = () => {
  const navigate = useNavigate();
  const [applications, setApplications] = useState<ApplicationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterTab>('ALL');

  useEffect(() => {
    const fetchApplications = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await apiClient.get('/students/me/applications', {
          params: { page: 1, page_size: 50 },
        });
        const rawItems = res.data.items || [];
        const normalized: ApplicationItem[] = rawItems.map((raw: any) => ({
          id: raw.id || raw.registration_id || String(Math.random()),
          drive_id: raw.drive_id,
          student_id: raw.student_id || '',
          status: raw.my_current_stage?.stage_status || raw.status || raw.drive_status || 'APPLIED',
          created_at: raw.registered_at || raw.created_at || new Date().toISOString(),
          drive_title: raw.drive_title || raw.title || '',
          company_name: raw.company_name || raw.company?.name || '',
          role_title: raw.role_title || raw.job_role || '',
          current_stage_name: raw.my_current_stage?.stage_name || raw.current_stage_name || null,
          current_stage_sequence: raw.my_current_stage?.stage_sequence ?? raw.current_stage_sequence ?? null,
          is_shortlisted: Boolean(
            raw.is_shortlisted ??
            (raw.my_current_stage?.stage_status === 'SHORTLISTED' ||
             raw.my_current_stage?.stage_status === 'SELECTED' ||
             raw.status === 'SHORTLISTED' ||
             raw.status === 'SELECTED')
          ),
        }));
        setApplications(normalized);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load applications.');
      } finally {
        setLoading(false);
      }
    };
    fetchApplications();
  }, []);

  const filteredApps = applications.filter((app) =>
    filter === 'ALL' ? true : app.status === filter
  );

  return (
    <div className="space-y-6 animate-fade-in">

      {/* ── Page Header ──────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Placement Journey
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Track every active pipeline — from application to offer.
          </p>
        </div>
        <Button
          variant="primary"
          size="sm"
          onClick={() => navigate('/drives')}
          leftIcon={
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          }
        >
          Explore Drives
        </Button>
      </div>

      {/* ── Stats Bar ────────────────────────────────────────────────────── */}
      {!loading && !error && applications.length > 0 && (
        <StatsBar applications={applications} />
      )}

      {/* ── Filter Tabs ──────────────────────────────────────────────────── */}
      {!loading && !error && applications.length > 0 && (
        <FilterTabs filter={filter} setFilter={setFilter} applications={applications} />
      )}

      {/* ── Content ──────────────────────────────────────────────────────── */}
      {loading ? (
        <div className="space-y-4">
          {[0, 1, 2].map((i) => <ApplicationCardSkeleton key={i} />)}
        </div>
      ) : error ? (
        <Card variant="subtle" className="border-rose-200 bg-rose-50">
          <CardContent className="flex items-start gap-3 py-4">
            <svg className="w-5 h-5 text-rose-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p className="text-sm font-bold text-rose-800">Failed to load applications</p>
              <p className="text-xs text-rose-600 mt-0.5">{error}</p>
            </div>
          </CardContent>
        </Card>
      ) : filteredApps.length === 0 ? (
        <EmptyState
          icon={
            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
          }
          title={
            filter !== 'ALL'
              ? `No ${filter.charAt(0) + filter.slice(1).toLowerCase()} applications`
              : 'No applications yet'
          }
          description={
            filter !== 'ALL'
              ? `No applications match the "${filter.charAt(0) + filter.slice(1).toLowerCase()}" filter. Try another.`
              : 'Explore active placement drives and apply to start tracking your recruitment journey here.'
          }
          action={
            filter === 'ALL' ? (
              <Button variant="primary" size="sm" onClick={() => navigate('/drives')}>
                Explore Placement Drives
              </Button>
            ) : (
              <Button variant="outline" size="sm" onClick={() => setFilter('ALL')}>
                View all applications
              </Button>
            )
          }
        />
      ) : (
        <div className="space-y-4">
          {filteredApps.map((app) => (
            <ApplicationCard key={app.id} app={app} onNavigate={navigate} />
          ))}
        </div>
      )}
    </div>
  );
};
