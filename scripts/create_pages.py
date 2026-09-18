import pathlib

base = pathlib.Path(r'D:\Btech\PROJECTS\AquaGuard_AI\frontend\src')

files = {}

# Loading spinner component
files['components/common/LoadingSpinner.tsx'] = """
export default function LoadingSpinner() {
  return (
    <div className=\"flex items-center justify-center min-h-screen\" style={{background:'#020617'}}>
      <div className=\"flex flex-col items-center gap-4\">
        <div className=\"w-12 h-12 border-4 border-slate-700 border-t-cyan-400 rounded-full animate-spin\" />
        <p className=\"text-slate-400 text-sm font-medium\">Loading AquaGuard AI...</p>
      </div>
    </div>
  );
}
"""

# Main Layout with sidebar
files['layouts/MainLayout.tsx'] = """import { Outlet, NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Video, Upload, Bell, Users,
  FlaskConical, Activity, Settings, Shield, Waves
} from 'lucide-react';

const navItems = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/monitoring', icon: Video, label: 'Live Monitoring' },
  { path: '/video-testing', icon: Upload, label: 'Video Testing' },
  { path: '/alerts', icon: Bell, label: 'Alerts' },
  { path: '/people', icon: Users, label: 'People Tracking' },
  { path: '/research', icon: FlaskConical, label: 'Research' },
  { path: '/system', icon: Activity, label: 'System' },
];

export default function MainLayout() {
  return (
    <div className=\"flex h-screen overflow-hidden\" style={{background:'#020617'}}>
      {/* Sidebar */}
      <aside className=\"w-64 flex-shrink-0 border-r flex flex-col\"
        style={{background:'#0f172a', borderColor:'rgba(51,65,85,0.5)'}}>
        {/* Logo */}
        <div className=\"flex items-center gap-3 px-6 py-5 border-b\"
          style={{borderColor:'rgba(51,65,85,0.5)'}}>
          <div className=\"w-8 h-8 rounded-lg flex items-center justify-center\"
            style={{background:'linear-gradient(135deg,#0090b0,#00b5d4)'}}>
            <Waves size={16} className=\"text-white\" />
          </div>
          <div>
            <p className=\"font-bold text-white text-sm\">AquaGuard AI</p>
            <p className=\"text-xs\" style={{color:'#64748b'}}>Safety Monitor</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className=\"flex-1 px-3 py-4 space-y-1 overflow-y-auto\">
          {navItems.map(({ path, icon: Icon, label }) => (
            <NavLink
              key={path}
              to={path}
              className={({ isActive }) =>
                lex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors 
              }
              style={({ isActive }) => isActive ? {
                background:'rgba(0,181,212,0.1)',
                color:'#22d3ee',
              } : {}}
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className=\"px-4 py-4 border-t\" style={{borderColor:'rgba(51,65,85,0.5)'}}>
          <div className=\"flex items-center gap-2 text-xs\" style={{color:'#64748b'}}>
            <div className=\"w-2 h-2 rounded-full bg-green-400\" />
            <span>Demo Mode Active</span>
          </div>
          <p className=\"text-xs mt-1\" style={{color:'#475569'}}>v1.0.0 | Phase 1</p>
        </div>
      </aside>

      {/* Main content */}
      <main className=\"flex-1 overflow-y-auto\">
        <Outlet />
      </main>
    </div>
  );
}
"""

# Status badge component
files['components/common/StatusBadge.tsx'] = """import type { BehaviorClass } from '../../types';

const config = {
  normal: { label: 'NORMAL', color: '#22c55e', bg: 'rgba(34,197,94,0.1)', border: 'rgba(34,197,94,0.3)' },
  distress: { label: 'DISTRESS', color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.3)' },
  potential_drowning: { label: 'DROWNING', color: '#ef4444', bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.3)' },
};

interface Props {
  behavior: BehaviorClass;
  size?: 'sm' | 'md';
  pulse?: boolean;
}

export default function StatusBadge({ behavior, size = 'md', pulse }: Props) {
  const c = config[behavior];
  return (
    <span
      className={inline-flex items-center font-bold rounded tracking-wider  }
      style={{ color: c.color, background: c.bg, border: 1px solid  }}
    >
      {c.label}
    </span>
  );
}
"""

