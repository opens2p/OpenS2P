import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { apiPost, apiGet, setToken, clearToken, getToken, isTokenExpired } from '../api/client';
import type { User, LoginResponse, MeResponse } from '../api/types';

interface AuthState {
  user: User | null;
  roles: string[];
  tenantId: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [roles, setRoles] = useState<string[]>([]);
  const [tenantId, setTenantId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // On mount, try to restore session from stored token
  useEffect(() => {
    const token = getToken();
    if (!token || isTokenExpired(token)) {
      clearToken();
      setLoading(false);
      return;
    }
    apiGet<MeResponse>('/api/v1/auth/me')
      .then((data) => {
        setUser(data.user);
        setRoles(data.roles);
        setTenantId(data.tenant_id);
      })
      .catch(() => {
        clearToken();
      })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const data = await apiPost<LoginResponse>(
      `/api/v1/auth/login?username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`,
    );
    setToken(data.access_token);
    setUser(data.user);
    // Fetch full profile with roles
    const me = await apiGet<MeResponse>('/api/v1/auth/me');
    setRoles(me.roles);
    setTenantId(me.tenant_id);
    setUser(me.user);
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    setRoles([]);
    setTenantId(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        roles,
        tenantId,
        loading,
        login,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
