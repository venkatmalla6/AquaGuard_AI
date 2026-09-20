// AquaGuard AI - System Page (Phase 8)
// Live system metrics from /ws/metrics WebSocket
import { useEffect, useState } from 'react';
import { Server, Cpu, HardDrive, Zap, Database, Activity, RefreshCw } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from 'recharts';
import { useWebSocket } from '../hooks/useWebSocket';
import type { SystemMetrics } from '../types';

const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

interface MetricPoint { time: string; cpu: number; ram: number; fps: number | null; }

export default function SystemPage() {
  const { status, lastMessage } = useWebSocket<SystemMetrics>(`${WS_BASE}/ws/metrics`);
  const [metrics,  setMetrics]  = useState<SystemMetrics | null>(null);
  const [history,  setHistory]  = useState<MetricPoint[]>([]);
  const [apiHealth, setApiHealth] = useState<'ok' | 'error' | 'checking'>('checking');

  useEffect(() => {
    // Health check
    fetch('http://localhost:8000/health')
      .then(r => r.ok ? setApiHealth('ok') : setApiHealth('error'))
      .catch(() => setApiHealth('error'));
  }, []);

  useEffect(() => {
    if (!lastMessage) return;
    setMetrics(lastMessage);
    setHistory(h => [
      ...h.slice(-29),
      {
        time: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        cpu:  lastMessage.cpu_percent  ?? 0,
        ram:  lastMessage.ram_percent  ?? 0,
        fps:  lastMessage.pipeline_fps ?? null,
      },
    ]);
  }, [lastMessage]);

  const rows = metrics ? [
    { label: 'API Backend',     val: apiHealth === 'ok' ? 'Online' : 'Error',      color: apiHealth === 'ok' ? '#22c55e' : '#ef4444' },
    { label: 'WebSocket',       val: status === 'connected' ? 'Connected' : status, color: status === 'connected' ? '#22c55e' : '#f59e0b' },
    { label: 'CPU Usage',       val: `${metrics.cpu_percent?.toFixed(1)}%`,         color: '#22d3ee' },
    { label: 'RAM Usage',       val: `${metrics.ram_percent?.toFixed(1)}%`,         color: '#818cf8' },
    { label: 'RAM Used',        val: `${metrics.ram_used_gb?.toFixed(2)} GB`,       color: '#94a3b8' },
    { label: 'GPU',             val: metrics.gpu_available ? 'CUDA' : 'Not available (CPU edge)', color: '#64748b' },
    { label: 'AI Scorer',       val: (metrics.scorer_mode ?? 'rule-based').toUpperCase(), color: metrics.scorer_mode === 'lstm' ? '#22c55e' : '#f59e0b' },
    { label: 'Pipeline FPS',    val: metrics.pipeline_fps != null ? `${metrics.pipeline_fps?.toFixed(1)} fps` : '—', color: '#94a3b8' },
    { label: 'Active Tracks',   val: String(metrics.active_tracks ?? 0),            color: '#22d3ee' },
    { label: 'Session Alerts',  val: String(metrics.total_alerts ?? 0),             color: metrics.total_alerts > 0 ? '#ef4444' : '#22c55e' },
    { label: 'Uptime',          val: `${Math.floor((metrics.uptime_seconds ?? 0) / 60)}m ${Math.round((metrics.uptime_seconds ?? 0) % 60)}s`, color: '#94a3b8' },
    { label: 'Database',        val: 'SQLite (development)',                         color: '#22c55e' },
    { label: 'IoT Device',      val: 'Simulated (ESP32)',                           color: '#64748b' },
  ] : [];

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Server size={18} className="text-cyan-400" /> System Monitor
          </h1>
          <p className="text-xs mt-0.5" style={{ color: '#64748b' }}>
            Live hardware metrics · Backend health · Pipeline status
          </p>
        </div>
        <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold ${
          status === 'connected' ? 'text-green-400' : 'text-yellow-400'
        }`} style={{ background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(51,65,85,0.5)' }}>
          <RefreshCw size={11} className={status === 'connected' ? 'animate-spin' : ''} />
          {status === 'connected' ? 'Live (5s)' : 'Connecting...'}
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { icon: <Cpu size={14} />,       label: 'CPU',       val: `${metrics?.cpu_percent?.toFixed(0) ?? '—'}%`,   color: '#22d3ee' },
          { icon: <HardDrive size={14} />, label: 'RAM',       val: `${metrics?.ram_percent?.toFixed(0) ?? '—'}%`,   color: '#818cf8' },
          { icon: <Zap size={14} />,       label: 'FPS',       val: metrics?.pipeline_fps != null ? `${metrics.pipeline_fps.toFixed(1)}` : '—', color: '#4ade80' },
          { icon: <Activity size={14} />,  label: 'AI Mode',   val: (metrics?.scorer_mode ?? '—').toUpperCase(),      color: '#f59e0b' },
        ].map(({ icon, label, val, color }) => (
          <div key={label} className="rounded-xl p-3 flex items-center gap-3"
            style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.4)' }}>
            <span style={{ color }}>{icon}</span>
            <div>
              <p className="text-xs" style={{ color: '#64748b' }}>{label}</p>
              <p className="text-sm font-bold text-white">{val}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* CPU + RAM chart */}
        <div className="rounded-xl p-4" style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.4)' }}>
          <h2 className="text-sm font-semibold text-white mb-3">CPU & RAM History (30s)</h2>
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={history}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(51,65,85,0.3)" />
              <XAxis dataKey="time" tick={{ fontSize: 9, fill: '#64748b' }} interval={4} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: '#64748b' }} unit="%" />
              <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', fontSize: 11 }}
                formatter={(v) => [typeof v === "number" ? `${v.toFixed(1)}%` : String(v ?? "")]}  />
              <Line type="monotone" dataKey="cpu" stroke="#22d3ee" dot={false} strokeWidth={1.5} name="CPU" />
              <Line type="monotone" dataKey="ram" stroke="#818cf8" dot={false} strokeWidth={1.5} name="RAM" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Status table */}
        <div className="rounded-xl p-4" style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.4)' }}>
          <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Database size={14} className="text-cyan-400" /> Component Status
          </h2>
          <div className="space-y-1.5">
            {rows.map(({ label, val, color }) => (
              <div key={label} className="flex justify-between py-1 border-b text-xs"
                style={{ borderColor: 'rgba(51,65,85,0.25)' }}>
                <span style={{ color: '#64748b' }}>{label}</span>
                <span style={{ color }} className="font-medium">{val}</span>
              </div>
            ))}
            {!metrics && (
              <p className="text-xs text-center py-4" style={{ color: '#64748b' }}>
                Connecting to metrics WebSocket...
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}