# Stat card
files['components/common/StatCard.tsx'] = """interface Props {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  color?: string;
  sub?: string;
}

export default function StatCard({ label, value, icon, color, sub }: Props) {
  return (
    <div className=\"glass-card p-4 fade-in\">
      <div className=\"flex items-center justify-between mb-2\">
        <p className=\"text-xs font-medium uppercase tracking-wider\" style={{color:'#64748b'}}>{label}</p>
        {icon && <span style={{color: color || '#00b5d4'}}>{icon}</span>}
      </div>
      <p className=\"text-2xl font-bold text-white\">{value}</p>
      {sub && <p className=\"text-xs mt-1\" style={{color:'#64748b'}}>{sub}</p>}
    </div>
  );
}
"""

# Dashboard page
files['pages/DashboardPage.tsx'] = """import { useEffect, useState } from 'react';
import { Activity, Users, Bell, Zap, Clock, Cpu, Wifi, WifiOff } from 'lucide-react';
import StatCard from '../components/common/StatCard';
import StatusBadge from '../components/common/StatusBadge';
import { useWebSocket } from '../hooks/useWebSocket';

const WS_URL = (import.meta.env.VITE_WS_URL || 'ws://localhost:8000') + '/ws/metrics';

// Demo tracked persons for UI demonstration
const DEMO_PERSONS = [
  { trackId: 1, behavior: 'normal' as const, confidence: 0.94, cx: 320, cy: 240 },
  { trackId: 2, behavior: 'distress' as const, confidence: 0.78, cx: 520, cy: 180 },
  { trackId: 3, behavior: 'potential_drowning' as const, confidence: 0.85, cx: 180, cy: 350 },
];

export default function DashboardPage() {
  const { status, lastMessage } = useWebSocket(WS_URL);
  const [metrics, setMetrics] = useState({ cpu: 0, ram: 0, fps: 0 });

  useEffect(() => {
    if (lastMessage && typeof lastMessage === 'object') {
      const m = lastMessage as Record<string,number>;
      setMetrics({
        cpu: m.cpu_percent ?? 0,
        ram: m.ram_percent ?? 0,
        fps: m.fps ?? 0,
      });
    }
  }, [lastMessage]);

  return (
    <div className=\"p-6 space-y-6\">
      {/* Header */}
      <div className=\"flex items-center justify-between\">
        <div>
          <h1 className=\"text-xl font-bold text-white\">Dashboard</h1>
          <p className=\"text-sm\" style={{color:'#64748b'}}>Real-time pool safety monitoring</p>
        </div>
        <div className=\"flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium\"
          style={{background:'rgba(0,181,212,0.1)', color:'#22d3ee', border:'1px solid rgba(0,181,212,0.2)'}}>
          {status === 'connected'
            ? <><Wifi size={12}/> Live</>
            : <><WifiOff size={12}/> Connecting...</>}
        </div>
      </div>

      {/* ── DEMO MODE NOTICE ── */}
      <div className=\"rounded-lg px-4 py-3 text-sm\"
        style={{background:'rgba(245,158,11,0.08)', border:'1px solid rgba(245,158,11,0.3)', color:'#fbbf24'}}>
        <strong>DEMO MODE</strong> — Simulated detections displayed. Connect a real camera or upload a video to run AI inference.
      </div>

      {/* Stats Row */}
      <div className=\"grid grid-cols-2 lg:grid-cols-4 gap-4\">
        <StatCard label=\"People Detected\" value={3} icon={<Users size={16}/>} sub=\"Demo data\" />
        <StatCard label=\"Active Alerts\" value={1} icon={<Bell size={16}/>} color=\"#ef4444\" sub=\"1 Critical\" />
        <StatCard label=\"Avg FPS\" value=\"—\" icon={<Zap size={16}/>} sub=\"Not measured\" />
        <StatCard label=\"Alert Latency\" value=\"—\" icon={<Clock size={16}/>} sub=\"Not measured\" />
      </div>

      {/* System metrics + Live detections */}
      <div className=\"grid grid-cols-1 lg:grid-cols-3 gap-6\">
        {/* Tracked persons */}
        <div className=\"lg:col-span-2 glass-card p-4\">
          <h2 className=\"text-sm font-semibold text-white mb-4 flex items-center gap-2\">
            <Users size={14} className=\"text-cyan-400\" />
            Tracked Persons (Demo)
          </h2>
          <div className=\"space-y-3\">
            {DEMO_PERSONS.map(p => (
              <div key={p.trackId}
                className=\"flex items-center justify-between p-3 rounded-lg\"
                style={{background:'rgba(15,23,42,0.6)', border:'1px solid rgba(51,65,85,0.4)'}}>
                <div className=\"flex items-center gap-3\">
                  <div className=\"w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold\"
                    style={{background:'rgba(0,181,212,0.15)', color:'#22d3ee', border:'1px solid rgba(0,181,212,0.3)'}}>
                    {String(p.trackId).padStart(2,'0')}
                  </div>
                  <div>
                    <p className=\"text-sm font-medium text-white\">Person #{String(p.trackId).padStart(2,'0')}</p>
                    <p className=\"text-xs\" style={{color:'#64748b'}}>Confidence: {(p.confidence*100).toFixed(0)}%</p>
                  </div>
                </div>
                <StatusBadge behavior={p.behavior} pulse={p.behavior === 'potential_drowning'} />
              </div>
            ))}
          </div>
        </div>

        {/* System health */}
        <div className=\"glass-card p-4 space-y-4\">
          <h2 className=\"text-sm font-semibold text-white flex items-center gap-2\">
            <Activity size={14} className=\"text-cyan-400\" />
            System Health
          </h2>
          {[
            { label: 'CPU', value: metrics.cpu, color: '#00b5d4' },
            { label: 'RAM', value: metrics.ram, color: '#818cf8' },
          ].map(m => (
            <div key={m.label}>
              <div className=\"flex justify-between text-xs mb-1\">
                <span style={{color:'#94a3b8'}}>{m.label}</span>
                <span className=\"text-white\">{m.value.toFixed(0)}%</span>
              </div>
              <div className=\"h-1.5 rounded-full\" style={{background:'rgba(51,65,85,0.5)'}}>
                <div className=\"h-full rounded-full transition-all duration-500\"
                  style={{width:${m.value}%, background:m.color}} />
              </div>
            </div>
          ))}
          <div className=\"pt-2 space-y-2 text-xs\">
            <div className=\"flex justify-between\">
              <span style={{color:'#64748b'}}>GPU</span>
              <span style={{color:'#64748b'}}>Not Available</span>
            </div>
            <div className=\"flex justify-between\">
              <span style={{color:'#64748b'}}>AI Model</span>
              <span style={{color:'#fbbf24'}}>Not Loaded</span>
            </div>
            <div className=\"flex justify-between\">
              <span style={{color:'#64748b'}}>Database</span>
              <span style={{color:'#22c55e'}}>Connected</span>
            </div>
            <div className=\"flex justify-between\">
              <span style={{color:'#64748b'}}>IoT Device</span>
              <span style={{color:'#64748b'}}>Simulation</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── POTENTIAL DROWNING ALERT ── */}
      <div className=\"alert-critical rounded-xl p-4 alert-pulse\">
        <div className=\"flex items-center gap-3\">
          <div className=\"w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0\"
            style={{background:'rgba(239,68,68,0.2)'}}>
            <Bell size={18} className=\"text-red-400\" />
          </div>
          <div className=\"flex-1\">
            <p className=\"font-bold text-red-400 text-sm\">CRITICAL ALERT — DEMO</p>
            <p className=\"text-xs text-red-300 mt-0.5\">
              Person #03 — POTENTIAL DROWNING detected • Confidence: 85%
            </p>
          </div>
          <button className=\"px-3 py-1.5 rounded text-xs font-medium text-white transition-colors\"
            style={{background:'#ef4444'}}>
            Acknowledge
          </button>
        </div>
      </div>
    </div>
  );
}
"""

