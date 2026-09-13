import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { driveService } from '../services/driveService';
import { apiClient } from '../services/apiClient';
import { CreateDriveModal } from '../components/CreateDriveModal';
import { ManualBroadcastModal } from '../components/ManualBroadcastModal';
import type { PlacementDrive, EligibilityResult } from '../types/drive';

export const PlacementDrivesPage: React.FC = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const isStudent = user?.role === 'STUDENT';
  const isOfficerOrAdmin = user?.role === 'OFFICER' || user?.role === 'ADMIN';

  const [drives, setDrives] = useState<PlacementDrive[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Modals
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isBroadcastModalOpen, setIsBroadcastModalOpen] = useState(false);
  const [broadcastTargetDrive, setBroadcastTargetDrive] = useState<{ id: string; title: string } | null>(null);

  useEffect(() => {
    if (searchParams.get('create') === 'true') {
      setIsCreateModalOpen(true);
      searchParams.delete('create');
      setSearchParams(searchParams, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  // Student registration and eligibility state
  const [appliedDriveIds, setAppliedDriveIds] = useState<Set<string>>(new Set());
  const [eligibilityMap, setEligibilityMap] = useState<Record<string, EligibilityResult>>({});
  const [checkingEligibility, setCheckingEligibility] = useState<Record<string, boolean>>({});
  const [registeringDriveId, setRegisteringDriveId] = useState<string | null>(null);
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(null);

  const fetchDrives = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await driveService.listDrives({ page: 1, page_size: 100 });
      const items = res.items || [];
      setDrives(items);

      // If student, also fetch existing applications to see registered status
      if (isStudent) {
        try {
          const appsRes = await apiClient.get('/students/me/applications');
          const appItems = appsRes.data.items || [];
          const ids = new Set<string>(appItems.map((app: any) => app.drive_id));
          setAppliedDriveIds(ids);
        } catch {
          // ignore if no applications
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load placement drives.');
    } finally {
      setLoading(false);
    }
  }, [isStudent]);

  useEffect(() => {
    fetchDrives();
  }, [fetchDrives]);

  const handleCheckEligibility = async (driveId: string) => {
    if (!isStudent) return;
    setCheckingEligibility((prev) => ({ ...prev, [driveId]: true }));
    try {
      const res = await driveService.checkEligibility(driveId);
      setEligibilityMap((prev) => ({ ...prev, [driveId]: res }));
    } catch (err: any) {
      setEligibilityMap((prev) => ({
        ...prev,
        [driveId]: {
          is_eligible: false,
          reasons: [err.response?.data?.detail || 'Unable to verify eligibility'],
        },
      }));
    } finally {
      setCheckingEligibility((prev) => ({ ...prev, [driveId]: false }));
    }
  };

  const handleRegister = async (driveId: string) => {
    if (!isStudent) return;
    setRegisteringDriveId(driveId);
    setActionSuccessMessage(null);
    try {
      await driveService.registerStudent(driveId);
      setAppliedDriveIds((prev) => new Set([...prev, driveId]));
      setActionSuccessMessage('Successfully registered for the placement drive!');
      setTimeout(() => setActionSuccessMessage(null), 5000);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Registration failed.');
    } finally {
      setRegisteringDriveId(null);
    }
  };

  const handleQuickPublish = async (driveId: string) => {
    try {
      await driveService.updateDriveStatus(driveId, 'PUBLISHED');
      setActionSuccessMessage('Drive published successfully! Students have been notified.');
      setTimeout(() => setActionSuccessMessage(null), 5000);
      fetchDrives();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to publish drive.');
    }
  };

  const handleOpenBroadcast = (drive: PlacementDrive) => {
    const compName = drive.company?.name || 'Recruiting Company';
    setBroadcastTargetDrive({
      id: drive.id,
      title: `${compName} — ${drive.job_role}`,
    });
    setIsBroadcastModalOpen(true);
  };

  const formatPackage = (ctcLpa?: number | null, stipendMonthly?: number | null, packageDetails?: any) => {
    const ctc = ctcLpa ?? packageDetails?.ctc_lpa;
    if (ctc) return `₹${ctc} LPA`;
    if (stipendMonthly) return `₹${stipendMonthly.toLocaleString()}/mo Stipend`;
    return 'Package Disclosed on Selection';
  };

  const formatDeadline = (dateStr?: string | null) => {
    if (!dateStr) return 'Rolling Applications';
    const date = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    if (diffDays < 0) return 'Registration Closed';
    if (diffDays === 0) return 'Closes Today';
    if (diffDays === 1) return 'Closes Tomorrow';
    return `Closes in ${diffDays} days (${date.toLocaleDateString()})`;
  };

  const filteredDrives = drives.filter((drive) => {
    const compName = (drive as any).company_name || drive.company?.name || drive.title || '';
    const role = (drive as any).role_title || drive.job_role || '';
    const loc = drive.location || '';

    const matchesSearch =
      compName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      role.toLowerCase().includes(searchQuery.toLowerCase()) ||
      loc.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;

    if (statusFilter === 'ALL') return true;
    if (statusFilter === 'APPLIED') return appliedDriveIds.has(drive.id);
    if (statusFilter === 'OPEN') return drive.status === 'REGISTRATION_OPEN' || drive.status === 'PUBLISHED';
    if (statusFilter === 'DRAFT') return drive.status === 'DRAFT';
    if (statusFilter === 'PUBLISHED') return drive.status === 'PUBLISHED';
    if (statusFilter === 'CLOSED') return drive.status === 'REGISTRATION_CLOSED' || drive.status === 'COMPLETED';
    return drive.status === statusFilter;
  });

  return (
    <div className="space-y-6">
      {/* HEADER SECTION */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Placement Drives
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Discover verified recruitment opportunities, review eligibility criteria, and track selection rounds.
          </p>
        </div>

        {isOfficerOrAdmin ? (
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-600/20 transition self-start sm:self-auto flex items-center space-x-1.5"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
            </svg>
            <span>+ Create New Drive</span>
          </button>
        ) : (
          <button
            onClick={() => navigate('/applications')}
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition self-start sm:self-auto flex items-center space-x-1.5"
          >
            <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <span>View My Applications</span>
          </button>
        )}
      </div>

      {actionSuccessMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-emerald-800 text-xs font-semibold flex items-center space-x-2 animate-fade-in">
          <svg className="w-5 h-5 text-emerald-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
          </svg>
          <span>{actionSuccessMessage}</span>
        </div>
      )}

      {/* FILTER CONTROLS BAR */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            placeholder="Search by company, role, location..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none transition bg-slate-50/50"
          />
        </div>

        <div className="flex items-center space-x-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
          <button
            onClick={() => setStatusFilter('ALL')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
              statusFilter === 'ALL'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            All Drives ({drives.length})
          </button>
          <button
            onClick={() => setStatusFilter('OPEN')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
              statusFilter === 'OPEN'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Open for Registration
          </button>

          {isStudent && (
            <button
              onClick={() => setStatusFilter('APPLIED')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
                statusFilter === 'APPLIED'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              Applied ({appliedDriveIds.size})
            </button>
          )}

          {isOfficerOrAdmin && (
            <>
              <button
                onClick={() => setStatusFilter('DRAFT')}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
                  statusFilter === 'DRAFT'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                Drafts ({drives.filter((d) => d.status === 'DRAFT').length})
              </button>
              <button
                onClick={() => setStatusFilter('PUBLISHED')}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
                  statusFilter === 'PUBLISHED'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                Published ({drives.filter((d) => d.status === 'PUBLISHED').length})
              </button>
            </>
          )}
        </div>
      </div>

      {/* DRIVES LIST / GRID */}
      {loading ? (
        <div className="p-12 text-center bg-white rounded-3xl border border-slate-200/80 shadow-sm">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-indigo-500 border-t-transparent mb-3" />
          <p className="text-xs text-slate-500 font-medium">Loading placement drives...</p>
        </div>
      ) : error ? (
        <div className="p-6 bg-red-50 border border-red-200 rounded-3xl text-center">
          <p className="text-xs text-red-700 font-semibold">{error}</p>
          <button
            onClick={fetchDrives}
            className="mt-3 px-4 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-xl transition"
          >
            Retry
          </button>
        </div>
      ) : filteredDrives.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-3xl border border-slate-200/80 shadow-sm">
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-3">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <h3 className="text-sm font-bold text-slate-900">No placement drives found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            {searchQuery
              ? 'No drives match your search query. Try clearing filters.'
              : isOfficerOrAdmin
              ? 'There are currently no placement drives in this category. Click "+ Create New Drive" to add one.'
              : 'There are currently no active placement drives published.'}
          </p>
          {isOfficerOrAdmin && (
            <button
              onClick={() => setIsCreateModalOpen(true)}
              className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition shadow-sm"
            >
              + Create First Drive
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredDrives.map((drive) => {
            const isApplied = appliedDriveIds.has(drive.id);
            const elig = eligibilityMap[drive.id] || drive.my_eligibility;
            const isChecking = checkingEligibility[drive.id];
            const isRegistering = registeringDriveId === drive.id;

            const compName = (drive as any).company_name || drive.company?.name || drive.title || 'Placement Drive';
            const role = (drive as any).role_title || drive.job_role || 'Engineering Role';
            const deadline = drive.registration_deadline || (drive as any).registration_end;

            return (
              <div
                key={drive.id}
                className="bg-white border border-slate-200/90 hover:border-indigo-300 rounded-3xl p-5 shadow-sm hover:shadow-md transition flex flex-col justify-between group"
              >
                <div>
                  {/* Top Badges */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider ${
                        drive.status === 'DRAFT'
                          ? 'bg-amber-50 text-amber-800 border border-amber-200'
                          : 'bg-indigo-50 text-indigo-700 border border-indigo-100'
                      }`}
                    >
                      {drive.status.replace(/_/g, ' ')}
                    </span>
                    {isApplied ? (
                      <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800 flex items-center space-x-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                        <span>Registered</span>
                      </span>
                    ) : (
                      <span className="text-[11px] text-slate-500 font-medium">
                        {formatDeadline(deadline)}
                      </span>
                    )}
                  </div>

                  {/* Company & Role */}
                  <div className="flex items-start space-x-3 mb-3">
                    <div className="w-11 h-11 rounded-2xl bg-slate-900 text-white flex items-center justify-center font-extrabold text-base flex-shrink-0 group-hover:bg-indigo-600 transition shadow-sm">
                      {compName.charAt(0).toUpperCase()}
                    </div>
                    <div className="min-w-0">
                      <h3 className="text-base font-bold text-slate-900 leading-tight truncate">
                        {compName}
                      </h3>
                      <p className="text-xs font-semibold text-slate-600 mt-0.5 truncate">
                        {role}
                      </p>
                      {drive.location && (
                        <p className="text-[11px] text-slate-400 mt-0.5 truncate">{drive.location}</p>
                      )}
                    </div>
                  </div>

                  {/* Package and Details */}
                  <div className="py-2.5 px-3 bg-slate-50 rounded-2xl border border-slate-100 mb-3 space-y-1 text-xs">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Compensation</span>
                      <span className="font-bold text-emerald-700">
                        {formatPackage(drive.ctc_lpa, drive.stipend_monthly, (drive as any).package_details)}
                      </span>
                    </div>
                  </div>

                  {/* Eligibility Criteria Summary */}
                  {drive.eligibility_criteria && (
                    <div className="mb-4 text-[11px] text-slate-600 space-y-1">
                      <div className="flex items-center space-x-1.5">
                        <span className="text-slate-400 font-medium">Min CGPA:</span>
                        <span className="font-semibold text-slate-800">
                          {drive.eligibility_criteria.min_cgpa ?? 'Any'}
                        </span>
                        <span className="text-slate-300">•</span>
                        <span className="text-slate-400 font-medium">Backlogs:</span>
                        <span className="font-semibold text-slate-800">
                          ≤ {drive.eligibility_criteria.max_active_backlogs ?? 0}
                        </span>
                      </div>
                      {drive.eligibility_criteria.eligible_branches && (
                        <div className="flex items-center space-x-1 truncate">
                          <span className="text-slate-400 font-medium flex-shrink-0">Branches:</span>
                          <span className="font-semibold text-indigo-700 truncate">
                            {drive.eligibility_criteria.eligible_branches.join(', ')}
                          </span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Live Eligibility Check Output */}
                  {elig && (
                    <div
                      className={`p-2.5 rounded-2xl text-xs mb-3 border ${
                        elig.is_eligible
                          ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                          : 'bg-rose-50 border-rose-200 text-rose-800'
                      }`}
                    >
                      <div className="flex items-center space-x-1.5 font-bold">
                        {elig.is_eligible ? (
                          <>
                            <svg className="w-4 h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                            </svg>
                            <span>Verified Eligible</span>
                          </>
                        ) : (
                          <>
                            <svg className="w-4 h-4 text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                            <span>Not Eligible</span>
                          </>
                        )}
                      </div>
                      {elig.reasons && elig.reasons.length > 0 && (
                        <p className="text-[11px] mt-1 text-slate-600 leading-snug">
                          {elig.reasons.join(', ')}
                        </p>
                      )}
                    </div>
                  )}
                </div>

                {/* Card Actions */}
                <div className="pt-3 border-t border-slate-100 space-y-2">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => navigate(`/drives/${drive.id}`)}
                      className="flex-1 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1"
                    >
                      <span>View Details</span>
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                      </svg>
                    </button>

                    {isStudent && !isApplied && !elig && (
                      <button
                        onClick={() => handleCheckEligibility(drive.id)}
                        disabled={isChecking}
                        className="py-2 px-3 bg-slate-50 hover:bg-slate-100 text-indigo-600 border border-slate-200 rounded-xl text-xs font-semibold transition disabled:opacity-50"
                      >
                        {isChecking ? 'Checking...' : 'Check Eligibility'}
                      </button>
                    )}
                  </div>

                  {isStudent ? (
                    isApplied ? (
                      <button
                        onClick={() => navigate('/applications')}
                        className="w-full py-2 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1.5"
                      >
                        <span>View Application Status</span>
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                        </svg>
                      </button>
                    ) : (
                      <button
                        onClick={() => handleRegister(drive.id)}
                        disabled={isRegistering || (elig && !elig.is_eligible)}
                        className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-sm transition"
                      >
                        {isRegistering ? 'Registering...' : 'Register for Drive'}
                      </button>
                    )
                  ) : (
                    <div className="flex items-center gap-2">
                      {drive.status === 'DRAFT' && (
                        <button
                          onClick={() => handleQuickPublish(drive.id)}
                          className="flex-1 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-sm transition"
                        >
                          Publish Now
                        </button>
                      )}
                      <button
                        onClick={() => handleOpenBroadcast(drive)}
                        className="flex-1 py-2 bg-purple-50 text-purple-700 hover:bg-purple-100 rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1"
                      >
                        <span>Broadcast</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Drive Modal */}
      {isCreateModalOpen && (
        <CreateDriveModal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          onSuccess={(newDrive, isPublished) => {
            setActionSuccessMessage(
              `Drive "${newDrive.title}" has been successfully ${isPublished ? 'published' : 'saved as draft'}!`
            );
            setTimeout(() => setActionSuccessMessage(null), 6000);
            fetchDrives();
          }}
        />
      )}

      {/* Manual Broadcast Modal */}
      {isBroadcastModalOpen && broadcastTargetDrive && (
        <ManualBroadcastModal
          isOpen={isBroadcastModalOpen}
          driveId={broadcastTargetDrive.id}
          driveTitle={broadcastTargetDrive.title}
          onClose={() => {
            setIsBroadcastModalOpen(false);
            setBroadcastTargetDrive(null);
          }}
        />
      )}
    </div>
  );
};
