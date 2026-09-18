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

export const authAPI = {
  login: (email: string, password: string) => api.post('/api/auth/login', { email, password }),
  logout: () => api.post('/api/auth/logout'),
};

export const systemAPI = {
  health: () => api.get('/health'),
};

export const alertAPI = {
  list:        (params?: Record<string, string>) => api.get('/api/alerts', { params }),
  acknowledge: (id: number) => api.post(`/api/alerts/${id}/acknowledge`),
  resolve:     (id: number) => api.post(`/api/alerts/${id}/resolve`),
};

export const experimentAPI = {
  list:       () => api.get('/api/experiments'),
  create:     (data: Record<string, unknown>) => api.post('/api/experiments', data),
  getMetrics: (id: number) => api.get(`/api/experiments/${id}/metrics`),
};