# Placeholder pages
for page, title, subtitle in [
    ('LiveMonitoringPage', 'Live Monitoring', 'Real-time camera feed with AI overlay'),
    ('VideoTestingPage', 'Video Testing', 'Upload and test videos with AI models'),
    ('AlertsPage', 'Alerts', 'Incident history and alert management'),
    ('PeopleTrackingPage', 'People Tracking', 'Active tracked persons and movement data'),
    ('ResearchPage', 'Research & Experiments', 'Configure experiments and compare model performance'),
    ('SystemPage', 'System Health', 'Backend status, logs, and diagnostics'),
]:
    files[f'pages/{page}.tsx'] = f"""import {{ Construction }} from 'lucide-react';

export default function {page}() {{
  return (
    <div className=\"flex flex-col items-center justify-center h-full p-12 text-center\">
      <Construction size={{48}} className=\"text-cyan-400 mb-4\" />
      <h1 className=\"text-xl font-bold text-white mb-2\">{title}</h1>
      <p className=\"text-sm\" style={{{{color:'#64748b'}}}}>
        {subtitle}
      </p>
      <p className=\"text-xs mt-4 px-4 py-2 rounded-lg\"
        style={{{{background:'rgba(0,181,212,0.08)', color:'#22d3ee', border:'1px solid rgba(0,181,212,0.2)'}}}}>
        Phase 9+ — This page will be implemented in the next development phase.
      </p>
    </div>
  );
}}
"""

