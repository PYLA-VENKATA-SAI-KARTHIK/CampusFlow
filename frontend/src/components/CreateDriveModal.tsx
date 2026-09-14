import React, { useState, useEffect } from 'react';
import { driveService } from '../services/driveService';
import { preparationService } from '../services/preparationService';
import type {
  Company,
  PlacementDrive,
  PlacementStageCreate,
  StageType,
} from '../types/drive';

interface CreateDriveModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (drive: PlacementDrive, isPublished: boolean) => void;
}

export const CreateDriveModal: React.FC<CreateDriveModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Reference data
  const [companies, setCompanies] = useState<Company[]>([]);
  const [availableBranches, setAvailableBranches] = useState<string[]>(['CSE', 'IT', 'ECE', 'EEE', 'MECH', 'CIVIL']);
  const [availableRoles, setAvailableRoles] = useState<string[]>([
    'Software Developer',
    'AI/ML Engineer',
    'Data Analyst',
    'Cloud & DevOps Engineer',
    'QA / Test Automation Engineer',
    'Associate Software Engineer',
  ]);

  // Step 1: Company & Job Profile
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>('');
  const [isCreatingNewCompany, setIsCreatingNewCompany] = useState<boolean>(false);
  const [newCompanyName, setNewCompanyName] = useState<string>('');
  const [newCompanyWebsite, setNewCompanyWebsite] = useState<string>('');
  const [newCompanyIndustry, setNewCompanyIndustry] = useState<string>('Information Technology');
  const [newCompanyDescription, setNewCompanyDescription] = useState<string>('');

  const [jobRole, setJobRole] = useState<string>('Associate Software Engineer');
  const [customJobRole, setCustomJobRole] = useState<string>('');
  const [driveTitle, setDriveTitle] = useState<string>('');
  const [jobLocation, setJobLocation] = useState<string>('Bengaluru / Chennai');
  const [jobDescription, setJobDescription] = useState<string>('');

  // Step 2: Compensation
  const [ctcLpa, setCtcLpa] = useState<string>('4.5');
  const [stipendMonthly, setStipendMonthly] = useState<string>('');
  const [bondDetails, setBondDetails] = useState<string>('');

  // Step 3: Eligibility Criteria
  const [minCgpa, setMinCgpa] = useState<string>('7.0');
  const [maxBacklogs, setMaxBacklogs] = useState<string>('0');
  const [selectedBranches, setSelectedBranches] = useState<string[]>(['CSE', 'IT']);
  const [selectedBatchYears, setSelectedBatchYears] = useState<number[]>([2026, 2027]);
  const [genderCriteria, setGenderCriteria] = useState<'MALE' | 'FEMALE' | 'OTHER' | ''>('');

  // Step 4: Registration & Selection Stages
  const [registrationDeadline, setRegistrationDeadline] = useState<string>(() => {
    const d = new Date();
    d.setDate(d.getDate() + 7);
    return d.toISOString().slice(0, 16);
  });

  const [stages, setStages] = useState<PlacementStageCreate[]>([
    {
      name: 'Online Aptitude & Reasoning Test',
      stage_type: 'APTITUDE',
      sequence_order: 1,
      scheduled_at: null,
      location_or_link: 'CampusFlow Online Assessment Portal',
      instructions: '60 minutes timed assessment covering quantitative, verbal, and logical sections.',
    },
    {
      name: 'Technical & Coding Interview',
      stage_type: 'CODING',
      sequence_order: 2,
      scheduled_at: null,
      location_or_link: 'Virtual Platform (Link will be shared)',
      instructions: 'Live data structures, algorithms, and domain knowledge evaluation.',
    },
    {
      name: 'HR & Cultural Fit Discussion',
      stage_type: 'HR',
      sequence_order: 3,
      scheduled_at: null,
      location_or_link: 'Main Placement Auditorium / Online',
      instructions: 'Behavioral assessment, role alignment, and document verification.',
    },
  ]);

  // Load companies, branches, and roles on mount
  useEffect(() => {
    if (!isOpen) return;

    const loadInitialData = async () => {
      try {
        const [compRes, branchRes, roleRes] = await Promise.allSettled([
          driveService.listCompanies(),
          driveService.listBranches(),
          preparationService.getRoles(),
        ]);

        if (compRes.status === 'fulfilled' && compRes.value.items?.length > 0) {
          setCompanies(compRes.value.items);
          setSelectedCompanyId(compRes.value.items[0].id);
        }

        if (branchRes.status === 'fulfilled' && branchRes.value.length > 0) {
          setAvailableBranches(branchRes.value.map((b) => b.code));
        }

        if (roleRes.status === 'fulfilled' && roleRes.value.length > 0) {
          setAvailableRoles(roleRes.value.map((r) => r.name));
        }
      } catch {
        // Fallbacks already in state
      }
    };

    loadInitialData();
  }, [isOpen]);

  // Auto-update Drive Title when company or role changes
  useEffect(() => {
    let companyName = 'Company';
    if (isCreatingNewCompany && newCompanyName.trim()) {
      companyName = newCompanyName.trim();
    } else {
      const match = companies.find((c) => c.id === selectedCompanyId);
      if (match) companyName = match.name;
    }

    const effectiveRole = jobRole === 'OTHER' ? customJobRole || 'Role' : jobRole;
    setDriveTitle(`${companyName} — ${effectiveRole}`);
  }, [selectedCompanyId, isCreatingNewCompany, newCompanyName, jobRole, customJobRole, companies]);

  if (!isOpen) return null;

  // Retry & Error Recovery State
  const [createdDrive, setCreatedDrive] = useState<PlacementDrive | null>(null);
  const [createdStageIndexes, setCreatedStageIndexes] = useState<Set<number>>(new Set());
  const [showDismissConfirm, setShowDismissConfirm] = useState<boolean>(false);

  const isFormDirty =
    currentStep > 1 ||
    Boolean(createdDrive) ||
    newCompanyName.trim().length > 0 ||
    customJobRole.trim().length > 0 ||
    jobDescription.trim().length > 0 ||
    bondDetails.trim().length > 0;

  const handleRequestClose = () => {
    if (isFormDirty && !showDismissConfirm) {
      setShowDismissConfirm(true);
      return;
    }
    handleForceClose();
  };

  const handleForceClose = () => {
    setShowDismissConfirm(false);
    setErrorMessage(null);
    setCurrentStep(1);
    setCreatedDrive(null);
    setCreatedStageIndexes(new Set());
    onClose();
  };

  const toggleBranch = (branch: string) => {
    setSelectedBranches((prev) =>
      prev.includes(branch) ? prev.filter((b) => b !== branch) : [...prev, branch]
    );
  };

  const toggleBatchYear = (year: number) => {
    setSelectedBatchYears((prev) =>
      prev.includes(year) ? prev.filter((y) => y !== year) : [...prev, year]
    );
  };

  const handleAddStage = () => {
    const nextOrder = stages.length + 1;
    setStages((prev) => [
      ...prev,
      {
        name: `Stage ${nextOrder}`,
        stage_type: 'TECHNICAL',
        sequence_order: nextOrder,
        scheduled_at: null,
        location_or_link: '',
        instructions: '',
      },
    ]);
  };

  const handleRemoveStage = (index: number) => {
    if (stages.length <= 1) return;
    const updated = stages.filter((_, i) => i !== index).map((s, i) => ({
      ...s,
      sequence_order: i + 1,
    }));
    setStages(updated);
  };

  const handleStageChange = (index: number, field: keyof PlacementStageCreate, value: any) => {
    setStages((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], [field]: value };
      return copy;
    });
  };

  const validateStep = (step: number): boolean => {
    setErrorMessage(null);
    if (step === 1) {
      if (isCreatingNewCompany && !newCompanyName.trim()) {
        setErrorMessage('Please enter the new company name.');
        return false;
      }
      if (!isCreatingNewCompany && !selectedCompanyId) {
        setErrorMessage('Please select a company.');
        return false;
      }
      const effectiveRole = jobRole === 'OTHER' ? customJobRole.trim() : jobRole.trim();
      if (!effectiveRole) {
        setErrorMessage('Please specify the job role.');
        return false;
      }
      if (!driveTitle.trim()) {
        setErrorMessage('Please enter a title for the placement drive.');
        return false;
      }
    } else if (step === 2) {
      if (ctcLpa && isNaN(Number(ctcLpa))) {
        setErrorMessage('CTC (LPA) must be a valid number.');
        return false;
      }
      if (stipendMonthly && isNaN(Number(stipendMonthly))) {
        setErrorMessage('Stipend must be a valid number.');
        return false;
      }
    } else if (step === 3) {
      if (minCgpa && (isNaN(Number(minCgpa)) || Number(minCgpa) < 0 || Number(minCgpa) > 10)) {
        setErrorMessage('Minimum CGPA must be a number between 0.0 and 10.0.');
        return false;
      }
      if (maxBacklogs && (isNaN(Number(maxBacklogs)) || Number(maxBacklogs) < 0)) {
        setErrorMessage('Max active backlogs must be 0 or greater.');
        return false;
      }
      if (selectedBranches.length === 0) {
        setErrorMessage('Please select at least one eligible branch.');
        return false;
      }
      if (selectedBatchYears.length === 0) {
        setErrorMessage('Please select at least one eligible batch year.');
        return false;
      }
    } else if (step === 4) {
      if (!registrationDeadline) {
        setErrorMessage('Registration deadline is required.');
        return false;
      }
      if (stages.length === 0) {
        setErrorMessage('Please configure at least one selection stage.');
        return false;
      }
    }
    return true;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep((prev) => Math.min(prev + 1, 5));
    }
  };

  const handleBack = () => {
    setErrorMessage(null);
    setCurrentStep((prev) => Math.max(prev - 1, 1));
  };

  const executeDriveCreation = async (publishImmediately: boolean) => {
    if (!validateStep(1) || !validateStep(2) || !validateStep(3) || !validateStep(4)) {
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      // 1. Resolve Company ID & Create Drive if not already created
      let driveToUse = createdDrive;
      if (!driveToUse) {
        let resolvedCompanyId = selectedCompanyId;
        if (isCreatingNewCompany) {
          const createdCompany = await driveService.createCompany({
            name: newCompanyName.trim(),
            website: newCompanyWebsite.trim() || undefined,
            industry: newCompanyIndustry.trim() || undefined,
            description: newCompanyDescription.trim() || undefined,
          });
          resolvedCompanyId = createdCompany.id;
        }

        const effectiveRole = jobRole === 'OTHER' ? customJobRole.trim() : jobRole.trim();
        const criteriaPayload = {
          min_cgpa: minCgpa ? Number(minCgpa) : null,
          max_active_backlogs: maxBacklogs ? Number(maxBacklogs) : null,
          eligible_branches: selectedBranches,
          eligible_batch_years: selectedBatchYears,
          gender: genderCriteria || null,
        };

        const deadlineIso = new Date(registrationDeadline).toISOString();

        const drivePayload = {
          company_id: resolvedCompanyId,
          title: driveTitle.trim(),
          job_role: effectiveRole,
          description: jobDescription.trim() || undefined,
          ctc_lpa: ctcLpa ? Number(ctcLpa) : undefined,
          stipend_monthly: stipendMonthly ? Number(stipendMonthly) : undefined,
          location: jobLocation.trim() || undefined,
          bond_details: bondDetails.trim() || undefined,
          registration_deadline: deadlineIso,
          eligibility_criteria: criteriaPayload,
        };

        driveToUse = await driveService.createDrive(drivePayload);
        setCreatedDrive(driveToUse);
      }

      // 2. Create Remaining Stages (prevents duplicate stage creations on retry)
      const updatedIndexes = new Set(createdStageIndexes);
      for (let i = 0; i < stages.length; i++) {
        if (updatedIndexes.has(i)) continue;
        const stage = stages[i];
        await driveService.createStage(driveToUse.id, {
          name: stage.name.trim(),
          stage_type: stage.stage_type,
          sequence_order: stage.sequence_order,
          scheduled_at: stage.scheduled_at ? new Date(stage.scheduled_at).toISOString() : null,
          location_or_link: stage.location_or_link?.trim() || null,
          instructions: stage.instructions?.trim() || null,
        });
        updatedIndexes.add(i);
        setCreatedStageIndexes(new Set(updatedIndexes));
      }

      // 3. If publish requested, transition status from DRAFT -> PUBLISHED
      let finalDrive = driveToUse;
      if (publishImmediately) {
        finalDrive = await driveService.updateDriveStatus(driveToUse.id, 'PUBLISHED');
      }

      onSuccess(finalDrive, publishImmediately);
      handleForceClose();
    } catch (err: any) {
      const apiMsg = err.response?.data?.detail || err.message || 'Failed to complete drive setup.';
      if (createdDrive) {
        setErrorMessage(
          `Drive saved as Draft (ID: ${createdDrive.id}), but stage setup did not complete: ${apiMsg}. You can click retry to complete setup without creating a duplicate drive.`
        );
      } else {
        setErrorMessage(apiMsg || 'Failed to create placement drive. Please verify the entered details.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const getCompanyName = () => {
    if (isCreatingNewCompany) return newCompanyName || 'New Company';
    return companies.find((c) => c.id === selectedCompanyId)?.name || 'Company';
  };

  const getEffectiveRole = () => {
    return jobRole === 'OTHER' ? customJobRole || 'Job Role' : jobRole;
  };

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-sm flex items-center justify-center p-3 sm:p-5"
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-drive-modal-title"
    >
      <div className="bg-white rounded-3xl shadow-2xl max-w-2xl w-full p-6 sm:p-8 transition-all transform animate-fade-in flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex justify-between items-center border-b border-slate-100 pb-4 flex-shrink-0">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-indigo-50 text-indigo-700 border border-indigo-100">
                Step {currentStep} of 5
              </span>
              <h2 id="create-drive-modal-title" className="text-lg font-bold text-slate-900">
                Create New Placement Drive
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Configure company hiring profile, eligibility rules, and selection stages.
            </p>
          </div>

          <button
            onClick={handleRequestClose}
            className="text-slate-400 hover:text-slate-600 rounded-lg p-1.5 transition"
            aria-label="Close modal"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Unsaved Changes Confirmation Warning */}
        {showDismissConfirm && (
          <div className="my-2 p-3.5 bg-amber-50 border border-amber-200 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs animate-fade-in flex-shrink-0">
            <div className="flex items-center space-x-2 text-amber-900 font-semibold">
              <svg className="w-4 h-4 text-amber-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>You have unsaved changes. Are you sure you want to discard your progress?</span>
            </div>
            <div className="flex items-center space-x-2 shrink-0">
              <button
                type="button"
                onClick={() => setShowDismissConfirm(false)}
                className="px-3 py-1 bg-white border border-amber-300 text-amber-900 rounded-lg font-bold hover:bg-amber-100 transition"
              >
                Stay
              </button>
              <button
                type="button"
                onClick={handleForceClose}
                className="px-3 py-1 bg-rose-600 text-white rounded-lg font-bold hover:bg-rose-700 transition"
              >
                Discard & Exit
              </button>
            </div>
          </div>
        )}

        {/* Step Progress Bar */}
        <div className="grid grid-cols-5 gap-1.5 my-4 flex-shrink-0">
          {['Company', 'Compensation', 'Eligibility', 'Stages', 'Preview'].map((stepLabel, idx) => {
            const stepNum = idx + 1;
            const isCompleted = stepNum < currentStep;
            const isCurrent = stepNum === currentStep;

            return (
              <div key={stepLabel} className="space-y-1">
                <div
                  className={`h-1.5 rounded-full transition-all ${
                    isCompleted
                      ? 'bg-emerald-500'
                      : isCurrent
                      ? 'bg-indigo-600'
                      : 'bg-slate-100'
                  }`}
                />
                <span
                  className={`text-[10px] block truncate font-medium text-center ${
                    isCurrent ? 'text-indigo-700 font-bold' : 'text-slate-400'
                  }`}
                >
                  {stepLabel}
                </span>
              </div>
            );
          })}
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-2.5 rounded-xl text-xs flex items-center space-x-2 flex-shrink-0 animate-fade-in">
            <svg className="w-4 h-4 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Scrollable Form Body */}
        <div className="overflow-y-auto flex-1 pr-1 space-y-4">
          {/* ========================================================================= */}
          {/* STEP 1: COMPANY & JOB PROFILE                                             */}
          {/* ========================================================================= */}
          {currentStep === 1 && (
            <div className="space-y-4 animate-fade-in">
              {/* Company Selection */}
              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                    Recruiting Company *
                  </label>
                  <button
                    type="button"
                    onClick={() => setIsCreatingNewCompany(!isCreatingNewCompany)}
                    className="text-xs font-bold text-indigo-600 hover:text-indigo-800 transition"
                  >
                    {isCreatingNewCompany ? '← Choose Existing Company' : '+ Add New Company'}
                  </button>
                </div>

                {!isCreatingNewCompany ? (
                  <select
                    value={selectedCompanyId}
                    onChange={(e) => setSelectedCompanyId(e.target.value)}
                    className="w-full border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs sm:text-sm font-medium focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none bg-white shadow-sm"
                  >
                    {companies.length === 0 && <option value="">No registered companies found</option>}
                    {companies.map((comp) => (
                      <option key={comp.id} value={comp.id}>
                        {comp.name} {comp.industry ? `(${comp.industry})` : ''}
                      </option>
                    ))}
                  </select>
                ) : (
                  <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-2xl space-y-3">
                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 mb-1">Company Name *</label>
                      <input
                        type="text"
                        placeholder="e.g. Accenture, Google, TCS"
                        value={newCompanyName}
                        onChange={(e) => setNewCompanyName(e.target.value)}
                        className="w-full border border-slate-300 rounded-xl px-3 py-2 text-xs focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none bg-white"
                      />
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-[11px] font-bold text-slate-700 mb-1">Industry</label>
                        <input
                          type="text"
                          placeholder="e.g. IT Services, FinTech"
                          value={newCompanyIndustry}
                          onChange={(e) => setNewCompanyIndustry(e.target.value)}
                          className="w-full border border-slate-300 rounded-xl px-3 py-2 text-xs focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none bg-white"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-bold text-slate-700 mb-1">Website URL</label>
                        <input
                          type="url"
                          placeholder="https://company.com"
                          value={newCompanyWebsite}
                          onChange={(e) => setNewCompanyWebsite(e.target.value)}
                          className="w-full border border-slate-300 rounded-xl px-3 py-2 text-xs focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none bg-white"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 mb-1">Company Description</label>
                      <input
                        type="text"
                        placeholder="Brief overview of the organization"
                        value={newCompanyDescription}
                        onChange={(e) => setNewCompanyDescription(e.target.value)}
                        className="w-full border border-slate-300 rounded-xl px-3 py-2 text-xs focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none bg-white"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Job Role */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Job Role *
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-2">
                  {availableRoles.map((role) => (
                    <button
                      key={role}
                      type="button"
                      onClick={() => {
                        setJobRole(role);
                        setCustomJobRole('');
                      }}
                      className={`text-left px-3 py-2 rounded-xl text-xs font-semibold border transition ${
                        jobRole === role
                          ? 'border-indigo-600 bg-indigo-50 text-indigo-900 shadow-sm'
                          : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                      }`}
                    >
                      {role}
                    </button>
                  ))}
                  <button
                    type="button"
                    onClick={() => setJobRole('OTHER')}
                    className={`text-left px-3 py-2 rounded-xl text-xs font-semibold border transition ${
                      jobRole === 'OTHER'
                        ? 'border-indigo-600 bg-indigo-50 text-indigo-900 shadow-sm'
                        : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    + Custom / Other Role
                  </button>
                </div>

                {jobRole === 'OTHER' && (
                  <input
                    type="text"
                    placeholder="Enter custom job role (e.g. Embedded Firmware Engineer)"
                    value={customJobRole}
                    onChange={(e) => setCustomJobRole(e.target.value)}
                    className="w-full border border-slate-300 rounded-xl px-3.5 py-2 text-xs sm:text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none"
                  />
                )}
              </div>

              {/* Drive Title */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Drive Title *
                </label>
                <input
                  type="text"
                  value={driveTitle}
                  onChange={(e) => setDriveTitle(e.target.value)}
                  placeholder="e.g. Accenture — Associate Software Engineer 2027"
                  className="w-full border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs sm:text-sm font-semibold focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none shadow-sm"
                />
              </div>

              {/* Location */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Work Location
                </label>
                <input
                  type="text"
                  value={jobLocation}
                  onChange={(e) => setJobLocation(e.target.value)}
                  placeholder="e.g. Bengaluru / Chennai / Hyderabad (Hybrid)"
                  className="w-full border border-slate-300 rounded-xl px-3.5 py-2 text-xs sm:text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none shadow-sm"
                />
              </div>

              {/* Job Description */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Job Description & Overview
                </label>
                <textarea
                  rows={3}
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Describe key responsibilities, requirements, and hiring details..."
                  className="w-full border border-slate-300 rounded-xl px-3.5 py-2 text-xs sm:text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none resize-none shadow-sm"
                />
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* STEP 2: COMPENSATION & DETAILS                                            */}
          {/* ========================================================================= */}
          {currentStep === 2 && (
            <div className="space-y-4 animate-fade-in">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                    Annual CTC (in Lakhs INR / LPA)
                  </label>
                  <div className="relative">
                    <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slate-400 font-bold text-xs">₹</span>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      placeholder="e.g. 4.5"
                      value={ctcLpa}
                      onChange={(e) => setCtcLpa(e.target.value)}
                      className="w-full pl-8 pr-3.5 py-2.5 border border-slate-300 rounded-xl text-xs sm:text-sm font-bold text-emerald-800 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none shadow-sm"
                    />
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">E.g., 4.5 represents ₹4,50,000 per annum</p>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                    Monthly Internship Stipend (Optional)
                  </label>
                  <div className="relative">
                    <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slate-400 font-bold text-xs">₹</span>
                    <input
                      type="number"
                      step="1000"
                      min="0"
                      placeholder="e.g. 25000"
                      value={stipendMonthly}
                      onChange={(e) => setStipendMonthly(e.target.value)}
                      className="w-full pl-8 pr-3.5 py-2.5 border border-slate-300 rounded-xl text-xs sm:text-sm font-medium focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none shadow-sm"
                    />
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">Leave blank if no internship / direct full-time</p>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Service Agreement / Bond Terms
                </label>
                <textarea
                  rows={2}
                  value={bondDetails}
                  onChange={(e) => setBondDetails(e.target.value)}
                  placeholder="e.g. 1 year service agreement, or None"
                  className="w-full border border-slate-300 rounded-xl px-3.5 py-2 text-xs sm:text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none resize-none shadow-sm"
                />
              </div>

              <div className="p-4 bg-indigo-50/50 border border-indigo-100 rounded-2xl">
                <div className="flex items-start space-x-2.5">
                  <svg className="w-5 h-5 text-indigo-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="text-xs text-indigo-900">
                    <span className="font-bold">Transparent Candidate Packages</span>
                    <p className="text-indigo-700 mt-0.5">
                      Compensation details will be displayed clearly on student cards and drive detail views to ensure high application engagement.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* STEP 3: ELIGIBILITY CRITERIA                                              */}
          {/* ========================================================================= */}
          {currentStep === 3 && (
            <div className="space-y-4 animate-fade-in">
              <div className="p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-900 rounded-2xl text-xs flex items-start space-x-2">
                <svg className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <span className="font-bold">Authoritative Placement Eligibility Engine</span>
                  <p className="text-emerald-700 mt-0.5">
                    CampusFlow automatically validates every student’s academic profile against these rules. Students who meet all criteria are marked eligible instantly.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                    Minimum CGPA (0.00 – 10.00)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="10"
                    value={minCgpa}
                    onChange={(e) => setMinCgpa(e.target.value)}
                    className="w-full border border-slate-300 rounded-xl px-3.5 py-2 text-xs sm:text-sm font-semibold focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none shadow-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                    Maximum Active Backlogs Allowed
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={maxBacklogs}
                    onChange={(e) => setMaxBacklogs(e.target.value)}
                    className="w-full border border-slate-300 rounded-xl px-3.5 py-2 text-xs sm:text-sm font-semibold focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none shadow-sm"
                  />
                </div>
              </div>

              {/* Eligible Branches */}
              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                    Eligible Academic Departments / Branches *
                  </label>
                  <button
                    type="button"
                    onClick={() =>
                      setSelectedBranches(
                        selectedBranches.length === availableBranches.length ? [] : [...availableBranches]
                      )
                    }
                    className="text-[11px] font-bold text-indigo-600 hover:text-indigo-800"
                  >
                    {selectedBranches.length === availableBranches.length ? 'Deselect All' : 'Select All'}
                  </button>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {availableBranches.map((branch) => {
                    const isSelected = selectedBranches.includes(branch);
                    return (
                      <button
                        key={branch}
                        type="button"
                        onClick={() => toggleBranch(branch)}
                        className={`flex items-center space-x-2 px-3 py-2 rounded-xl text-xs font-semibold border transition ${
                          isSelected
                            ? 'border-indigo-600 bg-indigo-50 text-indigo-900 shadow-sm'
                            : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        <span
                          className={`w-3.5 h-3.5 rounded flex items-center justify-center border text-[10px] ${
                            isSelected
                              ? 'bg-indigo-600 border-indigo-600 text-white'
                              : 'border-slate-300 bg-white'
                          }`}
                        >
                          {isSelected ? '✓' : ''}
                        </span>
                        <span>{branch}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Eligible Batch Years */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Eligible Graduation Batch Years *
                </label>
                <div className="flex flex-wrap gap-2">
                  {[2025, 2026, 2027, 2028].map((year) => {
                    const isSelected = selectedBatchYears.includes(year);
                    return (
                      <button
                        key={year}
                        type="button"
                        onClick={() => toggleBatchYear(year)}
                        className={`px-3.5 py-1.5 rounded-xl text-xs font-bold border transition ${
                          isSelected
                            ? 'border-indigo-600 bg-indigo-600 text-white shadow-sm'
                            : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                        }`}
                      >
                        {year} Batch
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Gender Preference */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Gender Preference
                </label>
                <select
                  value={genderCriteria}
                  onChange={(e) => setGenderCriteria(e.target.value as any)}
                  className="w-full border border-slate-300 rounded-xl px-3.5 py-2 text-xs sm:text-sm font-medium focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none bg-white shadow-sm"
                >
                  <option value="">Any / All Genders Eligible</option>
                  <option value="FEMALE">Female Only (Diversity Drive)</option>
                  <option value="MALE">Male Only</option>
                </select>
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* STEP 4: REGISTRATION & SELECTION STAGES                                   */}
          {/* ========================================================================= */}
          {currentStep === 4 && (
            <div className="space-y-4 animate-fade-in">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Application & Registration Deadline *
                </label>
                <input
                  type="datetime-local"
                  value={registrationDeadline}
                  onChange={(e) => setRegistrationDeadline(e.target.value)}
                  className="w-full border border-slate-300 rounded-xl px-3.5 py-2 text-xs sm:text-sm font-medium focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none shadow-sm"
                />
                <p className="text-[11px] text-slate-400 mt-1">
                  Students will not be able to submit applications after this timestamp.
                </p>
              </div>

              {/* Selection Process Stages */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                      Selection Process Stages ({stages.length})
                    </h4>
                    <p className="text-[11px] text-slate-400">
                      Define the sequential rounds candidates will undergo.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={handleAddStage}
                    className="text-xs font-bold text-indigo-600 hover:text-indigo-800 transition"
                  >
                    + Add Round
                  </button>
                </div>

                <div className="space-y-3">
                  {stages.map((stage, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 bg-slate-50 border border-slate-200 rounded-2xl space-y-2.5 relative group"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <span className="w-5 h-5 rounded-full bg-slate-900 text-white text-[10px] font-extrabold flex items-center justify-center">
                            {stage.sequence_order}
                          </span>
                          <span className="text-xs font-bold text-slate-900">Round {stage.sequence_order}</span>
                        </div>

                        {stages.length > 1 && (
                          <button
                            type="button"
                            onClick={() => handleRemoveStage(idx)}
                            className="text-slate-400 hover:text-rose-600 text-xs transition"
                            title="Remove this round"
                          >
                            Remove
                          </button>
                        )}
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        <div>
                          <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">
                            Round Name
                          </label>
                          <input
                            type="text"
                            value={stage.name}
                            onChange={(e) => handleStageChange(idx, 'name', e.target.value)}
                            placeholder="e.g. Technical Interview"
                            className="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs bg-white focus:ring-1 focus:ring-indigo-500 outline-none"
                          />
                        </div>

                        <div>
                          <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">
                            Stage Type
                          </label>
                          <select
                            value={stage.stage_type}
                            onChange={(e) => handleStageChange(idx, 'stage_type', e.target.value as StageType)}
                            className="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs bg-white focus:ring-1 focus:ring-indigo-500 outline-none"
                          >
                            <option value="APTITUDE">Aptitude Test</option>
                            <option value="CODING">Coding Assessment</option>
                            <option value="TECHNICAL">Technical Interview</option>
                            <option value="HR">HR Interview</option>
                            <option value="GD">Group Discussion</option>
                            <option value="OTHER">Other / Miscellaneous</option>
                          </select>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        <div>
                          <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">
                            Location / Platform
                          </label>
                          <input
                            type="text"
                            value={stage.location_or_link || ''}
                            onChange={(e) => handleStageChange(idx, 'location_or_link', e.target.value)}
                            placeholder="e.g. Online Platform / Seminar Hall"
                            className="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs bg-white focus:ring-1 focus:ring-indigo-500 outline-none"
                          />
                        </div>

                        <div>
                          <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">
                            Instructions for Students
                          </label>
                          <input
                            type="text"
                            value={stage.instructions || ''}
                            onChange={(e) => handleStageChange(idx, 'instructions', e.target.value)}
                            placeholder="e.g. Keep resume and college ID ready"
                            className="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs bg-white focus:ring-1 focus:ring-indigo-500 outline-none"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* STEP 5: PREVIEW & PUBLISH                                                 */}
          {/* ========================================================================= */}
          {currentStep === 5 && (
            <div className="space-y-4 animate-fade-in">
              <div className="p-3.5 bg-indigo-50 border border-indigo-200 rounded-2xl text-xs text-indigo-900">
                <span className="font-bold">Student View Preview</span>
                <p className="text-indigo-700 mt-0.5">
                  Review the recruitment drive card below. Once published, it will be visible to eligible candidates immediately.
                </p>
              </div>

              {/* Preview Card */}
              <div className="bg-white border-2 border-indigo-100 rounded-2xl p-5 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-100">
                    PUBLISHED
                  </span>
                  <span className="text-[11px] text-amber-700 font-semibold bg-amber-50 px-2 py-0.5 rounded-md">
                    Deadline: {new Date(registrationDeadline).toLocaleDateString()}
                  </span>
                </div>

                <div className="flex items-start space-x-3">
                  <div className="w-12 h-12 rounded-2xl bg-slate-900 text-white flex items-center justify-center font-extrabold text-base flex-shrink-0">
                    {(getCompanyName() || 'C').charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-900">{getCompanyName()}</h3>
                    <p className="text-xs font-semibold text-indigo-600">{getEffectiveRole()}</p>
                    {jobLocation && <p className="text-[11px] text-slate-400 mt-0.5">{jobLocation}</p>}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs py-2 px-3 bg-slate-50 rounded-xl">
                  <div>
                    <span className="text-slate-400 text-[10px] block font-bold uppercase">Compensation</span>
                    <span className="font-bold text-emerald-700">{ctcLpa ? `₹${ctcLpa} LPA` : 'Disclosed Later'}</span>
                  </div>
                  {stipendMonthly && (
                    <div>
                      <span className="text-slate-400 text-[10px] block font-bold uppercase">Stipend</span>
                      <span className="font-medium text-slate-800">₹{Number(stipendMonthly).toLocaleString()}/mo</span>
                    </div>
                  )}
                </div>

                {/* Eligibility Summary */}
                <div className="text-xs space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Eligibility</span>
                  <div className="flex flex-wrap gap-1.5">
                    <span className="px-2 py-0.5 bg-slate-100 rounded text-slate-700 text-[11px] font-medium">
                      CGPA ≥ {minCgpa || '0'}
                    </span>
                    <span className="px-2 py-0.5 bg-slate-100 rounded text-slate-700 text-[11px] font-medium">
                      Backlogs ≤ {maxBacklogs || '0'}
                    </span>
                    <span className="px-2 py-0.5 bg-slate-100 rounded text-slate-700 text-[11px] font-medium">
                      Branches: {selectedBranches.join(', ')}
                    </span>
                    <span className="px-2 py-0.5 bg-slate-100 rounded text-slate-700 text-[11px] font-medium">
                      Batches: {selectedBatchYears.join(', ')}
                    </span>
                  </div>
                </div>

                {/* Stages Sequence */}
                <div className="text-xs space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                    Selection Process ({stages.length} Rounds)
                  </span>
                  <div className="flex items-center space-x-1.5 overflow-x-auto py-1">
                    {stages.map((st, i) => (
                      <React.Fragment key={i}>
                        <span className="px-2 py-1 rounded-lg bg-indigo-50 border border-indigo-100 text-indigo-900 text-[11px] font-semibold whitespace-nowrap">
                          {st.sequence_order}. {st.name}
                        </span>
                        {i < stages.length - 1 && <span className="text-slate-300 text-xs">&rarr;</span>}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="border-t border-slate-100 pt-4 mt-4 flex items-center justify-between flex-shrink-0">
          <div>
            {currentStep > 1 && (
              <button
                type="button"
                onClick={handleBack}
                disabled={isSubmitting}
                className="px-4 py-2 text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition"
              >
                &larr; Back
              </button>
            )}
          </div>

          <div className="flex items-center space-x-2.5">
            <button
              type="button"
              onClick={handleRequestClose}
              disabled={isSubmitting}
              className="px-4 py-2 text-xs font-bold text-slate-500 hover:text-slate-700 transition"
            >
              Cancel
            </button>

            {currentStep < 5 ? (
              <button
                type="button"
                onClick={handleNext}
                className="px-5 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-md shadow-indigo-600/20 transition"
              >
                Continue &rarr;
              </button>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => executeDriveCreation(false)}
                  disabled={isSubmitting}
                  className="px-4 py-2 text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition"
                >
                  {isSubmitting ? 'Saving...' : 'Save Draft'}
                </button>

                <button
                  type="button"
                  onClick={() => executeDriveCreation(true)}
                  disabled={isSubmitting}
                  className="px-5 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-md shadow-emerald-600/20 transition flex items-center space-x-1.5"
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Publishing...</span>
                    </>
                  ) : (
                    <span>Publish Drive Now</span>
                  )}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
