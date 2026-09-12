import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';
import { apiClient } from '../services/apiClient';

interface ProfileData {
  id?: string;
  user_id?: string;
  roll_number?: string;
  branch_code?: string;
  batch_year?: number;
  cgpa?: number;
  active_backlogs?: number;
  phone_number?: string | null;
  personal_email?: string | null;
  gender?: string | null;
  section?: string | null;
  tenth_mark?: number | null;
  twelfth_mark?: number | null;
  diploma_mark?: number | null;
  portfolio_url?: string | null;
  resume_gcs_path?: string | null;
  resume_uploaded_at?: string | null;
  avatar_gcs_path?: string | null;
}

export const MyProfilePage: React.FC = () => {
  const { user } = useAuthStore();
  const location = useLocation();
  const resumeSectionRef = useRef<HTMLDivElement>(null);

  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // SECTION 1: Personal details edit state
  const [isEditingPersonal, setIsEditingPersonal] = useState(false);
  const [phone, setPhone] = useState('');
  const [personalEmail, setPersonalEmail] = useState('');
  const [gender, setGender] = useState('');
  const [savingPersonal, setSavingPersonal] = useState(false);
  const [personalMessage, setPersonalMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // SECTION 2: Academic details edit state
  const [isEditingAcademic, setIsEditingAcademic] = useState(false);
  const [section, setSection] = useState('');
  const [tenthMark, setTenthMark] = useState('');
  const [twelfthMark, setTwelfthMark] = useState('');
  const [diplomaMark, setDiplomaMark] = useState('');
  const [savingAcademic, setSavingAcademic] = useState(false);
  const [academicMessage, setAcademicMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // SECTION 3: Resume & Portfolio state
  const [isEditingPortfolio, setIsEditingPortfolio] = useState(false);
  const [portfolioUrl, setPortfolioUrl] = useState('');
  const [savingPortfolio, setSavingPortfolio] = useState(false);
  const [portfolioMessage, setPortfolioMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Resume upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadingResume, setUploadingResume] = useState(false);
  const [resumeMessage, setResumeMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [downloadingResume, setDownloadingResume] = useState(false);

  const populateFormFields = (data: ProfileData) => {
    setPhone(data.phone_number || '');
    setPersonalEmail(data.personal_email || '');
    setGender(data.gender || '');
    setSection(data.section || '');
    setTenthMark(data.tenth_mark !== null && data.tenth_mark !== undefined ? String(data.tenth_mark) : '');
    setTwelfthMark(data.twelfth_mark !== null && data.twelfth_mark !== undefined ? String(data.twelfth_mark) : '');
    setDiplomaMark(data.diploma_mark !== null && data.diploma_mark !== undefined ? String(data.diploma_mark) : '');
    setPortfolioUrl(data.portfolio_url || '');
  };

  const fetchProfile = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get('/students/me');
      setProfile(res.data);
      populateFormFields(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load profile data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  useEffect(() => {
    // If navigated to /resume or hash is #resume, scroll to resume section
    if (location.pathname === '/resume' || location.hash === '#resume') {
      setTimeout(() => {
        resumeSectionRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 300);
    }
  }, [location.pathname, location.hash, loading]);

  // Handle Personal Details Save
  const handleSavePersonal = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingPersonal(true);
    setPersonalMessage(null);
    try {
      const res = await apiClient.patch('/students/me', {
        phone_number: phone.trim() || null,
        personal_email: personalEmail.trim() || null,
        gender: gender || null,
      });
      setProfile(res.data);
      populateFormFields(res.data);
      setIsEditingPersonal(false);
      setPersonalMessage({ type: 'success', text: 'Personal details updated successfully.' });
      setTimeout(() => setPersonalMessage(null), 4000);
    } catch (err: any) {
      setPersonalMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to update personal details.',
      });
    } finally {
      setSavingPersonal(false);
    }
  };

  const handleCancelPersonal = () => {
    if (profile) {
      setPhone(profile.phone_number || '');
      setPersonalEmail(profile.personal_email || '');
      setGender(profile.gender || '');
    }
    setIsEditingPersonal(false);
    setPersonalMessage(null);
  };

  // Handle Academic Details Save
  const handleSaveAcademic = async (e: React.FormEvent) => {
    e.preventDefault();
    setAcademicMessage(null);

    // Client-side range validation
    const validateMark = (val: string, name: string): number | null | false => {
      if (!val.trim()) return null;
      const num = parseFloat(val);
      if (isNaN(num) || num < 0 || num > 100) {
        setAcademicMessage({
          type: 'error',
          text: `${name} must be a valid percentage between 0 and 100.`,
        });
        return false;
      }
      return num;
    };

    const tenth = validateMark(tenthMark, '10th / SSLC Mark');
    if (tenth === false) return;

    const twelfth = validateMark(twelfthMark, '12th / Intermediate Mark');
    if (twelfth === false) return;

    const diploma = validateMark(diplomaMark, 'Diploma Mark');
    if (diploma === false) return;

    setSavingAcademic(true);
    try {
      const res = await apiClient.patch('/students/me', {
        section: section.trim() || null,
        tenth_mark: tenth,
        twelfth_mark: twelfth,
        diploma_mark: diploma,
      });
      setProfile(res.data);
      populateFormFields(res.data);
      setIsEditingAcademic(false);
      setAcademicMessage({ type: 'success', text: 'Academic details updated successfully.' });
      setTimeout(() => setAcademicMessage(null), 4000);
    } catch (err: any) {
      setAcademicMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to update academic details.',
      });
    } finally {
      setSavingAcademic(false);
    }
  };

  const handleCancelAcademic = () => {
    if (profile) {
      setSection(profile.section || '');
      setTenthMark(profile.tenth_mark !== null && profile.tenth_mark !== undefined ? String(profile.tenth_mark) : '');
      setTwelfthMark(profile.twelfth_mark !== null && profile.twelfth_mark !== undefined ? String(profile.twelfth_mark) : '');
      setDiplomaMark(profile.diploma_mark !== null && profile.diploma_mark !== undefined ? String(profile.diploma_mark) : '');
    }
    setIsEditingAcademic(false);
    setAcademicMessage(null);
  };

  // Handle Portfolio URL Save
  const handleSavePortfolio = async (e: React.FormEvent) => {
    e.preventDefault();
    setPortfolioMessage(null);

    const trimmedUrl = portfolioUrl.trim();
    if (trimmedUrl) {
      try {
        const parsed = new URL(trimmedUrl);
        if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
          throw new Error('Must start with http:// or https://');
        }
      } catch {
        setPortfolioMessage({
          type: 'error',
          text: 'Please enter a valid HTTP or HTTPS portfolio URL (e.g. https://github.com/yourname).',
        });
        return;
      }
    }

    setSavingPortfolio(true);
    try {
      const res = await apiClient.patch('/students/me', {
        portfolio_url: trimmedUrl || null,
      });
      setProfile(res.data);
      populateFormFields(res.data);
      setIsEditingPortfolio(false);
      setPortfolioMessage({ type: 'success', text: 'Portfolio link updated successfully.' });
      setTimeout(() => setPortfolioMessage(null), 4000);
    } catch (err: any) {
      setPortfolioMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to update portfolio link.',
      });
    } finally {
      setSavingPortfolio(false);
    }
  };

  const handleCancelPortfolio = () => {
    if (profile) {
      setPortfolioUrl(profile.portfolio_url || '');
    }
    setIsEditingPortfolio(false);
    setPortfolioMessage(null);
  };

  // Resume Upload Handlers
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.type !== 'application/pdf') {
        setResumeMessage({ type: 'error', text: 'Only PDF documents are accepted.' });
        return;
      }
      if (file.size > 5 * 1024 * 1024) {
        setResumeMessage({ type: 'error', text: 'File size must be under 5MB.' });
        return;
      }
      setSelectedFile(file);
      setResumeMessage(null);
    }
  };

  const handleUploadResume = async () => {
    if (!selectedFile) return;
    setUploadingResume(true);
    setResumeMessage(null);

    try {
      const urlRes = await apiClient.get('/students/me/resume-upload-url');
      const { upload_url, object_path } = urlRes.data;

      await axios.put(upload_url, selectedFile, {
        headers: {
          'Content-Type': 'application/pdf',
        },
      });

      const confirmRes = await apiClient.post('/students/me/resume-confirm', {
        object_path,
      });

      setProfile(confirmRes.data);
      setSelectedFile(null);
      setResumeMessage({ type: 'success', text: 'Resume uploaded and verified successfully!' });
      setTimeout(() => setResumeMessage(null), 5000);
    } catch (err: any) {
      setResumeMessage({
        type: 'error',
        text: err.response?.data?.detail || err.message || 'Failed to upload resume. Please try again.',
      });
    } finally {
      setUploadingResume(false);
    }
  };

  const handleDownloadResume = async () => {
    setDownloadingResume(true);
    try {
      const res = await apiClient.get('/students/me/resume-download-url');
      if (res.data.url) {
        window.open(res.data.url, '_blank', 'noopener,noreferrer');
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || 'No resume available to download.');
    } finally {
      setDownloadingResume(false);
    }
  };

  const formatPercentage = (mark?: number | null) => {
    if (mark === null || mark === undefined) {
      return 'Not Applicable';
    }
    return `${Number(mark).toFixed(2)}%`;
  };

  return (
    <div className="space-y-8 animate-fade-in max-w-5xl mx-auto">
      {/* PAGE HEADER */}
      <div className="border-b border-slate-200 pb-5">
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
          My Profile & Career Credentials
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Manage your personal contact details, review institutional academic credentials, and maintain your verified resume & portfolio.
        </p>
      </div>

      {loading ? (
        <div className="p-12 text-center bg-white rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-indigo-500 border-t-transparent mb-3" />
          <p className="text-xs text-slate-500 font-medium">Loading profile information...</p>
        </div>
      ) : error ? (
        <div className="p-6 bg-red-50 border border-red-200 rounded-2xl text-center">
          <p className="text-xs text-red-700 font-semibold">{error}</p>
        </div>
      ) : (
        <div className="space-y-8">
          {/* USER SUMMARY CARD */}
          <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-2xl p-6 text-white shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-center space-x-4">
              <div className="w-16 h-16 rounded-2xl bg-indigo-600 text-white flex items-center justify-center font-extrabold text-2xl shadow-md shadow-indigo-600/30 border border-indigo-400/30">
                {user?.full_name?.charAt(0).toUpperCase() || 'S'}
              </div>
              <div>
                <div className="flex items-center space-x-2.5">
                  <h2 className="text-lg font-bold text-white">{user?.full_name}</h2>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                    Student
                  </span>
                </div>
                <p className="text-xs text-slate-300 font-mono mt-0.5">{user?.email}</p>
                <p className="text-xs text-indigo-300 mt-1">
                  Roll No: <span className="font-mono font-bold text-white">{profile?.roll_number || '—'}</span> &bull; {profile?.branch_code || '—'} &bull; Batch of {profile?.batch_year || '—'}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-3 bg-white/5 border border-white/10 p-3 rounded-xl backdrop-blur-sm self-start md:self-auto">
              <div className="text-center px-3 border-r border-white/10">
                <div className="text-[10px] font-bold uppercase text-slate-400">CGPA</div>
                <div className="text-base font-extrabold text-emerald-400 mt-0.5">
                  {profile?.cgpa !== undefined ? profile.cgpa.toFixed(2) : '—'}
                </div>
              </div>
              <div className="text-center px-3 border-r border-white/10">
                <div className="text-[10px] font-bold uppercase text-slate-400">Backlogs</div>
                <div className="text-base font-extrabold text-slate-200 mt-0.5">
                  {profile?.active_backlogs ?? 0}
                </div>
              </div>
              <div className="text-center px-3">
                <div className="text-[10px] font-bold uppercase text-slate-400">Section</div>
                <div className="text-base font-extrabold text-indigo-300 mt-0.5">
                  {profile?.section || 'Not Set'}
                </div>
              </div>
            </div>
          </div>

          {/* ========================================================================= */}
          {/* SECTION 1: PERSONAL DETAILS                                               */}
          {/* ========================================================================= */}
          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-slate-900">Personal Details</h2>
                <p className="text-xs text-slate-500">Contact information and basic profile details</p>
              </div>
              {!isEditingPersonal ? (
                <button
                  type="button"
                  onClick={() => setIsEditingPersonal(true)}
                  className="px-4 py-1.5 bg-white border border-slate-300 hover:border-indigo-400 hover:text-indigo-600 text-slate-700 text-xs font-bold rounded-xl transition shadow-sm flex items-center space-x-1.5"
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                  <span>Edit Personal Details</span>
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleCancelPersonal}
                  className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs font-semibold rounded-xl transition"
                >
                  Cancel
                </button>
              )}
            </div>

            <form onSubmit={handleSavePersonal} className="p-6 space-y-6">
              {personalMessage && (
                <div
                  className={`p-3 rounded-xl text-xs font-semibold flex items-center space-x-2 ${
                    personalMessage.type === 'success'
                      ? 'bg-emerald-50 border border-emerald-200 text-emerald-800'
                      : 'bg-rose-50 border border-rose-200 text-rose-800'
                  }`}
                >
                  <span>{personalMessage.text}</span>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                {/* Full Name — Institutional */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                      Full Name
                    </label>
                    <span className="text-[10px] text-slate-400 font-medium">Read-Only</span>
                  </div>
                  <input
                    type="text"
                    disabled
                    value={user?.full_name || ''}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-700 text-xs font-semibold cursor-not-allowed"
                  />
                </div>

                {/* University Email — Institutional */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                      University Email
                    </label>
                    <span className="text-[10px] text-slate-400 font-medium">Read-Only</span>
                  </div>
                  <input
                    type="email"
                    disabled
                    value={user?.email || ''}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-700 text-xs font-mono cursor-not-allowed"
                  />
                </div>

                {/* Personal Email — Student Editable */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                      Personal Email
                    </label>
                    <span className="text-[10px] text-indigo-600 font-medium">Student-Managed</span>
                  </div>
                  <input
                    type="email"
                    placeholder="student.personal@example.com"
                    disabled={!isEditingPersonal}
                    value={personalEmail}
                    onChange={(e) => setPersonalEmail(e.target.value)}
                    className={`w-full px-3.5 py-2.5 rounded-xl border text-xs outline-none transition ${
                      isEditingPersonal
                        ? 'border-slate-300 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-500/20 text-slate-900 bg-white'
                        : 'border-slate-200 bg-slate-50/70 text-slate-700 cursor-default'
                    }`}
                  />
                </div>

                {/* Phone Number — Student Editable */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                      Phone Number
                    </label>
                    <span className="text-[10px] text-indigo-600 font-medium">Student-Managed</span>
                  </div>
                  <input
                    type="tel"
                    placeholder="+91 9876543210"
                    disabled={!isEditingPersonal}
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className={`w-full px-3.5 py-2.5 rounded-xl border text-xs outline-none transition ${
                      isEditingPersonal
                        ? 'border-slate-300 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-500/20 text-slate-900 bg-white'
                        : 'border-slate-200 bg-slate-50/70 text-slate-700 cursor-default'
                    }`}
                  />
                </div>

                {/* Gender — Student Editable */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                      Gender
                    </label>
                    <span className="text-[10px] text-indigo-600 font-medium">Student-Managed</span>
                  </div>
                  <select
                    disabled={!isEditingPersonal}
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                    className={`w-full px-3.5 py-2.5 rounded-xl border text-xs outline-none transition ${
                      isEditingPersonal
                        ? 'border-slate-300 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-500/20 text-slate-900 bg-white'
                        : 'border-slate-200 bg-slate-50/70 text-slate-700 cursor-default'
                    }`}
                  >
                    <option value="">Not Specified</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                    <option value="Prefer not to say">Prefer not to say</option>
                  </select>
                </div>
              </div>

              {isEditingPersonal && (
                <div className="flex justify-end space-x-3 pt-2 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={handleCancelPersonal}
                    className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={savingPersonal}
                    className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-sm transition"
                  >
                    {savingPersonal ? 'Saving...' : 'Save Personal Details'}
                  </button>
                </div>
              )}
            </form>
          </div>

          {/* ========================================================================= */}
          {/* SECTION 2: ACADEMIC DETAILS                                               */}
          {/* ========================================================================= */}
          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-slate-900">Academic Details</h2>
                <p className="text-xs text-slate-500">Official university credentials and self-reported educational marks</p>
              </div>
              {!isEditingAcademic ? (
                <button
                  type="button"
                  onClick={() => setIsEditingAcademic(true)}
                  className="px-4 py-1.5 bg-white border border-slate-300 hover:border-indigo-400 hover:text-indigo-600 text-slate-700 text-xs font-bold rounded-xl transition shadow-sm flex items-center space-x-1.5"
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                  <span>Edit Academic Details</span>
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleCancelAcademic}
                  className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs font-semibold rounded-xl transition"
                >
                  Cancel
                </button>
              )}
            </div>

            <div className="p-6 space-y-6">
              {academicMessage && (
                <div
                  className={`p-3 rounded-xl text-xs font-semibold flex items-center space-x-2 ${
                    academicMessage.type === 'success'
                      ? 'bg-emerald-50 border border-emerald-200 text-emerald-800'
                      : 'bg-rose-50 border border-rose-200 text-rose-800'
                  }`}
                >
                  <span>{academicMessage.text}</span>
                </div>
              )}

              {/* Institutional Read-Only Highlights */}
              <div>
                <div className="flex items-center space-x-2 mb-3">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                    Institutional Verified Records
                  </span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
                    Read-Only &bull; Verified by TPO
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3.5">
                  <div className="p-3.5 bg-slate-50 border border-slate-200/70 rounded-xl text-center">
                    <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Roll Number</div>
                    <div className="text-xs font-bold text-slate-900 font-mono mt-1">
                      {profile?.roll_number || '—'}
                    </div>
                  </div>

                  <div className="p-3.5 bg-slate-50 border border-slate-200/70 rounded-xl text-center">
                    <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Department</div>
                    <div className="text-xs font-bold text-indigo-700 mt-1">
                      {profile?.branch_code || '—'}
                    </div>
                  </div>

                  <div className="p-3.5 bg-slate-50 border border-slate-200/70 rounded-xl text-center">
                    <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Batch Year</div>
                    <div className="text-xs font-bold text-slate-900 mt-1">
                      {profile?.batch_year || '—'}
                    </div>
                  </div>

                  <div className="p-3.5 bg-slate-50 border border-slate-200/70 rounded-xl text-center">
                    <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Cumulative CGPA</div>
                    <div className="text-xs font-bold text-emerald-700 mt-1">
                      {profile?.cgpa !== undefined ? profile.cgpa.toFixed(2) : '—'}
                    </div>
                  </div>

                  <div className="p-3.5 bg-slate-50 border border-slate-200/70 rounded-xl text-center">
                    <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Active Backlogs</div>
                    <div className="text-xs font-bold text-slate-900 mt-1">
                      {profile?.active_backlogs ?? 0}
                    </div>
                  </div>
                </div>
              </div>

              {/* Student-Managed Academic Fields */}
              <form onSubmit={handleSaveAcademic} className="space-y-5 pt-2 border-t border-slate-100">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                    Student-Managed Academic Details
                  </span>
                  <span className="text-[10px] font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full border border-indigo-100">
                    Self-Editable
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  {/* Section */}
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                      Section
                    </label>
                    {isEditingAcademic ? (
                      <input
                        type="text"
                        maxLength={10}
                        placeholder="e.g. A, B, C"
                        value={section}
                        onChange={(e) => setSection(e.target.value)}
                        className="w-full px-3.5 py-2 rounded-xl border border-slate-300 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-500/20 text-xs text-slate-900 outline-none transition bg-white"
                      />
                    ) : (
                      <div className="px-3.5 py-2 rounded-xl bg-slate-50 border border-slate-200/70 text-xs font-bold text-slate-800">
                        {profile?.section || 'Not Set'}
                      </div>
                    )}
                  </div>

                  {/* 10th / SSLC Mark */}
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                      10th / SSLC Mark (%)
                    </label>
                    {isEditingAcademic ? (
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        max="100"
                        placeholder="e.g. 92.50"
                        value={tenthMark}
                        onChange={(e) => setTenthMark(e.target.value)}
                        className="w-full px-3.5 py-2 rounded-xl border border-slate-300 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-500/20 text-xs text-slate-900 outline-none transition bg-white"
                      />
                    ) : (
                      <div className="px-3.5 py-2 rounded-xl bg-slate-50 border border-slate-200/70 text-xs font-bold text-slate-800">
                        {formatPercentage(profile?.tenth_mark)}
                      </div>
                    )}
                  </div>

                  {/* 12th / Intermediate Mark */}
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                      12th / Inter Mark (%)
                    </label>
                    {isEditingAcademic ? (
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        max="100"
                        placeholder="e.g. 88.00 (Optional)"
                        value={twelfthMark}
                        onChange={(e) => setTwelfthMark(e.target.value)}
                        className="w-full px-3.5 py-2 rounded-xl border border-slate-300 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-500/20 text-xs text-slate-900 outline-none transition bg-white"
                      />
                    ) : (
                      <div className="px-3.5 py-2 rounded-xl bg-slate-50 border border-slate-200/70 text-xs font-bold text-slate-800">
                        {formatPercentage(profile?.twelfth_mark)}
                      </div>
                    )}
                  </div>

                  {/* Diploma Mark */}
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                      Diploma Mark (%)
                    </label>
                    {isEditingAcademic ? (
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        max="100"
                        placeholder="e.g. 82.00 (Optional)"
                        value={diplomaMark}
                        onChange={(e) => setDiplomaMark(e.target.value)}
                        className="w-full px-3.5 py-2 rounded-xl border border-slate-300 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-500/20 text-xs text-slate-900 outline-none transition bg-white"
                      />
                    ) : (
                      <div className="px-3.5 py-2 rounded-xl bg-slate-50 border border-slate-200/70 text-xs font-bold text-slate-800">
                        {formatPercentage(profile?.diploma_mark)}
                      </div>
                    )}
                  </div>
                </div>

                <p className="text-[11px] text-slate-400">
                  Note: Provide 12th/Intermediate or Diploma percentage based on your educational path. Unfilled fields display as "Not Applicable".
                </p>

                {isEditingAcademic && (
                  <div className="flex justify-end space-x-3 pt-2 border-t border-slate-100">
                    <button
                      type="button"
                      onClick={handleCancelAcademic}
                      className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={savingAcademic}
                      className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-sm transition"
                    >
                      {savingAcademic ? 'Saving...' : 'Save Academic Details'}
                    </button>
                  </div>
                )}
              </form>
            </div>
          </div>

          {/* ========================================================================= */}
          {/* SECTION 3: RESUME & PORTFOLIO                                             */}
          {/* ========================================================================= */}
          <div
            ref={resumeSectionRef}
            id="resume-section"
            className="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden"
          >
            <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-slate-900">Resume & Portfolio</h2>
                <p className="text-xs text-slate-500">Official recruitment credentials, PDF resume, and public professional links</p>
              </div>
              <span className="text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-100 px-2.5 py-1 rounded-lg">
                Recruitment Assets
              </span>
            </div>

            <div className="p-6 space-y-6">
              {/* SUBSECTION A: RESUME DOCUMENT */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                    Verified Resume Document
                  </span>
                  <span className="text-[10px] text-slate-500">PDF Format &bull; Max 5MB</span>
                </div>

                {resumeMessage && (
                  <div
                    className={`p-3 rounded-xl text-xs font-semibold flex items-center space-x-2 ${
                      resumeMessage.type === 'success'
                        ? 'bg-emerald-50 border border-emerald-200 text-emerald-800'
                        : 'bg-rose-50 border border-rose-200 text-rose-800'
                    }`}
                  >
                    <span>{resumeMessage.text}</span>
                  </div>
                )}

                {/* Status Card */}
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center font-bold flex-shrink-0">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <div>
                      <div className="text-xs font-bold text-slate-900">
                        {profile?.resume_gcs_path ? 'Official Resume Document on File' : 'No Resume Uploaded'}
                      </div>
                      <div className="text-[11px] text-slate-500 mt-0.5">
                        {profile?.resume_uploaded_at
                          ? `Last updated: ${new Date(profile.resume_uploaded_at).toLocaleString()}`
                          : 'Upload a PDF resume to complete placement drive eligibility'}
                      </div>
                    </div>
                  </div>

                  {profile?.resume_gcs_path && (
                    <button
                      type="button"
                      onClick={handleDownloadResume}
                      disabled={downloadingResume}
                      className="px-4 py-2 bg-white border border-slate-300 hover:bg-slate-100 text-slate-800 text-xs font-bold rounded-xl transition shadow-sm flex items-center space-x-1.5 self-start sm:self-auto"
                    >
                      <svg className="w-4 h-4 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      <span>{downloadingResume ? 'Loading...' : 'Download Resume PDF'}</span>
                    </button>
                  )}
                </div>

                {/* Upload File Input */}
                <div className="p-4 rounded-xl border border-slate-200 space-y-2">
                  <label className="block text-xs font-bold text-slate-700">
                    Upload or Replace Resume
                  </label>
                  <div className="flex flex-col sm:flex-row items-center gap-3">
                    <input
                      type="file"
                      accept="application/pdf"
                      onChange={handleFileChange}
                      className="w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 cursor-pointer"
                    />
                    <button
                      type="button"
                      onClick={handleUploadResume}
                      disabled={!selectedFile || uploadingResume}
                      className="w-full sm:w-auto px-5 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-bold rounded-xl shadow-sm transition whitespace-nowrap"
                    >
                      {uploadingResume ? 'Uploading...' : 'Confirm Upload'}
                    </button>
                  </div>
                </div>
              </div>

              {/* SUBSECTION B: PROFESSIONAL PORTFOLIO URL */}
              <div className="pt-5 border-t border-slate-100 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                      Professional Portfolio & Project Showcase
                    </span>
                    <p className="text-[11px] text-slate-400">Personal portfolio, GitHub profile, or LinkedIn link</p>
                  </div>
                  {!isEditingPortfolio ? (
                    <button
                      type="button"
                      onClick={() => setIsEditingPortfolio(true)}
                      className="px-3.5 py-1.5 bg-white border border-slate-300 hover:border-indigo-400 hover:text-indigo-600 text-slate-700 text-xs font-bold rounded-xl transition shadow-sm flex items-center space-x-1"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                      </svg>
                      <span>Edit Portfolio</span>
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={handleCancelPortfolio}
                      className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs font-semibold rounded-xl transition"
                    >
                      Cancel
                    </button>
                  )}
                </div>

                {portfolioMessage && (
                  <div
                    className={`p-3 rounded-xl text-xs font-semibold flex items-center space-x-2 ${
                      portfolioMessage.type === 'success'
                        ? 'bg-emerald-50 border border-emerald-200 text-emerald-800'
                        : 'bg-rose-50 border border-rose-200 text-rose-800'
                    }`}
                  >
                    <span>{portfolioMessage.text}</span>
                  </div>
                )}

                {!isEditingPortfolio ? (
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </div>
                      <div>
                        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Portfolio URL</div>
                        {profile?.portfolio_url ? (
                          <a
                            href={profile.portfolio_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 hover:underline flex items-center space-x-1 mt-0.5"
                          >
                            <span className="truncate max-w-md">{profile.portfolio_url}</span>
                            <svg className="w-3 h-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </a>
                        ) : (
                          <span className="text-xs text-slate-500 italic mt-0.5 block">Not Provided</span>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <form onSubmit={handleSavePortfolio} className="space-y-4">
                    <div>
                      <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                        Portfolio URL (GitHub, LinkedIn, Personal Site)
                      </label>
                      <input
                        type="url"
                        placeholder="https://github.com/yourusername or https://myportfolio.dev"
                        value={portfolioUrl}
                        onChange={(e) => setPortfolioUrl(e.target.value)}
                        className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-500/20 text-xs text-slate-900 outline-none transition bg-white font-mono"
                      />
                    </div>

                    <div className="flex justify-end space-x-3">
                      <button
                        type="button"
                        onClick={handleCancelPortfolio}
                        className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={savingPortfolio}
                        className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-sm transition"
                      >
                        {savingPortfolio ? 'Saving...' : 'Save Portfolio'}
                      </button>
                    </div>
                  </form>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
