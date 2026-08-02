import axios from 'axios';
import type { HealthResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const healthApi = {
  check: async (): Promise<HealthResponse> => {
    const response = await axios.get<HealthResponse>(`${API_BASE_URL}/health`);
    return response.data;
  },
};
