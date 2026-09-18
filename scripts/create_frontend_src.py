import pathlib

base = pathlib.Path(r'D:\Btech\PROJECTS\AquaGuard_AI\frontend\src')

files = {}

# Types
files['types/index.ts'] = '''export type BehaviorClass = 'normal' | 'distress' | 'potential_drowning';
export type AlertSeverity = 'warning' | 'critical';
export type AlertStatus = 'active' | 'acknowledged' | 'resolved' | 'false_alarm';
export type CameraStatus = 'online' | 'offline' | 'error';

export interface TrackedPerson {
  trackId: number;
  behavior: BehaviorClass;
  confidence: number;
  cx: number;
  cy: number;
  bbox: [number, number, number, number];
  frames: number;
}

export interface Alert {
  id: number;
  alertUid: string;
  trackId: number;
  severity: AlertSeverity;
  status: AlertStatus;
  behavior: BehaviorClass;
  confidence: number;
  triggeredAt: string;
  acknowledgedAt?: string;
  cameraId?: number;
  consecutiveFrames: number;
  alertLatencyMs?: number;
}

export interface Experiment {
  id: number;
  experimentUid: string;
  name: string;
  description?: string;
  modelType: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  createdAt: string;
}

export interface ExperimentMetrics {
  precision?: number;
  recall?: number;
  f1Score?: number;
  map50?: number;
  falsePositiveRate?: number;
  falseNegativeRate?: number;
  avgFps?: number;
  avgInferenceLatencyMs?: number;
  avgAlertLatencyMs?: number;
  confusionMatrixJson?: string;
}

export interface SystemMetrics {
  cpuPercent: number;
  ramPercent: number;
  ramUsedGb: number;
  gpuAvailable: boolean;
  fps?: number;
  latencyMs?: number;
}
'''

# API service
files['services/api.ts'] = """import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = Bearer ;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

export const authAPI = {
  login: (email: string, password: string) =>
    api.post('/api/auth/login', { email, password }),
  logout: () => api.post('/api/auth/logout'),
};

export const systemAPI = {
  health: () => api.get('/health'),
};

export const alertAPI = {
  list: (params?: Record<string, string>) => api.get('/api/alerts', { params }),
  acknowledge: (id: number) => api.post(/api/alerts//acknowledge),
  resolve: (id: number) => api.post(/api/alerts//resolve),
};

export const experimentAPI = {
  list: () => api.get('/api/experiments'),
  create: (data: Record<string, unknown>) => api.post('/api/experiments', data),
  getMetrics: (id: number) => api.get(/api/experiments//metrics),
};
"""

# WebSocket hook
files['hooks/useWebSocket.ts'] = """import { useEffect, useRef, useState, useCallback } from 'react';

type WSStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export function useWebSocket(url: string) {
  const ws = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<WSStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<unknown>(null);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;
    setStatus('connecting');
    const socket = new WebSocket(url);
    ws.current = socket;

    socket.onopen = () => setStatus('connected');
    socket.onmessage = (e) => {
      try { setLastMessage(JSON.parse(e.data)); }
      catch { setLastMessage(e.data); }
    };
    socket.onerror = () => setStatus('error');
    socket.onclose = () => {
      setStatus('disconnected');
      setTimeout(connect, 3000); // auto-reconnect
    };
  }, [url]);

  const disconnect = useCallback(() => {
    ws.current?.close();
    ws.current = null;
  }, []);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  return { status, lastMessage };
}
"""

# Main App.tsx with router
files['App.tsx'] = """import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
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
"""

# main.tsx
files['main.tsx'] = """import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
"""

for rel, content in files.items():
    p = base / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')
    print(f'Written: {rel}')

print('Frontend src files created.')
