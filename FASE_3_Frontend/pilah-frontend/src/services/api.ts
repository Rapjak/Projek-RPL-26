import axios from 'axios';

// Base URL: Vite env override or default to local Django dev server
const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Media base URL: derive from API base by stripping any trailing /api/v\d+ or /api
// suffix, so we get the Django root used to prefix relative /media/... paths.
export const mediaBaseURL = baseURL.replace(/\/api(\/v\d+)?\/?$/, '');

const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor - attach JWT
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - on 401, attempt token refresh once; if that fails, logout.
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config as any;
    if (
      error.response?.status === 401 &&
      !original._retry &&
      !original.url.includes('/auth/login') &&
      !original.url.includes('/auth/register') &&
      !original.url.includes('/token/refresh')
    ) {
      original._retry = true;
      const refresh = localStorage.getItem('refresh_token');
      if (refresh) {
        try {
          const resp = await axios.post(
            `${baseURL}/token/refresh/`,
            { refresh },
            { headers: { 'Content-Type': 'application/json' } }
          );
          const newAccess = resp.data.access;
          localStorage.setItem('access_token', newAccess);
          original.headers.Authorization = `Bearer ${newAccess}`;
          return api(original);
        } catch (refreshErr) {
          // refresh failed -> force logout
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
          return Promise.reject(refreshErr);
        }
      } else {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
