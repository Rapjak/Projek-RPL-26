import api from './api';
import type {
  AdminDashboard,
  AdminActivitiesResponse,
  Reward,
  EducationMaterial,
} from '../types';

export const adminService = {
  async getDashboard(params?: {
    tanggal_mulai?: string;
    tanggal_akhir?: string;
  }): Promise<AdminDashboard> {
    const response = await api.get<AdminDashboard>('/admin/dashboard/', { params });
    return response.data;
  },

  async getActivities(params?: {
    page?: number;
    unit_gedung?: string;
    tanggal_mulai?: string;
    tanggal_akhir?: string;
    kategori?: string;
  }): Promise<AdminActivitiesResponse> {
    const response = await api.get<AdminActivitiesResponse>('/admin/activities/', { params });
    return response.data;
  },

  async createReward(data: Partial<Reward>): Promise<{ reward: Reward; message: string }> {
    const response = await api.post('/admin/rewards/', data);
    return response.data;
  },

  async updateReward(rewardId: string, data: Partial<Reward>): Promise<{ reward: Reward; message: string }> {
    const response = await api.put(`/admin/rewards/${rewardId}/`, data);
    return response.data;
  },

  async deleteReward(rewardId: string): Promise<void> {
    await api.delete(`/admin/rewards/${rewardId}/`);
  },

  async createEducation(data: Partial<EducationMaterial>): Promise<{ id_edukasi: string; message: string }> {
    const response = await api.post('/admin/education/', data);
    return response.data;
  },

  async updateEducation(eduId: string, data: Partial<EducationMaterial>): Promise<{ message: string }> {
    const response = await api.put(`/admin/education/${eduId}/`, data);
    return response.data;
  },

  async deleteEducation(eduId: string): Promise<void> {
    await api.delete(`/admin/education/${eduId}/`);
  },
};
