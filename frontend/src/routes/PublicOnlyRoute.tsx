import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

export const PublicOnlyRoute = () => {
  const { isAuthenticated } = useAuthStore();

  // If already logged in, don't show login page
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
};
