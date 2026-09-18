import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Waves, Eye, EyeOff } from 'lucide-react';

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
    await new Promise((r) => setTimeout(r, 800));
    if (email && password) {
      localStorage.setItem('access_token', 'demo-token');
      navigate('/dashboard');
    } else {
      setError('Please enter email and password.');
    }
    setLoading(false);
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4"
      style={{ background: 'linear-gradient(135deg, #020617 0%, #0f172a 50%, #020617 100%)' }}
    >
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div
            className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4"
            style={{ background: 'linear-gradient(135deg,#0090b0,#00b5d4)' }}
          >
            <Waves size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">AquaGuard AI</h1>
          <p className="text-sm mt-1" style={{ color: '#64748b' }}>
            Real-Time Drowning Detection System
          </p>
        </div>

        <div className="glass-card p-8">
          <h2 className="text-lg font-semibold text-white mb-6">Sign in</h2>

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
                Email
              </label>
              <input
                id="login-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg text-sm text-white outline-none"
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
                  className="w-full px-3 py-2.5 pr-10 rounded-lg text-sm text-white outline-none"
                  style={{ background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(51,65,85,0.6)' }}
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPwd(!showPwd)}
                  className="absolute right-3 top-1/2 -translate-y-1/2"
                  style={{ color: '#64748b' }}
                >
                  {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg text-sm font-semibold text-white transition-opacity"
              style={{
                background: 'linear-gradient(135deg,#0090b0,#00b5d4)',
                opacity: loading ? 0.7 : 1,
              }}
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <p className="text-center text-xs mt-6" style={{ color: '#475569' }}>
            Demo credentials pre-filled. Click <strong>Sign in</strong> to continue.
          </p>
        </div>

        <p className="text-center text-xs mt-4" style={{ color: '#334155' }}>
          AquaGuard AI v1.0 — B.Tech CSE Research Project
        </p>
      </div>
    </div>
  );
}