import api from './api';
import type { EducationMaterial, EducationMaterialList } from '../types';

interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export const educationService = {
  async list(params?: { page?: number; kategori_sampah?: string; search?: string }): Promise<Paginated<EducationMaterialList>> {
    const response = await api.get<Paginated<EducationMaterialList>>('/education/', { params });
    return response.data;
  },

  async getById(id: string): Promise<EducationMaterial> {
    const response = await api.get<EducationMaterial>(`/education/${id}/`);
    return response.data;
  },
};
