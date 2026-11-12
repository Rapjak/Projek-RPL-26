import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import { authService } from '../services/auth';
import type { User, RegisterRequest } from '../types';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (identifier: string, password: string) => Promise<User>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  error: string | null;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshUser = useCallback(async () => {
    try {
      const profile = await authService.getProfile();
      // Normalize profile fields into the User shape used by frontend
      const u: User = {
        user_id: profile.id,
        npm_nip: profile.npm_nip,
        name: profile.name,
        email: profile.email,
        peran: profile.role,
        unit_gedung: profile.unit_gedung,
        total_poin: profile.total_poin,
      };
      setUser(u);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    const initAuth = async () => {
      if (authService.isAuthenticated()) {
        await refreshUser();
      }
      setLoading(false);
    };
    initAuth();
  }, [refreshUser]);

  const login = async (identifier: string, password: string) => {
    try {
      setError(null);
      const resp = await authService.login({ identifier, password });
      setUser(resp.user);
      return resp.user;
    } catch (err: any) {
      const msg =
        err.response?.data?.error?.message ||
        err.response?.data?.detail ||
        'Login gagal. Periksa NPM/Email dan kata sandi Anda.';
      setError(msg);
      throw err;
    }
  };

  const register = async (data: RegisterRequest) => {
    try {
      setError(null);
      await authService.register(data);
    } catch (err: any) {
      // Pull first validation error message
      const data = err.response?.data;
      let msg = 'Registrasi gagal.';
      if (data) {
        if (data.error?.message) msg = data.error.message;
        else if (Array.isArray(data.email)) msg = data.email[0];
        else if (Array.isArray(data.npm_nip)) msg = data.npm_nip[0];
        else if (Array.isArray(data.password)) msg = data.password[0];
        else if (typeof data.detail === 'string') msg = data.detail;
      }
      setError(msg);
      throw err;
    }
  };

  const logout = async () => {
    await authService.logout();
    setUser(null);
  };

  const clearError = () => setError(null);

  const isAdmin = user?.peran === 'admin_gogreen' || user?.peran === 'pimpinan';

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        isAdmin,
        login,
        register,
        logout,
        refreshUser,
        error,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
