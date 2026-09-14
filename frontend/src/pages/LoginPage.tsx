import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useAuthStore } from '../store/authStore';
import { apiClient } from '../services/apiClient';
import { useForm } from 'react-hook-form';
import { CampusFlowLogo } from '../components/common/CampusFlowLogo';
import { extractErrorMessage } from '../utils/errorUtils';

const loginSchema = z.object({
  email: z.string().min(1, 'Email or registration number is required'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormValues = z.infer<typeof loginSchema>;


export const LoginPage = () => {
  const [serverError, setServerError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const { setSession } = useAuthStore();
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormValues) => {
    let authSuccess = false;
    try {
      setServerError(null);
      const cleanIdentifier = data.email.trim();
      const payload = {
        email: cleanIdentifier,
        identifier: cleanIdentifier,
        password: data.password,
      };
      const response = await apiClient.post('/auth/login', payload);

      const { access_token, refresh_token, user } = response.data;
      setSession(access_token, refresh_token, user);
      authSuccess = true;
    } catch (error: any) {
      const msg = extractErrorMessage(
        error,
        'Invalid email address, registration number, or password. Please try again.'
      );
      setServerError(msg);
    }

    if (authSuccess) {
      navigate('/');
    }
  };

  const handleFillDemo = (email: string, pass: string) => {
    setServerError(null);
    setValue('email', email, { shouldValidate: true, shouldDirty: true, shouldTouch: true });
    setValue('password', pass, { shouldValidate: true, shouldDirty: true, shouldTouch: true });
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-slate-50 font-sans antialiased text-slate-900">
      {/* LEFT PANEL: Clean Editorial Brand & Journey Showcase */}
      <div className="relative hidden lg:flex lg:w-1/2 bg-slate-950 text-white p-12 xl:p-16 flex-col justify-between overflow-hidden border-r border-slate-800/80">
        {/* Subtle Brand Ambient Highlight */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-slate-800/20 rounded-full blur-3xl pointer-events-none" />

        {/* Top Branding */}
        <div className="relative z-10">
          <CampusFlowLogo size="lg" variant="light" showTagline />
          <div className="mt-4 inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-slate-300 text-xs font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Campus Placement Workspace Active</span>
          </div>
        </div>

        {/* Center Value Proposition & Journey Pillars */}
        <div className="relative z-10 space-y-8 my-auto max-w-lg">
          <div className="space-y-3">
            <p className="text-[11px] font-bold uppercase tracking-wider text-indigo-400">
              Campus Placement Operating Platform
            </p>
            <h1 className="text-3xl xl:text-4xl font-extrabold tracking-tight text-white leading-tight">
              Your campus placement journey, organized in one place.
            </h1>
            <p className="text-sm xl:text-base text-slate-300 leading-relaxed font-normal">
              Discover verified placement drives, prepare for company rounds, practice timed assessments, and track recruitment progress seamlessly.
            </p>
          </div>

          {/* Structured Journey Pillars */}
          <div className="grid grid-cols-5 gap-2 pt-2">
            {[
              { step: '01', label: 'Discover' },
              { step: '02', label: 'Prepare' },
              { step: '03', label: 'Practice' },
              { step: '04', label: 'Apply' },
              { step: '05', label: 'Track' },
            ].map((item) => (
              <div
                key={item.step}
                className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80 text-center space-y-1 shadow-2xs"
              >
                <div className="text-[10px] font-mono text-indigo-400 font-bold">{item.step}</div>
                <div className="text-xs font-bold text-slate-200">{item.label}</div>
              </div>
            ))}
          </div>

          {/* Verified Institutional Core Highlights */}
          <div className="space-y-3 pt-2">
            <div className="flex items-start space-x-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/60">
              <div className="w-7 h-7 rounded-lg bg-indigo-600/20 text-indigo-300 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h4 className="text-xs font-bold text-white">Automated Eligibility Verification</h4>
                <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">
                  Real-time validation against verified CGPA, batch year, and branch criteria.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/60">
              <div className="w-7 h-7 rounded-lg bg-emerald-600/20 text-emerald-300 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <h4 className="text-xs font-bold text-white">Full-Funnel Stage Management</h4>
                <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">
                  Clear stage timelines from aptitude assessments to technical rounds and offers.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Footer Info */}
        <div className="relative z-10 pt-6 border-t border-slate-800 flex items-center justify-between text-xs text-slate-500">
          <span>CampusFlow • Institutional Edition</span>
          <span>Security Hardened & RBAC Protected</span>
        </div>
      </div>

      {/* RIGHT PANEL: Clean Authentication Form */}
      <div className="flex-1 flex flex-col justify-center px-4 sm:px-6 lg:px-16 xl:px-24 py-12">
        <div className="w-full max-w-md mx-auto space-y-7">
          {/* Mobile Logo View */}
          <div className="lg:hidden flex flex-col items-center text-center pb-2">
            <CampusFlowLogo size="lg" showTagline />
          </div>

          {/* Form Header */}
          <div className="space-y-1.5">
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900">
              Sign in to your account
            </h2>
            <p className="text-xs sm:text-sm text-slate-500">
              Welcome back to CampusFlow. Enter your credentials to access your portal.
            </p>
          </div>

          {/* Error Alert Box (Preserves .bg-red-50 for Playwright E2E assertion) */}
          {serverError && (
            <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl text-xs sm:text-sm flex items-start space-x-3 animate-fade-in" role="alert">
              <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="flex-1">
                <p className="font-bold">Authentication failed</p>
                <p className="text-xs text-red-600 mt-0.5 leading-relaxed">{serverError}</p>
              </div>
            </div>
          )}

          {/* Form */}
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
            {/* Email Field */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Email address or Registration Number
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.206" />
                  </svg>
                </div>
                <input
                  type="text"
                  inputMode="text"
                  autoComplete="username"
                  data-testid="input-identifier"
                  placeholder="student1@campusflow.edu or 99230041249"
                  {...register('email')}
                  className="block w-full pl-10 pr-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-sm placeholder-slate-400 text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 transition shadow-2xs"
                />
              </div>

              {errors.email && (
                <p className="mt-1.5 text-xs font-semibold text-rose-600">
                  {errors.email.message}
                </p>
              )}
            </div>

            {/* Password Field */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  placeholder="••••••••••••"
                  {...register('password')}
                  className="block w-full pl-10 pr-10 py-2.5 bg-white border border-slate-200 rounded-xl text-sm placeholder-slate-400 text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 transition shadow-2xs"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 focus:outline-none"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l18 18" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1.5 text-xs font-semibold text-rose-600">
                  {errors.password.message}
                </p>
              )}
            </div>

            {/* Primary Submit CTA */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex items-center justify-center py-2.5 px-4 rounded-xl shadow-sm shadow-indigo-600/20 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition duration-150"
            >
              {isSubmitting ? (
                <div className="flex items-center space-x-2">
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Signing in...</span>
                </div>
              ) : (
                <span>Sign in</span>
              )}
            </button>

            {/* Account Registration Entry Point */}
            <div className="text-center pt-2">
              <p className="text-xs text-slate-500">
                New to CampusFlow?{' '}
                <Link
                  to="/register"
                  className="font-bold text-indigo-600 hover:text-indigo-700 underline underline-offset-2 transition"
                >
                  Register your account
                </Link>
              </p>
            </div>
          </form>


          {/* Quick Demo Credentials Helper */}
          <div className="pt-4 border-t border-slate-200">
            <div className="flex items-center justify-between mb-2.5">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                Demo access
              </span>
              <span className="text-[10px] text-slate-400">
                Pre-seeded test accounts
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleFillDemo('student1@campusflow.edu', 'TestStudent@123')}
                className="p-2.5 text-center rounded-xl border border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/50 bg-white transition group shadow-2xs"
              >
                <span className="block text-xs font-bold text-slate-700 group-hover:text-indigo-600">Student</span>
                <span className="block text-[10px] text-slate-400 font-mono mt-0.5">student1</span>
              </button>
              <button
                type="button"
                onClick={() => handleFillDemo('officer@campusflow.edu', 'TestOfficer@123')}
                className="p-2.5 text-center rounded-xl border border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/50 bg-white transition group shadow-2xs"
              >
                <span className="block text-xs font-bold text-slate-700 group-hover:text-indigo-600">Officer</span>
                <span className="block text-[10px] text-slate-400 font-mono mt-0.5">officer</span>
              </button>
              <button
                type="button"
                onClick={() => handleFillDemo('admin@campusflow.edu', 'TestAdmin@123')}
                className="p-2.5 text-center rounded-xl border border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/50 bg-white transition group shadow-2xs"
              >
                <span className="block text-xs font-bold text-slate-700 group-hover:text-indigo-600">Admin</span>
                <span className="block text-[10px] text-slate-400 font-mono mt-0.5">admin</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
