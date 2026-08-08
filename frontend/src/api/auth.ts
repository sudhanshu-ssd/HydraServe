import { apiClient } from './client';
import type { LoginRequest, TokenResponse, RegisterRequest, RegisterResponse, ForgotPasswordRequest, ResetPasswordRequest } from '../types';

export const authApi = {
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const formData = new URLSearchParams();
    formData.append('username', data.username);
    formData.append('password', data.password);
    const response = await apiClient.post<TokenResponse>('/token', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<RegisterResponse> => {
    const response = await apiClient.post<RegisterResponse>('/users/register', data);
    return response.data;
  },

  forgotPassword: async (data: ForgotPasswordRequest): Promise<{message: string}> => {
    const response = await apiClient.post<{message: string}>('/users/forgot-password', data);
    return response.data;
  },

  resetPassword: async (data: ResetPasswordRequest): Promise<{message: string}> => {
    const response = await apiClient.post<{message: string}>('/users/reset-password', data);
    return response.data;
  },

  getMe: async (): Promise<{username: string, profile_pic: string | null}> => {
    const response = await apiClient.get<{username: string, profile_pic: string | null}>('/users/me');
    return response.data;
  },
};
