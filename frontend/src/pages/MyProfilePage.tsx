import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';
import { apiClient } from '../services/apiClient';
import {
  PageHeader,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Badge,
  Button,
  Label,
  Alert,
  LoadingSpinner,
} from '../components/ui';

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
  user?: {
    id: string;
    email: string;
    full_name: string;
    role: string;
    is_active: boolean;
  } | null;
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
  const [fullName, setFullName] = useState('');
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
    setFullName(data.user?.full_name || user?.full_name || '');
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
      if (res.data.user) {
        useAuthStore.getState().updateUser({ full_name: res.data.user.full_name });
      }
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
    if (location.pathname === '/resume' || location.hash === '#resume-section' || location.hash === '#resume') {
      setTimeout(() => {
        resumeSectionRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 300);
    }
  }, [location.pathname, location.hash, loading]);

  // Handle Personal Details Save
  const handleSavePersonal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName.trim()) {
      setPersonalMessage({ type: 'error', text: 'Student name cannot be empty.' });
      return;
    }
    setSavingPersonal(true);
    setPersonalMessage(null);
    try {
      const res = await apiClient.patch('/students/me', {
        full_name: fullName.trim(),
        phone_number: phone.trim() || null,
        personal_email: personalEmail.trim() || null,
        gender: gender || null,
      });
      setProfile(res.data);
      if (res.data.user) {
        useAuthStore.getState().updateUser({ full_name: res.data.user.full_name });
      }
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
      setFullName(profile.user?.full_name || user?.full_name || '');
      setPhone(profile.phone_number || '');
      setPersonalEmail(profile.personal_email || '');
      setGender(profile.gender || '');
    } else if (user) {
      setFullName(user.full_name || '');
    }
    setIsEditingPersonal(false);
    setPersonalMessage(null);
  };

  // Handle Academic Details Save
  const handleSaveAcademic = async (e: React.FormEvent) => {
    e.preventDefault();
    setAcademicMessage(null);

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

      let targetUrl = upload_url;
      if (targetUrl.startsWith('/')) {
        const baseURL = (apiClient.defaults.baseURL || '').replace(/\/api\/v1\/?$/, '');
        targetUrl = `${baseURL}${targetUrl}`;
      }

      await axios.put(targetUrl, selectedFile, {
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
      let errorMsg = 'Failed to upload resume. Please try again.';
      if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail;
      } else if (err.message === 'Network Error' || err.code === 'ERR_NETWORK') {
        errorMsg = 'Network connection failed while uploading resume. Please check your connection and try again.';
      } else if (err.message) {
        errorMsg = err.message;
      }
      setResumeMessage({
        type: 'error',
        text: errorMsg,
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
        let downloadUrl = res.data.url;
        if (downloadUrl.startsWith('/')) {
          const baseURL = (apiClient.defaults.baseURL || '').replace(/\/api\/v1\/?$/, '');
          downloadUrl = `${baseURL}${downloadUrl}`;
        }
        window.open(downloadUrl, '_blank', 'noopener,noreferrer');
      }
    } catch (err: any) {
      setResumeMessage({
        type: 'error',
        text: err.response?.data?.detail || 'No resume available to download.',
      });
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
    <div className="space-y-8 animate-fade-in max-w-5xl mx-auto pb-12">
      {/* PAGE HEADER */}
      <PageHeader
        eyebrow="Placement Identity"
        title="My Profile & Career Credentials"
        description="Manage your personal contact details, review institutional academic credentials, and maintain your verified resume & portfolio."
      />

      {loading ? (
        <Card className="p-12 text-center">
          <LoadingSpinner size="lg" label="Loading profile information..." />
        </Card>
      ) : error ? (
        <Alert variant="danger">
          <span className="font-semibold">{error}</span>
        </Alert>
      ) : (
        <div className="space-y-8">
          {/* USER HERO / IDENTITY CARD */}
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 p-6 md:p-8 text-white shadow-xl border border-indigo-900/40">
            <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div className="flex items-center space-x-4">
                <div className="w-16 h-16 rounded-2xl bg-indigo-600 text-white flex items-center justify-center font-black text-2xl shadow-lg shadow-indigo-600/30 border border-indigo-400/30">
                  {user?.full_name?.charAt(0).toUpperCase() || 'S'}
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2.5">
                    <h2 className="text-xl font-bold text-white tracking-tight">{user?.full_name}</h2>
                    <Badge variant="success" size="sm" dot>
                      STUDENT
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-300 font-mono mt-1">{user?.email}</p>
                  <p className="text-xs text-indigo-200/90 mt-1 flex flex-wrap items-center gap-1.5 font-medium">
                    <span>Roll No: <strong className="font-mono text-white">{profile?.roll_number || '—'}</strong></span>
                    <span>&bull;</span>
                    <span>{profile?.branch_code || '—'}</span>
                    <span>&bull;</span>
                    <span>Batch of {profile?.batch_year || '—'}</span>
                  </p>
                </div>
              </div>

              {/* Stat Pills */}
              <div className="flex items-center space-x-3 bg-white/10 border border-white/15 p-3.5 rounded-2xl backdrop-blur-md self-start md:self-auto shadow-inner">
                <div className="text-center px-3.5 border-r border-white/10">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-indigo-200">CGPA</div>
                  <div className="text-lg font-black text-emerald-400 mt-0.5">
                    {profile?.cgpa !== undefined ? profile.cgpa.toFixed(2) : '—'}
                  </div>
                </div>
                <div className="text-center px-3.5 border-r border-white/10">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-indigo-200">Backlogs</div>
                  <div className="text-lg font-black text-slate-200 mt-0.5">
                    {profile?.active_backlogs ?? 0}
                  </div>
                </div>
                <div className="text-center px-3.5">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-indigo-200">Section</div>
                  <div className="text-lg font-black text-indigo-300 mt-0.5">
                    {profile?.section || 'Not Set'}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* ========================================================================= */}
          {/* SECTION 1: PERSONAL DETAILS                                               */}
          {/* ========================================================================= */}
          <Card>
            <CardHeader
              action={
                !isEditingPersonal ? (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsEditingPersonal(true)}
                    leftIcon={
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                      </svg>
                    }
                  >
                    Edit Personal Details
                  </Button>
                ) : (
                  <Button variant="ghost" size="sm" onClick={handleCancelPersonal}>
                    Cancel
                  </Button>
                )
              }
            >
              <CardTitle>Personal Details</CardTitle>
              <CardDescription>Contact information and student communication preferences</CardDescription>
            </CardHeader>

            <form onSubmit={handleSavePersonal}>
              <CardContent className="space-y-6">
                {personalMessage && (
                  <Alert variant={personalMessage.type === 'success' ? 'success' : 'danger'}>
                    {personalMessage.text}
                  </Alert>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  {/* Full Name — Student Editable */}
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <Label className="text-xs font-bold uppercase tracking-wider text-slate-700">
                        Full Name
                      </Label>
                      <Badge variant="primary" size="sm">Student-Managed</Badge>
                    </div>
                    <input
                      type="text"
                      id="student-full-name"
                      data-testid="input-student-name"
                      placeholder="Enter your full name"
                      disabled={!isEditingPersonal}
                      value={isEditingPersonal ? fullName : (profile?.user?.full_name || user?.full_name || fullName || '')}
                      onChange={(e) => setFullName(e.target.value)}
                      className={`w-full px-3.5 py-2.5 rounded-xl border text-xs outline-none transition font-medium ${
                        isEditingPersonal
                          ? 'border-slate-300 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-500/20 text-slate-900 bg-white shadow-xs'
                          : 'border-slate-200 bg-slate-50/70 text-slate-700 cursor-default'
                      }`}
                    />
                  </div>

                  {/* University Email — Institutional */}
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <Label className="text-xs font-bold uppercase tracking-wider text-slate-500">
                        University Email
                      </Label>
                      <Badge variant="neutral" size="sm">Read-Only</Badge>
                    </div>
                    <input
                      type="email"
                      disabled
                      value={user?.email || profile?.user?.email || ''}
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-600 text-xs font-mono cursor-not-allowed"
                    />
                  </div>

                  {/* Personal Email — Student Editable */}
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <Label className="text-xs font-bold uppercase tracking-wider text-slate-700">
                        Personal Email
                      </Label>
                      <Badge variant="primary" size="sm">Student-Managed</Badge>
                    </div>
                    <input
                      type="email"
                      placeholder="student.personal@example.com"
                      disabled={!isEditingPersonal}
                      value={personalEmail}
                      onChange={(e) => setPersonalEmail(e.target.value)}
                      className={`w-full px-3.5 py-2.5 rounded-xl border text-xs outline-none transition font-medium ${
                        isEditingPersonal
                          ? 'border-slate-300 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-500/20 text-slate-900 bg-white shadow-xs'
                          : 'border-slate-200 bg-slate-50/70 text-slate-700 cursor-default'
                      }`}
                    />
                  </div>

                  {/* Phone Number — Student Editable */}
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <Label className="text-xs font-bold uppercase tracking-wider text-slate-700">
                        Phone Number
                      </Label>
                      <Badge variant="primary" size="sm">Student-Managed</Badge>
                    </div>
                    <input
                      type="tel"
                      placeholder="+91 9876543210"
                      disabled={!isEditingPersonal}
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      className={`w-full px-3.5 py-2.5 rounded-xl border text-xs outline-none transition font-medium ${
                        isEditingPersonal
                          ? 'border-slate-300 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-500/20 text-slate-900 bg-white shadow-xs'
                          : 'border-slate-200 bg-slate-50/70 text-slate-700 cursor-default'
                      }`}
                    />
                  </div>

                  {/* Gender — Student Editable */}
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <Label className="text-xs font-bold uppercase tracking-wider text-slate-700">
                        Gender
                      </Label>
                      <Badge variant="primary" size="sm">Student-Managed</Badge>
                    </div>
                    <select
                      disabled={!isEditingPersonal}
                      value={gender}
                      onChange={(e) => setGender(e.target.value)}
                      className={`w-full px-3.5 py-2.5 rounded-xl border text-xs outline-none transition font-medium ${
                        isEditingPersonal
                          ? 'border-slate-300 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-500/20 text-slate-900 bg-white shadow-xs'
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
              </CardContent>

              {isEditingPersonal && (
                <CardFooter className="justify-end gap-3">
                  <Button variant="outline" size="sm" onClick={handleCancelPersonal}>
                    Cancel
                  </Button>
                  <Button type="submit" variant="primary" size="sm" isLoading={savingPersonal}>
                    Save Personal Details
                  </Button>
                </CardFooter>
              )}
            </form>
          </Card>

          {/* ========================================================================= */}
          {/* SECTION 2: ACADEMIC DETAILS                                               */}
          {/* ========================================================================= */}
          <Card>
            <CardHeader
              action={
                !isEditingAcademic ? (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsEditingAcademic(true)}
                    leftIcon={
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                      </svg>
                    }
                  >
                    Edit Academic Details
                  </Button>
                ) : (
                  <Button variant="ghost" size="sm" onClick={handleCancelAcademic}>
                    Cancel
                  </Button>
                )
              }
            >
              <CardTitle>Academic Details</CardTitle>
              <CardDescription>Official university credentials and self-reported educational marks</CardDescription>
            </CardHeader>

            <div className="p-6 space-y-6">
              {academicMessage && (
                <Alert variant={academicMessage.type === 'success' ? 'success' : 'danger'}>
                  {academicMessage.text}
                </Alert>
              )}

              {/* Institutional Read-Only Highlights */}
              <div className="space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                    Institutional Verified Records
                  </span>
                  <Badge variant="warning" size="sm" dot>
                    Read-Only &bull; Verified by TPO
                  </Badge>
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
              <form onSubmit={handleSaveAcademic} className="space-y-5 pt-4 border-t border-slate-100">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                    Student-Managed Academic Details
                  </span>
                  <Badge variant="primary" size="sm">Self-Editable</Badge>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  {/* Section */}
                  <div>
                    <Label className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                      Section
                    </Label>
                    {isEditingAcademic ? (
                      <input
                        type="text"
                        maxLength={10}
                        placeholder="e.g. A, B, C"
                        value={section}
                        onChange={(e) => setSection(e.target.value)}
                        className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-500/20 text-xs text-slate-900 outline-none transition bg-white shadow-xs font-medium"
                      />
                    ) : (
                      <div className="px-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200/70 text-xs font-bold text-slate-800">
                        {profile?.section || 'Not Set'}
                      </div>
                    )}
                  </div>

                  {/* 10th / SSLC Mark */}
                  <div>
                    <Label className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                      10th / SSLC Mark (%)
                    </Label>
                    {isEditingAcademic ? (
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        max="100"
                        placeholder="e.g. 92.50"
                        value={tenthMark}
                        onChange={(e) => setTenthMark(e.target.value)}
                        className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-500/20 text-xs text-slate-900 outline-none transition bg-white shadow-xs font-medium"
                      />
                    ) : (
                      <div className="px-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200/70 text-xs font-bold text-slate-800">
                        {formatPercentage(profile?.tenth_mark)}
                      </div>
                    )}
                  </div>

                  {/* 12th / Intermediate Mark */}
                  <div>
                    <Label className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                      12th / Inter Mark (%)
                    </Label>
                    {isEditingAcademic ? (
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        max="100"
                        placeholder="e.g. 88.00 (Optional)"
                        value={twelfthMark}
                        onChange={(e) => setTwelfthMark(e.target.value)}
                        className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-500/20 text-xs text-slate-900 outline-none transition bg-white shadow-xs font-medium"
                      />
                    ) : (
                      <div className="px-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200/70 text-xs font-bold text-slate-800">
                        {formatPercentage(profile?.twelfth_mark)}
                      </div>
                    )}
                  </div>

                  {/* Diploma Mark */}
                  <div>
                    <Label className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                      Diploma Mark (%)
                    </Label>
                    {isEditingAcademic ? (
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        max="100"
                        placeholder="e.g. 82.00 (Optional)"
                        value={diplomaMark}
                        onChange={(e) => setDiplomaMark(e.target.value)}
                        className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-500/20 text-xs text-slate-900 outline-none transition bg-white shadow-xs font-medium"
                      />
                    ) : (
                      <div className="px-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200/70 text-xs font-bold text-slate-800">
                        {formatPercentage(profile?.diploma_mark)}
                      </div>
                    )}
                  </div>
                </div>

                <p className="text-[11px] text-slate-400">
                  Note: Provide 12th/Intermediate or Diploma percentage based on your educational path. Unfilled fields display as "Not Applicable".
                </p>

                {isEditingAcademic && (
                  <div className="flex justify-end space-x-3 pt-3 border-t border-slate-100">
                    <Button variant="outline" size="sm" onClick={handleCancelAcademic}>
                      Cancel
                    </Button>
                    <Button type="submit" variant="primary" size="sm" isLoading={savingAcademic}>
                      Save Academic Details
                    </Button>
                  </div>
                )}
              </form>
            </div>
          </Card>

          {/* ========================================================================= */}
          {/* SECTION 3: RESUME & PORTFOLIO                                             */}
          {/* ========================================================================= */}
          <div ref={resumeSectionRef} id="resume-section">
            <Card>
              <CardHeader
                action={
                  <Badge variant="primary" size="sm">
                    Recruitment Assets
                  </Badge>
                }
              >
                <CardTitle>Resume & Portfolio</CardTitle>
                <CardDescription>Official recruitment credentials, PDF resume, and public professional links</CardDescription>
              </CardHeader>

              <div className="p-6 space-y-6">
                {/* SUBSECTION A: RESUME DOCUMENT */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                      Verified Resume Document
                    </span>
                    <span className="text-[10px] text-slate-500 font-medium">PDF Format &bull; Max 5MB</span>
                  </div>

                  {resumeMessage && (
                    <Alert variant={resumeMessage.type === 'success' ? 'success' : 'danger'}>
                      {resumeMessage.text}
                    </Alert>
                  )}

                  {/* Status Card */}
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-center space-x-3.5">
                      <div className="w-11 h-11 rounded-xl bg-indigo-600 text-white flex items-center justify-center font-bold shrink-0 shadow-sm shadow-indigo-600/20">
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
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleDownloadResume}
                        isLoading={downloadingResume}
                        leftIcon={
                          <svg className="w-4 h-4 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                          </svg>
                        }
                        className="self-start sm:self-auto"
                      >
                        Download Resume PDF
                      </Button>
                    )}
                  </div>

                  {/* Upload File Input */}
                  <div className="p-4 rounded-xl border border-slate-200/80 bg-white space-y-2">
                    <Label className="text-xs font-bold text-slate-700">
                      Upload or Replace Resume
                    </Label>
                    <div className="flex flex-col sm:flex-row items-center gap-3">
                      <input
                        type="file"
                        accept="application/pdf"
                        onChange={handleFileChange}
                        className="w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 cursor-pointer"
                      />
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={handleUploadResume}
                        disabled={!selectedFile || uploadingResume}
                        isLoading={uploadingResume}
                        className="w-full sm:w-auto whitespace-nowrap"
                      >
                        Confirm Upload
                      </Button>
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
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setIsEditingPortfolio(true)}
                        leftIcon={
                          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                          </svg>
                        }
                      >
                        Edit Portfolio
                      </Button>
                    ) : (
                      <Button variant="ghost" size="sm" onClick={handleCancelPortfolio}>
                        Cancel
                      </Button>
                    )}
                  </div>

                  {portfolioMessage && (
                    <Alert variant={portfolioMessage.type === 'success' ? 'success' : 'danger'}>
                      {portfolioMessage.text}
                    </Alert>
                  )}

                  {!isEditingPortfolio ? (
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold shrink-0">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </div>
                        <div className="min-w-0">
                          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Portfolio URL</div>
                          {profile?.portfolio_url ? (
                            <a
                              href={profile.portfolio_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 hover:underline flex items-center space-x-1 mt-0.5"
                            >
                              <span className="truncate max-w-md">{profile.portfolio_url}</span>
                              <svg className="w-3 h-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
                        <Label className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                          Portfolio URL (GitHub, LinkedIn, Personal Site)
                        </Label>
                        <input
                          type="url"
                          placeholder="https://github.com/yourusername or https://myportfolio.dev"
                          value={portfolioUrl}
                          onChange={(e) => setPortfolioUrl(e.target.value)}
                          className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-500/20 text-xs text-slate-900 outline-none transition bg-white font-mono shadow-xs"
                        />
                      </div>

                      <div className="flex justify-end space-x-3">
                        <Button variant="outline" size="sm" onClick={handleCancelPortfolio}>
                          Cancel
                        </Button>
                        <Button type="submit" variant="primary" size="sm" isLoading={savingPortfolio}>
                          Save Portfolio
                        </Button>
                      </div>
                    </form>
                  )}
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

