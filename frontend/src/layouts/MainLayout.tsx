import { Outlet, NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Video, Upload, Bell, Users,
  FlaskConical, Activity, Waves,
} from 'lucide-react';

const navItems = [
  { path: '/dashboard',     icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/monitoring',    icon: Video,           label: 'Live Monitoring' },
  { path: '/video-testing', icon: Upload,          label: 'Video Testing' },
  { path: '/alerts',        icon: Bell,            label: 'Alerts' },
  { path: '/people',        icon: Users,           label: 'People Tracking' },
  { path: '/research',      icon: FlaskConical,    label: 'Research' },
  { path: '/system',        icon: Activity,        label: 'System' },
];

export default function MainLayout() {
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
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg,#0090b0,#00b5d4)' }}
          >
            <Waves size={16} className="text-white" />
          </div>
          <div>
            <p className="font-bold text-white text-sm">AquaGuard AI</p>
            <p className="text-xs" style={{ color: '#64748b' }}>Safety Monitor</p>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map(({ path, icon: Icon, label }) => (
            <NavLink
              key={path}
              to={path}
              style={({ isActive }) =>
                isActive ? { background: 'rgba(0,181,212,0.1)', color: '#22d3ee' } : {}
              }
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'text-cyan-400'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-4 py-4 border-t" style={{ borderColor: 'rgba(51,65,85,0.5)' }}>
          <div className="flex items-center gap-2 text-xs" style={{ color: '#64748b' }}>
            <div className="w-2 h-2 rounded-full bg-green-400" />
            <span>Demo Mode Active</span>
          </div>
          <p className="text-xs mt-1" style={{ color: '#475569' }}>v1.0.0 | Phase 1</p>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}