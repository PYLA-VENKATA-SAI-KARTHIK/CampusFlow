import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useAuthStore } from '../store/authStore';
import { apiClient } from '../services/apiClient';
import { useForm } from 'react-hook-form';
import { extractErrorMessage } from '../utils/errorUtils';

const loginSchema = z.object({
  email: z.string().min(1, 'Email or registration number is required'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export const LoginPage = () => {
  const [serverError, setServerError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
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
    <div className="min-h-screen flex flex-col lg:flex-row bg-[#f4f5f8] font-sans antialiased text-slate-900 selection:bg-[#9b86d9] selection:text-black">
      {/* ── LEFT PANEL: University Campus Panoramic Showcase ─────────────────── */}
      <div className="relative hidden lg:flex lg:w-1/2 min-h-screen bg-slate-950 overflow-hidden flex-col justify-between p-8 xl:p-12 select-none border-r border-slate-800">
        {/* Background Campus Image */}
        <div
          className="absolute inset-0 bg-cover bg-center transition-transform duration-1000 scale-100 hover:scale-105"
          style={{ backgroundImage: "url('/assets/images/campus_sunrise.jpg')" }}
        />
        {/* Soft Vignette Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-slate-950/40 to-slate-950/60 pointer-events-none" />

        {/* TOP: Institutional Crest & Technical Metadata */}
        <div className="relative z-10 flex items-start justify-between animate-fade-in">
          <div className="flex items-center space-x-3.5">
            <div className="w-14 h-14 rounded-md bg-white/95 p-1.5 shadow-xl border border-white/40 flex items-center justify-center backdrop-blur-sm">
              {/* University Insignia Logo */}
              <svg viewBox="0 0 100 100" className="w-full h-full text-indigo-900" fill="none">
                <circle cx="50" cy="50" r="45" stroke="#1e3a8a" strokeWidth="4" strokeDasharray="3 2" />
                <circle cx="50" cy="50" r="38" fill="#1e40af" fillOpacity="0.08" stroke="#f59e0b" strokeWidth="2" />
                {/* Flame / Diya */}
                <path d="M50 22 C43 32 40 38 40 46 C40 54 45 58 50 58 C55 58 60 54 60 46 C60 38 57 32 50 22 Z" fill="#f59e0b" />
                <path d="M50 28 C46 34 44 38 44 44 C44 49 47 52 50 52 C53 52 56 49 56 44 C56 38 54 34 50 28 Z" fill="#ef4444" />
                {/* Diya Base */}
                <path d="M30 54 C30 54 34 68 50 68 C66 68 70 54 70 54 L30 54 Z" fill="#1e3a8a" />
                <rect x="42" y="68" width="16" height="4" rx="2" fill="#1e3a8a" />
                <rect x="36" y="72" width="28" height="4" rx="2" fill="#f59e0b" />
              </svg>
            </div>
            <div className="text-white drop-shadow-md">
              <h3 className="text-xs font-black uppercase tracking-wider text-amber-300 font-display">
                Kalasalingam Academy of Research and Education
              </h3>
              <p className="text-[11px] font-mono text-slate-200 tracking-wide">
                Deemed to be University • Anand Nagar, Krishnankoil
              </p>
            </div>
          </div>

          <div className="font-mono text-[10px] text-white/70 tracking-widest text-right">
            <div>[SEC.03]</div>
            <div>X:0142 Y:0096</div>
          </div>
        </div>

        {/* BOTTOM: Campus Career Platform Headline */}
        <div className="relative z-10 text-white drop-shadow-lg space-y-3">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-sm bg-slate-950/75 backdrop-blur-md border border-white/20 text-[11px] font-mono font-semibold text-slate-200">
            <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
            <span>CAMPUS PLACEMENT OPERATING PLATFORM ACTIVE</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white font-display tracking-tight leading-snug max-w-lg">
            Institutional Career Intelligence & Drive Governance
          </h2>
          <p className="text-xs font-medium text-slate-300 max-w-md leading-relaxed font-sans">
            Authoritative platform for institutional placement drives, automated eligibility validation, assessment rounds, and talent progression.
          </p>
        </div>
      </div>

      {/* ── RIGHT PANEL: Editorial Minimalist Login Form ─────────────────── */}
      <div className="flex-1 flex flex-col justify-between p-6 sm:p-12 lg:p-16 xl:p-20 bg-white border-l border-slate-200">
        <div className="w-full max-w-md mx-auto space-y-7 my-auto">
          {/* Header */}
          <div className="space-y-2.5">
            <div className="flex items-center space-x-2 font-mono text-[11px] text-[#6d50b4] font-bold uppercase tracking-widest">
              <span>[SEC.01]</span>
              <span>//</span>
              <span>AUTH.GATEWAY</span>
            </div>

            <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-950 font-display tracking-tight">
              Sign In // <span className="text-[#9b86d9]">CampusFlow</span>
            </h1>

            <p className="font-mono text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              Student Information System & Placement Intelligence
            </p>

            <p className="text-xs text-slate-600 leading-relaxed">
              Institutional portal for real-time placement drives, eligibility validation, assessment rounds, and career progression.
            </p>
          </div>

          {/* Error Alert Box (Preserves .bg-red-50 for Playwright E2E assertion) */}
          {serverError && (
            <div
              className="bg-red-50 border border-red-300 text-red-800 p-3.5 rounded-sm text-xs flex items-start space-x-2.5 animate-fade-in shadow-[2px_2px_0px_#fca5a5]"
              role="alert"
            >
              <svg className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="flex-1 font-sans">
                <p className="font-bold">Login Failed</p>
                <p className="text-xs text-red-700 mt-0.5 leading-relaxed">{serverError}</p>
              </div>
            </div>
          )}

          {/* Form */}
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
            {/* Registration No. / Email */}
            <div>
              <label className="block text-[11px] font-mono font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                Registration No. / University Email
              </label>
              <input
                type="text"
                inputMode="text"
                autoComplete="username"
                data-testid="input-identifier"
                placeholder="e.g. 99230041249 or student@campusflow.edu"
                {...register('email')}
                className="block w-full px-3.5 py-2.5 bg-[#f5f6f9] border border-slate-300 focus:border-[#9b86d9] focus:bg-white rounded-sm text-xs sm:text-sm placeholder-slate-400 text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#9b86d9]/30 transition shadow-xs"
              />
              {errors.email && (
                <p className="mt-1 font-mono text-[11px] font-semibold text-rose-600">
                  {errors.email.message}
                </p>
              )}
            </div>

            {/* Password */}
            <div className="relative">
              <label className="block text-[11px] font-mono font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                Security Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  placeholder="Enter your password"
                  {...register('password')}
                  className="block w-full px-3.5 py-2.5 bg-[#f5f6f9] border border-slate-300 focus:border-[#9b86d9] focus:bg-white rounded-sm text-xs sm:text-sm placeholder-slate-400 text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#9b86d9]/30 transition pr-10 shadow-xs"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-700 focus:outline-none cursor-pointer"
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
                <p className="mt-1 font-mono text-[11px] font-semibold text-rose-600">
                  {errors.password.message}
                </p>
              )}
            </div>

            {/* Remember Me & SIGN IN Button */}
            <div className="flex items-center justify-between pt-2">
              <label className="flex items-center space-x-2 text-xs text-slate-600 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded-xs border-slate-300 text-[#6d50b4] focus:ring-[#9b86d9] cursor-pointer"
                />
                <span className="font-medium">Remember me</span>
              </label>

              <button
                type="submit"
                disabled={isSubmitting}
                className="inline-flex items-center justify-center px-7 py-2.5 rounded-sm bg-[#0a0b10] hover:bg-[#1f202b] active:translate-x-[1px] active:translate-y-[1px] active:shadow-none text-white text-xs font-mono font-bold uppercase tracking-wider shadow-[3px_3px_0px_#9b86d9] transition border border-[#0a0b10] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                {isSubmitting ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>AUTHENTICATING...</span>
                  </div>
                ) : (
                  <span>SIGN IN</span>
                )}
              </button>
            </div>

            {/* Account Registration Link */}
            <div className="pt-2 text-center sm:text-left">
              <p className="text-xs text-slate-600">
                New candidate to CampusFlow?{' '}
                <Link
                  to="/register"
                  className="font-bold text-[#6d50b4] hover:text-[#4b3679] underline underline-offset-4 decoration-[#9b86d9] transition"
                >
                  Register your student account
                </Link>
              </p>
            </div>
          </form>

          {/* ── Demo Access Selector (Tactile Hardware Keys) ───────────────── */}
          <div className="pt-6 border-t border-slate-200">
            <div className="flex items-center justify-between mb-2.5">
              <span className="text-[10px] font-mono font-bold text-slate-500 uppercase tracking-widest">
                [SYS.ACCESS] ONE-CLICK DEMO KEYS
              </span>
              <span className="text-[10px] font-mono text-[#6d50b4] font-semibold">
                PRE-AUTHENTICATED
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2.5">
              <button
                type="button"
                onClick={() => handleFillDemo('student1@campusflow.edu', 'TestStudent@123')}
                className="p-2.5 text-center rounded-sm border border-slate-300 hover:border-[#9b86d9] hover:bg-[#f6f3fc] bg-white transition group shadow-[2px_2px_0px_rgba(10,11,16,0.06)] active:shadow-none active:translate-x-[1px] active:translate-y-[1px] cursor-pointer"
              >
                <span className="block text-xs font-bold text-slate-900 group-hover:text-[#5a4195] font-display">Student</span>
                <span className="block text-[10px] text-slate-500 font-mono mt-0.5">student1</span>
              </button>
              <button
                type="button"
                onClick={() => handleFillDemo('dhilipanrajkumar@gmail.com', 'TestOfficer@123')}
                className="p-2.5 text-center rounded-sm border border-slate-300 hover:border-[#9b86d9] hover:bg-[#f6f3fc] bg-white transition group shadow-[2px_2px_0px_rgba(10,11,16,0.06)] active:shadow-none active:translate-x-[1px] active:translate-y-[1px] cursor-pointer"
              >
                <span className="block text-xs font-bold text-slate-900 group-hover:text-[#5a4195] font-display">Officer</span>
                <span className="block text-[10px] text-slate-500 font-mono mt-0.5 truncate">officer</span>
              </button>
              <button
                type="button"
                onClick={() => handleFillDemo('admin@campusflow.edu', 'TestAdmin@123')}
                className="p-2.5 text-center rounded-sm border border-slate-300 hover:border-[#9b86d9] hover:bg-[#f6f3fc] bg-white transition group shadow-[2px_2px_0px_rgba(10,11,16,0.06)] active:shadow-none active:translate-x-[1px] active:translate-y-[1px] cursor-pointer"
              >
                <span className="block text-xs font-bold text-slate-900 group-hover:text-[#5a4195] font-display">Admin</span>
                <span className="block text-[10px] text-slate-500 font-mono mt-0.5">admin</span>
              </button>
            </div>
          </div>
        </div>

        {/* ── Footer ────────────────────────────────────────────────────────── */}
        <div className="pt-6 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500 mt-6 font-mono">
          <div className="flex items-center space-x-3 text-slate-500 text-xs">
            <span className="hover:text-[#9b86d9] transition cursor-pointer font-bold">KARE</span>
            <span>•</span>
            <span className="hover:text-[#9b86d9] transition cursor-pointer font-bold">SIS</span>
            <span>•</span>
            <span className="hover:text-[#9b86d9] transition cursor-pointer font-bold">PLACEMENT</span>
          </div>
          <div className="text-[11px] text-slate-500 text-center sm:text-right">
            [SYS.BUILD 2.4.0] // CAMPUSFLOW OPERATING PLATFORM
          </div>
        </div>
      </div>
    </div>
  );
};
