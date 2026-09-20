// AquaGuard AI - Alerts Page (Phase 8)
// Live alert feed from API + WS session alerts
import { useEffect, useState } from 'react';
import { AlertTriangle, Bell, CheckCircle2, XCircle, Filter, Volume2, VolumeX } from 'lucide-react';
import { alertAudio } from '../utils/audioAlert';
import { formatDistanceToNow } from 'date-fns';
import { alertAPI } from '../services/api';
import type { Alert } from '../types';

const SEVERITY_CFG = {
  critical: { color: '#ef4444', bg: 'rgba(239,68,68,0.1)',  label: 'CRITICAL' },
  warning:  { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', label: 'WARNING'  },
};
const STATUS_CFG = {
  active:        { color: '#ef4444', label: 'Active'        },
  acknowledged:  { color: '#f59e0b', label: 'Acknowledged'  },
  resolved:      { color: '#22c55e', label: 'Resolved'      },
  false_alarm:   { color: '#64748b', label: 'False Alarm'   },
};

function AlertRow({ alert, onAck, onResolve }: {
  alert: Alert;
  onAck: (id: number) => void;
  onResolve: (id: number) => void;
}) {
  const sev = SEVERITY_CFG[alert.severity] ?? SEVERITY_CFG.warning;
  const sta = STATUS_CFG[alert.status]     ?? STATUS_CFG.active;
  return (
    <div className="p-4 rounded-xl transition-all"
      style={{ background: 'rgba(15,23,42,0.7)', border: `1px solid ${sev.color}33` }}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
            style={{ background: sev.bg }}>
            <AlertTriangle size={16} style={{ color: sev.color }} />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-0.5">
              <span className="text-xs font-bold px-1.5 py-0.5 rounded"
                style={{ background: sev.bg, color: sev.color }}>
                {sev.label}
              </span>
              <span className="text-xs px-1.5 py-0.5 rounded"
                style={{ background: 'rgba(51,65,85,0.5)', color: sta.color }}>
                {sta.label}
              </span>
            </div>
            <p className="text-sm font-semibold text-white">
              Person #{alert.trackId} — {alert.behavior.replace('_', ' ').toUpperCase()}
            </p>
            <p className="text-xs mt-0.5" style={{ color: '#94a3b8' }}>
              Confidence: {(alert.confidence * 100).toFixed(0)}% ·{' '}
              {alert.consecutiveFrames} consecutive frames ·{' '}
              {formatDistanceToNow(new Date(alert.triggeredAt), { addSuffix: true })}
            </p>
          </div>
        </div>

        {alert.status === 'active' && (
          <div className="flex gap-2 flex-shrink-0">
            <button onClick={() => onAck(alert.id)}
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors"
              style={{ background: 'rgba(245,158,11,0.15)', color: '#fbbf24', border: '1px solid rgba(245,158,11,0.3)' }}>
              <CheckCircle2 size={11} /> Ack
            </button>
            <button onClick={() => onResolve(alert.id)}
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors"
              style={{ background: 'rgba(34,197,94,0.15)', color: '#4ade80', border: '1px solid rgba(34,197,94,0.3)' }}>
              <XCircle size={11} /> Resolve
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function AlertsPage() {
  const [alerts,     setAlerts]     = useState<Alert[]>([]);
  const [loading,    setLoading]    = useState(true);
  const [filter,     setFilter]     = useState<'all' | 'active' | 'critical'>('all');
  const [error,      setError]      = useState('');
  const [isMuted,    setIsMuted]    = useState(alertAudio.isMuted());

  useEffect(() => {
    const hasActiveCritical = alerts.some(a => a.severity === 'critical' && a.status === 'active');
    if (hasActiveCritical && !isMuted) {
      alertAudio.playCriticalSiren();
    } else {
      alertAudio.stopSiren();
    }
    return () => {
      alertAudio.stopSiren();
    };
  }, [alerts, isMuted]);

  const fetchAlerts = async () => {
    try {
      const r = await alertAPI.list();
      setAlerts(r.data ?? []);
    } catch {
      setError('Could not load alerts from API.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAlerts(); }, []);

  const handleAck = async (id: number) => {
    try { await alertAPI.acknowledge(id); fetchAlerts(); } catch {}
  };
  const handleResolve = async (id: number) => {
    try { await alertAPI.resolve(id); fetchAlerts(); } catch {}
  };

  const filtered = alerts.filter(a => {
    if (filter === 'active')   return a.status === 'active';
    if (filter === 'critical') return a.severity === 'critical';
    return true;
  });

  const counts = {
    active:   alerts.filter(a => a.status === 'active').length,
    critical: alerts.filter(a => a.severity === 'critical').length,
    total:    alerts.length,
  };

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Bell size={18} className="text-cyan-400" /> Alerts
          </h1>
          <p className="text-xs mt-0.5" style={{ color: '#64748b' }}>
            {counts.total} total · {counts.active} active · {counts.critical} critical
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              const next = alertAudio.toggleMute();
              setIsMuted(next);
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              isMuted
                ? "text-slate-400 border border-slate-700 bg-slate-800/60"
                : "text-red-400 border border-red-500/40 bg-red-500/10"
            }`}
            title={isMuted ? "Siren alarm muted (click to unmute)" : "Siren alarm active (click to mute)"}
          >
            {isMuted ? <VolumeX size={13} /> : <Volume2 size={13} className="animate-pulse" />}
            <span>{isMuted ? "Alarm Muted" : "Alarm Armed"}</span>
          </button>
          <button onClick={fetchAlerts}
            className="px-3 py-1.5 rounded-lg text-xs font-medium"
            style={{ background: 'rgba(0,181,212,0.1)', color: '#22d3ee', border: '1px solid rgba(0,181,212,0.3)' }}>
            Refresh
          </button>
        </div>
      </div>

      {/* Stat pills */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Active',   val: counts.active,   color: '#ef4444' },
          { label: 'Critical', val: counts.critical, color: '#f97316' },
          { label: 'Total',    val: counts.total,    color: '#22d3ee' },
        ].map(({ label, val, color }) => (
          <div key={label} className="rounded-xl p-3 text-center"
            style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.4)' }}>
            <p className="text-2xl font-bold" style={{ color }}>{val}</p>
            <p className="text-xs mt-0.5" style={{ color: '#64748b' }}>{label}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {(['all', 'active', 'critical'] as const).map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
            style={{
              background: filter === f ? 'rgba(0,181,212,0.15)' : 'rgba(15,23,42,0.7)',
              border: `1px solid ${filter === f ? 'rgba(0,181,212,0.5)' : 'rgba(51,65,85,0.4)'}`,
              color:  filter === f ? '#22d3ee' : '#94a3b8',
            }}>
            <Filter size={10} className="inline mr-1" />
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* List */}
      <div className="space-y-3">
        {loading && <p className="text-sm text-center py-8" style={{ color: '#64748b' }}>Loading alerts...</p>}
        {error   && <p className="text-sm text-center py-4 text-red-400">{error}</p>}
        {!loading && filtered.length === 0 && (
          <div className="text-center py-12">
            <Bell size={36} className="mx-auto mb-3 text-slate-600" />
            <p className="text-sm" style={{ color: '#64748b' }}>No alerts match the current filter</p>
          </div>
        )}
        {filtered.map(a => (
          <AlertRow key={a.id} alert={a} onAck={handleAck} onResolve={handleResolve} />
        ))}
      </div>
    </div>
  );
}


