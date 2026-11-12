import api from './api';
import type {
  Reward,
  RedeemResponse,
  Redemption,
  PointTransactionsResponse,
  LeaderboardResponse,
} from '../types';

interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export const rewardService = {
  async list(params?: { page?: number }): Promise<Paginated<Reward>> {
    const response = await api.get<Paginated<Reward>>('/rewards', { params });
    return response.data;
  },

  async redeem(rewardId: string): Promise<RedeemResponse> {
    const response = await api.post<RedeemResponse>(`/rewards/${rewardId}/redeem`);
    return response.data;
  },

  async listRedemptions(params?: { page?: number }): Promise<Paginated<Redemption>> {
    const response = await api.get<Paginated<Redemption>>('/rewards/redemptions', { params });
    return response.data;
  },

  async getTransactions(params?: { page?: number }): Promise<PointTransactionsResponse> {
    const response = await api.get<PointTransactionsResponse>('/points/transactions', { params });
    return response.data;
  },

  async getLeaderboard(params: { type: 'user' | 'building'; page?: number; limit?: number }): Promise<LeaderboardResponse> {
    const response = await api.get<LeaderboardResponse>('/leaderboard', { params });
    return response.data;
  },
};
