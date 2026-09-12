import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useAuthStore } from '../store/authStore';
import { apiClient } from '../services/apiClient';
import { useForm } from 'react-hook-form';
import { CampusFlowLogo } from '../components/common/CampusFlowLogo';

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
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
      const response = await apiClient.post('/auth/login', data);

      const { access_token, refresh_token, user } = response.data;
      setSession(access_token, refresh_token, user);
      authSuccess = true;
    } catch (error: any) {
      if (error.response?.data?.title) {
        setServerError(error.response.data.title);
      } else if (error.response?.data?.detail) {
        setServerError(error.response.data.detail);
      } else if (!error.response) {
        setServerError('Unable to reach the server. Please check that the backend is running on port 8000.');
      } else {
        setServerError('Invalid email address or password. Please try again.');
      }
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
    <div className="min-h-screen flex flex-col lg:flex-row bg-slate-50">
      {/* LEFT PANEL: Rich Brand & Value Showcase */}
      <div className="relative hidden lg:flex lg:w-1/2 bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-900 text-white p-12 flex-col justify-between overflow-hidden">
        {/* Subtle Ambient Background Orbs */}
        <div className="absolute -top-24 -left-24 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-sky-500/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-[100px] pointer-events-none" />

        {/* Top Branding */}
        <div className="relative z-10">
          <CampusFlowLogo size="lg" variant="light" showTagline />
          <div className="mt-4 inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-400/20 text-indigo-300 text-xs font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Campus Placement Portal Active</span>
          </div>
        </div>

        {/* Center Value Proposition & Workflow Visual */}
        <div className="relative z-10 space-y-8 my-auto max-w-lg">
          <div className="space-y-3">
            <h1 className="text-3xl xl:text-4xl font-extrabold tracking-tight text-white leading-tight">
              One central flow for your career journey.
            </h1>
            <p className="text-sm xl:text-base text-slate-300 leading-relaxed">
              Discover verified placement drives, verify eligibility in real time, apply seamlessly, and track recruitment stages from one unified dashboard.
            </p>
          </div>

          {/* Interactive Flow Step Pills */}
          <div className="space-y-3.5">
            <div className="flex items-center space-x-3.5 p-3 rounded-xl bg-white/5 border border-white/10 backdrop-blur-sm">
              <div className="w-8 h-8 rounded-lg bg-indigo-500/20 text-indigo-300 flex items-center justify-center font-bold text-xs">
                01
              </div>
              <div>
                <h4 className="text-xs font-bold text-white uppercase tracking-wider">Automated Eligibility</h4>
                <p className="text-xs text-slate-400">Instant verification against CGPA, batch, and branch rules.</p>
              </div>
            </div>

            <div className="flex items-center space-x-3.5 p-3 rounded-xl bg-white/5 border border-white/10 backdrop-blur-sm">
              <div className="w-8 h-8 rounded-lg bg-sky-500/20 text-sky-300 flex items-center justify-center font-bold text-xs">
                02
              </div>
              <div>
                <h4 className="text-xs font-bold text-white uppercase tracking-wider">Multi-Stage Funnel</h4>
                <p className="text-xs text-slate-400">Track aptitude, technical interviews, and HR offers in real time.</p>
              </div>
            </div>

            <div className="flex items-center space-x-3.5 p-3 rounded-xl bg-white/5 border border-white/10 backdrop-blur-sm">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-300 flex items-center justify-center font-bold text-xs">
                03
              </div>
              <div>
                <h4 className="text-xs font-bold text-white uppercase tracking-wider">Instant Push & Reminders</h4>
                <p className="text-xs text-slate-400">Never miss a deadline or round update with web push alerts.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Footer Info */}
        <div className="relative z-10 pt-6 border-t border-white/10 flex items-center justify-between text-xs text-slate-400">
          <span>CampusFlow • Institutional Edition</span>
          <span>Security Hardened & RBAC Protected</span>
        </div>
      </div>

      {/* RIGHT PANEL: Authentication Form */}
      <div className="flex-1 flex flex-col justify-center px-4 sm:px-6 lg:px-16 xl:px-24 py-12">
        <div className="w-full max-w-md mx-auto space-y-8">
          {/* Mobile Logo View */}
          <div className="lg:hidden flex flex-col items-center text-center">
            <CampusFlowLogo size="lg" showTagline />
          </div>

          {/* Form Header */}
          <div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
              Sign in to your account
            </h2>
            <p className="text-sm text-slate-500 mt-2">
              Welcome back to CampusFlow. Enter your credentials to access your portal.
            </p>
          </div>

          {/* Error Alert Box (Retains .bg-red-50 for Playwright E2E assertion) */}
          {serverError && (
            <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl text-sm flex items-start space-x-3 animate-fade-in">
              <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="flex-1">
                <p className="font-semibold">Authentication failed</p>
                <p className="text-xs text-red-600 mt-0.5">{serverError}</p>
              </div>
            </div>
          )}

          {/* Form */}
          <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
            {/* Email Field */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Email address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.206" />
                  </svg>
                </div>
                <input
                  type="email"
                  autoComplete="email"
                  placeholder="student1@campusflow.edu"
                  {...register('email')}
                  className="block w-full pl-10 pr-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-sm placeholder-slate-400 text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition shadow-sm"
                />
              </div>
              {errors.email && (
                <p className="mt-1.5 text-xs font-medium text-rose-600 flex items-center space-x-1">
                  <span>{errors.email.message}</span>
                </p>
              )}
            </div>

            {/* Password Field */}
            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Password
                </label>
              </div>
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
                  className="block w-full pl-10 pr-10 py-2.5 bg-white border border-slate-300 rounded-xl text-sm placeholder-slate-400 text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition shadow-sm"
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
                <p className="mt-1.5 text-xs font-medium text-rose-600 flex items-center space-x-1">
                  <span>{errors.password.message}</span>
                </p>
              )}
            </div>

            {/* Primary Submit CTA */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex items-center justify-center py-3 px-4 rounded-xl shadow-md shadow-indigo-500/20 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 active:scale-[0.99] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isSubmitting ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Signing in...</span>
                </div>
              ) : (
                <span>Sign in</span>
              )}
            </button>

            {/* Issue 2: Account Activation Entry Point */}
            <div className="text-center pt-2">
              <p className="text-xs text-slate-500">
                New to CampusFlow?{' '}
                <Link
                  to="/activate"
                  className="font-semibold text-indigo-600 hover:text-indigo-700 underline underline-offset-2 transition"
                >
                  Activate your account
                </Link>
              </p>
            </div>
          </form>

          {/* Quick Demo Credentials Helper (Visually secondary demo access) */}
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
                className="p-2 text-center rounded-xl border border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/50 bg-white transition group shadow-sm"
              >
                <span className="block text-[11px] font-bold text-slate-700 group-hover:text-indigo-600">Student</span>
                <span className="block text-[9px] text-slate-400 font-mono">student1</span>
              </button>
              <button
                type="button"
                onClick={() => handleFillDemo('officer@campusflow.edu', 'TestOfficer@123')}
                className="p-2 text-center rounded-xl border border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/50 bg-white transition group shadow-sm"
              >
                <span className="block text-[11px] font-bold text-slate-700 group-hover:text-indigo-600">Officer</span>
                <span className="block text-[9px] text-slate-400 font-mono">officer</span>
              </button>
              <button
                type="button"
                onClick={() => handleFillDemo('admin@campusflow.edu', 'TestAdmin@123')}
                className="p-2 text-center rounded-xl border border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/50 bg-white transition group shadow-sm"
              >
                <span className="block text-[11px] font-bold text-slate-700 group-hover:text-indigo-600">Admin</span>
                <span className="block text-[9px] text-slate-400 font-mono">admin</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
