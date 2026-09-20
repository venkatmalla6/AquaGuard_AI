// AquaGuard AI - Extended Types (Phase 8)
export type BehaviorClass = 'normal' | 'distress' | 'drowning' | 'potential_drowning';
export type AlertSeverity = 'warning' | 'critical';
export type AlertStatus   = 'active' | 'acknowledged' | 'resolved' | 'false_alarm';
export type CameraStatus  = 'online' | 'offline' | 'error';
export type ScorerMode    = 'rule-based' | 'lstm';

// --- Live Pipeline Types (from /ws/monitoring) ---
export interface LiveTrack {
  track_id:        number;
  bbox:            [number, number, number, number]; // x1,y1,x2,y2
  center:          [number, number];
  confidence:      number;
  behavior:        BehaviorClass;
  c_normal:        number;
  c_distress:      number;
  c_drowning:      number;
  feature_vector:  number[] | null;   // 16-D
  sequence_ready:  boolean;
  alert:           LiveAlert | null;
}

export interface LiveAlert {
  track_id:            number;
  level:               'warning' | 'critical';
  behavior:            BehaviorClass;
  confidence_drowning: number;
  confidence_distress: number;
  consecutive_frames:  number;
  timestamp:           string;
}

export interface PipelineStats {
  is_running:      boolean;
  total_frames:    number;
  total_alerts:    number;
  active_tracks:   number;
  uptime_seconds:  number;
  session_fps:     number;
  scorer_mode:     ScorerMode;
}

export interface FrameResult {
  type:           'frame_result' | 'pipeline_status' | 'heartbeat' | 'alerts_ready';
  frame_number?:  number;
  timestamp?:     number;
  processing_ms?: number;
  alert_count?:   number;
  tracks?:        LiveTrack[];
  stats?:         PipelineStats;
  message?:       string;
}

// --- System Metrics (from /ws/metrics) ---
export interface SystemMetrics {
  type:            string;
  cpu_percent:     number;
  ram_percent:     number;
  ram_used_gb:     number;
  gpu_available:   boolean;
  pipeline_fps:    number | null;
  active_tracks:   number;
  total_alerts:    number;
  scorer_mode:     ScorerMode;
  uptime_seconds:  number;
}

// --- API Response Types ---
export interface Alert {
  id:                 number;
  alertUid:           string;
  trackId:            number;
  severity:           AlertSeverity;
  status:             AlertStatus;
  behavior:           BehaviorClass;
  confidence:         number;
  triggeredAt:        string;
  acknowledgedAt?:    string;
  cameraId?:          number;
  consecutiveFrames:  number;
  alertLatencyMs?:    number;
}

export interface Experiment {
  id:             number;
  experimentUid:  string;
  name:           string;
  description?:   string;
  modelType:      string;
  status:         'pending' | 'running' | 'completed' | 'failed';
  createdAt:      string;
}

export interface ExperimentMetrics {
  precision?:              number;
  recall?:                 number;
  f1Score?:                number;
  map50?:                  number;
  falsePositiveRate?:      number;
  falseNegativeRate?:      number;
  avgFps?:                 number;
  avgInferenceLatencyMs?:  number;
  avgAlertLatencyMs?:      number;
  confusionMatrixJson?:    string;
}

// Feature dimension labels (matches FeatureScorer.FEATURE_IDX)
export const FEATURE_LABELS = [
  'cx_norm','cy_norm','w_norm','h_norm','aspect_ratio','area_norm',
  'displacement','vel_x','vel_y','speed','acceleration',
  'dir_sin','dir_cos','mv_variance','vert_ratio','inactivity',
];

export const BEHAVIOR_CONFIG: Record<BehaviorClass, { label: string; color: string; bg: string; pulse: boolean }> = {
  normal:            { label: 'Normal',    color: '#22c55e', bg: 'rgba(34,197,94,0.12)',   pulse: false },
  distress:          { label: 'Distress',  color: '#f59e0b', bg: 'rgba(245,158,11,0.12)',  pulse: true  },
  drowning:          { label: 'DROWNING',  color: '#ef4444', bg: 'rgba(239,68,68,0.15)',   pulse: true  },
  potential_drowning:{ label: 'DROWNING',  color: '#ef4444', bg: 'rgba(239,68,68,0.15)',   pulse: true  },
};
