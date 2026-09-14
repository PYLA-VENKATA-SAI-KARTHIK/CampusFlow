import { lazy, Suspense } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { AuthLayout } from './layouts/AuthLayout';
import { AppLayout } from './layouts/AppLayout';
import { LoadingSpinner } from './components/ui/StatusFeedback';
import { ErrorBoundary } from './components/ErrorBoundary';

// Eagerly loaded entry shell pages
import { LoginPage } from './pages/LoginPage';
import { ActivateAccountPage } from './pages/ActivateAccountPage';
import { DashboardPage } from './pages/DashboardPage';
import { UnauthorizedPage } from './pages/UnauthorizedPage';
import { NotFoundPage } from './pages/NotFoundPage';

// Route guards
import { ProtectedRoute } from './routes/ProtectedRoute';
import { PublicOnlyRoute } from './routes/PublicOnlyRoute';

// Lazy-loaded feature pages (Code-Split)
const PlacementDrivesPage = lazy(() =>
  import('./pages/PlacementDrivesPage').then((m) => ({ default: m.PlacementDrivesPage }))
);
const DriveDetailsPage = lazy(() =>
  import('./pages/DriveDetailsPage').then((m) => ({ default: m.DriveDetailsPage }))
);
const MyApplicationsPage = lazy(() =>
  import('./pages/MyApplicationsPage').then((m) => ({ default: m.MyApplicationsPage }))
);
const MyProfilePage = lazy(() =>
  import('./pages/MyProfilePage').then((m) => ({ default: m.MyProfilePage }))
);
const SettingsPage = lazy(() =>
  import('./pages/SettingsPage').then((m) => ({ default: m.SettingsPage }))
);
const NotificationCenterPage = lazy(() =>
  import('./pages/NotificationCenterPage').then((m) => ({ default: m.NotificationCenterPage }))
);
const AnalyticsDashboardPage = lazy(() =>
  import('./pages/AnalyticsDashboardPage').then((m) => ({ default: m.AnalyticsDashboardPage }))
);
const DriveAnalyticsPage = lazy(() =>
  import('./pages/DriveAnalyticsPage').then((m) => ({ default: m.DriveAnalyticsPage }))
);
const AdminUsersPage = lazy(() =>
  import('./pages/AdminUsersPage').then((m) => ({ default: m.AdminUsersPage }))
);
const AdminAuditLogsPage = lazy(() =>
  import('./pages/AdminAuditLogsPage').then((m) => ({ default: m.AdminAuditLogsPage }))
);
const PreparationHubPage = lazy(() =>
  import('./pages/PreparationHubPage').then((m) => ({ default: m.PreparationHubPage }))
);
const AssessmentsPage = lazy(() =>
  import('./pages/AssessmentsPage').then((m) => ({ default: m.AssessmentsPage }))
);
const AssessmentBuilderPage = lazy(() =>
  import('./pages/AssessmentBuilderPage').then((m) => ({ default: m.AssessmentBuilderPage }))
);
const AssessmentPlayerPage = lazy(() =>
  import('./pages/AssessmentPlayerPage').then((m) => ({ default: m.AssessmentPlayerPage }))
);
const AssessmentResultPage = lazy(() =>
  import('./pages/AssessmentResultPage').then((m) => ({ default: m.AssessmentResultPage }))
);
const MasterStudentListPage = lazy(() =>
  import('./pages/MasterStudentListPage').then((m) => ({ default: m.MasterStudentListPage }))
);

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Suspense
          fallback={
            <LoadingSpinner
              size="lg"
              label="Loading workspace..."
              className="min-h-[50vh] flex items-center justify-center"
            />
          }
        >
          <Routes>
            {/* Public Routes (only for unauthenticated users) */}
            <Route element={<PublicOnlyRoute />}>
              <Route element={<AuthLayout />}>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<ActivateAccountPage />} />
                <Route path="/activate" element={<ActivateAccountPage />} />
              </Route>

            </Route>

            {/* Protected Routes (requires authentication) */}
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/drives" element={<PlacementDrivesPage />} />
                <Route path="/drives/:id" element={<DriveDetailsPage />} />
                <Route path="/applications" element={<MyApplicationsPage />} />
                <Route path="/preparation" element={<PreparationHubPage />} />
                <Route path="/assessments" element={<AssessmentsPage />} />
                <Route path="/assessments/results/:attemptId" element={<AssessmentResultPage />} />
                <Route path="/profile" element={<MyProfilePage />} />
                <Route path="/resume" element={<MyProfilePage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/notifications" element={<NotificationCenterPage />} />
                <Route path="/unauthorized" element={<UnauthorizedPage />} />

                {/* Student Assessment Player */}
                <Route element={<ProtectedRoute allowedRoles={['STUDENT']} />}>
                  <Route path="/assessments/player/:attemptId" element={<AssessmentPlayerPage />} />
                </Route>

                {/* Officer & Admin Assessment Builder & Analytics */}
                <Route element={<ProtectedRoute allowedRoles={['OFFICER', 'ADMIN']} />}>
                  <Route path="/assessments/builder/:id" element={<AssessmentBuilderPage />} />
                  <Route path="/analytics" element={<AnalyticsDashboardPage />} />
                  <Route path="/drives/:id/analytics" element={<DriveAnalyticsPage />} />
                  <Route path="/students/master" element={<MasterStudentListPage />} />
                  <Route path="/officer/students" element={<MasterStudentListPage />} />
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
        </Suspense>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
