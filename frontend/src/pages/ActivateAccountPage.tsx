import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { apiClient } from '../services/apiClient';

const activateSchema = z.object({
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type ActivateFormValues = z.infer<typeof activateSchema>;

export const ActivateAccountPage = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ActivateFormValues>({
    resolver: zodResolver(activateSchema),
  });

  const onSubmit = async (data: ActivateFormValues) => {
    if (!token) {
      setServerError("Activation token is missing from the URL.");
      return;
    }

    try {
      setServerError(null);
      await apiClient.post('/auth/activate', {
        activation_token: token,
        new_password: data.password,
      });
      setSuccess(true);
      setTimeout(() => navigate('/login'), 3000);
    } catch (error: any) {
      if (error.response?.data?.title) {
        setServerError(error.response.data.title);
      } else {
        setServerError('An unexpected error occurred. Please try again.');
      }
    }
  };

  if (!token) {
    return (
      <div className="text-center py-8">
        <h3 className="text-lg font-medium text-red-600 mb-2">Invalid Link</h3>
        <p className="text-gray-600">The activation link is malformed or missing the token.</p>
      </div>
    );
  }

  if (success) {
    return (
      <div className="text-center py-8">
        <h3 className="text-xl font-bold text-green-600 mb-2">Account Activated!</h3>
        <p className="text-gray-600">Your account is ready. Redirecting to login...</p>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-xl font-bold mb-4 text-center">Activate your account</h3>
      <p className="text-sm text-gray-500 text-center mb-6">
        Please set a secure password to complete your account activation.
      </p>

      <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
        {serverError && (
          <div className="bg-red-50 text-red-700 p-3 rounded text-sm text-center">
            {serverError}
          </div>
        )}
        
        <div>
          <label className="block text-sm font-medium text-gray-700">New Password</label>
          <div className="mt-1">
            <input
              type="password"
              {...register('password')}
              className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            />
            {errors.password && (
              <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
            )}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Confirm Password</label>
          <div className="mt-1">
            <input
              type="password"
              {...register('confirmPassword')}
              className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            />
            {errors.confirmPassword && (
              <p className="mt-1 text-sm text-red-600">{errors.confirmPassword.message}</p>
            )}
          </div>
        </div>

        <div>
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
          >
            {isSubmitting ? 'Activating...' : 'Activate Account'}
          </button>
        </div>
      </form>
    </div>
  );
};
