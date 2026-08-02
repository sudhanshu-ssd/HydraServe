import { apiClient } from './client';

export interface ModelOption {
  model_id: number;
  model_name: string;
  provider: string;
}

export const modelsApi = {
  list: async (): Promise<ModelOption[]> => {
    const response = await apiClient.get<ModelOption[]>('/models');
    return response.data;
  },
};
