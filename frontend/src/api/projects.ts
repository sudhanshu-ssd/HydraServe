import { apiClient } from './client';
import type { Project, ProjectCreate, ProjectUpdate, ApiKey, ApiKeyCreateResponse, ApiKeyCreateRequest } from '../types';

export const projectsApi = {
  list: async (): Promise<Project[]> => {
    const response = await apiClient.get<Project[]>('/projects');
    return response.data;
  },

  create: async (data: ProjectCreate): Promise<Project> => {
    const response = await apiClient.post<Project>('/projects', data);
    return response.data;
  },

  update: async (id: number, data: ProjectUpdate): Promise<Project> => {
    const response = await apiClient.patch<Project>(`/projects/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/projects/${id}`);
  },

  listKeys: async (projectId: number): Promise<ApiKey[]> => {
    const response = await apiClient.get<ApiKey[]>(`/projects/${projectId}/keys`);
    return response.data;
  },

  createKey: async (projectId: number, data: ApiKeyCreateRequest): Promise<ApiKeyCreateResponse> => {
    const response = await apiClient.post<ApiKeyCreateResponse>(`/projects/${projectId}/keys`, data);
    return response.data;
  },

  deleteKey: async (projectId: number, keyId: number): Promise<void> => {
    await apiClient.delete(`/projects/${projectId}/keys/${keyId}`);
  },
};
