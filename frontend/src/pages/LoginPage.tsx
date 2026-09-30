import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Waves, Eye, EyeOff, ShieldCheck, Video, FlaskConical, LayoutDashboard } from 'lucide-react';
import api from '../services/api';
import { getDefaultHomeForRole } from '../App';

export default function LoginPage() {
  const navigate = useNavigate();
  const [email,    setEmail]    = useState('admin@aquaguard.ai');
  const [password, setPassword] = useState('demo1234');
  const [showPwd,  setShowPwd]  = useState(false);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await api.post('/api/auth/login', {
        email: email.trim(),
        password: password,
      });

      if (res.data?.access_token) {
        localStorage.setItem('access_token', res.data.access_token);
        let userRole = 'admin';
        if (res.data.user) {
          localStorage.setItem('user', JSON.stringify(res.data.user));
          userRole = (res.data.user.role || 'admin').toLowerCase();
        } else {
          userRole = email.startsWith('operator') ? 'operator' : (email.startsWith('researcher') ? 'researcher' : 'admin');
          localStorage.setItem('user', JSON.stringify({
            id: 1,
            email: email.trim(),
            name: userRole === 'operator' ? 'Head Lifeguard' : (userRole === 'researcher' ? 'AI Research Engineer' : 'Safety Commander'),
            role: userRole,
          }));
        }
        // Route to designated role workstation
        navigate(getDefaultHomeForRole(userRole));
        return;
      }
    } catch (err: any) {
      console.warn('Backend login error, trying demo fallback:', err);
      const trimmed = email.trim();
      if (password === 'demo1234' && (trimmed === 'admin@aquaguard.ai' || trimmed === 'operator@aquaguard.ai' || trimmed === 'researcher@aquaguard.ai')) {
        const userRole = trimmed.startsWith('operator') ? 'operator' : (trimmed.startsWith('researcher') ? 'researcher' : 'admin');
        localStorage.setItem('access_token', 'demo-token');
        localStorage.setItem('user', JSON.stringify({
          id: 1,
          email: trimmed,
          name: userRole === 'operator' ? 'Head Lifeguard (Operator)' : (userRole === 'researcher' ? 'AI Research Engineer' : 'System Administrator'),
          role: userRole,
          is_active: true,
        }));
        navigate(getDefaultHomeForRole(userRole));
        return;
      }
      const msg = err.response?.data?.detail || 'Invalid email or password. Please verify credentials.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const setRolePreset = (presetEmail: string) => {
    setEmail(presetEmail);
    setPassword('demo1234');
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4"
      style={{ background: 'linear-gradient(135deg, #020617 0%, #0f172a 50%, #020617 100%)' }}
    >
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <div
            className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4 shadow-lg shadow-cyan-500/20"
            style={{ background: 'linear-gradient(135deg,#0090b0,#00b5d4)' }}
          >
            <Waves size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-wide">AquaGuard AI</h1>
          <p className="text-sm mt-1" style={{ color: '#64748b' }}>
            Real-Time Edge Pool Safety & Drowning Detection
          </p>
        </div>

        <div className="glass-card p-8 rounded-2xl border" style={{ borderColor: 'rgba(51, 65, 85, 0.6)' }}>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-white">Sign In</h2>
              <p className="text-xs text-slate-400 mt-0.5">Role-Based Workstation Access</p>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/30">
              <ShieldCheck size={12} />
              <span>RBAC Enabled</span>
            </div>
          </div>

          {error && (
            <div
              className="mb-4 p-3 rounded-lg text-sm text-red-400"
              style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)' }}
            >
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-medium mb-1.5" style={{ color: '#94a3b8' }}>
                Email Address
              </label>
              <input
                id="login-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg text-sm text-white outline-none focus:ring-1 focus:ring-cyan-500"
                style={{ background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(51,65,85,0.6)' }}
                placeholder="admin@aquaguard.ai"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium mb-1.5" style={{ color: '#94a3b8' }}>
                Password
              </label>
              <div className="relative">
                <input
                  id="login-password"
                  type={showPwd ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3 py-2.5 pr-10 rounded-lg text-sm text-white outline-none focus:ring-1 focus:ring-cyan-500"
                  style={{ background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(51,65,85,0.6)' }}
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPwd(!showPwd)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 cursor-pointer"
                >
                  {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg text-sm font-semibold text-white transition-all shadow-md hover:brightness-110 active:scale-95 cursor-pointer"
              style={{
                background: 'linear-gradient(135deg,#0090b0,#00b5d4)',
                opacity: loading ? 0.7 : 1,
              }}
            >
              {loading ? 'Authenticating...' : 'Sign In to Station'}
            </button>
          </form>

          {/* Quick presets with explicit role descriptions */}
          <div className="mt-6 pt-5 border-t" style={{ borderColor: 'rgba(51, 65, 85, 0.4)' }}>
            <p className="text-center text-[11px] font-medium text-slate-400 mb-2.5">
              Select Role Workstation (Password: <code className="text-cyan-400 font-mono">demo1234</code>)
            </p>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setRolePreset('admin@aquaguard.ai')}
                className="p-2 rounded-lg text-left border transition-all hover:bg-cyan-500/10 border-cyan-500/30 cursor-pointer group"
              >
                <div className="flex items-center gap-1 text-cyan-300 font-bold text-xs mb-1">
                  <LayoutDashboard size={13} />
                  <span>Admin</span>
                </div>
                <p className="text-[10px] text-slate-400 leading-tight">
                  All 7 Modules + System Settings
                </p>
              </button>

              <button
                type="button"
                onClick={() => setRolePreset('operator@aquaguard.ai')}
                className="p-2 rounded-lg text-left border transition-all hover:bg-amber-500/10 border-amber-500/30 cursor-pointer group"
              >
                <div className="flex items-center gap-1 text-amber-300 font-bold text-xs mb-1">
                  <Video size={13} />
                  <span>Operator</span>
                </div>
                <p className="text-[10px] text-slate-400 leading-tight">
                  Live Feeds, Sirens & Active Alerts
                </p>
              </button>

              <button
                type="button"
                onClick={() => setRolePreset('researcher@aquaguard.ai')}
                className="p-2 rounded-lg text-left border transition-all hover:bg-purple-500/10 border-purple-500/30 cursor-pointer group"
              >
                <div className="flex items-center gap-1 text-purple-300 font-bold text-xs mb-1">
                  <FlaskConical size={13} />
                  <span>Researcher</span>
                </div>
                <p className="text-[10px] text-slate-400 leading-tight">
                  Benchmarks, NPU & Video Testing
                </p>
              </button>
            </div>
          </div>
        </div>

        <p className="text-center text-xs mt-4" style={{ color: '#475569' }}>
          AquaGuard AI v1.0 • B.Tech CSE Research Project
        </p>
      </div>
    </div>
  );
}