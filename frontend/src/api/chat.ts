import axios from 'axios';
import type { ChatRequest, ChatResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const chatApi = {
  send: async (apiKey: string, data: ChatRequest): Promise<ChatResponse> => {
    const response = await axios.post<ChatResponse>(`${API_BASE_URL}/chat`, data, {
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`,
      },
    });
    return response.data;
  },
};