# Login page
files['pages/LoginPage.tsx'] = """import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Waves, Eye, EyeOff } from 'lucide-react';

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('admin@aquaguard.ai');
  const [password, setPassword] = useState('demo1234');
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    // Demo mode: accept any credentials
    await new Promise(r => setTimeout(r, 800));
    if (email && password) {
      localStorage.setItem('access_token', 'demo-token');
      navigate('/dashboard');
    } else {
      setError('Please enter email and password.');
    }
    setLoading(false);
  };

  return (
    <div className=\"min-h-screen flex items-center justify-center p-4\"
      style={{background:'linear-gradient(135deg, #020617 0%, #0f172a 50%, #020617 100%)'}}>
      <div className=\"w-full max-w-md\">
        {/* Logo */}
        <div className=\"text-center mb-8\">
          <div className=\"inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4\"
            style={{background:'linear-gradient(135deg,#0090b0,#00b5d4)'}}>
            <Waves size={28} className=\"text-white\" />
          </div>
          <h1 className=\"text-2xl font-bold text-white\">AquaGuard AI</h1>
          <p className=\"text-sm mt-1\" style={{color:'#64748b'}}>Real-Time Drowning Detection System</p>
        </div>

        {/* Card */}
        <div className=\"glass-card p-8\">
          <h2 className=\"text-lg font-semibold text-white mb-6\">Sign in</h2>

          {error && (
            <div className=\"mb-4 p-3 rounded-lg text-sm text-red-400\"
              style={{background:'rgba(239,68,68,0.1)', border:'1px solid rgba(239,68,68,0.3)'}}>
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className=\"space-y-4\">
            <div>
              <label className=\"block text-xs font-medium mb-1.5\" style={{color:'#94a3b8'}}>Email</label>
              <input
                id=\"login-email\"
                type=\"email\"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className=\"w-full px-3 py-2.5 rounded-lg text-sm text-white outline-none transition-all\"
                style={{
                  background:'rgba(15,23,42,0.8)',
                  border:'1px solid rgba(51,65,85,0.6)',
                }}
                placeholder=\"admin@aquaguard.ai\"
                required
              />
            </div>

            <div>
              <label className=\"block text-xs font-medium mb-1.5\" style={{color:'#94a3b8'}}>Password</label>
              <div className=\"relative\">
                <input
                  id=\"login-password\"
                  type={showPwd ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className=\"w-full px-3 py-2.5 pr-10 rounded-lg text-sm text-white outline-none\"
                  style={{
                    background:'rgba(15,23,42,0.8)',
                    border:'1px solid rgba(51,65,85,0.6)',
                  }}
                  placeholder=\"••••••••\"
                  required
                />
                <button type=\"button\" onClick={() => setShowPwd(!showPwd)}
                  className=\"absolute right-3 top-1/2 -translate-y-1/2\"
                  style={{color:'#64748b'}}>
                  {showPwd ? <EyeOff size={16}/> : <Eye size={16}/>}
                </button>
              </div>
            </div>

            <button
              id=\"login-submit\"
              type=\"submit\"
              disabled={loading}
              className=\"w-full py-2.5 rounded-lg text-sm font-semibold text-white transition-opacity\"
              style={{
                background:'linear-gradient(135deg,#0090b0,#00b5d4)',
                opacity: loading ? 0.7 : 1,
              }}>
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <p className=\"text-center text-xs mt-6\" style={{color:'#475569'}}>
            Demo credentials pre-filled. Click Sign in to continue.
          </p>
        </div>

        <p className=\"text-center text-xs mt-4\" style={{color:'#334155'}}>
          AquaGuard AI v1.0 — B.Tech CSE Research Project
        </p>
      </div>
    </div>
  );
}
"""

for rel, content in files.items():
    p = base / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')
    print(f'Written: {rel}')

print('All frontend pages created.')
