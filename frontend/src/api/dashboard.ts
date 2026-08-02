import { apiClient } from './client';
import type { DashboardOverview, RequestHistoryItem, ModelUsage, TokenTrend, RequestTrend } from '../types';

export const dashboardApi = {
  getOverview: async (): Promise<DashboardOverview> => {
    const response = await apiClient.get<DashboardOverview>('/dashboard/overview');
    return response.data;
  },

  getRequestHistory: async (): Promise<RequestHistoryItem[]> => {
    const response = await apiClient.get<RequestHistoryItem[]>('/dashboard/request-history');
    return response.data;
  },

  getModelUsage: async (): Promise<ModelUsage[]> => {
    const response = await apiClient.get<ModelUsage[]>('/dashboard/model-usage');
    return response.data;
  },

  getTokenTrend: async (): Promise<TokenTrend[]> => {
    const response = await apiClient.get<TokenTrend[]>('/dashboard/token-trend');
    return response.data;
  },

  getRequestTrend: async (): Promise<RequestTrend[]> => {
    const response = await apiClient.get<RequestTrend[]>('/dashboard/request-trend');
    return response.data;
  },
};
