import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { apiClient } from '../services/apiClient';
import { ManualBroadcastModal } from '../components/ManualBroadcastModal';

interface StudentProfileData {
  roll_number?: string;
  branch_code?: string;
  batch_year?: number;
  cgpa?: number;
  active_backlogs?: number;
}

interface PlacementDriveSummary {
  id: string;
  company_name: string;
  role_title: string;
  package_details?: any;
  location?: string | null;
  registration_end?: string;
  status: string;
  eligibility_criteria?: {
    min_cgpa?: number;
    eligible_branches?: string[];
    max_backlogs?: number;
  };
}

interface StudentApplicationSummary {
  id: string;
  drive_id: string;
  company_name?: string;
  role_title?: string;
  status: string;
  current_stage_name?: string | null;
  created_at: string;
}

export const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const isStudent = user?.role === 'STUDENT';
  const isOfficerOrAdmin = user?.role === 'OFFICER' || user?.role === 'ADMIN';

  // Officer / Admin manual broadcast tool state (Preserved for E2E tests)
  const [isBroadcastModalOpen, setIsBroadcastModalOpen] = useState(false);
  const [selectedDriveId, setSelectedDriveId] = useState('');
  const [selectedDriveTitle, setSelectedDriveTitle] = useState('');
  const [inputDriveId, setInputDriveId] = useState('');

  // Student Command Center data state
  const [studentProfile, setStudentProfile] = useState<StudentProfileData | null>(null);
  const [drives, setDrives] = useState<PlacementDriveSummary[]>([]);
  const [applications, setApplications] = useState<StudentApplicationSummary[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
    try {
      if (isStudent) {
        // Fetch profile
        try {
          const profRes = await apiClient.get('/students/me');
          setStudentProfile(profRes.data);
        } catch {}

        // Fetch drives
        try {
          const drivesRes = await apiClient.get('/drives', { params: { page: 1, page_size: 6 } });
          setDrives(drivesRes.data.items || []);
        } catch {}

        // Fetch applications
        try {
          const appsRes = await apiClient.get('/students/me/applications', { params: { page: 1, page_size: 5 } });
          setApplications(appsRes.data.items || []);
        } catch {}
      } else {
        // Fetch drives for officer/admin
        try {
          const drivesRes = await apiClient.get('/drives', { params: { page: 1, page_size: 6 } });
          setDrives(drivesRes.data.items || []);
        } catch {}
      }
    } finally {
      setLoading(false);
    }
  }, [isStudent]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const handleOpenBroadcastModal = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputDriveId.trim()) {
      const match = drives.find((d) => d.id === inputDriveId.trim());
      const displayTitle = match
        ? `${match.company_name || (match as any).company?.name || 'Company'} — ${match.role_title || (match as any).job_role || 'Role'}`
        : `Drive ID: ${inputDriveId.trim()}`;
      setSelectedDriveId(inputDriveId.trim());
      setSelectedDriveTitle(displayTitle);
      setIsBroadcastModalOpen(true);
    }
  };

  const getRoleBadge = (role?: string) => {
    switch (role) {
      case 'ADMIN':
        return 'bg-purple-100 text-purple-800 border border-purple-200';
      case 'OFFICER':
        return 'bg-blue-100 text-blue-800 border border-blue-200';
      case 'STUDENT':
      default:
        return 'bg-emerald-100 text-emerald-800 border border-emerald-200';
    }
  };

  const formatPackage = (pkg: any) => {
    if (!pkg) return 'Package Disclosed on Selection';
    if (typeof pkg === 'string') return pkg;
    if (pkg.ctc_lpa) return `₹${pkg.ctc_lpa} LPA`;
    if (pkg.stipend_monthly) return `₹${pkg.stipend_monthly.toLocaleString()}/mo Stipend`;
    return 'Competitive Compensation';
  };

  const formatDeadline = (dateStr?: string) => {
    if (!dateStr) return 'Rolling Applications';
    const date = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    if (diffDays < 0) return 'Closed';
    if (diffDays === 0) return 'Closes today';
    if (diffDays === 1) return 'Closes in 1 day';
    return `Closes in ${diffDays} days`;
  };

  // Student metrics calculations
  const appliedDriveIds = new Set(applications.map((a) => a.drive_id));
  const shortlistedCount = applications.filter((a) => a.status === 'SHORTLISTED' || a.status === 'SELECTED').length;
  const upcomingDeadlinesCount = drives.filter((d) => {
    if (!d.registration_end) return false;
    const diffDays = Math.ceil((new Date(d.registration_end).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24));
    return diffDays >= 0 && diffDays <= 7;
  }).length;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* ========================================================================= */}
      {/* 1. WELCOME HERO & COMMAND BANNER                                          */}
      {/* ========================================================================= */}
      <div className="relative overflow-hidden bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-2xl p-6 sm:p-8 text-white shadow-xl">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-white/10 text-indigo-300 text-xs font-semibold backdrop-blur-sm border border-white/10">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span>CampusFlow Active Workspace</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              {isStudent ? `Welcome back, ${user?.full_name || 'Student'}` : 'Welcome to CampusFlow'}
            </h1>
            <p className="text-sm text-slate-300">
              Welcome to CampusFlow — You are successfully logged in. Stay on top of your placement opportunities.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
            {isOfficerOrAdmin ? (
              <button
                onClick={() => navigate('/analytics')}
                className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-indigo-600/30 transition flex items-center space-x-2"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <span>Placement Analytics</span>
              </button>
            ) : (
              <button
                onClick={() => navigate('/drives')}
                className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-indigo-600/30 transition flex items-center space-x-2"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <span>Explore Drives</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 2. STUDENT KPI SUMMARY CARDS                                              */}
      {/* ========================================================================= */}
      {isStudent && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div
            onClick={() => navigate('/drives')}
            className="p-5 bg-white border border-slate-200/90 rounded-2xl shadow-sm hover:border-indigo-300 hover:shadow-md transition cursor-pointer group"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Eligible Drives
              </span>
              <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center group-hover:scale-110 transition">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div className="text-2xl font-extrabold text-slate-900">{drives.length}</div>
            <div className="text-[11px] text-slate-400 mt-1">Open matching opportunities</div>
          </div>

          <div
            onClick={() => navigate('/applications')}
            className="p-5 bg-white border border-slate-200/90 rounded-2xl shadow-sm hover:border-indigo-300 hover:shadow-md transition cursor-pointer group"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Applications
              </span>
              <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center group-hover:scale-110 transition">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
            </div>
            <div className="text-2xl font-extrabold text-slate-900">{applications.length}</div>
            <div className="text-[11px] text-slate-400 mt-1">Submitted & in review</div>
          </div>

          <div
            onClick={() => navigate('/applications')}
            className="p-5 bg-white border border-slate-200/90 rounded-2xl shadow-sm hover:border-indigo-300 hover:shadow-md transition cursor-pointer group"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Shortlisted
              </span>
              <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center group-hover:scale-110 transition">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                </svg>
              </div>
            </div>
            <div className="text-2xl font-extrabold text-indigo-700">{shortlistedCount}</div>
            <div className="text-[11px] text-slate-400 mt-1">Advanced interview stages</div>
          </div>

          <div
            onClick={() => navigate('/drives')}
            className="p-5 bg-white border border-slate-200/90 rounded-2xl shadow-sm hover:border-indigo-300 hover:shadow-md transition cursor-pointer group"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Upcoming Deadlines
              </span>
              <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center group-hover:scale-110 transition">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div className="text-2xl font-extrabold text-amber-600">{upcomingDeadlinesCount}</div>
            <div className="text-[11px] text-slate-400 mt-1">Closing within 7 days</div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 3. STUDENT PRIMARY SECTION: UPCOMING PLACEMENT DRIVES                     */}
      {/* ========================================================================= */}
      {isStudent && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-slate-900">Upcoming Placement Drives</h2>
              <p className="text-xs text-slate-500">Verified institutional hiring opportunities</p>
            </div>
            <button
              onClick={() => navigate('/drives')}
              className="text-xs font-bold text-indigo-600 hover:text-indigo-800 transition flex items-center space-x-1"
            >
              <span>View All Drives</span>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>

          {loading ? (
            <div className="p-8 text-center bg-white rounded-2xl border border-slate-200">
              <div className="inline-block animate-spin rounded-full h-6 w-6 border-2 border-indigo-600 border-t-transparent mb-2" />
              <p className="text-xs text-slate-500">Loading placement drives...</p>
            </div>
          ) : drives.length === 0 ? (
            <div className="p-8 text-center bg-white rounded-2xl border border-slate-200 shadow-sm">
              <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-2">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-sm font-bold text-slate-800">No active placement drives</h3>
              <p className="text-xs text-slate-500 mt-0.5">New recruitment drives will appear here once published by the TPO.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {drives.slice(0, 3).map((drive: any, idx: number) => {
                const isApplied = appliedDriveIds.has(drive.id);
                const compName = drive.company?.name || drive.company_name || drive.title || 'Placement Drive';
                const role = drive.job_role || drive.role_title || 'Engineering Role';

                return (
                  <div
                    key={drive.id || `drive-${idx}`}
                    className="bg-white border border-slate-200/90 hover:border-indigo-300 rounded-2xl p-5 shadow-sm hover:shadow-md transition flex flex-col justify-between group"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-700">
                          {(drive.status || 'PUBLISHED').replace(/_/g, ' ')}
                        </span>
                        <span className="text-[11px] text-amber-700 font-semibold bg-amber-50 px-2 py-0.5 rounded-md border border-amber-100">
                          {formatDeadline(drive.registration_deadline || drive.registration_end)}
                        </span>
                      </div>

                      <div className="flex items-start space-x-3 mb-3">
                        <div className="w-10 h-10 rounded-xl bg-slate-900 text-white flex items-center justify-center font-bold text-sm flex-shrink-0 group-hover:bg-indigo-600 transition">
                          {compName.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <h4 className="text-sm font-bold text-slate-900 leading-snug">
                            {compName}
                          </h4>
                          <p className="text-xs text-slate-600">{role}</p>
                        </div>
                      </div>

                      <div className="py-2 px-3 bg-slate-50 rounded-xl border border-slate-100 text-xs mb-3 flex justify-between items-center">
                        <span className="text-slate-500 font-medium">Compensation</span>
                        <span className="font-bold text-emerald-700">{formatPackage(drive.ctc_lpa ? { ctc_lpa: drive.ctc_lpa } : drive.package_details)}</span>
                      </div>
                    </div>

                    <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                      {isApplied ? (
                        <span className="text-xs font-bold text-emerald-700 flex items-center space-x-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                          <span>Application Submitted</span>
                        </span>
                      ) : (
                        <span className="text-xs font-medium text-slate-500">Eligibility in Review</span>
                      )}

                      <button
                        onClick={() => navigate(drive.id ? `/drives/${drive.id}` : '/drives')}
                        className="px-3.5 py-1.5 bg-slate-900 hover:bg-indigo-600 text-white rounded-xl text-xs font-bold transition shadow-sm"
                      >
                        {isApplied ? 'View Status' : 'View Drive'}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* 4. STUDENT SECONDARY SECTION: MY APPLICATIONS SNAPSHOT                     */}
      {/* ========================================================================= */}
      {isStudent && (
        <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-base font-bold text-slate-900">My Recent Applications</h2>
              <p className="text-xs text-slate-500">Track active recruitment rounds and stage outcomes</p>
            </div>
            <button
              onClick={() => navigate('/applications')}
              className="text-xs font-bold text-indigo-600 hover:text-indigo-800 transition"
            >
              View All Applications
            </button>
          </div>

          {applications.length === 0 ? (
            <div className="py-8 text-center">
              <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-2">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <h3 className="text-sm font-bold text-slate-800">No applications yet</h3>
              <p className="text-xs text-slate-500 mt-0.5">Explore placement drives to get started.</p>
              <button
                onClick={() => navigate('/drives')}
                className="mt-3 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-sm transition"
              >
                Explore Drives
              </button>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {applications.map((app, idx) => (
                <div key={app.id || `app-${idx}`} className="py-3 flex items-center justify-between gap-3">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-700 flex items-center justify-center font-bold text-xs">
                      {(app.company_name || 'C').charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-slate-900">{app.company_name || 'Placement Drive'}</h4>
                      <p className="text-[11px] text-slate-500">{app.role_title || 'Engineering Role'}</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-800 border border-blue-100">
                      {app.status}
                    </span>
                    <button
                      onClick={() => navigate('/applications')}
                      className="text-xs font-semibold text-slate-600 hover:text-indigo-600"
                    >
                      Details &rarr;
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* 5. USER PROFILE & METRICS CARD (Preserved for E2E selectors)               */}
      {/* ========================================================================= */}
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center font-bold text-sm shadow-md shadow-indigo-500/20">
              {user?.full_name?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">User Account Overview</h2>
              <p className="text-xs text-slate-500">Authenticated Profile Details</p>
            </div>
          </div>
          <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${getRoleBadge(user?.role)}`}>
            {user?.role}
          </span>
        </div>

        <div className="p-6">
          <dl className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/60">
              <dt className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">Full name</dt>
              <dd className="text-sm font-bold text-slate-900">{user?.full_name}</dd>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/60">
              <dt className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">Email address</dt>
              <dd className="text-sm font-bold text-slate-900 font-mono">{user?.email}</dd>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/60">
              <dt className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">Account Role</dt>
              <dd className="text-sm font-bold text-slate-900 flex items-center space-x-2">
                <span>{user?.role}</span>
                <span className="text-xs text-emerald-600 font-medium">(Active)</span>
              </dd>
            </div>
          </dl>

          {studentProfile && (
            <div className="mt-6 pt-6 border-t border-slate-100">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-4">
                Academic Profile & Eligibility Metrics
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <div className="p-3 bg-white border border-slate-200 rounded-xl text-center">
                  <div className="text-xs text-slate-500">Roll Number</div>
                  <div className="text-sm font-bold text-slate-900 font-mono mt-0.5">{studentProfile.roll_number || '—'}</div>
                </div>
                <div className="p-3 bg-white border border-slate-200 rounded-xl text-center">
                  <div className="text-xs text-slate-500">Department</div>
                  <div className="text-sm font-bold text-indigo-600 mt-0.5">{studentProfile.branch_code || '—'}</div>
                </div>
                <div className="p-3 bg-white border border-slate-200 rounded-xl text-center">
                  <div className="text-xs text-slate-500">Batch Year</div>
                  <div className="text-sm font-bold text-slate-900 mt-0.5">{studentProfile.batch_year || '—'}</div>
                </div>
                <div className="p-3 bg-white border border-slate-200 rounded-xl text-center">
                  <div className="text-xs text-slate-500">Current CGPA</div>
                  <div className="text-sm font-bold text-emerald-600 mt-0.5">{studentProfile.cgpa !== undefined ? studentProfile.cgpa.toFixed(2) : '—'}</div>
                </div>
                <div className="p-3 bg-white border border-slate-200 rounded-xl text-center">
                  <div className="text-xs text-slate-500">Active Backlogs</div>
                  <div className="text-sm font-bold text-slate-900 mt-0.5">{studentProfile.active_backlogs ?? 0}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 6. OFFICER & ADMIN TOOL: MANUAL BROADCAST MANAGEMENT (CRITICAL FOR E2E)   */}
      {/* ========================================================================= */}
      {isOfficerOrAdmin && (
        <div className="bg-white shadow-sm rounded-2xl p-6 sm:p-8 border border-slate-200 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-5 border-b border-slate-100 gap-2">
            <div>
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center font-bold">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
                  </svg>
                </div>
                <h2 className="text-lg font-bold text-slate-900">
                  Drive Manual Broadcast Management
                </h2>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Send targeted in-app announcements and Web Push notifications to eligible, registered, or shortlisted candidates.
              </p>
            </div>
            <span className="text-xs bg-purple-100 text-purple-800 font-bold px-3 py-1 rounded-full border border-purple-200 self-start sm:self-auto">
              Placement Officer Tool
            </span>
          </div>

          <form onSubmit={handleOpenBroadcastModal} className="space-y-3">
            {drives.length > 0 && (
              <div>
                <label htmlFor="drive-select-dropdown" className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Select Placement Drive
                </label>
                <select
                  id="drive-select-dropdown"
                  value={inputDriveId}
                  onChange={(e) => {
                    setInputDriveId(e.target.value);
                    const match = drives.find((d) => d.id === e.target.value);
                    if (match) {
                      const comp = match.company_name || (match as any).company?.name || 'Company';
                      const role = match.role_title || (match as any).job_role || 'Role';
                      setSelectedDriveTitle(`${comp} — ${role}`);
                    }
                  }}
                  className="w-full border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs sm:text-sm font-semibold focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none bg-white shadow-sm transition"
                >
                  <option value="">-- Choose a Placement Drive to Broadcast --</option>
                  {drives.map((d) => {
                    const comp = d.company_name || (d as any).company?.name || 'Company';
                    const role = d.role_title || (d as any).job_role || 'Role';
                    return (
                      <option key={d.id} value={d.id}>
                        {comp} — {role} ({d.status})
                      </option>
                    );
                  })}
                </select>
              </div>
            )}

            <div className="flex flex-col sm:flex-row gap-3">
              <div className="flex-1 relative">
                <label htmlFor="drive-id-input" className="sr-only">Drive UUID</label>
                <input
                  id="drive-id-input"
                  type="text"
                  placeholder="Placement Drive UUID (auto-populated when selecting a drive above)"
                  value={inputDriveId}
                  onChange={(e) => setInputDriveId(e.target.value)}
                  className="w-full border border-slate-300 rounded-xl px-4 py-2.5 text-xs sm:text-sm font-mono focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none transition shadow-sm bg-slate-50"
                />
              </div>
              <button
                type="submit"
                disabled={!inputDriveId.trim()}
                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs sm:text-sm font-semibold rounded-xl shadow-md shadow-indigo-600/20 whitespace-nowrap transition"
              >
                Compose Broadcast
              </button>
            </div>
          </form>

          {selectedDriveId && (
            <ManualBroadcastModal
              isOpen={isBroadcastModalOpen}
              driveId={selectedDriveId}
              driveTitle={selectedDriveTitle}
              onClose={() => setIsBroadcastModalOpen(false)}
            />
          )}
        </div>
      )}
    </div>
  );
};
