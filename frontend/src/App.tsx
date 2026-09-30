import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import MainLayout from './layouts/MainLayout';
import LoadingSpinner from './components/common/LoadingSpinner';

// Lazy load pages for performance
const LoginPage = lazy(() => import('./pages/LoginPage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const LiveMonitoringPage = lazy(() => import('./pages/LiveMonitoringPage'));
const VideoTestingPage = lazy(() => import('./pages/VideoTestingPage'));
const AlertsPage = lazy(() => import('./pages/AlertsPage'));
const PeopleTrackingPage = lazy(() => import('./pages/PeopleTrackingPage'));
const ResearchPage = lazy(() => import('./pages/ResearchPage'));
const SystemPage = lazy(() => import('./pages/SystemPage'));

function getUserRole(): string {
  try {
    const raw = localStorage.getItem('user');
    if (raw) {
      const u = JSON.parse(raw);
      if (u.role) return u.role.toLowerCase();
    }
  } catch {
    // fallback
  }
  return 'admin';
}

export function getDefaultHomeForRole(role: string): string {
  if (role === 'operator') return '/monitoring';
  if (role === 'researcher') return '/research';
  return '/dashboard';
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('access_token');
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function RoleRoute({ allowedRoles, children }: { allowedRoles: string[]; children: React.ReactNode }) {
  const role = getUserRole();
  if (!allowedRoles.includes(role)) {
    return <Navigate to={getDefaultHomeForRole(role)} replace />;
  }
  return <>{children}</>;
}

function RootRedirect() {
  const role = getUserRole();
  return <Navigate to={getDefaultHomeForRole(role)} replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<RootRedirect />} />
            
            {/* Dashboard: Accessible by all roles */}
            <Route
              path="dashboard"
              element={
                <RoleRoute allowedRoles={['admin', 'operator', 'researcher']}>
                  <DashboardPage />
                </RoleRoute>
              }
            />

            {/* Live Monitoring: Operator & Admin */}
            <Route
              path="monitoring"
              element={
                <RoleRoute allowedRoles={['admin', 'operator']}>
                  <LiveMonitoringPage />
                </RoleRoute>
              }
            />

            {/* Emergency Alerts & Dispatch: Operator & Admin */}
            <Route
              path="alerts"
              element={
                <RoleRoute allowedRoles={['admin', 'operator']}>
                  <AlertsPage />
                </RoleRoute>
              }
            />

            {/* People Tracking: All roles */}
            <Route
              path="people"
              element={
                <RoleRoute allowedRoles={['admin', 'operator', 'researcher']}>
                  <PeopleTrackingPage />
                </RoleRoute>
              }
            />

            {/* Video Testing: Researcher & Admin */}
            <Route
              path="video-testing"
              element={
                <RoleRoute allowedRoles={['admin', 'researcher']}>
                  <VideoTestingPage />
                </RoleRoute>
              }
            />

            {/* Research Benchmarks: Researcher & Admin */}
            <Route
              path="research"
              element={
                <RoleRoute allowedRoles={['admin', 'researcher']}>
                  <ResearchPage />
                </RoleRoute>
              }
            />

            {/* Hardware & System Health: Researcher & Admin */}
            <Route
              path="system"
              element={
                <RoleRoute allowedRoles={['admin', 'researcher']}>
                  <SystemPage />
                </RoleRoute>
              }
            />
          </Route>

          <Route path="*" element={<RootRedirect />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}