import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { apiClient } from '../services/apiClient';
import { CampusFlowLogo } from '../components/common/CampusFlowLogo';
import { extractErrorMessage } from '../utils/errorUtils';

const registerSchema = z
  .object({
    registrationNumber: z
      .string()
      .min(1, 'Student registration number is required')
      .max(50, 'Registration number cannot exceed 50 characters'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  });

type RegisterFormValues = z.infer<typeof registerSchema>;

export const ActivateAccountPage = () => {
  const [searchParams] = useSearchParams();
  const initialRegNo = searchParams.get('reg') || searchParams.get('registration_number') || '';
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      registrationNumber: initialRegNo,
    },
  });

  const onSubmit = async (data: RegisterFormValues) => {
    try {
      setServerError(null);
      const res = await apiClient.post('/auth/register', {
        registration_number: data.registrationNumber.trim(),
        password: data.password,
      });
      if (res.data?.email) {
        setRegisteredEmail(res.data.email);
      }
      setSuccess(true);
      setTimeout(() => navigate('/login'), 2500);
    } catch (error: any) {
      const msg = extractErrorMessage(
        error,
        'An unexpected error occurred. Please verify your registration number.'
      );
      setServerError(msg);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white border border-slate-200/80 rounded-2xl shadow-sm p-8 text-center space-y-4 animate-fade-in">
          <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 border border-emerald-200 flex items-center justify-center mx-auto">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-slate-900 tracking-tight">Account Registered!</h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            Registration completed successfully. You can now sign in using:
          </p>
          <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3 text-left space-y-1.5 text-xs text-slate-700">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-600"></span>
              <span><strong>Registration Number</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-600"></span>
              <span><strong>University Email</strong></span>
            </div>
          </div>
          {registeredEmail && (
            <p className="text-xs font-medium text-slate-600 bg-indigo-50/50 border border-indigo-100 rounded-lg py-2 px-3">
              University email: <span className="font-mono text-indigo-700 font-bold">{registeredEmail}</span>
            </p>
          )}
          <div className="pt-2">
            <Link
              to="/login"
              id="return-to-login-btn"
              className="inline-flex items-center justify-center py-2.5 px-5 rounded-xl shadow-sm text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 transition duration-150"
            >
              Sign In Now
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white border border-slate-200/80 rounded-2xl shadow-sm p-8 space-y-6 animate-fade-in">
        <div className="text-center">
          <CampusFlowLogo size="md" className="justify-center mb-4" />
          <h3 className="text-2xl font-extrabold text-slate-900 tracking-tight">New User Registration</h3>
          <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
            Register your CampusFlow student account using your registration number.
          </p>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
          {serverError && (
            <div className="bg-red-50 border border-red-200 text-red-700 p-3.5 rounded-xl text-xs font-medium animate-fade-in" role="alert">
              {serverError}
            </div>
          )}

          <div>
            <label htmlFor="registration-number" className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              Student Registration Number
            </label>
            <input
              type="text"
              id="registration-number"
              placeholder="Enter your registration number"
              {...register('registrationNumber')}
              className="w-full px-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-xs font-mono text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 transition shadow-2xs"
            />
            {errors.registrationNumber && (
              <p className="mt-1 text-xs font-semibold text-rose-600">{errors.registrationNumber.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="new-password" className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              New Password
            </label>
            <input
              type="password"
              id="new-password"
              placeholder="Minimum 8 characters"
              {...register('password')}
              className="w-full px-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 transition shadow-2xs"
            />
            {errors.password && (
              <p className="mt-1 text-xs font-semibold text-rose-600">{errors.password.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="confirm-password" className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              Confirm Password
            </label>
            <input
              type="password"
              id="confirm-password"
              placeholder="Re-enter your password"
              {...register('confirmPassword')}
              className="w-full px-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 transition shadow-2xs"
            />
            {errors.confirmPassword && (
              <p className="mt-1 text-xs font-semibold text-rose-600">{errors.confirmPassword.message}</p>
            )}
          </div>

          <button
            type="submit"
            id="register-submit-button"
            disabled={isSubmitting}
            className="w-full py-2.5 px-4 rounded-xl shadow-sm shadow-indigo-600/20 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 transition duration-150"
          >
            {isSubmitting ? 'Registering...' : 'Complete Registration'}
          </button>

          <div className="text-center pt-2">
            <Link
              to="/login"
              className="text-xs text-slate-500 hover:text-indigo-600 font-medium transition"
            >
              &larr; Return to Sign In
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};
