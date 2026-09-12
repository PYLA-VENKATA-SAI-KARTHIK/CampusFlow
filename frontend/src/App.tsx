import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { AuthLayout } from './layouts/AuthLayout';
import { AppLayout } from './layouts/AppLayout';
import { LoginPage } from './pages/LoginPage';
import { ActivateAccountPage } from './pages/ActivateAccountPage';
import { DashboardPage } from './pages/DashboardPage';
import { PlacementDrivesPage } from './pages/PlacementDrivesPage';
import { MyApplicationsPage } from './pages/MyApplicationsPage';
import { MyProfilePage } from './pages/MyProfilePage';
import { SettingsPage } from './pages/SettingsPage';
import { NotificationCenterPage } from './pages/NotificationCenterPage';
import { AnalyticsDashboardPage } from './pages/AnalyticsDashboardPage';
import { DriveAnalyticsPage } from './pages/DriveAnalyticsPage';
import { AdminUsersPage } from './pages/AdminUsersPage';
import { AdminAuditLogsPage } from './pages/AdminAuditLogsPage';
import { UnauthorizedPage } from './pages/UnauthorizedPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { ProtectedRoute } from './routes/ProtectedRoute';
import { PublicOnlyRoute } from './routes/PublicOnlyRoute';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes (only for unauthenticated users) */}
        <Route element={<PublicOnlyRoute />}>
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/activate" element={<ActivateAccountPage />} />
          </Route>
        </Route>

        {/* Protected Routes (requires authentication) */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/drives" element={<PlacementDrivesPage />} />
            <Route path="/applications" element={<MyApplicationsPage />} />
            <Route path="/profile" element={<MyProfilePage />} />
            <Route path="/resume" element={<MyProfilePage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/notifications" element={<NotificationCenterPage />} />
            <Route path="/unauthorized" element={<UnauthorizedPage />} />

            {/* Officer & Admin Analytics */}
            <Route element={<ProtectedRoute allowedRoles={['OFFICER', 'ADMIN']} />}>
              <Route path="/analytics" element={<AnalyticsDashboardPage />} />
              <Route path="/drives/:id/analytics" element={<DriveAnalyticsPage />} />
            </Route>

            {/* Admin Only Routes */}
            <Route element={<ProtectedRoute allowedRoles={['ADMIN']} />}>
              <Route path="/admin/users" element={<AdminUsersPage />} />
              <Route path="/admin/audit-logs" element={<AdminAuditLogsPage />} />
            </Route>
          </Route>
        </Route>

        {/* Catch-all 404 */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
