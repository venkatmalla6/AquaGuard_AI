import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  },
);

export default api;

export interface EdgeConfigPayload {
  engine: 'onnx' | 'torchscript' | 'pytorch';
  enable_frame_skipping: boolean;
  target_fps: number;
}

export interface EdgeStatusResponse {
  status: string;
  active_engine: 'onnx' | 'torchscript' | 'pytorch';
  available_engines: string[];
  frame_skipping: {
    enabled: boolean;
    target_fps: number;
    idle_stride: number;
    max_stride: number;
    estimated_cpu_saving_idle_pct: number;
  };
  opencv_acceleration: {
    use_optimized: boolean;
    num_threads: number;
    opencl_available: boolean;
    build_info_simd: string;
    cpu_threads_configured: number;
  };
  hardware_concurrency: {
    logical_cores: number;
    physical_cores: number;
    cpu_percent: number;
  };
  models: {
    onnx: { available: boolean; size_kb: number; path: string };
    torchscript: { available: boolean; size_kb: number; path: string };
    pytorch: { available: boolean; size_kb: number; path: string };
  };
}

export interface BenchmarkMetrics {
  mean_ms: number;
  std_ms: number;
  p50_ms: number;
  p95_ms: number;
  p99_ms: number;
  min_ms: number;
  max_ms: number;
  throughput_samples_per_sec: number;
  speedup_vs_pytorch: number;
}

export interface BenchmarkResponse {
  status: string;
  benchmark: {
    benchmark_date: string;
    iterations: number;
    results: Record<string, Record<string, BenchmarkMetrics>>;
    summary: {
      recommended_backend: string;
      tested_backends: string[];
    };
  };
}


export interface ScenarioItem {
  id: string;
  title: string;
  description: string;
  risk_level: string;
  primary_label: string;
  typical_onset_sec: number;
  default_duration_sec: number;
}

export interface ScenarioEvaluationResponse {
  status: string;
  scenario: string;
  evaluation: {
    track_id: number;
    scenario_type: string;
    total_frames: number;
    ground_truth_label: string;
    frame_accuracy: number;
    alerts_count: number;
    first_alert: { frame_index: number; timestamp: number; level: string; behavior: string } | null;
    time_to_detect_seconds: number | null;
    false_alarms_before_onset: number;
    predictions_sample: Array<{
      frame_index: number;
      timestamp: number;
      ground_truth: string;
      predicted: string;
      c_drowning: number;
      c_distress: number;
      c_normal: number;
    }>;
  };
  summary: {
    time_to_detect_seconds: number | null;
    accuracy_percent: number;
    false_alarms: number;
    sla_met: boolean;
  };
}

export const authAPI = {
  login: (email: string, password: string) => api.post('/api/auth/login', { email, password }),
  logout: () => api.post('/api/auth/logout'),
};

export const systemAPI = {
  health: () => api.get('/health'),
  getStatus: () => api.get('/api/system/status'),
  getConfig: () => api.get('/api/system/config'),
  getEdgeStatus: () => api.get<EdgeStatusResponse>('/api/system/edge'),
  configureEdge: (payload: EdgeConfigPayload) => api.post('/api/system/edge/configure', payload),
  runBenchmark: (iterations: number = 25, batch_sizes: number[] = [1, 4, 16]) =>
    api.post<BenchmarkResponse>('/api/system/edge/benchmark', { iterations, batch_sizes }),
  exportModels: () => api.post('/api/system/edge/export-models'),
};

export const alertAPI = {
  list:          (params?: Record<string, string>) => api.get('/api/alerts', { params }),
  acknowledge:   (id: number) => api.post(`/api/alerts/${id}/acknowledge`),
  resolve:       (id: number) => api.post(`/api/alerts/${id}/resolve`),
  getChannels:   () => api.get('/api/alerts/channels'),
  testDispatch:  () => api.post('/api/alerts/test-dispatch'),
  dispatchAlert: (id: number) => api.post(`/api/alerts/${id}/dispatch`),
  getHistory:    (id: number) => api.get(`/api/alerts/${id}/history`),
};

export const experimentAPI = {
  list:          () => api.get('/api/experiments'),
  create:        (data: Record<string, unknown>) => api.post('/api/experiments', data),
  getMetrics:    (id: number) => api.get(`/api/experiments/${id}/metrics`),
  getComparison: () => api.get('/api/experiments/comparison'),
  runAll:        () => api.post('/api/experiments/run-all'),
};

export const videoAPI = {
  list: () => api.get('/api/videos'),
  get: (id: number) => api.get(`/api/videos/${id}`),
  upload: (file: File, autoProcess = true, onProgress?: (pct: number) => void) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/api/videos/upload?auto_process=${autoProcess}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const pct = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(pct);
        }
      },
    });
  },
  process: (id: number) => api.post(`/api/videos/${id}/process`),
  delete: (id: number) => api.delete(`/api/videos/${id}`),
  getStreamUrl: (id: number) => `${api.defaults.baseURL || ''}/api/videos/${id}/stream`,
};


export const scenarioAPI = {
  list: () => api.get<{ status: string; count: number; scenarios: ScenarioItem[] }>('/api/scenarios'),
  generate: (data: { scenario_type: string; duration_seconds: number; num_swimmers: number; distress_onset_second: number; render_video: boolean }) =>
    api.post('/api/scenarios/generate', data),
  evaluate: (data: { scenario_type: string; duration_seconds: number; distress_onset_second: number; edge_backend: string }) =>
    api.post<ScenarioEvaluationResponse>('/api/scenarios/evaluate', data),
};
