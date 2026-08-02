import { apiClient } from './client';

export const userApi = {
  uploadProfilePic: async (file: File): Promise<void> => {
    const formData = new FormData();
    formData.append('file', file);
    await apiClient.patch('/users/profile_pic', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  deleteProfilePic: async (): Promise<void> => {
    await apiClient.delete('/users/profile_pic');
  }
};
