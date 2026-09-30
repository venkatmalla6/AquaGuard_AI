import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Waves, Eye, EyeOff, ShieldCheck } from 'lucide-react';
import api from '../services/api';

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
        if (res.data.user) {
          localStorage.setItem('user', JSON.stringify(res.data.user));
        } else {
          localStorage.setItem('user', JSON.stringify({
            id: 1,
            email: email.trim(),
            name: email.startsWith('admin') ? 'Safety Commander' : (email.startsWith('operator') ? 'Lead Lifeguard' : 'Safety Researcher'),
            role: email.startsWith('admin') ? 'admin' : (email.startsWith('operator') ? 'operator' : 'researcher'),
          }));
        }
        navigate('/dashboard');
        return;
      }
    } catch (err: any) {
      console.warn('Backend login error, trying demo fallback:', err);
      if (email.trim() === 'admin@aquaguard.ai' && password === 'demo1234') {
        localStorage.setItem('access_token', 'demo-token');
        localStorage.setItem('user', JSON.stringify({
          id: 1,
          email: 'admin@aquaguard.ai',
          name: 'Safety Commander',
          role: 'admin',
          is_active: true,
        }));
        navigate('/dashboard');
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
      <div className="w-full max-w-md">
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
            <h2 className="text-lg font-semibold text-white">Sign In</h2>
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/30">
              <ShieldCheck size={12} />
              <span>Mesh v1.0.0</span>
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
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
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
              {loading ? 'Authenticating...' : 'Sign In to Mission Control'}
            </button>
          </form>

          {/* Quick presets for testing */}
          <div className="mt-6 pt-5 border-t" style={{ borderColor: 'rgba(51, 65, 85, 0.4)' }}>
            <p className="text-center text-[11px] font-medium text-slate-400 mb-2.5">
              Quick Select Role Presets (Password: <code className="text-cyan-400 font-mono">demo1234</code>)
            </p>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setRolePreset('admin@aquaguard.ai')}
                className="px-2 py-1.5 rounded text-[11px] font-semibold border transition-all text-cyan-300 hover:bg-cyan-500/10 border-cyan-500/30"
              >
                Admin
              </button>
              <button
                type="button"
                onClick={() => setRolePreset('operator@aquaguard.ai')}
                className="px-2 py-1.5 rounded text-[11px] font-semibold border transition-all text-amber-300 hover:bg-amber-500/10 border-amber-500/30"
              >
                Operator
              </button>
              <button
                type="button"
                onClick={() => setRolePreset('researcher@aquaguard.ai')}
                className="px-2 py-1.5 rounded text-[11px] font-semibold border transition-all text-purple-300 hover:bg-purple-500/10 border-purple-500/30"
              >
                Researcher
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