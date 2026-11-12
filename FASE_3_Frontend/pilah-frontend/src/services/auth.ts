import api from './api';
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  UserProfile,
  UserPoints,
} from '../types';

export const authService = {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/auth/login', credentials);
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
    }
    return response.data;
  },

  async register(data: RegisterRequest): Promise<RegisterResponse> {
    const response = await api.post<RegisterResponse>('/auth/register', data);
    return response.data;
  },

  async logout(): Promise<void> {
    const refresh = localStorage.getItem('refresh_token');
    try {
      await api.post('/auth/logout', { refresh_token: refresh });
    } catch {
      // ignore errors on logout
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  },

  async getProfile(): Promise<UserProfile> {
    const response = await api.get<UserProfile>('/auth/profile');
    return response.data;
  },

  async updateProfile(data: { name?: string; unit_gedung?: string }): Promise<UserProfile> {
    const response = await api.put<UserProfile>('/auth/profile', data);
    return response.data;
  },

  async getPoints(): Promise<UserPoints> {
    const response = await api.get<UserPoints>('/points/me');
    return response.data;
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  },
};
