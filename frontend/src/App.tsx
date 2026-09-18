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

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('access_token') || 'demo-mode';
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
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
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="monitoring" element={<LiveMonitoringPage />} />
            <Route path="video-testing" element={<VideoTestingPage />} />
            <Route path="alerts" element={<AlertsPage />} />
            <Route path="people" element={<PeopleTrackingPage />} />
            <Route path="research" element={<ResearchPage />} />
            <Route path="system" element={<SystemPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
