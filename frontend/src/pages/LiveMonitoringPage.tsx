// AquaGuard AI - Live Monitoring Page (Phase 8)
// Real-time WebSocket-driven track visualisation + feature vector display
import { useEffect, useState, useRef } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { Activity, Wifi, WifiOff, AlertTriangle, Users, Cpu, Zap, Clock } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { FEATURE_LABELS, BEHAVIOR_CONFIG, type FrameResult, type LiveTrack, type SystemMetrics } from '../types';

const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

function BehaviorBadge({ behavior, pulse }: { behavior: string; pulse?: boolean }) {
  const cfg = BEHAVIOR_CONFIG[behavior as keyof typeof BEHAVIOR_CONFIG] ?? BEHAVIOR_CONFIG.normal;
  return (
    <span
      className={`px-2 py-0.5 rounded-full text-xs font-bold ${pulse ? 'animate-pulse' : ''}`}
      style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.color}44` }}
    >
      {cfg.label}
    </span>
  );
}

function FeatureBar({ vector }: { vector: number[] }) {
  const data = FEATURE_LABELS.map((label, i) => ({
    label: label.replace('_', ' '),
    value: Math.abs(vector[i] ?? 0),
    raw:   vector[i] ?? 0,
  }));
  return (
    <div className="mt-3">
      <p className="text-xs font-semibold mb-1" style={{ color: '#94a3b8' }}>16-D Feature Vector</p>
      <ResponsiveContainer width="100%" height={80}>
        <BarChart data={data} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
          <XAxis dataKey="label" tick={{ fontSize: 7, fill: '#64748b' }} interval={0} angle={-45} textAnchor="end" height={30} />
          <YAxis tick={false} width={0} />
          <Tooltip
            contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', fontSize: 11 }}
            content={({ payload }) => payload?.[0] ? <div style={{fontSize:10,color:"#94a3b8"}}>{payload[0].payload.label}: {payload[0].payload.raw.toFixed(3)}</div> : null}
          />
          <Bar dataKey="value" radius={[2, 2, 0, 0]}>
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.raw > 0.5 ? '#ef4444' : entry.raw > 0.2 ? '#f59e0b' : '#22d3ee'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function TrackCard({ track, selected, onClick }: { track: LiveTrack; selected: boolean; onClick: () => void }) {
  const cfg = BEHAVIOR_CONFIG[track.behavior] ?? BEHAVIOR_CONFIG.normal;
  return (
    <div
      onClick={onClick}
      className="p-3 rounded-xl cursor-pointer transition-all duration-200"
      style={{
        background: selected ? cfg.bg : 'rgba(15,23,42,0.7)',
        border: `1px solid ${selected ? cfg.color + '66' : 'rgba(51,65,85,0.5)'}`,
        boxShadow: selected ? `0 0 12px ${cfg.color}22` : 'none',
      }}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold"
            style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.color}55` }}>
            {String(track.track_id).padStart(2, '0')}
          </div>
          <span className="text-sm font-medium text-white">Person #{track.track_id}</span>
        </div>
        <BehaviorBadge behavior={track.behavior} pulse={track.behavior !== 'normal'} />
      </div>

      {/* Confidence bars */}
      <div className="space-y-1">
        {[
          { label: 'Normal',   val: track.c_normal,   color: '#22c55e' },
          { label: 'Distress', val: track.c_distress,  color: '#f59e0b' },
          { label: 'Drowning', val: track.c_drowning,  color: '#ef4444' },
        ].map(({ label, val, color }) => (
          <div key={label} className="flex items-center gap-2">
            <span className="text-xs w-14" style={{ color: '#64748b' }}>{label}</span>
            <div className="flex-1 h-1.5 rounded-full" style={{ background: 'rgba(51,65,85,0.4)' }}>
              <div className="h-full rounded-full transition-all duration-300"
                style={{ width: `${(val * 100).toFixed(0)}%`, background: color }} />
            </div>
            <span className="text-xs w-8 text-right" style={{ color: '#94a3b8' }}>
              {(val * 100).toFixed(0)}%
            </span>
          </div>
        ))}
      </div>

      {/* Sequence accumulation */}
      <div className="mt-2 flex items-center gap-1.5">
        <div className={`w-1.5 h-1.5 rounded-full ${track.sequence_ready ? 'bg-green-400' : 'bg-yellow-400'}`} />
        <span className="text-xs" style={{ color: '#64748b' }}>
          {track.sequence_ready ? 'LSTM sequence ready' : 'Accumulating sequence...'}
        </span>
      </div>

      {/* Feature vector */}
      {selected && track.feature_vector && <FeatureBar vector={track.feature_vector} />}
    </div>
  );
}

