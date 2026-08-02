import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { authApi } from '../api/auth';
import type { LoginRequest, RegisterRequest } from '../types';

interface AuthContextType {
  isAuthenticated: boolean;
  username: string | null;
  profilePic: string | null;
  isLoading: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState<string | null>(null);
  const [profilePic, setProfilePic] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const data = await authApi.getMe();
      setUsername(data.username);
      setProfilePic(data.profile_pic);
      setIsAuthenticated(true);
    } catch {
      localStorage.removeItem('access_token');
      setIsAuthenticated(false);
      setUsername(null);
      setProfilePic(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = async (data: LoginRequest) => {
    const response = await authApi.login(data);
    localStorage.setItem('access_token', response.access_token);
    const userData = await authApi.getMe();
    setUsername(userData.username);
    setProfilePic(userData.profile_pic);
    setIsAuthenticated(true);
  };

  const register = async (data: RegisterRequest) => {
    await authApi.register(data);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setIsAuthenticated(false);
    setUsername(null);
    setProfilePic(null);
  };

  const refreshProfile = async () => {
    try {
      const data = await authApi.getMe();
      setUsername(data.username);
      setProfilePic(data.profile_pic);
    } catch (e) {
      console.error("Failed to refresh profile", e);
    }
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, username, profilePic, isLoading, login, register, logout, refreshProfile }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
