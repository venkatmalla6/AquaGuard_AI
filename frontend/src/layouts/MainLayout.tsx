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

interface NavItemConfig {
  path: string;
  icon: any;
  label: string;
  desc: string;
  roles: string[];
}

const navItems: NavItemConfig[] = [
  {
    path: '/dashboard',
    icon: LayoutDashboard,
    label: 'Dashboard',
    desc: 'Real-Time Pool Safety Overview',
    roles: ['admin', 'operator', 'researcher'],
  },
  {
    path: '/monitoring',
    icon: Video,
    label: 'Live Monitoring',
    desc: 'Dual Camera Streams & YOLOV8 Inference',
    roles: ['admin', 'operator'],
  },
  {
    path: '/alerts',
    icon: Bell,
    label: 'Alerts & Dispatch',
    desc: 'Emergency Incident Desk & Sirens',
    roles: ['admin', 'operator'],
  },
  {
    path: '/people',
    icon: Users,
    label: 'People Tracking',
    desc: 'Multi-Swimmer ByteTrack Trajectories',
    roles: ['admin', 'operator', 'researcher'],
  },
  {
    path: '/video-testing',
    icon: Upload,
    label: 'Video Testing',
    desc: 'Synthetic & Offline Video Pipeline',
    roles: ['admin', 'researcher'],
  },
  {
    path: '/research',
    icon: FlaskConical,
    label: 'Research',
    desc: 'Edge vs Cloud Benchmark Suite',
    roles: ['admin', 'researcher'],
  },
  {
    path: '/system',
    icon: Activity,
    label: 'System',
    desc: 'Hardware Health & ONNX Runtime',
    roles: ['admin', 'researcher'],
  },
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

const roleStyles: Record<string, { badge: string; pillBorder: string; avatarBg: string; titleSub: string }> = {
  admin: {
    badge: 'bg-cyan-950/80 text-cyan-300 border-cyan-700/60',
    pillBorder: 'rgba(14, 165, 233, 0.4)',
    avatarBg: 'linear-gradient(135deg, #0ea5e9, #0284c7)',
    titleSub: 'Full Mission Control',
  },
  operator: {
    badge: 'bg-amber-950/80 text-amber-300 border-amber-700/60',
    pillBorder: 'rgba(245, 158, 11, 0.4)',
    avatarBg: 'linear-gradient(135deg, #f59e0b, #d97706)',
    titleSub: 'Lifeguard Surveillance Station',
  },
  researcher: {
    badge: 'bg-purple-950/80 text-purple-300 border-purple-700/60',
    pillBorder: 'rgba(168, 85, 247, 0.4)',
    avatarBg: 'linear-gradient(135deg, #a855f7, #7c3aed)',
    titleSub: 'AI & Edge Vision Lab',
  },
};

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

  const userRole = (user.role || 'admin').toLowerCase();
  const visibleNavItems = navItems.filter((item) => item.roles.includes(userRole));
  const currentRoleStyle = roleStyles[userRole] || roleStyles.admin;

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
    alertAudio.stopAll();
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    navigate('/login', { replace: true });
  };

  const currentModule = visibleNavItems.find((item) => item.path === location.pathname) || visibleNavItems[0] || navItems[0];
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
            style={{ background: currentRoleStyle.avatarBg }}
          >
            <Waves size={18} className="text-white" />
          </div>
          <div className="min-w-0">
            <p className="font-bold text-white text-sm tracking-wide">AquaGuard AI</p>
            <p className="text-[11px] text-slate-400 font-medium truncate">{currentRoleStyle.titleSub}</p>
          </div>
        </div>

        {/* Dynamic Nav Links filtered for active role */}
        <div className="px-4 pt-3 pb-1">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
            {userRole.toUpperCase()} MODULES ({visibleNavItems.length})
          </p>
        </div>

        <nav className="flex-1 px-3 py-1 space-y-1 overflow-y-auto">
          {visibleNavItems.map(({ path, icon: Icon, label }) => {
            const isAlerts = path === '/alerts';
            return (
              <NavLink
                key={path}
                to={path}
                style={({ isActive }) =>
                  isActive
                    ? {
                        background:
                          userRole === 'operator'
                            ? 'rgba(245,158,11,0.12)'
                            : userRole === 'researcher'
                            ? 'rgba(168,85,247,0.12)'
                            : 'rgba(0,181,212,0.12)',
                        color:
                          userRole === 'operator'
                            ? '#fbbf24'
                            : userRole === 'researcher'
                            ? '#c084fc'
                            : '#22d3ee',
                      }
                    : {}
                }
                className={({ isActive }) =>
                  'flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ' +
                  (isActive
                    ? 'font-semibold'
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
              borderColor: currentRoleStyle.pillBorder,
            }}
          >
            <div className="flex items-center gap-2.5 min-w-0">
              <div
                className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center font-bold text-xs text-white uppercase shadow-sm"
                style={{ background: currentRoleStyle.avatarBg }}
              >
                {user.name ? user.name.charAt(0) : 'U'}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-slate-200 truncate">{user.name}</p>
                <p className="text-[10px] text-slate-400 truncate font-mono">{user.email}</p>
              </div>
            </div>
            <span className={'px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider border ' + currentRoleStyle.badge}>
              {userRole}
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
        {activeEmergency && location.pathname !== '/alerts' && userRole !== 'researcher' && (
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

        {/* Universal Top Navigation Header */}
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
                background:
                  userRole === 'operator'
                    ? 'rgba(245, 158, 11, 0.12)'
                    : userRole === 'researcher'
                    ? 'rgba(168, 85, 247, 0.12)'
                    : 'rgba(14, 165, 233, 0.12)',
                borderColor: currentRoleStyle.pillBorder,
              }}
            >
              <CurrentIcon
                size={18}
                className={
                  userRole === 'operator'
                    ? 'text-amber-400'
                    : userRole === 'researcher'
                    ? 'text-purple-400'
                    : 'text-cyan-400'
                }
              />
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

          {/* Center Badges */}
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
                borderColor: currentRoleStyle.pillBorder,
              }}
            >
              <div
                className="w-6 h-6 rounded-full flex items-center justify-center font-bold text-[11px] text-white uppercase shadow-inner"
                style={{ background: currentRoleStyle.avatarBg }}
              >
                {user.name ? user.name.charAt(0) : 'U'}
              </div>
              <div className="hidden md:block text-left">
                <p className="text-xs font-semibold text-white leading-tight">
                  {user.name}
                </p>
                <p className={'text-[9px] font-mono uppercase tracking-wider font-bold ' + (
                  userRole === 'operator' ? 'text-amber-400' : userRole === 'researcher' ? 'text-purple-400' : 'text-cyan-400'
                )}>
                  {userRole}
                </p>
              </div>
            </div>

            {/* Universal Logout Button */}
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