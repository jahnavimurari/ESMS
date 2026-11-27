import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi, setAuthHeader } from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [accessToken, setAccessToken] = useState(() => localStorage.getItem('esms_access_token'));
  const [refreshToken, setRefreshToken] = useState(() => localStorage.getItem('esms_refresh_token'));
  const [isLoading, setIsLoading] = useState(true);

  // Sync token header
  useEffect(() => {
    if (accessToken) {
      setAuthHeader(accessToken);
    } else {
      setAuthHeader(null);
    }
  }, [accessToken]);

  // Load user profile on startup if token exists
  useEffect(() => {
    const initAuth = async () => {
      const storedAccess = localStorage.getItem('esms_access_token');
      const storedRefresh = localStorage.getItem('esms_refresh_token');

      if (!storedAccess) {
        setIsLoading(false);
        return;
      }

      setAuthHeader(storedAccess);
      try {
        const response = await authApi.getCurrentUser();
        if (response.success && response.data) {
          setUser(response.data);
        }
      } catch (err) {
        // If access token expired, attempt refresh
        if (storedRefresh) {
          try {
            const refreshRes = await authApi.refresh(storedRefresh);
            if (refreshRes.success && refreshRes.data?.access_token) {
              const newAccess = refreshRes.data.access_token;
              localStorage.setItem('esms_access_token', newAccess);
              setAccessToken(newAccess);
              setAuthHeader(newAccess);
              const meRes = await authApi.getCurrentUser();
              if (meRes.success && meRes.data) {
                setUser(meRes.data);
              }
            }
          } catch (refreshErr) {
            // Both expired, clear session
            localStorage.removeItem('esms_access_token');
            localStorage.removeItem('esms_refresh_token');
            setAccessToken(null);
            setRefreshToken(null);
            setUser(null);
          }
        } else {
          localStorage.removeItem('esms_access_token');
          setAccessToken(null);
          setUser(null);
        }
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = useCallback(async (email, password) => {
    const result = await authApi.login({ email, password });
    if (result.success && result.data) {
      const { access_token, refresh_token, user: userData } = result.data;
      localStorage.setItem('esms_access_token', access_token);
      localStorage.setItem('esms_refresh_token', refresh_token);
      setAccessToken(access_token);
      setRefreshToken(refresh_token);
      setUser(userData);
      setAuthHeader(access_token);
      return userData;
    }
    throw new Error(result.error?.message || 'Login failed');
  }, []);

  const logout = useCallback(async () => {
    try {
      if (accessToken) {
        await authApi.logout(accessToken);
      }
    } catch (err) {
      console.warn('Logout API call failed or token already revoked:', err);
    } finally {
      localStorage.removeItem('esms_access_token');
      localStorage.removeItem('esms_refresh_token');
      setAccessToken(null);
      setRefreshToken(null);
      setUser(null);
      setAuthHeader(null);
    }
  }, [accessToken]);

  const value = {
    user,
    role: user?.role || null,
    isAuthenticated: Boolean(user && accessToken),
    isLoading,
    login,
    logout,
    accessToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

