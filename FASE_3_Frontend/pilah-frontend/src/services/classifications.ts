import api from './api';
import type {
  UploadAccepted,
  ClassificationPollResponse,
  CheckPointsResponse,
  HistoryResponse,
} from '../types';

export const classificationService = {
  async uploadAndClassify(file: File): Promise<UploadAccepted> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<UploadAccepted>('/classifications/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async pollStatus(uploadId: string): Promise<ClassificationPollResponse> {
    const response = await api.get<ClassificationPollResponse>(
      `/classifications/${uploadId}/`
    );
    return response.data;
  },

  async checkPoints(uploadId: string): Promise<CheckPointsResponse> {
    const response = await api.get<CheckPointsResponse>(
      `/classifications/${uploadId}/points/`
    );
    return response.data;
  },

  async listHistory(params?: {
    page?: number;
    kategori?: string;
  }): Promise<HistoryResponse> {
    const response = await api.get<HistoryResponse>('/classifications/', { params });
    return response.data;
  },
};
