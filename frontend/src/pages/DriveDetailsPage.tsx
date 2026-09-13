import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { driveService } from '../services/driveService';
import { ManualBroadcastModal } from '../components/ManualBroadcastModal';
import type { PlacementDrive, PlacementStage } from '../types/drive';

export const DriveDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const isStudent = user?.role === 'STUDENT';
  const isOfficerOrAdmin = user?.role === 'OFFICER' || user?.role === 'ADMIN';

  const [drive, setDrive] = useState<PlacementDrive | null>(null);
  const [stages, setStages] = useState<PlacementStage[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Student registration state
  const [isRegistering, setIsRegistering] = useState<boolean>(false);
  const [registrationSuccess, setRegistrationSuccess] = useState<string | null>(null);

  // Officer management state
  const [isPublishing, setIsPublishing] = useState<boolean>(false);
  const [isBroadcastModalOpen, setIsBroadcastModalOpen] = useState<boolean>(false);

  const fetchDriveDetails = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const [driveData, stageData] = await Promise.allSettled([
        driveService.getDrive(id),
        driveService.listStages(id),
      ]);

      if (driveData.status === 'fulfilled') {
        setDrive(driveData.value);
      } else {
        setError('Placement drive could not be found or you do not have permission to view it.');
      }

      if (stageData.status === 'fulfilled') {
        setStages(stageData.value || []);
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

  const handleRegister = async () => {
    if (!drive || !id) return;
    setIsRegistering(true);
    setRegistrationSuccess(null);
    try {
      await driveService.registerStudent(id);
      setDrive((prev) => (prev ? { ...prev, is_registered: true } : null));
      setRegistrationSuccess('Your application has been successfully submitted for this drive!');
      setTimeout(() => setRegistrationSuccess(null), 6000);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to submit application.');
    } finally {
      setIsRegistering(false);
    }
  };

  const handlePublishDrive = async () => {
    if (!drive || !id) return;
    setIsPublishing(true);
    try {
      const updated = await driveService.updateDriveStatus(id, 'PUBLISHED');
      setDrive(updated);
      alert('Drive published successfully! Eligible students have been notified.');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to publish drive.');
    } finally {
      setIsPublishing(false);
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
      <div className="p-12 text-center bg-white rounded-3xl border border-slate-200 shadow-sm animate-fade-in">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-indigo-600 border-t-transparent mb-3" />
        <p className="text-xs text-slate-500 font-semibold">Loading placement drive details...</p>
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
        <button
          onClick={() => navigate('/drives')}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl shadow-sm transition"
        >
          &larr; Back to Placement Drives
        </button>
      </div>
    );
  }

  const companyName = (drive as any).company_name || drive.company?.name || drive.title || 'Recruiting Partner';
  const jobRole = (drive as any).role_title || drive.job_role || 'Engineering Role';
  const deadlineStr = drive.registration_deadline || (drive as any).registration_end;
  const deadlineInfo = getDeadlineInfo(deadlineStr);
  const myEligibility = drive.my_eligibility;

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl mx-auto pb-12">
      {/* Navigation Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/drives')}
          className="inline-flex items-center space-x-1.5 text-xs font-bold text-slate-500 hover:text-indigo-600 transition"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>Back to Placement Drives</span>
        </button>

        <span className="px-3 py-1 rounded-full text-xs font-extrabold uppercase tracking-wider bg-indigo-50 text-indigo-700 border border-indigo-100">
          {drive.status.replace(/_/g, ' ')}
        </span>
      </div>

      {registrationSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-emerald-800 text-xs font-bold flex items-center space-x-2 animate-fade-in">
          <svg className="w-5 h-5 text-emerald-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
          </svg>
          <span>{registrationSuccess}</span>
        </div>
      )}

      {/* Main Drive Banner */}
      <div className="bg-white rounded-3xl border border-slate-200/90 shadow-sm p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="flex items-start space-x-4">
            <div className="w-16 h-16 rounded-2xl bg-slate-900 text-white flex items-center justify-center font-extrabold text-2xl flex-shrink-0 shadow-md">
              {companyName.charAt(0).toUpperCase()}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
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
                  <svg className="w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
          <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-100">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Package (CTC)</span>
            <span className="text-base font-extrabold text-emerald-700 mt-0.5 block">
              {formatPackage(drive.ctc_lpa, drive.stipend_monthly, (drive as any).package_details)}
            </span>
          </div>

          <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-100">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Min CGPA</span>
            <span className="text-base font-extrabold text-slate-900 mt-0.5 block">
              {drive.eligibility_criteria?.min_cgpa ?? 'Any'}
            </span>
          </div>

          <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-100">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Max Backlogs</span>
            <span className="text-base font-extrabold text-slate-900 mt-0.5 block">
              ≤ {drive.eligibility_criteria?.max_active_backlogs ?? 0}
            </span>
          </div>

          <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-100">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Selection Rounds</span>
            <span className="text-base font-extrabold text-indigo-700 mt-0.5 block">
              {stages.length} Stages
            </span>
          </div>
        </div>
      </div>

      {/* STUDENT ACTION & ELIGIBILITY BANNER */}
      {isStudent && (
        <div className="bg-white rounded-3xl border border-slate-200/90 p-6 sm:p-7 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700">
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
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-500 mt-1 flex-shrink-0" />
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
                <div className="inline-flex items-center space-x-2 px-4 py-2.5 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-2xl text-xs font-bold">
                  <svg className="w-4 h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span>Application Submitted</span>
                </div>
              ) : deadlineInfo.isExpired ? (
                <button
                  disabled
                  className="px-5 py-2.5 bg-slate-100 text-slate-400 rounded-2xl text-xs font-bold cursor-not-allowed"
                >
                  Registration Closed
                </button>
              ) : myEligibility && !myEligibility.is_eligible ? (
                <button
                  disabled
                  className="px-5 py-2.5 bg-rose-50 text-rose-400 border border-rose-100 rounded-2xl text-xs font-bold cursor-not-allowed"
                >
                  Not Eligible to Register
                </button>
              ) : (
                <button
                  onClick={handleRegister}
                  disabled={isRegistering}
                  className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-2xl text-xs font-bold shadow-lg shadow-indigo-600/30 transition flex items-center space-x-2"
                >
                  {isRegistering ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Submitting Application...</span>
                    </>
                  ) : (
                    <span>Register for Drive Now &rarr;</span>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* OFFICER & ADMIN MANAGEMENT PANEL */}
      {isOfficerOrAdmin && (
        <div className="bg-white rounded-3xl border border-purple-200/80 p-6 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-600" />
              <h2 className="text-xs font-extrabold uppercase tracking-wider text-purple-900">
                Placement Officer Management Controls
              </h2>
            </div>
            <span className="text-[11px] text-slate-400 font-mono">Drive ID: {drive.id}</span>
          </div>

          <div className="flex flex-wrap items-center gap-2 pt-2">
            {drive.status === 'DRAFT' && (
              <button
                onClick={handlePublishDrive}
                disabled={isPublishing}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl shadow-sm transition"
              >
                {isPublishing ? 'Publishing...' : 'Publish Drive Now'}
              </button>
            )}

            <button
              onClick={() => setIsBroadcastModalOpen(true)}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold rounded-xl shadow-sm transition flex items-center space-x-1.5"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
              </svg>
              <span>Broadcast Notification</span>
            </button>

            <button
              onClick={() => navigate(`/drives/${drive.id}/analytics`)}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition flex items-center space-x-1.5"
            >
              <svg className="w-3.5 h-3.5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span>Funnel Analytics</span>
            </button>
          </div>
        </div>
      )}

      {/* Two Column Section: Job Description & Eligibility Matrix */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left 2 Cols: Description & Selection Stages */}
        <div className="md:col-span-2 space-y-6">
          {/* Detailed Description */}
          <div className="bg-white rounded-3xl border border-slate-200/90 p-6 sm:p-7 shadow-sm space-y-3">
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
          </div>

          {/* Selection Stages Process Timeline */}
          <div className="bg-white rounded-3xl border border-slate-200/90 p-6 sm:p-7 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Recruitment & Selection Process
                </h3>
                <p className="text-xs text-slate-600 mt-0.5">
                  Sequential assessment rounds for candidate evaluation.
                </p>
              </div>
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-700">
                {stages.length} Stages
              </span>
            </div>

            {stages.length === 0 ? (
              <div className="p-6 bg-slate-50 rounded-2xl text-center text-xs text-slate-500">
                No stages configured for this recruitment drive yet.
              </div>
            ) : (
              <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-indigo-100">
                {stages.map((stage) => (
                  <div key={stage.id || stage.sequence_order} className="relative">
                    <div className="absolute -left-6 top-0 w-5 h-5 rounded-full bg-indigo-600 text-white text-[10px] font-extrabold flex items-center justify-center ring-4 ring-white">
                      {stage.sequence_order}
                    </div>

                    <div className="bg-slate-50/80 border border-slate-200/80 rounded-2xl p-4 space-y-1.5 hover:bg-slate-50 transition">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs sm:text-sm font-bold text-slate-900">{stage.name}</h4>
                        <span className="px-2 py-0.5 rounded text-[10px] font-extrabold bg-slate-200 text-slate-700">
                          {stage.stage_type}
                        </span>
                      </div>

                      {stage.location_or_link && (
                        <p className="text-xs text-indigo-700 font-medium flex items-center space-x-1">
                          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                          </svg>
                          <span>{stage.location_or_link}</span>
                        </p>
                      )}

                      {stage.instructions && (
                        <p className="text-xs text-slate-600 pt-1 border-t border-slate-200/60 leading-relaxed">
                          {stage.instructions}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Col: Eligibility Rules Matrix & Preparation Extension Point */}
        <div className="space-y-6">
          {/* Eligibility Matrix */}
          <div className="bg-white rounded-3xl border border-slate-200/90 p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Eligibility Matrix
            </h3>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-2 border-b border-slate-100">
                <span className="text-slate-500">Academic CGPA</span>
                <span className="font-bold text-slate-900">≥ {drive.eligibility_criteria?.min_cgpa ?? 'None'}</span>
              </div>

              <div className="flex justify-between py-2 border-b border-slate-100">
                <span className="text-slate-500">Active Backlogs</span>
                <span className="font-bold text-slate-900">≤ {drive.eligibility_criteria?.max_active_backlogs ?? 0}</span>
              </div>

              <div className="py-2 border-b border-slate-100 space-y-1">
                <span className="text-slate-500 block">Eligible Branches</span>
                <div className="flex flex-wrap gap-1">
                  {drive.eligibility_criteria?.eligible_branches?.map((b) => (
                    <span key={b} className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded text-[11px] font-semibold">
                      {b}
                    </span>
                  )) || <span className="font-bold text-slate-900">All Branches</span>}
                </div>
              </div>

              <div className="py-2 border-b border-slate-100 space-y-1">
                <span className="text-slate-500 block">Eligible Batches</span>
                <div className="flex flex-wrap gap-1">
                  {drive.eligibility_criteria?.eligible_batch_years?.map((yr) => (
                    <span key={yr} className="px-2 py-0.5 bg-slate-100 text-slate-800 rounded text-[11px] font-semibold">
                      {yr}
                    </span>
                  )) || <span className="font-bold text-slate-900">All Batches</span>}
                </div>
              </div>

              {drive.eligibility_criteria?.gender && (
                <div className="flex justify-between py-2">
                  <span className="text-slate-500">Gender Criteria</span>
                  <span className="font-bold text-slate-900">{drive.eligibility_criteria.gender}</span>
                </div>
              )}
            </div>
          </div>

          {/* Phase 5B Clean Extension Point: Preparation Roadmaps */}
          <div className="bg-gradient-to-br from-indigo-900 to-slate-900 rounded-3xl p-6 text-white shadow-md space-y-3">
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-white/20 text-indigo-200">
                Placement Readiness
              </span>
            </div>
            <h3 className="text-sm font-bold text-white">Prepare for {drive.job_role}</h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Access curated topic roadmaps, aptitude practice materials, and interview resources in the Preparation Hub.
            </p>
            <Link
              to="/preparation"
              className="inline-flex items-center space-x-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition shadow-sm"
            >
              <span>Explore Preparation Hub</span>
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </div>
      </div>

      {/* Manual Broadcast Modal if opened */}
      {isBroadcastModalOpen && (
        <ManualBroadcastModal
          isOpen={isBroadcastModalOpen}
          driveId={drive.id}
          driveTitle={`${companyName} — ${drive.job_role}`}
          onClose={() => setIsBroadcastModalOpen(false)}
        />
      )}
    </div>
  );
};
