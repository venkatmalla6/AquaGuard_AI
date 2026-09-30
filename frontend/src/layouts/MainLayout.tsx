import { useEffect, useState } from 'react';
import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Video, Upload, Bell, Users,
  FlaskConical, Activity, Waves, AlertTriangle, Volume2, VolumeX,
  LogOut, Shield, ChevronRight
} from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket';
import { alertAudio } from '../utils/audioAlert';
import { browserNotification } from '../utils/browserNotification';

const navItems = [
  { path: '/dashboard',     icon: LayoutDashboard, label: 'Dashboard',         desc: 'Real-Time Pool Safety Overview' },
  { path: '/monitoring',    icon: Video,           label: 'Live Monitoring',    desc: 'Dual Camera Streams & YOLOV8 Inference' },
  { path: '/video-testing', icon: Upload,          label: 'Video Testing',      desc: 'Synthetic & Offline Video Pipeline' },
  { path: '/alerts',        icon: Bell,            label: 'Alerts & Dispatch',  desc: 'Emergency Incident Desk & Sirens' },
  { path: '/people',        icon: Users,           label: 'People Tracking',    desc: 'Multi-Swimmer ByteTrack Trajectories' },
  { path: '/research',      icon: FlaskConical,    label: 'Research',           desc: 'Edge vs Cloud Benchmark Suite' },
  { path: '/system',        icon: Activity,        label: 'System',             desc: 'Hardware Health & ONNX Runtime' },
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

interface CurrentUser {
  id?: number;
  email: string;
  name: string;
  role: string;
}

export default function MainLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const [isMuted, setIsMuted] = useState(alertAudio.isMuted());
  const [activeEmergency, setActiveEmergency] = useState<{ id: number; track: number } | null>(null);

  // Parse current user from localStorage
  const [user, setUser] = useState<CurrentUser>(() => {
    try {
      const stored = localStorage.getItem('user');
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed.email) return parsed;
      }
    } catch {
      // fallback
    }
    return {
      email: 'admin@aquaguard.ai',
      name: 'Safety Commander',
      role: 'admin',
    };
  });

  useEffect(() => {
    try {
      const stored = localStorage.getItem('user');
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed.email) setUser(parsed);
      }
    } catch {
      // ignore
    }
  }, [location.pathname]);

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
          'CRITICAL DROWNING DETECTED',
          'Incident #' + id + ': Person #' + track_id + ' requires immediate emergency extraction!'
        );
      } else {
        alertAudio.playWarningChime();
      }
    }
  }, [lastMessage]);

  const handleLogout = () => {
    // Silence alarms immediately
    alertAudio.stopAll();
    // Clear user tokens and credentials
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    // Navigate cleanly to login page
    navigate('/login', { replace: true });
  };

  const currentModule = navItems.find((item) => item.path === location.pathname) || navItems[0];
  const CurrentIcon = currentModule.icon;

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: '#020617' }}>
      {/* Sidebar Navigation */}
      <aside
        className="w-64 flex-shrink-0 border-r flex flex-col"
        style={{ background: '#0f172a', borderColor: 'rgba(51,65,85,0.5)' }}
      >
        {/* Brand Header */}
        <div
          className="flex items-center gap-3 px-5 py-4 border-b"
          style={{ borderColor: 'rgba(51,65,85,0.5)' }}
        >
          <div
            className="w-9 h-9 rounded-lg flex items-center justify-center shadow-md shadow-cyan-500/20"
            style={{ background: 'linear-gradient(135deg,#0090b0,#00b5d4)' }}
          >
            <Waves size={18} className="text-white" />
          </div>
          <div className="min-w-0">
            <p className="font-bold text-white text-sm tracking-wide">AquaGuard AI</p>
            <p className="text-[11px] text-cyan-400 font-semibold truncate">Edge Safety Monitor</p>
          </div>
        </div>

        {/* Nav Links */}
        <nav className="flex-1 px-3 py-3 space-y-1 overflow-y-auto">
          {navItems.map(({ path, icon: Icon, label }) => {
            const isAlerts = path === '/alerts';
            return (
              <NavLink
                key={path}
                to={path}
                style={({ isActive }) =>
                  isActive ? { background: 'rgba(0,181,212,0.12)', color: '#22d3ee' } : {}
                }
                className={({ isActive }) =>
                  'flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ' +
                  (isActive
                    ? 'text-cyan-400 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/70')
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

        {/* Sidebar Footer with Profile & Dedicated Logout Button */}
        <div className="p-3 border-t space-y-2.5" style={{ borderColor: 'rgba(51,65,85,0.5)' }}>
          {/* User profile card */}
          <div
            className="p-2.5 rounded-lg border flex items-center justify-between"
            style={{
              background: 'rgba(15, 23, 42, 0.7)',
              borderColor: 'rgba(51, 65, 85, 0.6)',
            }}
          >
            <div className="flex items-center gap-2.5 min-w-0">
              <div
                className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center font-bold text-xs text-white uppercase shadow-sm"
                style={{ background: 'linear-gradient(135deg, #0ea5e9, #0369a1)' }}
              >
                {user.name ? user.name.charAt(0) : 'U'}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-slate-200 truncate">{user.name}</p>
                <p className="text-[10px] text-slate-400 truncate font-mono">{user.email}</p>
              </div>
            </div>
            <span className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-cyan-950/80 text-cyan-300 border border-cyan-700/50">
              {user.role}
            </span>
          </div>

          {/* Sidebar Sign Out Button */}
          <button
            id="sidebar-logout-btn"
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-bold transition-all border text-red-400 hover:text-white hover:bg-red-600/25 border-red-500/30 shadow-sm cursor-pointer"
            title="Sign out of AquaGuard AI"
          >
            <LogOut size={14} />
            <span>Sign Out</span>
          </button>

          {/* Siren & Status Info */}
          <div className="flex items-center justify-between text-xs pt-1 px-1" style={{ color: '#64748b' }}>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-slate-400 text-[11px] font-medium">Mesh Online</span>
            </div>
            <button
              onClick={() => {
                const next = alertAudio.toggleMute();
                setIsMuted(next);
              }}
              className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 transition-colors cursor-pointer"
              title={isMuted ? 'Alarm muted (click to unmute)' : 'Alarm active (click to mute)'}
            >
              {isMuted ? <VolumeX size={13} /> : <Volume2 size={13} className="text-red-400" />}
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area with Universal Top Bar */}
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

        {/* Universal Top Navigation Header (Present across EVERY Module) */}
        <header
          className="h-16 px-6 border-b flex items-center justify-between flex-shrink-0 z-10 backdrop-blur-md"
          style={{
            background: 'rgba(15, 23, 42, 0.85)',
            borderColor: 'rgba(51, 65, 85, 0.5)',
          }}
        >
          {/* Left: Active Module Breadcrumb */}
          <div className="flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-lg flex items-center justify-center border shadow-sm"
              style={{
                background: 'rgba(14, 165, 233, 0.12)',
                borderColor: 'rgba(14, 165, 233, 0.3)',
              }}
            >
              <CurrentIcon size={18} className="text-cyan-400" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  AquaGuard AI
                </span>
                <ChevronRight size={12} className="text-slate-600" />
                <span className="text-sm font-bold text-white tracking-wide">
                  {currentModule.label}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium hidden sm:block">
                {currentModule.desc}
              </p>
            </div>
          </div>

          {/* Center Badges: Real-time Edge status */}
          <div className="hidden lg:flex items-center gap-2">
            <div
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium border"
              style={{
                background: 'rgba(16, 185, 129, 0.1)',
                borderColor: 'rgba(16, 185, 129, 0.3)',
                color: '#34d399',
              }}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>ONNX CPU Engine</span>
            </div>

            <div
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium border"
              style={{
                background: 'rgba(56, 189, 248, 0.1)',
                borderColor: 'rgba(56, 189, 248, 0.3)',
                color: '#38bdf8',
              }}
            >
              <Shield size={12} />
              <span>Zero-False-Alarm Mesh</span>
            </div>
          </div>

          {/* Right: User Pill & Universal Logout Button */}
          <div className="flex items-center gap-3">
            {/* User Profile Pill */}
            <div
              className="flex items-center gap-2 px-2.5 py-1 rounded-lg border"
              style={{
                background: 'rgba(30, 41, 59, 0.6)',
                borderColor: 'rgba(51, 65, 85, 0.6)',
              }}
            >
              <div
                className="w-6 h-6 rounded-full flex items-center justify-center font-bold text-[11px] text-white uppercase shadow-inner"
                style={{ background: 'linear-gradient(135deg, #0ea5e9, #0284c7)' }}
              >
                {user.name ? user.name.charAt(0) : 'U'}
              </div>
              <div className="hidden md:block text-left">
                <p className="text-xs font-semibold text-white leading-tight">
                  {user.name}
                </p>
                <p className="text-[9px] text-cyan-400 font-mono uppercase tracking-wider">
                  {user.role}
                </p>
              </div>
            </div>

            {/* Universal Logout Button in Top Bar */}
            <button
              id="topbar-logout-btn"
              onClick={handleLogout}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-bold transition-all shadow-sm group hover:scale-[1.02] active:scale-95 cursor-pointer"
              style={{
                background: 'rgba(239, 68, 68, 0.12)',
                borderColor: 'rgba(239, 68, 68, 0.4)',
                color: '#fca5a5',
              }}
              title="Logout and end current session"
            >
              <LogOut size={14} className="text-red-400 group-hover:text-red-300 transition-colors" />
              <span>Logout</span>
            </button>
          </div>
        </header>

        {/* Page Module Outlet */}
        <div className="flex-1">
          <Outlet />
        </div>
      </main>
    </div>
  );
}