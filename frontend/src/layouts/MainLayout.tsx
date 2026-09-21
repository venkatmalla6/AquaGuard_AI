import { useEffect, useState } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Video, Upload, Bell, Users,
  FlaskConical, Activity, Waves, AlertTriangle, Volume2, VolumeX
} from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket';
import { alertAudio } from '../utils/audioAlert';
import { browserNotification } from '../utils/browserNotification';

const navItems = [
  { path: '/dashboard',     icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/monitoring',    icon: Video,           label: 'Live Monitoring' },
  { path: '/video-testing', icon: Upload,          label: 'Video Testing' },
  { path: '/alerts',        icon: Bell,            label: 'Alerts & Dispatch' },
  { path: '/people',        icon: Users,           label: 'People Tracking' },
  { path: '/research',      icon: FlaskConical,    label: 'Research' },
  { path: '/system',        icon: Activity,        label: 'System' },
];

interface AlertPayload {
  type: string;
  alert?: {
    id: number;
    track_id: number;
    severity: string;
    behavior: string;
  };
}

export default function MainLayout() {
  const location = useLocation();
  const [isMuted, setIsMuted] = useState(alertAudio.isMuted());
  const [activeEmergency, setActiveEmergency] = useState<{ id: number; track: number } | null>(null);

  // Connect to global emergency alert websocket
  const wsUrl = (import.meta.env.VITE_WS_URL || 'ws://localhost:8000') + '/ws/alerts';
  const { lastMessage } = useWebSocket<AlertPayload>(wsUrl);

  useEffect(() => {
    if (lastMessage && lastMessage.type === 'emergency_alert' && lastMessage.alert) {
      const { id, track_id, severity } = lastMessage.alert;
      setActiveEmergency({ id, track: track_id });

      if (severity === 'critical' || severity === 'CRITICAL') {
        if (!alertAudio.isMuted()) {
          alertAudio.playCriticalSiren();
        }
        browserNotification.sendEmergencyAlert(
          '🚨 CRITICAL DROWNING DETECTED',
          `Incident #${id}: Person #${track_id} requires immediate emergency extraction!`
        );
      } else {
        alertAudio.playWarningChime();
      }
    }
  }, [lastMessage]);

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: '#020617' }}>
      <aside
        className="w-64 flex-shrink-0 border-r flex flex-col"
        style={{ background: '#0f172a', borderColor: 'rgba(51,65,85,0.5)' }}
      >
        <div
          className="flex items-center gap-3 px-6 py-5 border-b"
          style={{ borderColor: 'rgba(51,65,85,0.5)' }}
        >
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center shadow-md shadow-cyan-500/20"
            style={{ background: 'linear-gradient(135deg,#0090b0,#00b5d4)' }}
          >
            <Waves size={16} className="text-white" />
          </div>
          <div>
            <p className="font-bold text-white text-sm">AquaGuard AI</p>
            <p className="text-xs text-cyan-400 font-medium">Edge Safety Monitor</p>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map(({ path, icon: Icon, label }) => {
            const isAlerts = path === '/alerts';
            return (
              <NavLink
                key={path}
                to={path}
                style={({ isActive }) =>
                  isActive ? { background: 'rgba(0,181,212,0.1)', color: '#22d3ee' } : {}
                }
                className={({ isActive }) =>
                  `flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'text-cyan-400'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                  }`
                }
              >
                <div className="flex items-center gap-3">
                  <Icon size={16} />
                  <span>{label}</span>
                </div>
                {isAlerts && activeEmergency && (
                  <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Siren & Status Footer */}
        <div className="px-4 py-3.5 border-t space-y-2.5" style={{ borderColor: 'rgba(51,65,85,0.5)' }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs" style={{ color: '#64748b' }}>
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-slate-300 font-medium">Mesh Online</span>
            </div>
            <button
              onClick={() => {
                const next = alertAudio.toggleMute();
                setIsMuted(next);
              }}
              className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 transition-colors"
              title={isMuted ? 'Alarm muted (click to unmute)' : 'Alarm active (click to mute)'}
            >
              {isMuted ? <VolumeX size={14} /> : <Volume2 size={14} className="text-red-400" />}
            </button>
          </div>

          <p className="text-[11px] text-slate-500 font-mono">
            v1.0.0 | Phase 11 Dispatch Mesh
          </p>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto flex flex-col">
        {/* Emergency Alert Sticky Banner */}
        {activeEmergency && location.pathname !== '/alerts' && (
          <div className="bg-red-600/95 text-white px-4 py-2.5 flex items-center justify-between shadow-xl animate-pulse">
            <div className="flex items-center gap-2.5 text-xs font-bold">
              <AlertTriangle size={16} />
              <span>EMERGENCY DISPATCH: Critical incident #{activeEmergency.id} active on Swimmer #{activeEmergency.track}!</span>
            </div>
            <div className="flex items-center gap-2">
              <NavLink
                to="/alerts"
                className="px-2.5 py-1 rounded bg-white text-red-700 font-bold text-xs hover:bg-slate-100"
              >
                Go to Alerts Desk
              </NavLink>
              <button
                onClick={() => setActiveEmergency(null)}
                className="text-white/80 hover:text-white text-xs px-1"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        <div className="flex-1">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