function AlertBanner({ alert }: { alert: { level: string; track_id: number; behavior: string; confidence_drowning: number } }) {
  return (
    <div className="rounded-xl p-3 flex items-center gap-3 animate-pulse"
      style={{ background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.4)' }}>
      <AlertTriangle size={18} className="text-red-400 flex-shrink-0" />
      <div className="flex-1">
        <p className="text-sm font-bold text-red-400">
          {alert.level.toUpperCase()} — Person #{alert.track_id}
        </p>
        <p className="text-xs" style={{ color: '#fca5a5' }}>
          {alert.behavior.toUpperCase()} · {(alert.confidence_drowning * 100).toFixed(0)}% drowning confidence
        </p>
      </div>
    </div>
  );
}

export default function LiveMonitoringPage() {
  const { status: monStatus, lastMessage: monMsg } =
    useWebSocket<FrameResult>(`${WS_BASE}/ws/monitoring`);
  const { lastMessage: metricsMsg } =
    useWebSocket<SystemMetrics>(`${WS_BASE}/ws/metrics`);

  const [tracks,        setTracks]        = useState<LiveTrack[]>([]);
  const [selectedTrack, setSelectedTrack] = useState<number | null>(null);
  const [activeAlerts,  setActiveAlerts]  = useState<LiveTrack['alert'][]>([]);
  const [stats,         setStats]         = useState<FrameResult['stats']>();
  const [metrics,       setMetrics]       = useState<SystemMetrics | null>(null);
  const [frameNo,       setFrameNo]       = useState(0);
  const [procMs,        setProcMs]        = useState(0);
  const alertLog = useRef<{ id: number; alert: NonNullable<LiveTrack['alert']>; ts: Date }[]>([]);
  const alertId  = useRef(0);

  useEffect(() => {
    if (!monMsg) return;
    if (monMsg.tracks) {
      setTracks(monMsg.tracks);
      setFrameNo(monMsg.frame_number ?? 0);
      setProcMs(monMsg.processing_ms ?? 0);
      // Collect live alerts from tracks
      const newAlerts = monMsg.tracks
        .map(t => t.alert)
        .filter((a): a is NonNullable<LiveTrack['alert']> => !!a);
      newAlerts.forEach(a => {
        alertLog.current = [
          { id: alertId.current++, alert: a, ts: new Date() },
          ...alertLog.current.slice(0, 19),
        ];
      });
      setActiveAlerts(newAlerts);
    }
    if (monMsg.stats) setStats(monMsg.stats);
  }, [monMsg]);

  useEffect(() => {
    if (metricsMsg) setMetrics(metricsMsg);
  }, [metricsMsg]);

  const criticalTracks = tracks.filter(t => t.behavior === 'drowning');
  // distressTracks: tracked but not rendered in this phase

  return (
    <div className="p-4 space-y-4 h-full overflow-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Activity size={18} className="text-cyan-400" /> Live Monitoring
          </h1>
          <p className="text-xs mt-0.5" style={{ color: '#64748b' }}>
            Real-time drowning detection · 16-D feature analysis
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-xs" style={{ color: '#64748b' }}>
            Frame #{frameNo} · {procMs.toFixed(0)}ms
          </div>
          <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold ${
            monStatus === 'connected' ? 'text-green-400' : 'text-yellow-400'
          }`} style={{ background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(51,65,85,0.5)' }}>
            {monStatus === 'connected'
              ? <><Wifi size={12} /> Live</>
              : <><WifiOff size={12} /> Connecting...</>}
          </div>
        </div>
      </div>

      {/* Pipeline status bar */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { icon: <Users size={13} />,  label: 'Active Tracks',   val: stats.active_tracks },
            { icon: <Zap size={13} />,    label: 'Session FPS',     val: stats.session_fps?.toFixed(1) ?? '-' },
            { icon: <AlertTriangle size={13} />, label: 'Total Alerts', val: stats.total_alerts },
            { icon: <Cpu size={13} />,    label: 'Scorer Mode',     val: stats.scorer_mode },
          ].map(({ icon, label, val }) => (
            <div key={label} className="rounded-xl p-3 flex items-center gap-2"
              style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.4)' }}>
              <span className="text-cyan-400">{icon}</span>
              <div>
                <p className="text-xs" style={{ color: '#64748b' }}>{label}</p>
                <p className="text-sm font-bold text-white">{val}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Track list */}
        <div className="lg:col-span-2 space-y-3">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Users size={14} className="text-cyan-400" />
            Tracked Persons ({tracks.length})
            {criticalTracks.length > 0 && (
              <span className="px-1.5 py-0.5 rounded text-xs font-bold bg-red-500/20 text-red-400 animate-pulse">
                {criticalTracks.length} CRITICAL
              </span>
            )}
          </h2>

          {tracks.length === 0 ? (
            <div className="rounded-xl p-8 text-center" style={{ background: 'rgba(15,23,42,0.5)', border: '1px solid rgba(51,65,85,0.3)' }}>
              <Users size={32} className="mx-auto mb-3 text-slate-600" />
              <p className="text-sm" style={{ color: '#64748b' }}>
                {monStatus === 'connected'
                  ? 'Pipeline active — no persons detected in current frame'
                  : 'Connecting to live pipeline...'}
              </p>
              <p className="text-xs mt-2" style={{ color: '#475569' }}>
                Upload a video or connect a camera to see real-time tracking
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {tracks.map(track => (
                <TrackCard
                  key={track.track_id}
                  track={track}
                  selected={selectedTrack === track.track_id}
                  onClick={() => setSelectedTrack(
                    selectedTrack === track.track_id ? null : track.track_id
                  )}
                />
              ))}
            </div>
          )}

          {/* Active alerts */}
          {activeAlerts.length > 0 && (
            <div className="space-y-2 mt-4">
              <h3 className="text-xs font-semibold" style={{ color: '#ef4444' }}>ACTIVE ALERTS</h3>
              {activeAlerts.map((a, i) => a && <AlertBanner key={i} alert={a} />)}
            </div>
          )}
        </div>

        {/* System panel */}
        <div className="space-y-3">
          {/* System metrics */}
          <div className="rounded-xl p-4" style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.4)' }}>
            <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Cpu size={14} className="text-cyan-400" /> System Health
            </h2>
            {metrics ? (
              <div className="space-y-3">
                {[
                  { label: 'CPU',  val: metrics.cpu_percent, color: '#22d3ee' },
                  { label: 'RAM',  val: metrics.ram_percent, color: '#818cf8' },
                ].map(({ label, val, color }) => (
                  <div key={label}>
                    <div className="flex justify-between text-xs mb-1">
                      <span style={{ color: '#94a3b8' }}>{label}</span>
                      <span className="text-white font-medium">{val?.toFixed(0)}%</span>
                    </div>
                    <div className="h-1.5 rounded-full" style={{ background: 'rgba(51,65,85,0.5)' }}>
                      <div className="h-full rounded-full transition-all duration-500"
                        style={{ width: `${val}%`, background: color }} />
                    </div>
                  </div>
                ))}
                <div className="pt-2 space-y-1.5 text-xs border-t" style={{ borderColor: 'rgba(51,65,85,0.4)' }}>
                  <div className="flex justify-between">
                    <span style={{ color: '#64748b' }}>RAM Used</span>
                    <span className="text-white">{metrics.ram_used_gb?.toFixed(2)} GB</span>
                  </div>
                  <div className="flex justify-between">
                    <span style={{ color: '#64748b' }}>Pipeline FPS</span>
                    <span className="text-white">{metrics.pipeline_fps?.toFixed(1) ?? '—'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span style={{ color: '#64748b' }}>AI Scorer</span>
                    <span style={{ color: metrics.scorer_mode === 'lstm' ? '#22c55e' : '#f59e0b' }}>
                      {metrics.scorer_mode?.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span style={{ color: '#64748b' }}>GPU</span>
                    <span style={{ color: '#64748b' }}>Not available (CPU edge)</span>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs" style={{ color: '#64748b' }}>Connecting to metrics...</p>
            )}
          </div>

          {/* Alert log */}
          <div className="rounded-xl p-4" style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.4)' }}>
            <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Clock size={14} className="text-cyan-400" /> Alert Log
            </h2>
            <div className="space-y-2 max-h-64 overflow-auto">
              {alertLog.current.length === 0 ? (
                <p className="text-xs" style={{ color: '#64748b' }}>No alerts this session</p>
              ) : alertLog.current.map(({ id, alert, ts }) => (
                <div key={id} className="p-2 rounded-lg" style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}>
                  <p className="text-xs font-semibold text-red-400">
                    [{alert.level.toUpperCase()}] Track #{alert.track_id}
                  </p>
                  <p className="text-xs" style={{ color: '#94a3b8' }}>
                    {alert.behavior} · {(alert.confidence_drowning * 100).toFixed(0)}% confidence
                  </p>
                  <p className="text-xs mt-0.5" style={{ color: '#475569' }}>
                    {ts.toLocaleTimeString()}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


