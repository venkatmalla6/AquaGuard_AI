// AquaGuard AI - People Tracking & Movement Telemetry Page (Phase 9)
// Multi-person track trajectory mapping, 2D pool radar, posture aspect ratio analysis
import { useState, useEffect, useRef } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import {
  Users, ShieldAlert, Wifi, Compass,
  CheckCircle2, AlertTriangle, RefreshCw
} from 'lucide-react';
import { BEHAVIOR_CONFIG, FEATURE_LABELS, type FrameResult, type BehaviorClass } from '../types';

const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

interface SwimmerHistory {
  track_id: number;
  positions: { x: number; y: number; time: number }[];
  duration_seconds: number;
  aspect_ratio: number;
  behavior: BehaviorClass;
  confidence: number;
  c_drowning: number;
  c_distress: number;
  feature_vector?: number[] | null;
  speed: number;
}

export default function PeopleTrackingPage() {
  const { status: wsStatus, lastMessage: monMsg } =
    useWebSocket<FrameResult>(`${WS_BASE}/ws/monitoring`);

  const [selectedTrackId, setSelectedTrackId] = useState<number | null>(null);
  const [filterRisk, setFilterRisk] = useState<'all' | 'normal' | 'distress' | 'drowning'>('all');
  const [historyMap, setHistoryMap] = useState<Record<number, SwimmerHistory>>({});

  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Ingest WebSocket live tracking frames
  useEffect(() => {
    if (!monMsg || !monMsg.tracks || monMsg.tracks.length === 0) return;

    setHistoryMap((prev) => {
      const updated = { ...prev };
      const now = Date.now();

      monMsg.tracks?.forEach((t) => {
        const [x1, y1, x2, y2] = t.bbox;
        const w = Math.max(1, x2 - x1);
        const h = Math.max(1, y2 - y1);
        const ar = w / h; // Aspect ratio: horizontal > 0.6, vertical distress < 0.5
        const cx = (x1 + x2) / (2 * 640);
        const cy = (y1 + y2) / (2 * 360);

        const existing = updated[t.track_id];
        const prevPos = existing?.positions[existing.positions.length - 1];
        let calcSpeed = 0;
        if (prevPos) {
          const dx = (cx - prevPos.x) * 640;
          const dy = (cy - prevPos.y) * 360;
          calcSpeed = Math.sqrt(dx * dx + dy * dy) * 10; // approx px/s
        }

        const newPositions = [
          ...(existing?.positions || []).slice(-25), // keep last 25 trail points
          { x: cx, y: cy, time: now },
        ];

        updated[t.track_id] = {
          track_id: t.track_id,
          positions: newPositions,
          duration_seconds: (existing?.duration_seconds || 0) + 0.5,
          aspect_ratio: ar,
          behavior: t.behavior,
          confidence: t.confidence,
          c_drowning: t.c_drowning,
          c_distress: t.c_distress,
          feature_vector: t.feature_vector,
          speed: calcSpeed,
        };
      });

      return updated;
    });
  }, [monMsg]);

  // Fallback demo simulation if WebSocket has no live tracks yet
  useEffect(() => {
    const interval = setInterval(() => {
      setHistoryMap((prev) => {
        if (Object.keys(prev).length > 0 && wsStatus === 'connected') return prev;

        const updated = { ...prev };
        const now = Date.now();

        // 3 synthetic swimmers
        const demoSwimmers = [
          { id: 101, baseAr: 1.15, beh: 'normal' as BehaviorClass, cd: 0.05, cs: 0.1, cx: 0.25 + Math.sin(now / 3000) * 0.15, cy: 0.35 + Math.cos(now / 3500) * 0.1 },
          { id: 102, baseAr: 0.85, beh: 'normal' as BehaviorClass, cd: 0.12, cs: 0.2, cx: 0.65 + Math.cos(now / 2500) * 0.2,  cy: 0.65 + Math.sin(now / 3000) * 0.15 },
          { id: 103, baseAr: 0.42, beh: 'drowning' as BehaviorClass, cd: 0.94, cs: 0.85, cx: 0.82 + Math.sin(now / 800) * 0.02,  cy: 0.78 + Math.cos(now / 900) * 0.02 },
        ];

        demoSwimmers.forEach((s) => {
          const existing = updated[s.id];
          const newPositions = [
            ...(existing?.positions || []).slice(-30),
            { x: s.cx, y: s.cy, time: now },
          ];
          updated[s.id] = {
            track_id: s.id,
            positions: newPositions,
            duration_seconds: (existing?.duration_seconds || 0) + 0.5,
            aspect_ratio: s.baseAr,
            behavior: s.beh,
            confidence: 0.92,
            c_drowning: s.cd,
            c_distress: s.cs,
            speed: s.beh === 'drowning' ? 4 : 45,
            feature_vector: [s.cx, s.cy, 0.1, 0.2, s.baseAr, 0.02, 0.01, 0.02, -0.01, 0.03, 0.0, 0.0, 1.0, 0.05, s.beh === 'drowning' ? 0.9 : 0.2, s.beh === 'drowning' ? 0.85 : 0.1],
          };
        });

        return updated;
      });
    }, 500);

    return () => clearInterval(interval);
  }, [wsStatus]);

  // Render 2D Pool Radar Canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;

    // Clear background (Pool Water Deep Slate Blue)
    ctx.fillStyle = '#061325';
    ctx.fillRect(0, 0, w, h);

    // Draw pool grid & lane ropes
    ctx.strokeStyle = 'rgba(0, 181, 212, 0.12)';
    ctx.lineWidth = 1;
    const lanes = 6;
    for (let i = 1; i < lanes; i++) {
      const y = (h / lanes) * i;
      ctx.beginPath();
      ctx.setLineDash([6, 6]);
      ctx.moveTo(20, y);
      ctx.lineTo(w - 20, y);
      ctx.stroke();
    }
    ctx.setLineDash([]);

    // Draw pool outer boundary
    ctx.strokeStyle = 'rgba(0, 181, 212, 0.4)';
    ctx.lineWidth = 2;
    ctx.strokeRect(15, 15, w - 30, h - 30);

    // Render each tracked swimmer
    Object.values(historyMap).forEach((swimmer) => {
      if (swimmer.positions.length === 0) return;
      const isSelected = selectedTrackId === swimmer.track_id;
      const cfg = BEHAVIOR_CONFIG[swimmer.behavior] ?? BEHAVIOR_CONFIG.normal;

      // Draw trajectory breadcrumb trail
      ctx.beginPath();
      ctx.strokeStyle = `${cfg.color}55`;
      ctx.lineWidth = isSelected ? 3 : 1.5;
      swimmer.positions.forEach((p, idx) => {
        const px = 20 + p.x * (w - 40);
        const py = 20 + p.y * (h - 40);
        if (idx === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      });
      ctx.stroke();

      // Current position
      const lastPos = swimmer.positions[swimmer.positions.length - 1];
      const curX = 20 + lastPos.x * (w - 40);
      const curY = 20 + lastPos.y * (h - 40);

      // Outer alert pulse if distress or drowning
      if (swimmer.behavior !== 'normal') {
        ctx.beginPath();
        ctx.arc(curX, curY, isSelected ? 22 : 16, 0, Math.PI * 2);
        ctx.fillStyle = `${cfg.color}22`;
        ctx.fill();
        ctx.strokeStyle = `${cfg.color}88`;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // Swimmer marker core
      ctx.beginPath();
      ctx.arc(curX, curY, isSelected ? 10 : 8, 0, Math.PI * 2);
      ctx.fillStyle = cfg.color;
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Swimmer label
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 10px monospace';
      ctx.textAlign = 'center';
      ctx.fillText(`#${swimmer.track_id}`, curX, curY - 12);
    });
  }, [historyMap, selectedTrackId]);

  const swimmersList = Object.values(historyMap);
  const filteredSwimmers = swimmersList.filter((s) => {
    if (filterRisk === 'all') return true;
    if (filterRisk === 'normal') return s.behavior === 'normal';
    if (filterRisk === 'distress') return s.behavior === 'distress';
    if (filterRisk === 'drowning') return s.behavior === 'drowning' || s.behavior === 'potential_drowning';
    return true;
  });

  const selectedSwimmer = selectedTrackId
    ? historyMap[selectedTrackId]
    : swimmersList[0] || null;

  const normalCount = swimmersList.filter((s) => s.behavior === 'normal').length;
  const distressCount = swimmersList.filter((s) => s.behavior === 'distress').length;
  const drowningCount = swimmersList.filter(
    (s) => s.behavior === 'drowning' || s.behavior === 'potential_drowning'
  ).length;

  return (
    <div className="p-4 space-y-4 h-full overflow-y-auto">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Users size={20} className="text-cyan-400" /> People Tracking &amp; Trajectories
          </h1>
          <p className="text-xs mt-0.5" style={{ color: '#64748b' }}>
            Multi-swimmer spatial tracking, trajectory mapping, and posture distress diagnostics
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold ${
              wsStatus === 'connected' ? 'text-green-400' : 'text-cyan-400'
            }`}
            style={{ background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(51,65,85,0.5)' }}
          >
            {wsStatus === 'connected' ? (
              <><Wifi size={12} /> Live Telemetry</>
            ) : (
              <><RefreshCw size={12} className="animate-spin" /> Radar Active (Simulation)</>
            )}
          </div>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div
          onClick={() => setFilterRisk('all')}
          className={`p-3.5 rounded-xl cursor-pointer transition-all ${
            filterRisk === 'all' ? 'border-cyan-500 bg-cyan-950/20' : 'border-slate-800 bg-slate-900/60'
          } border`}
        >
          <div className="flex items-center justify-between text-xs" style={{ color: '#64748b' }}>
            <span>Active Swimmers</span>
            <Users size={14} className="text-cyan-400" />
          </div>
          <div className="text-xl font-bold text-white mt-1">{swimmersList.length}</div>
        </div>

        <div
          onClick={() => setFilterRisk('normal')}
          className={`p-3.5 rounded-xl cursor-pointer transition-all ${
            filterRisk === 'normal' ? 'border-green-500 bg-green-950/20' : 'border-slate-800 bg-slate-900/60'
          } border`}
        >
          <div className="flex items-center justify-between text-xs" style={{ color: '#64748b' }}>
            <span>Normal Swimming</span>
            <CheckCircle2 size={14} className="text-green-400" />
          </div>
          <div className="text-xl font-bold text-green-400 mt-1">{normalCount}</div>
        </div>

        <div
          onClick={() => setFilterRisk('distress')}
          className={`p-3.5 rounded-xl cursor-pointer transition-all ${
            filterRisk === 'distress' ? 'border-amber-500 bg-amber-950/20' : 'border-slate-800 bg-slate-900/60'
          } border`}
        >
          <div className="flex items-center justify-between text-xs" style={{ color: '#64748b' }}>
            <span>Distress / Struggling</span>
            <AlertTriangle size={14} className="text-amber-400" />
          </div>
          <div className="text-xl font-bold text-amber-400 mt-1">{distressCount}</div>
        </div>

        <div
          onClick={() => setFilterRisk('drowning')}
          className={`p-3.5 rounded-xl cursor-pointer transition-all ${
            filterRisk === 'drowning' ? 'border-red-500 bg-red-950/20' : 'border-slate-800 bg-slate-900/60'
          } border`}
        >
          <div className="flex items-center justify-between text-xs" style={{ color: '#64748b' }}>
            <span>Critical Sinking</span>
            <ShieldAlert size={14} className="text-red-400" />
          </div>
          <div className="text-xl font-bold text-red-400 mt-1">{drowningCount}</div>
        </div>
      </div>

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left: 2D Overhead Pool Radar Canvas */}
        <div className="lg:col-span-7 space-y-4">
          <div
            className="rounded-2xl p-4 space-y-3"
            style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.5)' }}
          >
            <div className="flex items-center justify-between border-b pb-3" style={{ borderColor: 'rgba(51,65,85,0.4)' }}>
              <div className="flex items-center gap-2">
                <Compass size={16} className="text-cyan-400" />
                <h2 className="text-sm font-bold text-white">2D Overhead Pool Surveillance Radar</h2>
              </div>
              <div className="flex items-center gap-2 text-[11px]" style={{ color: '#94a3b8' }}>
                <span className="inline-block w-2 h-2 rounded-full bg-green-400"></span> Normal
                <span className="inline-block w-2 h-2 rounded-full bg-amber-400 ml-2"></span> Distress
                <span className="inline-block w-2 h-2 rounded-full bg-red-400 ml-2"></span> Sinking
              </div>
            </div>

            {/* Radar Canvas View */}
            <div className="relative rounded-xl overflow-hidden border border-cyan-950/60 shadow-inner">
              <canvas
                ref={canvasRef}
                width={640}
                height={340}
                className="w-full h-auto block"
              />
              <div className="absolute bottom-2 left-3 text-[10px] text-cyan-400/70 font-mono">
                AQUAGUARD 2D SPATIAL RADAR • 6 LANES • SCALE 1:1
              </div>
            </div>

            <p className="text-xs" style={{ color: '#64748b' }}>
              Click any swimmer marker on the map or in the table below to inspect their 16-D feature diagnostics, vertical posture index, and trajectory.
            </p>
          </div>

          {/* Swimmer Telemetry Table */}
          <div
            className="rounded-2xl p-4 space-y-3"
            style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.5)' }}
          >
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Tracked Swimmers Roster ({filteredSwimmers.length})
              </h3>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-500 font-semibold">
                    <th className="pb-2">Track ID</th>
                    <th className="pb-2">Behavior</th>
                    <th className="pb-2">Aspect Ratio (w/h)</th>
                    <th className="pb-2">Speed</th>
                    <th className="pb-2">Drowning Conf</th>
                    <th className="pb-2 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {filteredSwimmers.map((s) => {
                    const cfg = BEHAVIOR_CONFIG[s.behavior] ?? BEHAVIOR_CONFIG.normal;
                    const isSelected = selectedTrackId === s.track_id;

                    return (
                      <tr
                        key={s.track_id}
                        onClick={() => setSelectedTrackId(s.track_id)}
                        className={`cursor-pointer transition-colors ${
                          isSelected ? 'bg-cyan-950/40' : 'hover:bg-slate-800/30'
                        }`}
                      >
                        <td className="py-2.5 font-mono font-bold text-white">
                          #{s.track_id}
                        </td>
                        <td className="py-2.5">
                          <span
                            className="px-2 py-0.5 rounded-full text-[10px] font-bold"
                            style={{ background: cfg.bg, color: cfg.color }}
                          >
                            {cfg.label}
                          </span>
                        </td>
                        <td className="py-2.5 font-mono">
                          <span className={s.aspect_ratio < 0.6 ? 'text-red-400 font-bold' : 'text-slate-300'}>
                            {s.aspect_ratio.toFixed(2)}
                          </span>
                          <span className="text-[10px] text-slate-500 ml-1">
                            {s.aspect_ratio < 0.6 ? '(Vertical)' : '(Horizontal)'}
                          </span>
                        </td>
                        <td className="py-2.5 text-slate-300">
                          {s.speed.toFixed(0)} px/s
                        </td>
                        <td className="py-2.5">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                              <div
                                className="h-full bg-red-400"
                                style={{ width: `${(s.c_drowning * 100).toFixed(0)}%` }}
                              />
                            </div>
                            <span className="font-mono text-slate-300">
                              {(s.c_drowning * 100).toFixed(0)}%
                            </span>
                          </div>
                        </td>
                        <td className="py-2.5 text-right">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedTrackId(s.track_id);
                            }}
                            className="text-cyan-400 hover:text-cyan-300 font-semibold"
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right: Selected Swimmer Telemetry & 16-D Feature Inspector */}
        <div className="lg:col-span-5 space-y-4">
          <div
            className="rounded-2xl p-4 space-y-4"
            style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.5)' }}
          >
            {selectedSwimmer ? (
              <>
                <div className="flex items-center justify-between border-b pb-3" style={{ borderColor: 'rgba(51,65,85,0.4)' }}>
                  <div className="flex items-center gap-3">
                    <div
                      className="w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm"
                      style={{
                        background: BEHAVIOR_CONFIG[selectedSwimmer.behavior]?.bg || 'rgba(0,181,212,0.1)',
                        color: BEHAVIOR_CONFIG[selectedSwimmer.behavior]?.color || '#22d3ee',
                        border: `1px solid ${BEHAVIOR_CONFIG[selectedSwimmer.behavior]?.color || '#22d3ee'}44`,
                      }}
                    >
                      #{selectedSwimmer.track_id}
                    </div>
                    <div>
                      <h2 className="text-base font-bold text-white">
                        Swimmer #{selectedSwimmer.track_id} Telemetry
                      </h2>
                      <p className="text-xs" style={{ color: '#64748b' }}>
                        Tracked Duration: {selectedSwimmer.duration_seconds.toFixed(0)}s in pool
                      </p>
                    </div>
                  </div>
                  <span
                    className="px-2.5 py-1 rounded-full text-xs font-bold uppercase"
                    style={{
                      background: BEHAVIOR_CONFIG[selectedSwimmer.behavior]?.bg,
                      color: BEHAVIOR_CONFIG[selectedSwimmer.behavior]?.color,
                    }}
                  >
                    {BEHAVIOR_CONFIG[selectedSwimmer.behavior]?.label}
                  </span>
                </div>

                {/* Distress Risk Meters */}
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-slate-400">Behavior Classification Probabilities</div>
                  {[
                    { label: 'Normal Swimming', val: 1 - selectedSwimmer.c_drowning - selectedSwimmer.c_distress, color: '#22c55e' },
                    { label: 'Distress / Struggling', val: selectedSwimmer.c_distress, color: '#f59e0b' },
                    { label: 'Potential Drowning', val: selectedSwimmer.c_drowning, color: '#ef4444' },
                  ].map(({ label, val, color }) => {
                    const clamped = Math.max(0, Math.min(1, val));
                    return (
                      <div key={label} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span style={{ color: '#94a3b8' }}>{label}</span>
                          <span className="font-mono font-bold" style={{ color }}>
                            {(clamped * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-300"
                            style={{ width: `${clamped * 100}%`, background: color }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Spatial & Physical Diagnostics */}
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                    <span className="text-[11px] text-slate-500">Aspect Ratio (w/h)</span>
                    <p className={`text-base font-bold mt-0.5 ${selectedSwimmer.aspect_ratio < 0.6 ? 'text-red-400' : 'text-white'}`}>
                      {selectedSwimmer.aspect_ratio.toFixed(2)}
                    </p>
                    <span className="text-[10px] text-slate-500">Threshold: &gt; 0.6 normal</span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                    <span className="text-[11px] text-slate-500">Velocity</span>
                    <p className="text-base font-bold text-white mt-0.5">
                      {selectedSwimmer.speed.toFixed(0)} px/s
                    </p>
                    <span className="text-[10px] text-slate-500">Track movement speed</span>
                  </div>
                </div>

                {/* 16-D Feature Vector Bar Display */}
                {selectedSwimmer.feature_vector && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs font-semibold text-slate-400">
                      <span>16-D Spatial-Temporal Feature Breakdown</span>
                      <span className="text-[10px] text-cyan-400 font-mono">LSTM Input</span>
                    </div>
                    <div className="grid grid-cols-2 gap-1.5 max-h-56 overflow-y-auto pr-1">
                      {FEATURE_LABELS.map((lbl, idx) => {
                        const val = selectedSwimmer.feature_vector?.[idx] ?? 0;
                        const isHigh = Math.abs(val) > 0.5;
                        return (
                          <div key={lbl} className="p-1.5 rounded-lg bg-slate-900/80 border border-slate-800 flex items-center justify-between text-[10px]">
                            <span className="text-slate-400 font-mono truncate max-w-[90px]">{lbl}</span>
                            <span className={`font-mono font-bold ${isHigh ? 'text-cyan-400' : 'text-slate-300'}`}>
                              {val.toFixed(3)}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-16 text-xs text-slate-500">
                Select a swimmer from the radar or roster to inspect feature telemetry.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

