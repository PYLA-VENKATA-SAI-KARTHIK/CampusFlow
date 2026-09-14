import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { driveService } from '../services/driveService';
import { apiClient } from '../services/apiClient';
import { CreateDriveModal } from '../components/CreateDriveModal';
import { ManualBroadcastModal } from '../components/ManualBroadcastModal';
import { PageHeader } from '../components/ui/PageHeader';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Modal } from '../components/ui/Modal';
import { Skeleton, EmptyState, Alert } from '../components/ui/StatusFeedback';
import type { PlacementDrive, EligibilityResult, DriveStatus } from '../types/drive';

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

  // Delete Drive modal state
  const [driveToDelete, setDriveToDelete] = useState<PlacementDrive | null>(null);
  const [isDeletingDrive, setIsDeletingDrive] = useState(false);
  const [deleteDriveError, setDeleteDriveError] = useState<string | null>(null);

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
  const [actionErrorMessage, setActionErrorMessage] = useState<string | null>(null);

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
          reasons: [err.response?.data?.detail || 'Unable to compute real-time eligibility.'],
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
    setActionErrorMessage(null);
    try {
      await driveService.registerStudent(driveId);
      setAppliedDriveIds((prev) => new Set([...prev, driveId]));
      setActionSuccessMessage('Successfully registered for the placement drive!');
      setTimeout(() => setActionSuccessMessage(null), 5000);
    } catch (err: any) {
      setActionErrorMessage(err.response?.data?.detail || 'Registration failed.');
      setTimeout(() => setActionErrorMessage(null), 5000);
    } finally {
      setRegisteringDriveId(null);
    }
  };

  const handleUpdateStatus = async (driveId: string, newStatus: DriveStatus) => {
    setActionSuccessMessage(null);
    setActionErrorMessage(null);
    try {
      await driveService.updateDriveStatus(driveId, newStatus);
      const statusLabels: Record<string, string> = {
        PUBLISHED: 'Drive published successfully! Eligible students have been notified.',
        REGISTRATION_OPEN: 'Registration opened! Eligible students can now submit applications.',
        REGISTRATION_CLOSED: 'Registration closed successfully.',
      };
      setActionSuccessMessage(statusLabels[newStatus] || `Drive status updated to ${newStatus}.`);
      setTimeout(() => setActionSuccessMessage(null), 5000);
      fetchDrives();
    } catch (err: any) {
      setActionErrorMessage(err.response?.data?.detail || 'Failed to update drive status.');
      setTimeout(() => setActionErrorMessage(null), 5000);
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

  const handleConfirmDeleteDrive = async () => {
    if (!driveToDelete) return;
    setIsDeletingDrive(true);
    setDeleteDriveError(null);
    try {
      await driveService.deleteDrive(driveToDelete.id);
      setDrives((prev) => prev.filter((d) => d.id !== driveToDelete.id));
      setActionSuccessMessage(`Drive "${driveToDelete.company?.name || driveToDelete.title}" deleted successfully.`);
      setTimeout(() => setActionSuccessMessage(null), 5000);
      setDriveToDelete(null);
    } catch (err: any) {
      setDeleteDriveError(err.response?.data?.detail || 'Failed to delete placement drive.');
    } finally {
      setIsDeletingDrive(false);
    }
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
    <div className="space-y-6 animate-fade-in pb-12">
      {/* ========================================================================= */}
      {/* 1. EDITORIAL PAGE HEADER                                                  */}
      {/* ========================================================================= */}
      <PageHeader
        eyebrow="CAMPUS RECRUITMENT"
        title="Placement Drives"
        description="Discover placement drives you are eligible to explore, review academic requirements, and register for active hiring rounds."
        actions={
          isOfficerOrAdmin ? (
            <Button
              variant="primary"
              onClick={() => setIsCreateModalOpen(true)}
              leftIcon={
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                </svg>
              }
            >
              + Create New Drive
            </Button>
          ) : (
            <Button
              variant="outline"
              onClick={() => navigate('/applications')}
              leftIcon={
                <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              }
            >
              View My Applications
            </Button>
          )
        }
      />

      {/* ACTION FEEDBACK ALERT */}
      {actionSuccessMessage && (
        <Alert
          variant="success"
          onClose={() => setActionSuccessMessage(null)}
          icon={
            <svg className="w-4 h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
            </svg>
          }
        >
          {actionSuccessMessage}
        </Alert>
      )}

      {actionErrorMessage && (
        <Alert
          variant="danger"
          onClose={() => setActionErrorMessage(null)}
          icon={
            <svg className="w-4 h-4 text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        >
          {actionErrorMessage}
        </Alert>
      )}

      {/* ========================================================================= */}
      {/* 2. SEARCH & FILTER WORKSPACE                                              */}
      {/* ========================================================================= */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            placeholder="Search by company, role, location..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-xl text-xs sm:text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none transition bg-slate-50/50 placeholder-slate-400"
          />
        </div>

        <div className="flex items-center space-x-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
          <button
            onClick={() => setStatusFilter('ALL')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition cursor-pointer ${
              statusFilter === 'ALL'
                ? 'bg-indigo-600 text-white shadow-xs shadow-indigo-600/20'
                : 'bg-slate-100/80 text-slate-600 hover:bg-slate-200/80 hover:text-slate-900'
            }`}
          >
            All Drives ({drives.length})
          </button>
          <button
            onClick={() => setStatusFilter('OPEN')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition cursor-pointer ${
              statusFilter === 'OPEN'
                ? 'bg-indigo-600 text-white shadow-xs shadow-indigo-600/20'
                : 'bg-slate-100/80 text-slate-600 hover:bg-slate-200/80 hover:text-slate-900'
            }`}
          >
            Open for Registration
          </button>

          {isStudent && (
            <button
              onClick={() => setStatusFilter('APPLIED')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition cursor-pointer ${
                statusFilter === 'APPLIED'
                  ? 'bg-indigo-600 text-white shadow-xs shadow-indigo-600/20'
                  : 'bg-slate-100/80 text-slate-600 hover:bg-slate-200/80 hover:text-slate-900'
              }`}
            >
              Applied ({appliedDriveIds.size})
            </button>
          )}

          {isOfficerOrAdmin && (
            <>
              <button
                onClick={() => setStatusFilter('DRAFT')}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition cursor-pointer ${
                  statusFilter === 'DRAFT'
                    ? 'bg-indigo-600 text-white shadow-xs shadow-indigo-600/20'
                    : 'bg-slate-100/80 text-slate-600 hover:bg-slate-200/80 hover:text-slate-900'
                }`}
              >
                Drafts ({drives.filter((d) => d.status === 'DRAFT').length})
              </button>
              <button
                onClick={() => setStatusFilter('PUBLISHED')}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition cursor-pointer ${
                  statusFilter === 'PUBLISHED'
                    ? 'bg-indigo-600 text-white shadow-xs shadow-indigo-600/20'
                    : 'bg-slate-100/80 text-slate-600 hover:bg-slate-200/80 hover:text-slate-900'
                }`}
              >
                Published ({drives.filter((d) => d.status === 'PUBLISHED').length})
              </button>
            </>
          )}
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 3. OPPORTUNITIES LIST / GRID                                              */}
      {/* ========================================================================= */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div key={n} className="p-5 bg-white rounded-2xl border border-slate-200/80 space-y-4">
              <div className="flex justify-between items-center">
                <Skeleton className="h-4 w-24 rounded-md" />
                <Skeleton className="h-4 w-20 rounded-md" />
              </div>
              <div className="flex items-center space-x-3">
                <Skeleton variant="circular" className="h-11 w-11 shrink-0" />
                <div className="space-y-1.5 flex-1">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-1/2" />
                </div>
              </div>
              <Skeleton className="h-10 w-full rounded-xl" />
              <div className="flex gap-2 pt-2 border-t border-slate-100">
                <Skeleton className="h-8 flex-1 rounded-xl" />
                <Skeleton className="h-8 flex-1 rounded-xl" />
              </div>
            </div>
          ))}
        </div>
      ) : error ? (
        <Alert
          variant="danger"
          title="Error Loading Drives"
          icon={
            <svg className="w-4 h-4 text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        >
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <p className="font-semibold">{error}</p>
            <Button variant="danger" size="sm" onClick={fetchDrives}>
              Retry
            </Button>
          </div>
        </Alert>
      ) : filteredDrives.length === 0 ? (
        <EmptyState
          title="No placement drives found"
          description={
            searchQuery
              ? 'No drives match your search query. Try clearing filters.'
              : isOfficerOrAdmin
              ? 'There are currently no placement drives in this category. Click "+ Create New Drive" to add one.'
              : 'There are currently no active placement drives published.'
          }
          action={
            isOfficerOrAdmin && (
              <Button variant="primary" size="sm" onClick={() => setIsCreateModalOpen(true)}>
                + Create First Drive
              </Button>
            )
          }
        />
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
              <Card
                key={drive.id}
                variant="default"
                hoverable
                className="p-5 flex flex-col justify-between group rounded-2xl border-slate-200/80 shadow-xs hover:shadow-md hover:border-indigo-300 transition-all"
              >
                <div>
                  {/* Top Badges */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <Badge
                      variant={drive.status === 'DRAFT' ? 'warning' : 'primary'}
                      size="sm"
                    >
                      {drive.status.replace(/_/g, ' ')}
                    </Badge>
                    {isApplied ? (
                      <Badge variant="success" size="sm" dot>
                        Registered
                      </Badge>
                    ) : (
                      <span className="text-[11px] text-slate-500 font-medium">
                        {formatDeadline(deadline)}
                      </span>
                    )}
                  </div>

                  {/* Company & Role */}
                  <div className="flex items-start space-x-3 mb-3.5">
                    <div className="w-11 h-11 rounded-xl bg-slate-900 text-white flex items-center justify-center font-black text-base shrink-0 group-hover:bg-indigo-600 transition shadow-xs">
                      {(compName || 'P').charAt(0).toUpperCase()}
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="text-base font-bold text-slate-900 leading-snug truncate">
                        {compName}
                      </h3>
                      <p className="text-xs font-semibold text-slate-600 mt-0.5 truncate">
                        {role}
                      </p>
                      {drive.location && (
                        <p className="text-[11px] text-slate-400 mt-0.5 truncate flex items-center gap-1">
                          <svg className="w-3 h-3 text-slate-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                          <span>{drive.location}</span>
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Compensation Details */}
                  <div className="py-2.5 px-3 bg-slate-50/80 rounded-xl border border-slate-100 mb-3 space-y-1 text-xs">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500 font-medium">Compensation</span>
                      <span className="font-extrabold text-emerald-700">
                        {formatPackage(drive.ctc_lpa, drive.stipend_monthly, (drive as any).package_details)}
                      </span>
                    </div>
                  </div>

                  {/* Eligibility Criteria Summary */}
                  {drive.eligibility_criteria && (
                    <div className="mb-4 text-[11px] text-slate-600 space-y-1.5">
                      <div className="flex items-center space-x-1.5 flex-wrap">
                        <span className="text-slate-400 font-medium">Min CGPA:</span>
                        <span className="font-bold text-slate-800">
                          {drive.eligibility_criteria.min_cgpa ?? 'Any'}
                        </span>
                        <span className="text-slate-300">•</span>
                        <span className="text-slate-400 font-medium">Backlogs:</span>
                        <span className="font-bold text-slate-800">
                          ≤ {drive.eligibility_criteria.max_active_backlogs ?? 0}
                        </span>
                      </div>
                      {drive.eligibility_criteria.eligible_branches && (
                        <div className="flex items-center space-x-1 truncate">
                          <span className="text-slate-400 font-medium shrink-0">Branches:</span>
                          <span className="font-bold text-indigo-700 truncate">
                            {drive.eligibility_criteria.eligible_branches.join(', ')}
                          </span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Live Eligibility Check Output */}
                  {elig && (
                    <div
                      className={`p-2.5 rounded-xl text-xs mb-3 border ${
                        elig.is_eligible
                          ? 'bg-emerald-50/80 border-emerald-200/80 text-emerald-800'
                          : 'bg-rose-50/80 border-rose-200/80 text-rose-800'
                      }`}
                    >
                      <div className="flex items-center space-x-1.5 font-bold">
                        {elig.is_eligible ? (
                          <>
                            <svg className="w-4 h-4 text-emerald-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                            </svg>
                            <span>Verified Eligible</span>
                          </>
                        ) : (
                          <>
                            <svg className="w-4 h-4 text-rose-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigate(`/drives/${drive.id}`)}
                      className="flex-1"
                      rightIcon={
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                        </svg>
                      }
                    >
                      View Details
                    </Button>

                    {isStudent && !isApplied && !elig && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCheckEligibility(drive.id)}
                        disabled={isChecking}
                        className="text-indigo-600 border border-slate-200 hover:bg-indigo-50"
                      >
                        {isChecking ? 'Checking...' : 'Check Eligibility'}
                      </Button>
                    )}
                  </div>

                  {isStudent ? (
                    isApplied ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => navigate('/applications')}
                        className="w-full text-emerald-700 bg-emerald-50/60 hover:bg-emerald-100/80 border-emerald-200"
                        rightIcon={
                          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                          </svg>
                        }
                      >
                        View Application Status
                      </Button>
                    ) : drive.status === 'REGISTRATION_OPEN' ? (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleRegister(drive.id)}
                        disabled={isRegistering || (elig && !elig.is_eligible)}
                        isLoading={isRegistering}
                        className="w-full shadow-xs"
                      >
                        {isRegistering ? 'Registering...' : 'Register for Drive'}
                      </Button>
                    ) : drive.status === 'PUBLISHED' ? (
                      <Button
                        variant="outline"
                        size="sm"
                        disabled
                        className="w-full bg-amber-50 text-amber-800 border-amber-200 cursor-not-allowed font-bold"
                      >
                        Registration Not Yet Open
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        disabled
                        className="w-full bg-slate-100 text-slate-400 cursor-not-allowed border-slate-200 font-bold"
                      >
                        Registration Closed
                      </Button>
                    )
                  ) : (
                    <div className="flex items-center gap-2">
                      {drive.status === 'DRAFT' && (
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => handleUpdateStatus(drive.id, 'PUBLISHED')}
                          className="flex-1 bg-emerald-600 hover:bg-emerald-700 shadow-xs"
                        >
                          Publish Now
                        </Button>
                      )}
                      {drive.status === 'PUBLISHED' && (
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => handleUpdateStatus(drive.id, 'REGISTRATION_OPEN')}
                          className="flex-1 bg-emerald-600 hover:bg-emerald-700 shadow-xs"
                        >
                          Open Reg
                        </Button>
                      )}
                      {drive.status === 'REGISTRATION_OPEN' && (
                        <Button
                          variant="danger"
                          size="sm"
                          onClick={() => handleUpdateStatus(drive.id, 'REGISTRATION_CLOSED')}
                          className="flex-1 bg-amber-600 hover:bg-amber-700 shadow-xs text-white"
                        >
                          Close Reg
                        </Button>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleOpenBroadcast(drive)}
                        className="text-purple-700 bg-purple-50/60 hover:bg-purple-100/80 border-purple-200"
                      >
                        Broadcast
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setDeleteDriveError(null);
                          setDriveToDelete(drive);
                        }}
                        className="text-rose-600 bg-rose-50/60 hover:bg-rose-100/80 border-rose-200"
                        title="Delete Placement Drive"
                        data-testid={`delete-drive-btn-${drive.id}`}
                      >
                        Delete
                      </Button>
                    </div>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Delete Placement Drive Confirmation Modal */}
      {driveToDelete && (
        <Modal
          isOpen={!!driveToDelete}
          onClose={() => {
            if (!isDeletingDrive) {
              setDriveToDelete(null);
              setDeleteDriveError(null);
            }
          }}
          title="Delete Placement Drive"
        >
          <div className="space-y-4">
            <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-900 leading-relaxed">
              <p className="font-bold text-sm text-rose-950 mb-1">
                Are you sure you want to delete this placement drive?
              </p>
              <p className="font-medium text-slate-800">
                {(driveToDelete as any).company_name || driveToDelete.company?.name || driveToDelete.title} — {driveToDelete.job_role}
              </p>
              <p className="mt-2 text-rose-700">
                This drive will be archived and removed from active student discovery. All historical registrations, student records, and stages will remain safely preserved.
              </p>
            </div>

            {deleteDriveError && (
              <Alert variant="danger">
                {deleteDriveError}
              </Alert>
            )}

            <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-100">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setDriveToDelete(null);
                  setDeleteDriveError(null);
                }}
                disabled={isDeletingDrive}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={handleConfirmDeleteDrive}
                disabled={isDeletingDrive}
                isLoading={isDeletingDrive}
                className="bg-rose-600 hover:bg-rose-700 text-white shadow-xs"
                data-testid="confirm-delete-drive-btn"
              >
                {isDeletingDrive ? 'Deleting...' : 'Delete Drive'}
              </Button>
            </div>
          </div>
        </Modal>
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
