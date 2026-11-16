import { createContext, useContext, useState, useEffect, useCallback, type ReactNode, type FC } from 'react';
import type { User, LoginCredentials, RegisterData } from '@/types';
import {
  apiLogin,
  apiRegister,
  apiLogout,
  apiGetMe,
  apiRefreshToken,
  getStoredToken,
  clearStoredToken,
} from '@/services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<User>;
  register: (payload: RegisterData) => Promise<User>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(getStoredToken());
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const initAuth = useCallback(async () => {
    setIsLoading(true);
    const existingToken = getStoredToken();

    if (existingToken) {
      try {
        const currentUser = await apiGetMe();
        setUser(currentUser);
        setToken(existingToken);
        setIsLoading(false);
        return;
      } catch {
        // Token might be expired, try refreshing
      }
    }

    // Try refreshing via HttpOnly cookie
    try {
      const refreshed = await apiRefreshToken();
      setUser(refreshed.user);
      setToken(refreshed.access_token);
    } catch {
      setUser(null);
      setToken(null);
      clearStoredToken();
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    initAuth();

    const handleUnauthorized = () => {
      setUser(null);
      setToken(null);
      clearStoredToken();
    };

    window.addEventListener('vf_auth_unauthorized', handleUnauthorized);
    return () => {
      window.removeEventListener('vf_auth_unauthorized', handleUnauthorized);
    };
  }, [initAuth]);

  const login = async (credentials: LoginCredentials): Promise<User> => {
    setIsLoading(true);
    try {
      const resp = await apiLogin(credentials);
      setUser(resp.user);
      setToken(resp.access_token);
      return resp.user;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: RegisterData): Promise<User> => {
    setIsLoading(true);
    try {
      const newUser = await apiRegister(payload);
      // Automatically login after successful registration
      const loginResp = await apiLogin({
        email: payload.email,
        password: payload.password,
      });
      setUser(loginResp.user);
      setToken(loginResp.access_token);
      return newUser;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await apiLogout();
    } catch {
      // ignore
    } finally {
      setUser(null);
      setToken(null);
      clearStoredToken();
    }
  };

  const refreshUser = async (): Promise<void> => {
    try {
      const currentUser = await apiGetMe();
      setUser(currentUser);
    } catch {
      setUser(null);
      setToken(null);
      clearStoredToken();
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
