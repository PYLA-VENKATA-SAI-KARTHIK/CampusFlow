import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { driveService } from '../services/driveService';
import { ManualBroadcastModal } from '../components/ManualBroadcastModal';
import { StageQualifiedImportModal } from '../components/drives/StageQualifiedImportModal';
import { Card } from '../components/ui/Card';
import { Badge, StatusBadge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Textarea } from '../components/ui/Textarea';
import { Checkbox } from '../components/ui/Checkbox';
import { Modal } from '../components/ui/Modal';
import {
  TableContainer,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  TableEmpty,
} from '../components/ui/Table';
import { Skeleton, Alert } from '../components/ui/StatusFeedback';
import type {
  PlacementDrive,
  PlacementStage,
  Branch,
  DriveRegistrationWithStudent,
  AssignmentStatus,
  DriveStatus,
} from '../types/drive';

export const DriveDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const isStudent = user?.role === 'STUDENT';
  const isOfficerOrAdmin = user?.role === 'OFFICER' || user?.role === 'ADMIN';

  // Drive & Stages state
  const [drive, setDrive] = useState<PlacementDrive | null>(null);
  const [stages, setStages] = useState<PlacementStage[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Student registration state
  const [isRegistering, setIsRegistering] = useState<boolean>(false);
  const [registrationSuccess, setRegistrationSuccess] = useState<string | null>(null);
  const [registrationError, setRegistrationError] = useState<string | null>(null);

  // Officer management state
  const [isUpdatingStatus, setIsUpdatingStatus] = useState<boolean>(false);
  const [statusUpdateSuccess, setStatusUpdateSuccess] = useState<string | null>(null);
  const [statusUpdateError, setStatusUpdateError] = useState<string | null>(null);
  const [isBroadcastModalOpen, setIsBroadcastModalOpen] = useState<boolean>(false);
  const [selectedStageForUpload, setSelectedStageForUpload] = useState<PlacementStage | null>(null);
  const [isStageUploadModalOpen, setIsStageUploadModalOpen] = useState<boolean>(false);

  // Delete Drive modal state
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState<boolean>(false);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // ---------------------------------------------------------------------------
  // Applicant Workspace State (Officer / Admin Only)
  // ---------------------------------------------------------------------------
  const [applicants, setApplicants] = useState<DriveRegistrationWithStudent[]>([]);
  const [totalApplicants, setTotalApplicants] = useState<number>(0);
  const [applicantPage, setApplicantPage] = useState<number>(1);
  const [applicantPageSize, setApplicantPageSize] = useState<number>(20);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [debouncedSearch, setDebouncedSearch] = useState<string>('');
  const [branchFilter, setBranchFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [loadingApplicants, setLoadingApplicants] = useState<boolean>(false);
  const [applicantError, setApplicantError] = useState<string | null>(null);

  // Selection & Bulk Actions
  const [selectedStudentIds, setSelectedStudentIds] = useState<Set<string>>(new Set());
  const [isShortlistModalOpen, setIsShortlistModalOpen] = useState<boolean>(false);
  const [isBulkStatusModalOpen, setIsBulkStatusModalOpen] = useState<boolean>(false);
  const [isQuickViewModalOpen, setIsQuickViewModalOpen] = useState<boolean>(false);
  const [selectedCandidate, setSelectedCandidate] = useState<DriveRegistrationWithStudent | null>(null);

  // Modal form states
  const [targetStageId, setTargetStageId] = useState<string>('');
  const [targetStatus, setTargetStatus] = useState<AssignmentStatus>('SHORTLISTED');
  const [resultNotes, setResultNotes] = useState<string>('');
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [actionModalError, setActionModalError] = useState<string | null>(null);
  const [workspaceSuccessAlert, setWorkspaceSuccessAlert] = useState<string | null>(null);


  // Resume Download State
  const [isDownloadingResume, setIsDownloadingResume] = useState<boolean>(false);
  const [resumeDownloadError, setResumeDownloadError] = useState<string | null>(null);

  // Debounce search query by 300ms
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    searchTimeoutRef.current = setTimeout(() => {
      setDebouncedSearch(searchQuery);
      setApplicantPage(1);
      setSelectedStudentIds(new Set());
    }, 300);

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery]);

  // Reset pagination and selection on filter change
  const handleBranchFilterChange = (val: string) => {
    setBranchFilter(val);
    setApplicantPage(1);
    setSelectedStudentIds(new Set());
  };

  const handleStatusFilterChange = (val: string) => {
    setStatusFilter(val);
    setApplicantPage(1);
    setSelectedStudentIds(new Set());
  };

  // Fetch Drive & Stages
  const fetchDriveDetails = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const [driveData, stageData, branchData] = await Promise.allSettled([
        driveService.getDrive(id),
        driveService.listStages(id),
        driveService.listBranches(),
      ]);

      if (driveData.status === 'fulfilled') {
        setDrive(driveData.value);
      } else {
        setError('Placement drive could not be found or you do not have permission to view it.');
      }

      if (stageData.status === 'fulfilled') {
        setStages(stageData.value || []);
      }

      if (branchData.status === 'fulfilled') {
        setBranches(branchData.value || []);
      }
    } catch {
      setError('Unable to reach CampusFlow server.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchDriveDetails();
  }, [fetchDriveDetails]);

  // Fetch Applicants (Paginated + Filtered)
  const fetchApplicants = useCallback(async () => {
    if (!id || !isOfficerOrAdmin) return;
    setLoadingApplicants(true);
    setApplicantError(null);
    try {
      const res = await driveService.listRegistrations(id, {
        search: debouncedSearch.trim() || undefined,
        branch: branchFilter || undefined,
        status: statusFilter || undefined,
        page: applicantPage,
        page_size: applicantPageSize,
      });

      setApplicants(res.items || []);
      setTotalApplicants(res.total || 0);
    } catch {
      setApplicantError('Unable to load applicants. Please retry.');
    } finally {
      setLoadingApplicants(false);
    }
  }, [id, isOfficerOrAdmin, debouncedSearch, branchFilter, statusFilter, applicantPage, applicantPageSize]);

  useEffect(() => {
    if (isOfficerOrAdmin && id) {
      fetchApplicants();
    }
  }, [fetchApplicants, isOfficerOrAdmin, id]);

  // Clear selections when changing page
  const handlePageChange = (newPage: number) => {
    setApplicantPage(newPage);
    setSelectedStudentIds(new Set());
  };

  // Multi-Selection Logic
  const allCurrentPageSelected =
    applicants.length > 0 &&
    applicants.every((item) => selectedStudentIds.has(item.student_user_id));

  const handleToggleSelectAll = () => {
    if (allCurrentPageSelected) {
      // Deselect all on current page
      const next = new Set(selectedStudentIds);
      applicants.forEach((item) => next.delete(item.student_user_id));
      setSelectedStudentIds(next);
    } else {
      // Select all on current page
      const next = new Set(selectedStudentIds);
      applicants.forEach((item) => next.add(item.student_user_id));
      setSelectedStudentIds(next);
    }
  };

  const handleToggleSelectRow = (studentUserId: string) => {
    const next = new Set(selectedStudentIds);
    if (next.has(studentUserId)) {
      next.delete(studentUserId);
    } else {
      next.add(studentUserId);
    }
    setSelectedStudentIds(next);
  };

  // Bulk Shortlist Action
  const handleConfirmShortlist = async () => {
    if (!id || !targetStageId || selectedStudentIds.size === 0) return;
    setActionLoading(true);
    setActionModalError(null);
    try {
      const studentIds = Array.from(selectedStudentIds);
      const res = await driveService.shortlistStudents(id, targetStageId, studentIds);
      setIsShortlistModalOpen(false);
      setSelectedStudentIds(new Set());
      setTargetStageId('');
      setWorkspaceSuccessAlert(res.message || `${studentIds.length} candidate(s) shortlisted successfully.`);
      setTimeout(() => setWorkspaceSuccessAlert(null), 6000);
      await fetchApplicants();
    } catch (err: any) {
      setActionModalError(err.response?.data?.detail || 'Failed to shortlist selected candidates.');
    } finally {
      setActionLoading(false);
    }
  };

  // Bulk Status Update Action
  const handleConfirmBulkStatus = async () => {
    if (!id || !targetStageId || selectedStudentIds.size === 0) return;
    setActionLoading(true);
    setActionModalError(null);
    try {
      const studentIds = Array.from(selectedStudentIds);
      const res = await driveService.bulkUpdateStageStatus(id, targetStageId, {
        student_ids: studentIds,
        status: targetStatus,
        result_notes: resultNotes.trim() || undefined,
      });
      setIsBulkStatusModalOpen(false);
      setSelectedStudentIds(new Set());
      setTargetStageId('');
      setResultNotes('');
      setWorkspaceSuccessAlert(res.message || `${studentIds.length} candidate(s) updated to ${targetStatus}.`);
      setTimeout(() => setWorkspaceSuccessAlert(null), 6000);
      await fetchApplicants();
    } catch (err: any) {
      setActionModalError(err.response?.data?.detail || 'Failed to update candidate status.');
    } finally {
      setActionLoading(false);
    }
  };

  // Candidate Quick View Open
  const handleOpenQuickView = (candidate: DriveRegistrationWithStudent) => {
    setSelectedCandidate(candidate);
    setResumeDownloadError(null);
    setIsQuickViewModalOpen(true);
  };

  // Secure Resume Download Handler
  const handleDownloadResume = async (studentProfileId: string) => {
    setIsDownloadingResume(true);
    setResumeDownloadError(null);
    try {
      const url = await driveService.getStudentResumeDownloadUrl(studentProfileId);
      if (url) {
        window.open(url, '_blank', 'noopener,noreferrer');
      } else {
        setResumeDownloadError('No resume download URL available.');
      }
    } catch (err: any) {
      setResumeDownloadError(
        err.response?.data?.detail || 'Unable to access student resume securely.'
      );
    } finally {
      setIsDownloadingResume(false);
    }
  };

  // Student registration handler
  const handleRegister = async () => {
    if (!drive || !id) return;
    setIsRegistering(true);
    setRegistrationSuccess(null);
    setRegistrationError(null);
    try {
      await driveService.registerStudent(id);
      setDrive((prev) => (prev ? { ...prev, is_registered: true } : null));
      setRegistrationSuccess('Your application has been successfully submitted for this drive!');
      setTimeout(() => setRegistrationSuccess(null), 6000);
    } catch (err: any) {
      setRegistrationError(err.response?.data?.detail || 'Failed to submit application.');
      setTimeout(() => setRegistrationError(null), 6000);
    } finally {
      setIsRegistering(false);
    }
  };

  // Officer update drive status
  const handleUpdateStatus = async (newStatus: DriveStatus) => {
    if (!drive || !id) return;
    setIsUpdatingStatus(true);
    setStatusUpdateSuccess(null);
    setStatusUpdateError(null);
    try {
      const updated = await driveService.updateDriveStatus(id, newStatus);
      setDrive(updated);
      const statusLabels: Record<string, string> = {
        PUBLISHED: 'published successfully! Eligible students have been notified.',
        REGISTRATION_OPEN: 'opened for registrations! Eligible students can now submit applications.',
        REGISTRATION_CLOSED: 'closed for registrations.',
        SHORTLISTING: 'advanced to Shortlisting phase.',
        ASSESSMENT: 'advanced to Assessment phase.',
        INTERVIEW: 'advanced to Interview phase.',
        RESULT: 'advanced to Result phase.',
        COMPLETED: 'marked as Completed.',
      };
      setStatusUpdateSuccess(`Drive status updated: ${statusLabels[newStatus] || newStatus}`);
      setTimeout(() => setStatusUpdateSuccess(null), 6000);
    } catch (err: any) {
      setStatusUpdateError(err.response?.data?.detail || 'Failed to update drive status.');
      setTimeout(() => setStatusUpdateError(null), 6000);
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (!drive || !id) return;
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await driveService.deleteDrive(id);
      navigate('/drives');
    } catch (err: any) {
      setDeleteError(err.response?.data?.detail || 'Failed to delete placement drive.');
      setIsDeleting(false);
    }
  };

  const formatPackage = (ctcLpa?: number | null, stipendMonthly?: number | null, packageDetails?: any) => {
    const ctc = ctcLpa ?? packageDetails?.ctc_lpa;
    if (ctc) return `₹${ctc} LPA`;
    if (stipendMonthly) return `₹${stipendMonthly.toLocaleString()}/mo Stipend`;
    return 'Competitive Compensation';
  };

  const getDeadlineInfo = (deadlineStr?: string | null) => {
    if (!deadlineStr) return { text: 'Rolling Applications', isExpired: false, badgeClass: 'bg-slate-100 text-slate-700' };
    const date = new Date(deadlineStr);
    const now = new Date();
    const diffDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
      return { text: 'Registration Closed', isExpired: true, badgeClass: 'bg-rose-50 text-rose-800 border-rose-200' };
    }
    if (diffDays === 0) {
      return { text: `Closes Today (${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})`, isExpired: false, badgeClass: 'bg-amber-50 text-amber-800 border-amber-200' };
    }
    if (diffDays === 1) {
      return { text: 'Closes Tomorrow', isExpired: false, badgeClass: 'bg-amber-50 text-amber-800 border-amber-200' };
    }
    return { text: `Closes in ${diffDays} days (${date.toLocaleDateString()})`, isExpired: false, badgeClass: 'bg-emerald-50 text-emerald-800 border-emerald-200' };
  };

  if (loading) {
    return (
      <div className="space-y-6 max-w-5xl mx-auto pb-12 animate-fade-in">
        <div className="flex justify-between items-center">
          <Skeleton className="h-6 w-40 rounded-lg" />
          <Skeleton className="h-6 w-24 rounded-full" />
        </div>
        <Card className="p-8 rounded-3xl border-slate-200/90 space-y-6">
          <div className="flex items-center space-x-4">
            <Skeleton variant="circular" className="h-16 w-16 shrink-0" />
            <div className="space-y-2 flex-1">
              <Skeleton className="h-7 w-1/3" />
              <Skeleton className="h-4 w-1/4" />
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-slate-100">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-16 w-full rounded-2xl" />
            ))}
          </div>
        </Card>
      </div>
    );
  }

  if (error || !drive) {
    return (
      <div className="p-8 text-center bg-white rounded-3xl border border-slate-200 shadow-sm animate-fade-in max-w-lg mx-auto mt-6">
        <div className="w-12 h-12 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center mx-auto mb-3">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h2 className="text-base font-bold text-slate-900 mb-1">Drive Unavailable</h2>
        <p className="text-xs text-slate-500 mb-4">{error || 'Placement drive could not be loaded.'}</p>
        <Button variant="primary" size="sm" onClick={() => navigate('/drives')}>
          &larr; Back to Placement Drives
        </Button>
      </div>
    );
  }

  const companyName = (drive as any).company_name || drive.company?.name || drive.title || 'Recruiting Partner';
  const jobRole = (drive as any).role_title || drive.job_role || 'Engineering Role';
  const deadlineStr = drive.registration_deadline || (drive as any).registration_end;
  const deadlineInfo = getDeadlineInfo(deadlineStr);
  const myEligibility = drive.my_eligibility;

  // Derive branch options
  const branchOptions = branches.length > 0
    ? branches.map((b) => ({ value: b.code, label: `${b.code} - ${b.name}` }))
    : (drive.eligibility_criteria?.eligible_branches || []).map((b) => ({ value: b, label: b }));

  // Pagination bounds
  const startIdx = totalApplicants === 0 ? 0 : (applicantPage - 1) * applicantPageSize + 1;
  const endIdx = Math.min(applicantPage * applicantPageSize, totalApplicants);
  const totalPages = Math.max(1, Math.ceil(totalApplicants / applicantPageSize));

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl mx-auto pb-12">
      {/* Navigation Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/drives')}
          className="inline-flex items-center space-x-1.5 text-xs font-bold text-slate-500 hover:text-indigo-600 transition cursor-pointer"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>Back to Placement Drives</span>
        </button>

        <Badge
          variant={drive.status === 'DRAFT' ? 'warning' : 'primary'}
          size="md"
        >
          {drive.status.replace(/_/g, ' ')}
        </Badge>
      </div>

      {/* REGISTRATION & PUBLISH NOTIFICATIONS */}
      {registrationSuccess && (
        <Alert
          variant="success"
          onClose={() => setRegistrationSuccess(null)}
          icon={
            <svg className="w-4 h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
            </svg>
          }
        >
          {registrationSuccess}
        </Alert>
      )}

      {registrationError && (
        <Alert
          variant="danger"
          onClose={() => setRegistrationError(null)}
          icon={
            <svg className="w-4 h-4 text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        >
          {registrationError}
        </Alert>
      )}

      {statusUpdateSuccess && (
        <Alert
          variant="success"
          onClose={() => setStatusUpdateSuccess(null)}
          icon={
            <svg className="w-4 h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
            </svg>
          }
        >
          {statusUpdateSuccess}
        </Alert>
      )}

      {statusUpdateError && (
        <Alert
          variant="danger"
          onClose={() => setStatusUpdateError(null)}
          icon={
            <svg className="w-4 h-4 text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        >
          {statusUpdateError}
        </Alert>
      )}

      {/* ========================================================================= */}
      {/* 1. DOSSIER HERO BANNER                                                    */}
      {/* ========================================================================= */}
      <Card variant="elevated" className="rounded-3xl border-slate-200/90 p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="flex items-start space-x-4">
            <div className="w-16 h-16 rounded-2xl bg-slate-900 text-white flex items-center justify-center font-black text-2xl shrink-0 shadow-md">
              {(companyName || 'C').charAt(0).toUpperCase()}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
                  {companyName}
                </h1>
                {drive.company?.website && (
                  <a
                    href={drive.company.website}
                    target="_blank"
                    rel="noreferrer"
                    className="text-slate-400 hover:text-indigo-600 transition text-xs"
                    title="Visit official website"
                  >
                    <svg className="w-4 h-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                )}
              </div>
              <p className="text-sm font-bold text-indigo-600 mt-0.5">{jobRole}</p>
              {drive.location && (
                <p className="text-xs text-slate-500 mt-1 flex items-center space-x-1">
                  <svg className="w-3.5 h-3.5 text-slate-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <span>{drive.location}</span>
                </p>
              )}
            </div>
          </div>

          <div className="flex flex-col items-start sm:items-end gap-2">
            <span className={`px-3 py-1.5 rounded-xl text-xs font-bold border ${deadlineInfo.badgeClass}`}>
              {deadlineInfo.text}
            </span>
            <span className="text-[11px] text-slate-400">
              Published on {drive.published_at ? new Date(drive.published_at).toLocaleDateString() : 'Draft'}
            </span>
          </div>
        </div>

        {/* Quick Highlights Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-slate-100">
          <div className="p-3.5 bg-slate-50/80 rounded-2xl border border-slate-100">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Package (CTC)</span>
            <span className="text-base font-black text-emerald-700 mt-0.5 block">
              {formatPackage(drive.ctc_lpa, drive.stipend_monthly, (drive as any).package_details)}
            </span>
          </div>

          <div className="p-3.5 bg-slate-50/80 rounded-2xl border border-slate-100">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Min CGPA</span>
            <span className="text-base font-black text-slate-900 mt-0.5 block">
              {drive.eligibility_criteria?.min_cgpa ?? 'Any'}
            </span>
          </div>

          <div className="p-3.5 bg-slate-50/80 rounded-2xl border border-slate-100">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Max Backlogs</span>
            <span className="text-base font-black text-slate-900 mt-0.5 block">
              ≤ {drive.eligibility_criteria?.max_active_backlogs ?? 0}
            </span>
          </div>

          <div className="p-3.5 bg-slate-50/80 rounded-2xl border border-slate-100">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Selection Rounds</span>
            <span className="text-base font-black text-indigo-700 mt-0.5 block">
              {stages.length} Stages
            </span>
          </div>
        </div>
      </Card>

      {/* ========================================================================= */}
      {/* 2. STUDENT ACTION & ELIGIBILITY DIAGNOSTICS                               */}
      {/* ========================================================================= */}
      {isStudent && (
        <Card variant="default" className="rounded-3xl border-slate-200/90 p-6 sm:p-7 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-600">
                Your Institutional Eligibility Status
              </h2>
              {myEligibility ? (
                myEligibility.is_eligible ? (
                  <div className="flex items-center space-x-2 mt-1">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-base font-extrabold text-emerald-800">
                      You meet all eligibility criteria for this drive.
                    </span>
                  </div>
                ) : (
                  <div className="flex items-start space-x-2 mt-1">
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-500 mt-1 shrink-0" />
                    <div>
                      <span className="text-base font-extrabold text-rose-800 block">
                        Not Eligible
                      </span>
                      <p className="text-xs text-rose-700 mt-0.5">
                        {myEligibility.reasons.join(', ')}
                      </p>
                    </div>
                  </div>
                )
              ) : (
                <span className="text-xs text-slate-500 mt-1 block">
                  Eligibility verified authoritatively against your academic profile.
                </span>
              )}
            </div>

            {/* Registration Controls */}
            <div>
              {drive.is_registered ? (
                <div className="inline-flex items-center space-x-2 px-4 py-2.5 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-xl text-xs font-bold">
                  <svg className="w-4 h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span>Application Submitted</span>
                </div>
              ) : drive.status === 'REGISTRATION_CLOSED' || drive.status === 'COMPLETED' || deadlineInfo.isExpired ? (
                <Button
                  disabled
                  variant="outline"
                  className="bg-slate-100 text-slate-400 cursor-not-allowed border-slate-200 font-bold"
                >
                  Registration Closed
                </Button>
              ) : myEligibility && !myEligibility.is_eligible ? (
                <Button
                  disabled
                  variant="outline"
                  className="bg-rose-50 text-rose-400 border-rose-100 cursor-not-allowed font-bold"
                >
                  Not Eligible to Register
                </Button>
              ) : (
                <Button
                  variant="primary"
                  size="lg"
                  onClick={handleRegister}
                  disabled={isRegistering}
                  isLoading={isRegistering}
                  className="shadow-md shadow-indigo-600/30"
                >
                  {isRegistering ? 'Submitting Application...' : 'Register for Drive Now \u2192'}
                </Button>
              )}
            </div>
          </div>
        </Card>
      )}

      {/* ========================================================================= */}
      {/* 3. OFFICER & ADMIN MANAGEMENT PANEL                                       */}
      {/* ========================================================================= */}
      {isOfficerOrAdmin && (
        <Card variant="default" className="rounded-3xl border-purple-200/80 p-6 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-600" />
              <h2 className="text-xs font-black uppercase tracking-wider text-purple-900">
                Placement Officer Management Controls
              </h2>
            </div>
            <span className="text-[11px] text-slate-400 font-mono">Drive ID: {drive.id}</span>
          </div>

          <div className="flex flex-wrap items-center gap-2 pt-2">
            {drive.status === 'DRAFT' && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => handleUpdateStatus('PUBLISHED')}
                disabled={isUpdatingStatus}
                isLoading={isUpdatingStatus}
                className="bg-emerald-600 hover:bg-emerald-700 shadow-xs"
              >
                Publish Drive Now
              </Button>
            )}

            {drive.status === 'PUBLISHED' && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => handleUpdateStatus('REGISTRATION_OPEN')}
                disabled={isUpdatingStatus}
                isLoading={isUpdatingStatus}
                className="bg-emerald-600 hover:bg-emerald-700 shadow-xs"
                leftIcon={
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z" />
                  </svg>
                }
              >
                Open Registration Now
              </Button>
            )}

            {drive.status === 'REGISTRATION_OPEN' && (
              <Button
                variant="danger"
                size="sm"
                onClick={() => handleUpdateStatus('REGISTRATION_CLOSED')}
                disabled={isUpdatingStatus}
                isLoading={isUpdatingStatus}
                className="bg-amber-600 hover:bg-amber-700 shadow-xs text-white"
                leftIcon={
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                }
              >
                Close Registration
              </Button>
            )}

            {drive.status === 'REGISTRATION_CLOSED' && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => handleUpdateStatus('SHORTLISTING')}
                disabled={isUpdatingStatus}
                isLoading={isUpdatingStatus}
                className="bg-indigo-600 hover:bg-indigo-700 shadow-xs"
              >
                Advance to Shortlisting
              </Button>
            )}

            {drive.status === 'SHORTLISTING' && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => handleUpdateStatus('ASSESSMENT')}
                disabled={isUpdatingStatus}
                isLoading={isUpdatingStatus}
                className="bg-indigo-600 hover:bg-indigo-700 shadow-xs"
              >
                Advance to Assessment
              </Button>
            )}

            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsBroadcastModalOpen(true)}
              className="bg-purple-600 hover:bg-purple-700 shadow-xs"
              leftIcon={
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
                </svg>
              }
            >
              Broadcast Notification
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/drives/${drive.id}/analytics`)}
              leftIcon={
                <svg className="w-3.5 h-3.5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              }
            >
              Funnel Analytics
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setDeleteError(null);
                setIsDeleteModalOpen(true);
              }}
              className="text-rose-600 bg-rose-50/60 hover:bg-rose-100/80 border-rose-200"
              leftIcon={
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              }
              data-testid="officer-delete-drive-btn"
            >
              Delete Drive
            </Button>
          </div>
        </Card>
      )}

      {/* ========================================================================= */}
      {/* 4. TWO-COLUMN DOSSIER DETAILS                                             */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left 2 Cols: Description & Selection Stages Timeline */}
        <div className="md:col-span-2 space-y-6">
          {/* Detailed Role Description */}
          <Card variant="default" className="rounded-3xl border-slate-200/90 p-6 sm:p-7 shadow-xs space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Role Description & Expectations
            </h3>
            <div className="text-xs sm:text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
              {drive.description ||
                'Detailed job specifications and day-to-day responsibilities will be provided during pre-placement talk.'}
            </div>
            {drive.bond_details && (
              <div className="mt-4 pt-4 border-t border-slate-100 text-xs">
                <span className="font-bold text-slate-700 block mb-0.5">Service Agreement / Bond Terms:</span>
                <p className="text-slate-600">{drive.bond_details}</p>
              </div>
            )}
          </Card>

          {/* Selection Stages / Round Management Section */}
          <Card variant="default" className="rounded-3xl border-slate-200/90 p-6 sm:p-7 shadow-xs space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  {isOfficerOrAdmin ? 'Round / Stage Management' : 'Placement Updates & Selection Progression'}
                </h3>
                <p className="text-xs text-slate-600 mt-0.5">
                  {isOfficerOrAdmin
                    ? 'Manage sequential drive rounds and upload company-qualified student shortlists.'
                    : 'Real-time recruitment progression verified authoritatively by the placement office.'}
                </p>
              </div>
              <Badge variant="primary" size="sm">
                {stages.length} {stages.length === 1 ? 'Round' : 'Rounds'}
              </Badge>
            </div>

            {/* STUDENT PROGRESSION TIMELINE */}
            {isStudent && (
              <div className="space-y-4 pt-2">
                {/* Step 0: Application Status */}
                <div className="flex items-center justify-between p-3.5 bg-slate-50 border border-slate-200/80 rounded-2xl">
                  <div className="flex items-center space-x-3">
                    <div
                      className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs ${
                        drive.is_registered ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-500'
                      }`}
                    >
                      {drive.is_registered ? '✓' : '—'}
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-slate-900">Application Submitted</h4>
                      <p className="text-[11px] text-slate-500">Institutional registration for this drive</p>
                    </div>
                  </div>
                  <span
                    className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                      drive.is_registered
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    {drive.is_registered ? 'Applied' : 'Not Registered'}
                  </span>
                </div>

                {/* Steps 1..N: Dynamic Backend Stages */}
                {stages.map((stage) => {
                  const isQualified =
                    stage.my_status === 'SHORTLISTED' ||
                    stage.my_status === 'APPEARED' ||
                    stage.my_status === 'SELECTED';
                  const isRejected = stage.my_status === 'REJECTED';

                  return (
                    <div
                      key={stage.id}
                      className={`flex flex-col sm:flex-row sm:items-center sm:justify-between p-3.5 rounded-2xl border transition gap-3 ${
                        isQualified
                          ? 'bg-emerald-50/60 border-emerald-200'
                          : isRejected
                          ? 'bg-rose-50/60 border-rose-200'
                          : 'bg-slate-50/60 border-slate-200'
                      }`}
                    >
                      <div className="flex items-start space-x-3">
                        <div
                          className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs shrink-0 mt-0.5 ${
                            isQualified
                              ? 'bg-emerald-600 text-white ring-2 ring-emerald-200'
                              : isRejected
                              ? 'bg-rose-600 text-white'
                              : 'bg-slate-300 text-slate-700'
                          }`}
                        >
                          {isQualified ? '✓' : isRejected ? '✗' : stage.sequence_order}
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="text-[10px] font-bold text-slate-500 uppercase">
                              Round {stage.sequence_order}
                            </span>
                            <span className="text-slate-300">•</span>
                            <span className="text-[10px] font-semibold text-slate-600">
                              {stage.stage_type}
                            </span>
                          </div>
                          <h4 className="text-xs sm:text-sm font-bold text-slate-900 mt-0.5">
                            {stage.name}
                          </h4>
                          {stage.instructions && (
                            <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                              {stage.instructions}
                            </p>
                          )}
                        </div>
                      </div>

                      <div className="sm:self-center">
                        {isQualified ? (
                          <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 font-extrabold text-[11px]">
                            <svg className="w-3.5 h-3.5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
                            </svg>
                            <span>Qualified</span>
                          </span>
                        ) : isRejected ? (
                          <span className="px-3 py-1 rounded-full bg-rose-100 text-rose-800 font-bold text-[11px]">
                            Not Shortlisted
                          </span>
                        ) : (
                          <span className="px-3 py-1 rounded-full bg-slate-100 text-slate-600 font-medium text-[11px]">
                            Pending / Upcoming
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* OFFICER / ADMIN ROUND MANAGEMENT CARDS */}
            {isOfficerOrAdmin && (
              <div className="space-y-4">
                {stages.length === 0 ? (
                  <div className="p-6 bg-slate-50 rounded-2xl text-center text-xs text-slate-500">
                    No rounds configured for this placement drive yet.
                  </div>
                ) : (
                  stages.map((stage) => {
                    const studentCount = stage.student_count ?? 0;
                    return (
                      <div
                        key={stage.id}
                        className="bg-slate-50/90 border border-slate-200/90 rounded-2xl p-4 sm:p-5 hover:border-indigo-300 transition space-y-3"
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                          <div className="flex items-center space-x-2.5">
                            <span className="px-2.5 py-0.5 rounded-lg bg-indigo-600 text-white font-black text-xs">
                              ROUND {stage.sequence_order}
                            </span>
                            <h4 className="text-sm font-bold text-slate-900">{stage.name}</h4>
                          </div>

                          <div className="flex items-center space-x-2">
                            <span className="px-2 py-0.5 rounded bg-slate-200 text-slate-700 font-bold text-[10px]">
                              {stage.stage_type}
                            </span>
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                stage.is_published
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : 'bg-amber-100 text-amber-800'
                              }`}
                            >
                              {stage.is_published ? 'Published' : 'Draft'}
                            </span>
                          </div>
                        </div>

                        {/* Round Details & Count */}
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-2 border-t border-slate-200/60 text-xs">
                          <div className="flex items-center space-x-2">
                            <span className="text-slate-500">Current Qualified:</span>
                            <span className="font-extrabold text-slate-900 px-2.5 py-0.5 bg-white border border-slate-200 rounded-lg">
                              {studentCount} {studentCount === 1 ? 'Student' : 'Students'}
                            </span>
                          </div>

                          <div className="flex items-center space-x-2">
                            {studentCount > 0 && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  // Scroll to applicants table and filter by status
                                  setStatusFilter('SHORTLISTED');
                                  const workspace = document.getElementById('applicant-search-input');
                                  workspace?.scrollIntoView({ behavior: 'smooth' });
                                }}
                                className="text-xs"
                              >
                                View Qualified Students
                              </Button>
                            )}

                            <Button
                              variant="primary"
                              size="sm"
                              onClick={() => {
                                setSelectedStageForUpload(stage);
                                setIsStageUploadModalOpen(true);
                              }}
                              className="bg-indigo-600 hover:bg-indigo-700 text-xs shadow-xs"
                              leftIcon={
                                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                </svg>
                              }
                              data-testid={`upload-stage-btn-${stage.sequence_order}`}
                            >
                              {studentCount > 0 ? 'Upload Updated List' : 'Upload Qualified Students'}
                            </Button>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            )}
          </Card>
        </div>

        {/* Right Col: Eligibility Rules Matrix & Preparation Hub Extension */}
        <div className="space-y-6">
          {/* Eligibility Matrix */}
          <Card variant="default" className="rounded-3xl border-slate-200/90 p-6 shadow-xs space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Eligibility Matrix
            </h3>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-2 border-b border-slate-100">
                <span className="text-slate-500 font-medium">Academic CGPA</span>
                <span className="font-bold text-slate-900">≥ {drive.eligibility_criteria?.min_cgpa ?? 'None'}</span>
              </div>

              <div className="flex justify-between py-2 border-b border-slate-100">
                <span className="text-slate-500 font-medium">Active Backlogs</span>
                <span className="font-bold text-slate-900">≤ {drive.eligibility_criteria?.max_active_backlogs ?? 0}</span>
              </div>

              <div className="py-2 border-b border-slate-100 space-y-1">
                <span className="text-slate-500 font-medium block">Eligible Branches</span>
                <div className="flex flex-wrap gap-1">
                  {drive.eligibility_criteria?.eligible_branches?.map((b) => (
                    <span key={b} className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded text-[11px] font-bold">
                      {b}
                    </span>
                  )) || <span className="font-bold text-slate-900">All Branches</span>}
                </div>
              </div>

              <div className="py-2 border-b border-slate-100 space-y-1">
                <span className="text-slate-500 font-medium block">Eligible Batches</span>
                <div className="flex flex-wrap gap-1">
                  {drive.eligibility_criteria?.eligible_batch_years?.map((yr) => (
                    <span key={yr} className="px-2 py-0.5 bg-slate-100 text-slate-800 rounded text-[11px] font-bold">
                      {yr}
                    </span>
                  )) || <span className="font-bold text-slate-900">All Batches</span>}
                </div>
              </div>

              {drive.eligibility_criteria?.gender && (
                <div className="flex justify-between py-2">
                  <span className="text-slate-500 font-medium">Gender Criteria</span>
                  <span className="font-bold text-slate-900">{drive.eligibility_criteria.gender}</span>
                </div>
              )}
            </div>
          </Card>

          {/* Preparation Hub Extension Point */}
          <div className="bg-slate-900 rounded-3xl p-6 text-white shadow-sm space-y-3 border border-slate-800">
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-white/10 text-indigo-300 border border-white/10">
                Placement Readiness
              </span>
            </div>
            <h3 className="text-sm font-bold text-white">Prepare for {drive.job_role}</h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Access curated topic roadmaps, aptitude practice materials, and interview resources in the Preparation Hub.
            </p>
            <Link
              to="/preparation"
              className="inline-flex items-center space-x-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition shadow-xs"
            >
              <span>Explore Preparation Hub</span>
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 5. OFFICER APPLICANT TRIAGE WORKSPACE (OFFICER & ADMIN ONLY)              */}
      {/* ========================================================================= */}
      {isOfficerOrAdmin && (
        <Card
          data-testid="applicant-workspace"
          variant="default"
          className="rounded-3xl border-slate-200/90 p-6 sm:p-8 shadow-xs space-y-6"
        >
          {/* Workspace Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center space-x-2">
                <span className="w-2.5 h-2.5 rounded-full bg-indigo-600" />
                <h2 className="text-base sm:text-lg font-black text-slate-900 tracking-tight">
                  Applicant Management
                </h2>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Review registered candidates, shortlist applicants, and manage placement-stage outcomes.
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <Badge variant="neutral" size="md">
                {totalApplicants} {totalApplicants === 1 ? 'Applicant' : 'Applicants'}
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={() => fetchApplicants()}
                isLoading={loadingApplicants}
                title="Refresh applicant list"
              >
                Refresh
              </Button>
            </div>
          </div>

          {/* Action Success Alert */}
          {workspaceSuccessAlert && (
            <Alert
              variant="success"
              onClose={() => setWorkspaceSuccessAlert(null)}
              icon={
                <svg className="w-4 h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
              }
            >
              {workspaceSuccessAlert}
            </Alert>
          )}

          {/* Search and Filters Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-end">
            <div className="sm:col-span-5">
              <Input
                id="applicant-search-input"
                placeholder="Search student name, roll number, or email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                leftIcon={
                  <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                }
              />
            </div>

            <div className="sm:col-span-3">
              <Select
                id="applicant-branch-filter"
                value={branchFilter}
                onChange={(e) => handleBranchFilterChange(e.target.value)}
              >
                <option value="">All Branches</option>
                {branchOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </Select>
            </div>

            <div className="sm:col-span-3">
              <Select
                id="applicant-status-filter"
                value={statusFilter}
                onChange={(e) => handleStatusFilterChange(e.target.value)}
              >
                <option value="">All Registration Statuses</option>
                <option value="REGISTERED">Registered</option>
                <option value="SHORTLISTED">Shortlisted</option>
                <option value="OFFERED">Offered</option>
                <option value="REJECTED">Rejected</option>
                <option value="WITHDRAWN">Withdrawn</option>
              </Select>
            </div>

            <div className="sm:col-span-1 flex justify-end">
              {(searchQuery || branchFilter || statusFilter) && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setSearchQuery('');
                    setBranchFilter('');
                    setStatusFilter('');
                    setApplicantPage(1);
                    setSelectedStudentIds(new Set());
                  }}
                  className="text-slate-500 hover:text-slate-800 text-xs px-2"
                  title="Clear all filters"
                >
                  Reset
                </Button>
              )}
            </div>
          </div>

          {/* Floating Bulk Action Bar */}
          {selectedStudentIds.size > 0 && (
            <div
              data-testid="bulk-action-bar"
              className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 bg-indigo-50/90 border border-indigo-200/90 rounded-2xl animate-fade-in shadow-xs"
            >
              <div className="flex items-center space-x-2">
                <span className="w-2.5 h-2.5 rounded-full bg-indigo-600 animate-pulse" />
                <span className="text-xs font-bold text-indigo-950">
                  {selectedStudentIds.size} Candidate{selectedStudentIds.size === 1 ? '' : 's'} Selected
                </span>
                <span className="text-[11px] text-indigo-700/80">
                  (Current page selection)
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <Button
                  id="btn-bulk-shortlist"
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    setActionModalError(null);
                    setTargetStageId(stages.length > 0 ? stages[0].id : '');
                    setIsShortlistModalOpen(true);
                  }}
                  disabled={stages.length === 0}
                  className="bg-indigo-600 hover:bg-indigo-700"
                >
                  Shortlist to Stage
                </Button>

                <Button
                  id="btn-bulk-status"
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setActionModalError(null);
                    setTargetStageId(stages.length > 0 ? stages[0].id : '');
                    setTargetStatus('SHORTLISTED');
                    setResultNotes('');
                    setIsBulkStatusModalOpen(true);
                  }}
                  disabled={stages.length === 0}
                  className="border-indigo-300 text-indigo-800 hover:bg-indigo-100"
                >
                  Update Status
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedStudentIds(new Set())}
                  className="text-slate-500 hover:text-slate-800"
                >
                  Clear Selection
                </Button>
              </div>
            </div>
          )}

          {/* Applicant Error Banner */}
          {applicantError && (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <svg className="w-4 h-4 text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-xs font-semibold text-rose-800">{applicantError}</span>
              </div>
              <Button variant="outline" size="sm" onClick={() => fetchApplicants()} className="border-rose-300 text-rose-800">
                Retry
              </Button>
            </div>
          )}

          {/* Applicants Table */}
          <TableContainer>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12 text-center">
                    <Checkbox
                      id="select-all-applicants-checkbox"
                      aria-label="Select all applicants on this page"
                      checked={allCurrentPageSelected}
                      onChange={handleToggleSelectAll}
                      disabled={loadingApplicants || applicants.length === 0}
                    />
                  </TableHead>
                  <TableHead>Candidate</TableHead>
                  <TableHead>Roll Number</TableHead>
                  <TableHead>Branch</TableHead>
                  <TableHead>CGPA</TableHead>
                  <TableHead>Backlogs</TableHead>
                  <TableHead>Registration</TableHead>
                  <TableHead>Current Stage</TableHead>
                  <TableHead>Stage Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {loadingApplicants ? (
                  [1, 2, 3, 4, 5].map((i) => (
                    <TableRow key={i}>
                      <TableCell className="text-center">
                        <Skeleton className="h-4 w-4 mx-auto rounded" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-4 w-32" />
                        <Skeleton className="h-3 w-24 mt-1" />
                      </TableCell>
                      <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-12" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-10" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-8" /></TableCell>
                      <TableCell><Skeleton className="h-5 w-16 rounded-full" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                      <TableCell><Skeleton className="h-5 w-16 rounded-full" /></TableCell>
                      <TableCell className="text-right"><Skeleton className="h-7 w-16 ml-auto rounded-lg" /></TableCell>
                    </TableRow>
                  ))
                ) : applicants.length === 0 ? (
                  <TableEmpty
                    colSpan={10}
                    message={
                      debouncedSearch || branchFilter || statusFilter
                        ? 'No applicants match your search or filter criteria.'
                        : 'No applicants have registered for this drive yet.'
                    }
                  />
                ) : (
                  applicants.map((item) => {
                    const isSelected = selectedStudentIds.has(item.student_user_id);
                    const student = item.student;
                    const stage = item.current_stage;

                    return (
                      <TableRow
                        key={item.id}
                        className={isSelected ? 'bg-indigo-50/40' : undefined}
                      >
                        {/* 1. Selection Checkbox */}
                        <TableCell className="text-center">
                          <Checkbox
                            data-testid={`applicant-select-${item.student_user_id}`}
                            aria-label={`Select applicant: ${student.full_name}`}
                            checked={isSelected}
                            onChange={() => handleToggleSelectRow(item.student_user_id)}
                          />
                        </TableCell>

                        {/* 2. Candidate Info */}
                        <TableCell>
                          <div className="font-bold text-slate-900">{student.full_name}</div>
                          <div className="text-[11px] text-slate-500">{student.email}</div>
                        </TableCell>

                        {/* 3. Roll Number */}
                        <TableCell className="font-mono text-xs text-slate-700 font-semibold">
                          {student.roll_number}
                        </TableCell>

                        {/* 4. Branch */}
                        <TableCell>
                          <span className="px-2 py-0.5 bg-slate-100 text-slate-800 rounded font-semibold text-[11px]">
                            {student.branch}
                          </span>
                        </TableCell>

                        {/* 5. CGPA */}
                        <TableCell className="font-bold text-slate-900">
                          {student.cgpa !== undefined && student.cgpa !== null ? student.cgpa.toFixed(2) : '—'}
                        </TableCell>

                        {/* 6. Backlogs */}
                        <TableCell>
                          <span
                            className={`font-semibold ${
                              student.active_backlogs > 0 ? 'text-rose-600 font-bold' : 'text-slate-600'
                            }`}
                          >
                            {student.active_backlogs}
                          </span>
                        </TableCell>

                        {/* 7. Registration Status */}
                        <TableCell>
                          <StatusBadge status={item.status} size="sm" />
                        </TableCell>

                        {/* 8. Current Stage */}
                        <TableCell>
                          {stage ? (
                            <div>
                              <span className="font-semibold text-slate-900 block">
                                {stage.stage_name}
                              </span>
                              <span className="text-[10px] text-slate-400">
                                Round {stage.sequence_order} • {stage.stage_type}
                              </span>
                            </div>
                          ) : (
                            <span className="text-slate-400 italic text-[11px]">Not Assigned</span>
                          )}
                        </TableCell>

                        {/* 9. Stage Status */}
                        <TableCell>
                          {stage?.status ? (
                            <StatusBadge status={stage.status} size="sm" />
                          ) : (
                            <span className="text-slate-400 text-[11px]">—</span>
                          )}
                        </TableCell>

                        {/* 10. Actions */}
                        <TableCell className="text-right">
                          <Button
                            data-testid={`view-candidate-${item.student_user_id}`}
                            variant="outline"
                            size="sm"
                            onClick={() => handleOpenQuickView(item)}
                            className="text-[11px] px-2.5 py-1"
                          >
                            Review
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Server-Side Pagination Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pt-4 border-t border-slate-100">
            <div className="text-xs text-slate-500 font-medium">
              Showing <span className="font-bold text-slate-900">{startIdx}–{endIdx}</span> of{' '}
              <span className="font-bold text-slate-900">{totalApplicants}</span> applicants
            </div>

            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-1.5 text-xs text-slate-500">
                <span>Rows:</span>
                <select
                  value={applicantPageSize}
                  onChange={(e) => {
                    setApplicantPageSize(Number(e.target.value));
                    setApplicantPage(1);
                    setSelectedStudentIds(new Set());
                  }}
                  className="border border-slate-200 rounded-lg px-2 py-1 text-xs bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
              </div>

              <div className="flex items-center space-x-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(applicantPage - 1)}
                  disabled={applicantPage <= 1 || loadingApplicants}
                >
                  &larr; Previous
                </Button>
                <span className="text-xs font-semibold text-slate-600 px-2">
                  Page {applicantPage} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(applicantPage + 1)}
                  disabled={applicantPage >= totalPages || loadingApplicants}
                >
                  Next &rarr;
                </Button>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* ========================================================================= */}
      {/* 6. MODALS                                                                 */}
      {/* ========================================================================= */}

      {/* A. BULK SHORTLIST MODAL */}
      <Modal
        isOpen={isShortlistModalOpen}
        onClose={() => {
          if (!actionLoading) {
            setIsShortlistModalOpen(false);
            setActionModalError(null);
          }
        }}
        title="Shortlist Candidates to Stage"
        description="Assign selected candidates to a target recruitment stage."
        footer={
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsShortlistModalOpen(false)}
              disabled={actionLoading}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleConfirmShortlist}
              disabled={actionLoading || !targetStageId}
              isLoading={actionLoading}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              Confirm Shortlisting
            </Button>
          </>
        }
      >
        <div className="space-y-4 text-xs">
          {actionModalError && (
            <Alert variant="danger" onClose={() => setActionModalError(null)}>
              {actionModalError}
            </Alert>
          )}

          <div className="p-3 bg-indigo-50/80 border border-indigo-100 rounded-xl text-indigo-900">
            <span className="font-bold block">Selected Candidates:</span>
            <span>{selectedStudentIds.size} applicant(s) will be assigned.</span>
          </div>

          <div>
            <Select
              label="Target Placement Stage"
              required
              value={targetStageId}
              onChange={(e) => setTargetStageId(e.target.value)}
            >
              <option value="">Select Target Stage...</option>
              {stages.map((st) => (
                <option key={st.id} value={st.id}>
                  Stage {st.sequence_order}: {st.name} ({st.stage_type})
                </option>
              ))}
            </Select>
          </div>

          <p className="text-slate-500 leading-relaxed">
            This will assign the selected candidates to the chosen placement stage and establish their evaluation track.
          </p>
        </div>
      </Modal>

      {/* B. BULK STATUS UPDATE MODAL */}
      <Modal
        isOpen={isBulkStatusModalOpen}
        onClose={() => {
          if (!actionLoading) {
            setIsBulkStatusModalOpen(false);
            setActionModalError(null);
          }
        }}
        title="Update Candidate Stage Status"
        description="Update evaluation outcome for candidates in their assigned stage."
        footer={
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsBulkStatusModalOpen(false)}
              disabled={actionLoading}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleConfirmBulkStatus}
              disabled={actionLoading || !targetStageId}
              isLoading={actionLoading}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              Confirm Status Update
            </Button>
          </>
        }
      >
        <div className="space-y-4 text-xs">
          {actionModalError && (
            <Alert variant="danger" onClose={() => setActionModalError(null)}>
              {actionModalError}
            </Alert>
          )}

          <div className="p-3 bg-indigo-50/80 border border-indigo-100 rounded-xl text-indigo-900">
            <span className="font-bold block">Selected Candidates:</span>
            <span>{selectedStudentIds.size} candidate assignment(s) will be updated.</span>
          </div>

          <div>
            <Select
              label="Target Placement Stage"
              required
              value={targetStageId}
              onChange={(e) => setTargetStageId(e.target.value)}
            >
              <option value="">Select Target Stage...</option>
              {stages.map((st) => (
                <option key={st.id} value={st.id}>
                  Stage {st.sequence_order}: {st.name} ({st.stage_type})
                </option>
              ))}
            </Select>
          </div>

          <div>
            <Select
              label="Evaluation Outcome / Status"
              required
              value={targetStatus}
              onChange={(e) => setTargetStatus(e.target.value as AssignmentStatus)}
            >
              <option value="SHORTLISTED">SHORTLISTED</option>
              <option value="APPEARED">APPEARED</option>
              <option value="SELECTED">SELECTED</option>
              <option value="REJECTED">REJECTED</option>
            </Select>
          </div>

          <div>
            <Textarea
              label="Result Notes (Optional)"
              placeholder="e.g. Cleared technical interview with strong problem-solving proficiency."
              rows={3}
              value={resultNotes}
              onChange={(e) => setResultNotes(e.target.value)}
            />
          </div>

          <p className="text-slate-500 leading-relaxed">
            This will update the evaluation status for all selected candidates in the target stage. Candidates must already have an assignment in the selected stage.
          </p>
        </div>
      </Modal>

      {/* C. CANDIDATE QUICK VIEW MODAL */}
      {selectedCandidate && (
        <Modal
          isOpen={isQuickViewModalOpen}
          onClose={() => {
            setIsQuickViewModalOpen(false);
            setSelectedCandidate(null);
            setResumeDownloadError(null);
          }}
          title={
            <div className="flex items-center space-x-2">
              <span className="text-base font-bold text-slate-900">
                {selectedCandidate.student?.full_name || 'Candidate Review'}
              </span>
              <StatusBadge status={selectedCandidate.status} size="sm" />
            </div>
          }
          description={`Roll No: ${selectedCandidate.student?.roll_number || 'Not provided'} • Branch: ${selectedCandidate.student?.branch || 'Not provided'}`}
          footer={
            <div className="flex items-center justify-between w-full">
              <Button
                id="btn-download-resume"
                data-testid="btn-download-resume"
                variant="outline"
                size="sm"
                onClick={() => selectedCandidate.student?.id && handleDownloadResume(selectedCandidate.student.id)}
                disabled={isDownloadingResume}
                isLoading={isDownloadingResume}
                leftIcon={
                  <svg className="w-3.5 h-3.5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                }
              >
                View Official Resume
              </Button>

              <Button
                id="btn-close-review"
                data-testid="btn-close-review"
                variant="primary"
                size="sm"
                onClick={() => {
                  setIsQuickViewModalOpen(false);
                  setSelectedCandidate(null);
                }}
              >
                Close Review
              </Button>
            </div>
          }
        >
          <div className="space-y-4 text-xs">
            {resumeDownloadError && (
              <Alert variant="danger" onClose={() => setResumeDownloadError(null)}>
                {resumeDownloadError}
              </Alert>
            )}

            {/* Candidate Metadata Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 p-3.5 bg-slate-50 rounded-2xl border border-slate-100">
              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400 block">Email Address</span>
                <span className="font-semibold text-slate-900 block truncate" title={selectedCandidate.student?.email || 'Not provided'}>
                  {selectedCandidate.student?.email || 'Not provided'}
                </span>
              </div>

              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400 block">Batch Year</span>
                <span className="font-semibold text-slate-900 block">
                  {selectedCandidate.student?.batch_year || 'Not provided'}
                </span>
              </div>

              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400 block">Academic CGPA</span>
                <span className="font-bold text-slate-900 block">
                  {selectedCandidate.student?.cgpa !== undefined && selectedCandidate.student?.cgpa !== null
                    ? selectedCandidate.student.cgpa.toFixed(2)
                    : 'Not provided'}
                </span>
              </div>

              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400 block">Active Backlogs</span>
                <span
                  className={`font-semibold block ${
                    (selectedCandidate.student?.active_backlogs ?? 0) > 0 ? 'text-rose-600 font-bold' : 'text-slate-900'
                  }`}
                >
                  {selectedCandidate.student?.active_backlogs !== undefined ? selectedCandidate.student.active_backlogs : 'Not provided'}
                </span>
              </div>

              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400 block">Registered On</span>
                <span className="font-semibold text-slate-900 block">
                  {selectedCandidate.registered_at ? new Date(selectedCandidate.registered_at).toLocaleDateString() : 'Not provided'}
                </span>
              </div>

              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400 block">Registration Status</span>
                <span className="font-bold text-indigo-700 block">
                  {selectedCandidate.status || 'Not provided'}
                </span>
              </div>
            </div>

            {/* Current Stage Evaluation Section */}
            <div className="p-3.5 bg-indigo-50/50 rounded-2xl border border-indigo-100/80 space-y-2">
              <span className="text-[10px] uppercase font-black text-indigo-900 block tracking-wider">
                Current Stage Evaluation
              </span>

              {selectedCandidate.current_stage ? (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-bold text-slate-900 text-xs">
                        {selectedCandidate.current_stage.stage_name}
                      </h4>
                      <span className="text-[11px] text-slate-500">
                        Round {selectedCandidate.current_stage.sequence_order} • {selectedCandidate.current_stage.stage_type}
                      </span>
                    </div>
                    <StatusBadge status={selectedCandidate.current_stage.status} size="sm" />
                  </div>

                  {selectedCandidate.current_stage.result_notes && (
                    <div className="pt-2 border-t border-indigo-100 text-[11px]">
                      <span className="font-bold text-slate-700 block">Result Notes:</span>
                      <p className="text-slate-600 mt-0.5 whitespace-pre-wrap">
                        {selectedCandidate.current_stage.result_notes}
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-slate-500 italic text-xs">
                  Candidate has not been assigned to any placement stage yet.
                </p>
              )}
            </div>
          </div>
        </Modal>
      )}

      {/* Stage Qualified Student List Import Modal */}
      {isStageUploadModalOpen && selectedStageForUpload && id && (
        <StageQualifiedImportModal
          isOpen={isStageUploadModalOpen}
          onClose={() => {
            setIsStageUploadModalOpen(false);
            setSelectedStageForUpload(null);
          }}
          onSuccess={() => {
            fetchDriveDetails();
            fetchApplicants();
          }}
          driveId={id}
          stage={selectedStageForUpload}
          driveTitle={`${companyName} — ${jobRole}`}
        />
      )}

      {/* Manual Broadcast Modal */}
      {isBroadcastModalOpen && (
        <ManualBroadcastModal
          isOpen={isBroadcastModalOpen}
          driveId={drive.id}
          driveTitle={`${companyName} — ${drive.job_role}`}
          onClose={() => setIsBroadcastModalOpen(false)}
        />
      )}

      {/* Delete Placement Drive Confirmation Modal */}
      {isDeleteModalOpen && (
        <Modal
          isOpen={isDeleteModalOpen}
          onClose={() => {
            if (!isDeleting) {
              setIsDeleteModalOpen(false);
              setDeleteError(null);
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
                {companyName} — {jobRole}
              </p>
              <p className="mt-2 text-rose-700">
                This drive will be archived and removed from active student discovery. All historical registrations, student records, and stages will remain safely preserved.
              </p>
            </div>

            {deleteError && (
              <Alert variant="danger">
                {deleteError}
              </Alert>
            )}

            <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-100">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setIsDeleteModalOpen(false);
                  setDeleteError(null);
                }}
                disabled={isDeleting}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={handleConfirmDelete}
                disabled={isDeleting}
                isLoading={isDeleting}
                className="bg-rose-600 hover:bg-rose-700 text-white shadow-xs"
                data-testid="confirm-delete-drive-btn"
              >
                {isDeleting ? 'Deleting...' : 'Delete Drive'}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

