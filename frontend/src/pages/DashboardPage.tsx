// AquaGuard AI - Dashboard Page (Phase 8)
// Live WebSocket data: metrics + pipeline status + alert summary
import { useEffect, useState } from 'react';
import { Users, Bell, Zap, Clock, Wifi, WifiOff, Activity, AlertTriangle } from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket';
import { StatCard } from '../components/common/StatCard';
import { StatusBadge } from '../components/common/StatusBadge';
import { alertAPI } from '../services/api';
import type { FrameResult, SystemMetrics, Alert } from '../types';

const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export default function DashboardPage() {
  const { status: wsStatus, lastMessage: monMsg } =
    useWebSocket<FrameResult>(`${WS_BASE}/ws/monitoring`);
  const { lastMessage: metricMsg } =
    useWebSocket<SystemMetrics>(`${WS_BASE}/ws/metrics`);

  const [metrics,      setMetrics]      = useState({ cpu: 0, ram: 0, fps: null as number | null });
  const [pipeStats,    setPipeStats]    = useState<FrameResult['stats']>();
  const [recentAlerts, setRecentAlerts] = useState<Alert[]>([]);
  const [alertCount,   setAlertCount]   = useState({ active: 0, critical: 0 });

  useEffect(() => {
    if (metricMsg) {
      setMetrics({
        cpu: metricMsg.cpu_percent  ?? 0,
        ram: metricMsg.ram_percent  ?? 0,
        fps: metricMsg.pipeline_fps ?? null,
      });
    }
  }, [metricMsg]);

  useEffect(() => {
    if (monMsg?.stats) setPipeStats(monMsg.stats);
  }, [monMsg]);

  useEffect(() => {
    alertAPI.list().then(r => {
      const data: Alert[] = r.data ?? [];
      setRecentAlerts(data.slice(0, 5));
      setAlertCount({
        active:   data.filter(a => a.status === 'active').length,
        critical: data.filter(a => a.severity === 'critical').length,
      });
    }).catch(() => {});
  }, []);

  const activeTracks = pipeStats?.active_tracks ?? 0;
  const sessionAlerts = pipeStats?.total_alerts ?? 0;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Dashboard</h1>
          <p className="text-sm mt-0.5" style={{ color: '#64748b' }}>
            Real-time pool safety monitoring · AquaGuard AI
          </p>
        </div>
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold ${
          wsStatus === 'connected' ? 'text-green-400' : 'text-yellow-400'
        }`} style={{ background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(51,65,85,0.5)' }}>
          {wsStatus === 'connected'
            ? <><Wifi size={12} /> Live</>
            : <><WifiOff size={12} /> {wsStatus}</>}
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Active Persons"
          value={activeTracks}
          icon={<Users size={16} />}
          sub={activeTracks > 0 ? 'Tracked by ByteTrack' : 'No detections'}
        />
        <StatCard
          label="Active Alerts"
          value={alertCount.active}
          icon={<Bell size={16} />}
          color="#ef4444"
          sub={alertCount.critical > 0 ? `${alertCount.critical} Critical` : 'None critical'}
        />
        <StatCard
          label="Pipeline FPS"
          value={metrics.fps != null ? metrics.fps.toFixed(1) : '—'}
          icon={<Zap size={16} />}
          sub={pipeStats?.scorer_mode ? `Scorer: ${pipeStats.scorer_mode}` : 'Pipeline idle'}
        />
        <StatCard
          label="Session Alerts"
          value={sessionAlerts}
          icon={<Clock size={16} />}
          sub="This session"
        />
      </div>

      {/* Pipeline status banner */}
      {pipeStats && (
        <div className="rounded-xl px-4 py-3 flex items-center gap-3 text-sm"
          style={{ background: 'rgba(0,181,212,0.07)', border: '1px solid rgba(0,181,212,0.2)' }}>
          <Activity size={16} className="text-cyan-400 flex-shrink-0" />
          <div className="flex flex-wrap gap-4 text-xs">
            {[
              { k: 'Frames',        v: pipeStats.total_frames },
              { k: 'Active Tracks', v: pipeStats.active_tracks },
              { k: 'FPS',           v: pipeStats.session_fps?.toFixed(1) },
              { k: 'Uptime',        v: `${Math.floor(pipeStats.uptime_seconds / 60)}m` },
              { k: 'Scorer',        v: pipeStats.scorer_mode?.toUpperCase() },
            ].map(({ k, v }) => (
              <span key={k}>
                <span style={{ color: '#64748b' }}>{k}: </span>
                <span className="text-white font-semibold">{v}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Alerts */}
        <div className="lg:col-span-2 rounded-xl p-4 space-y-3"
          style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.4)' }}>
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Bell size={14} className="text-cyan-400" /> Recent Alerts
          </h2>
          {recentAlerts.length === 0 ? (
            <div className="text-center py-6">
              <Bell size={28} className="mx-auto mb-2 text-slate-600" />
              <p className="text-xs" style={{ color: '#64748b' }}>No alerts recorded</p>
            </div>
          ) : recentAlerts.map(a => (
            <div key={a.id} className="flex items-center justify-between p-3 rounded-lg"
              style={{ background: 'rgba(15,23,42,0.5)', border: `1px solid ${a.severity === 'critical' ? 'rgba(239,68,68,0.3)' : 'rgba(245,158,11,0.2)'}` }}>
              <div className="flex items-center gap-3">
                <AlertTriangle size={14} className={a.severity === 'critical' ? 'text-red-400' : 'text-yellow-400'} />
                <div>
                  <p className="text-sm font-medium text-white">
                    Person #{a.trackId} — {a.behavior.replace('_', ' ')}
                  </p>
                  <p className="text-xs" style={{ color: '#64748b' }}>
                    {(a.confidence * 100).toFixed(0)}% confidence · {a.consecutiveFrames} frames
                  </p>
                </div>
              </div>
              <StatusBadge behavior={a.behavior as never} />
            </div>
          ))}
        </div>

        {/* System health */}
        <div className="rounded-xl p-4 space-y-4"
          style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.4)' }}>
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Activity size={14} className="text-cyan-400" /> System Health
          </h2>
          {[
            { label: 'CPU', value: metrics.cpu, color: '#22d3ee' },
            { label: 'RAM', value: metrics.ram, color: '#818cf8' },
          ].map(m => (
            <div key={m.label}>
              <div className="flex justify-between text-xs mb-1">
                <span style={{ color: '#94a3b8' }}>{m.label}</span>
                <span className="text-white font-medium">{m.value.toFixed(0)}%</span>
              </div>
              <div className="h-1.5 rounded-full" style={{ background: 'rgba(51,65,85,0.5)' }}>
                <div className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${m.value}%`, background: m.color }} />
              </div>
            </div>
          ))}
          <div className="pt-2 space-y-2 text-xs border-t" style={{ borderColor: 'rgba(51,65,85,0.3)' }}>
            {[
              { label: 'GPU',        val: 'CPU Edge (No GPU)', c: '#64748b' },
              { label: 'AI Model',   val: pipeStats?.scorer_mode === 'lstm' ? 'LSTM Loaded ✓' : 'Rule-based', c: pipeStats?.scorer_mode === 'lstm' ? '#22c55e' : '#f59e0b' },
              { label: 'Tracker',    val: 'ByteTrack',         c: '#22d3ee' },
              { label: 'Database',   val: 'SQLite (dev)',       c: '#22c55e' },
              { label: 'IoT',        val: 'Simulation Mode',   c: '#64748b' },
            ].map(r => (
              <div key={r.label} className="flex justify-between">
                <span style={{ color: '#64748b' }}>{r.label}</span>
                <span style={{ color: r.c }} className="font-medium">{r.val}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
