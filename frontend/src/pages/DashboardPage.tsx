import { useEffect, useState } from 'react';
import { Activity, Users, Bell, Zap, Clock, Wifi, WifiOff } from 'lucide-react';
import StatCard from '../components/common/StatCard';
import StatusBadge from '../components/common/StatusBadge';
import { useWebSocket } from '../hooks/useWebSocket';
import type { BehaviorClass } from '../types';

const WS_URL = (import.meta.env.VITE_WS_URL || 'ws://localhost:8000') + '/ws/metrics';

interface DemoPerson { trackId: number; behavior: BehaviorClass; confidence: number; }
const DEMO_PERSONS: DemoPerson[] = [
  { trackId: 1, behavior: 'normal',             confidence: 0.94 },
  { trackId: 2, behavior: 'distress',           confidence: 0.78 },
  { trackId: 3, behavior: 'potential_drowning', confidence: 0.85 },
];

export default function DashboardPage() {
  const { status, lastMessage } = useWebSocket(WS_URL);
  const [metrics, setMetrics] = useState({ cpu: 0, ram: 0 });

  useEffect(() => {
    if (lastMessage && typeof lastMessage === 'object') {
      const m = lastMessage as { cpu_percent?: number; ram_percent?: number };
      setMetrics({ cpu: m.cpu_percent ?? 0, ram: m.ram_percent ?? 0 });
    }
  }, [lastMessage]);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Dashboard</h1>
          <p className="text-sm" style={{ color: '#64748b' }}>Real-time pool safety monitoring</p>
        </div>
        <div
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium"
          style={{ background: 'rgba(0,181,212,0.1)', color: '#22d3ee', border: '1px solid rgba(0,181,212,0.2)' }}
        >
          {status === 'connected' ? <><Wifi size={12} /> Live</> : <><WifiOff size={12} /> Connecting</>}
        </div>
      </div>

      {/* Demo notice */}
      <div
        className="rounded-lg px-4 py-3 text-sm"
        style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.3)', color: '#fbbf24' }}
      >
        <strong>DEMO MODE</strong> — Simulated detections. Connect a real camera or upload a video to run AI inference.
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="People Detected" value={3}   icon={<Users size={16} />} sub="Demo data" />
        <StatCard label="Active Alerts"   value={1}   icon={<Bell  size={16} />} color="#ef4444" sub="1 Critical" />
        <StatCard label="Avg FPS"         value="—"   icon={<Zap   size={16} />} sub="Not measured" />
        <StatCard label="Alert Latency"   value="—"   icon={<Clock size={16} />} sub="Not measured" />
      </div>

      {/* Persons + System Health */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-card p-4">
          <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Users size={14} className="text-cyan-400" /> Tracked Persons (Demo)
          </h2>
          <div className="space-y-3">
            {DEMO_PERSONS.map((p) => (
              <div
                key={p.trackId}
                className="flex items-center justify-between p-3 rounded-lg"
                style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(51,65,85,0.4)' }}
              >
                <div className="flex items-center gap-3">
                  <div
                    className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
                    style={{ background: 'rgba(0,181,212,0.15)', color: '#22d3ee', border: '1px solid rgba(0,181,212,0.3)' }}
                  >
                    {String(p.trackId).padStart(2, '0')}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white">
                      Person #{String(p.trackId).padStart(2, '0')}
                    </p>
                    <p className="text-xs" style={{ color: '#64748b' }}>
                      Confidence: {(p.confidence * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
                <StatusBadge behavior={p.behavior} pulse={p.behavior === 'potential_drowning'} />
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card p-4 space-y-4">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Activity size={14} className="text-cyan-400" /> System Health
          </h2>
          {([
            { label: 'CPU', value: metrics.cpu, color: '#00b5d4' },
            { label: 'RAM', value: metrics.ram, color: '#818cf8' },
          ] as const).map((m) => (
            <div key={m.label}>
              <div className="flex justify-between text-xs mb-1">
                <span style={{ color: '#94a3b8' }}>{m.label}</span>
                <span className="text-white">{m.value.toFixed(0)}%</span>
              </div>
              <div className="h-1.5 rounded-full" style={{ background: 'rgba(51,65,85,0.5)' }}>
                <div className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${m.value}%`, background: m.color }} />
              </div>
            </div>
          ))}
          <div className="pt-2 space-y-2 text-xs">
            {[
              { label: 'GPU',        val: 'Not Available', c: '#64748b' },
              { label: 'AI Model',   val: 'Not Loaded',    c: '#fbbf24' },
              { label: 'Database',   val: 'SQLite (dev)',  c: '#22c55e' },
              { label: 'IoT Device', val: 'Simulation',    c: '#64748b' },
            ].map((row) => (
              <div key={row.label} className="flex justify-between">
                <span style={{ color: '#64748b' }}>{row.label}</span>
                <span style={{ color: row.c }}>{row.val}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Critical alert banner */}
      <div className="alert-critical rounded-xl p-4 alert-pulse">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
            style={{ background: 'rgba(239,68,68,0.2)' }}
          >
            <Bell size={18} className="text-red-400" />
          </div>
          <div className="flex-1">
            <p className="font-bold text-red-400 text-sm">CRITICAL ALERT — DEMO</p>
            <p className="text-xs text-red-300 mt-0.5">
              Person #03 — POTENTIAL DROWNING detected · Confidence: 85%
            </p>
          </div>
          <button
            className="px-3 py-1.5 rounded text-xs font-medium text-white"
            style={{ background: '#ef4444' }}
          >
            Acknowledge
          </button>
        </div>
      </div>
    </div>
  );
}