import { Outlet, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { apiClient } from '../services/apiClient';
import { PushNotificationOptIn } from '../components/PushNotificationOptIn';

export const AppLayout = () => {
  const { user, clearSession, refreshToken } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      if (refreshToken) {
        await apiClient.post('/auth/logout', { refresh_token: refreshToken });
      }
    } catch (e) {
      // Ignore errors on logout
    } finally {
      clearSession();
      navigate('/login');
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-6">
              <div className="flex-shrink-0 flex items-center cursor-pointer" onClick={() => navigate('/')}>
                <span className="text-xl font-bold text-primary-600">CampusFlow</span>
              </div>
              <div className="hidden sm:flex items-center space-x-4">
                <button
                  onClick={() => navigate('/')}
                  className="text-xs font-semibold text-gray-700 hover:text-blue-600 px-2 py-1 rounded transition"
                >
                  Dashboard
                </button>
                {(user?.role === 'OFFICER' || user?.role === 'ADMIN') && (
                  <button
                    onClick={() => navigate('/analytics')}
                    className="text-xs font-semibold text-gray-700 hover:text-blue-600 px-2 py-1 rounded transition flex items-center space-x-1"
                  >
                    <svg className="w-3.5 h-3.5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    <span>Analytics</span>
                  </button>
                )}
                {user?.role === 'ADMIN' && (
                  <>
                    <button
                      onClick={() => navigate('/admin/users')}
                      className="text-xs font-semibold text-gray-700 hover:text-blue-600 px-2 py-1 rounded transition flex items-center space-x-1"
                    >
                      <svg className="w-3.5 h-3.5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                      </svg>
                      <span>Users</span>
                    </button>
                    <button
                      onClick={() => navigate('/admin/audit-logs')}
                      className="text-xs font-semibold text-gray-700 hover:text-blue-600 px-2 py-1 rounded transition flex items-center space-x-1"
                    >
                      <svg className="w-3.5 h-3.5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span>Audit Logs</span>
                    </button>
                  </>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <PushNotificationOptIn />
              <button
                onClick={() => navigate('/notifications')}
                className="p-1.5 text-gray-600 hover:text-blue-600 hover:bg-gray-50 rounded-lg transition-colors flex items-center space-x-1"
                title="Notifications"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
                <span className="text-xs font-semibold hidden sm:inline">Notifications</span>
              </button>
              <span className="text-sm text-gray-700 font-medium">
                {user?.full_name} ({user?.role})
              </span>
              <button
                onClick={handleLogout}
                className="text-sm text-red-600 hover:text-red-800 font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>


      <main className="flex-1 max-w-7xl w-full mx-auto py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  );
};
