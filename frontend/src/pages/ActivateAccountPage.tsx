import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { apiClient } from '../services/apiClient';
import { CampusFlowLogo } from '../components/common/CampusFlowLogo';

const activateSchema = z
  .object({
    token: z.string().min(1, 'Activation token is required'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  });

type ActivateFormValues = z.infer<typeof activateSchema>;

export const ActivateAccountPage = () => {
  const [searchParams] = useSearchParams();
  const urlToken = searchParams.get('token') || '';
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ActivateFormValues>({
    resolver: zodResolver(activateSchema),
    defaultValues: {
      token: urlToken,
      password: '',
      confirmPassword: '',
    },
  });

  const onSubmit = async (data: ActivateFormValues) => {
    try {
      setServerError(null);
      await apiClient.post('/auth/activate', {
        activation_token: data.token.trim(),
        new_password: data.password,
      });
      setSuccess(true);
      setTimeout(() => navigate('/login'), 2500);
    } catch (error: any) {
      if (error.response?.data?.title) {
        setServerError(error.response.data.title);
      } else if (error.response?.data?.detail) {
        setServerError(error.response.data.detail);
      } else {
        setServerError('An unexpected error occurred. Please verify your activation token.');
      }
    }
  };

  if (success) {
    return (
      <div className="max-w-md w-full mx-auto p-8 bg-white border border-slate-200 rounded-2xl shadow-xl text-center space-y-4 animate-fade-in">
        <div className="w-12 h-12 rounded-2xl bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 className="text-xl font-bold text-slate-900">Account Activated!</h3>
        <p className="text-xs text-slate-500">
          Your credentials have been verified and your password is set. Redirecting you to the sign-in page...
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-md w-full mx-auto p-8 bg-white border border-slate-200 rounded-2xl shadow-xl space-y-6 animate-fade-in">
      <div className="text-center">
        <CampusFlowLogo size="md" className="justify-center mb-4" />
        <h3 className="text-2xl font-bold text-slate-900 tracking-tight">Activate your account</h3>
        <p className="text-xs text-slate-500 mt-1">
          {urlToken
            ? 'Set your password to complete your account setup.'
            : 'Enter the activation token from your university onboarding email to complete setup.'}
        </p>
      </div>

      <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
        {serverError && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-xl text-xs text-center font-medium">
            {serverError}
          </div>
        )}

        {/* If token is not in URL, let user paste it */}
        {!urlToken ? (
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              Activation Token
            </label>
            <input
              type="text"
              placeholder="Paste your activation token"
              {...register('token')}
              className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-xs font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition shadow-sm"
            />
            {errors.token && (
              <p className="mt-1 text-xs font-semibold text-rose-600">{errors.token.message}</p>
            )}
          </div>
        ) : (
          <input type="hidden" {...register('token')} />
        )}

        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
            New Password
          </label>
          <input
            type="password"
            placeholder="Minimum 8 characters"
            {...register('password')}
            className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition shadow-sm"
          />
          {errors.password && (
            <p className="mt-1 text-xs font-semibold text-rose-600">{errors.password.message}</p>
          )}
        </div>

        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
            Confirm Password
          </label>
          <input
            type="password"
            placeholder="Re-enter your password"
            {...register('confirmPassword')}
            className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition shadow-sm"
          />
          {errors.confirmPassword && (
            <p className="mt-1 text-xs font-semibold text-rose-600">{errors.confirmPassword.message}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-3 px-4 rounded-xl shadow-md shadow-indigo-600/20 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 transition"
        >
          {isSubmitting ? 'Activating...' : 'Activate Account'}
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
  );
};
