export type BehaviorClass = 'normal' | 'distress' | 'potential_drowning';
export type AlertSeverity = 'warning' | 'critical';
export type AlertStatus = 'active' | 'acknowledged' | 'resolved' | 'false_alarm';
export type CameraStatus = 'online' | 'offline' | 'error';

export interface TrackedPerson {
  trackId: number;
  behavior: BehaviorClass;
  confidence: number;
  cx: number;
  cy: number;
  bbox: [number, number, number, number];
  frames: number;
}

export interface Alert {
  id: number;
  alertUid: string;
  trackId: number;
  severity: AlertSeverity;
  status: AlertStatus;
  behavior: BehaviorClass;
  confidence: number;
  triggeredAt: string;
  acknowledgedAt?: string;
  cameraId?: number;
  consecutiveFrames: number;
  alertLatencyMs?: number;
}

export interface Experiment {
  id: number;
  experimentUid: string;
  name: string;
  description?: string;
  modelType: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  createdAt: string;
}

export interface ExperimentMetrics {
  precision?: number;
  recall?: number;
  f1Score?: number;
  map50?: number;
  falsePositiveRate?: number;
  falseNegativeRate?: number;
  avgFps?: number;
  avgInferenceLatencyMs?: number;
  avgAlertLatencyMs?: number;
  confusionMatrixJson?: string;
}

export interface SystemMetrics {
  cpuPercent: number;
  ramPercent: number;
  ramUsedGb: number;
  gpuAvailable: boolean;
  fps?: number;
  latencyMs?: number;
}
