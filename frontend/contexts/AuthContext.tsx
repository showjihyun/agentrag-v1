'use client';

/**
 * Authentication Context for managing user authentication state.
 * Provides login, register, logout, and user refresh functionality.
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { UserResponse } from '@/lib/types';
import { apiClient } from '@/lib/api-client';
import { setTokens, clearTokens, getAccessToken, isTokenExpired } from '@/lib/auth';

interface AuthContextType {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = user !== null;

  /**
   * Load user from token on mount.
   */
  useEffect(() => {
    const loadUser = async () => {
      const token = getAccessToken();
      
      if (!token) {
        setIsLoading(false);
        return;
      }

      // Check if token is expired
      if (isTokenExpired(token)) {
        clearTokens();
        setIsLoading(false);
        return;
      }

      try {
        // Fetch user info from API
        const userData = await apiClient.me();
        setUser(userData);
      } catch (error) {
        console.error('Failed to load user:', error);
        clearTokens();
      } finally {
        setIsLoading(false);
      }
    };

    loadUser();
  }, []);

  /**
   * Login with email and password.
   */
  const login = async (email: string, password: string): Promise<void> => {
    try {
      const response = await apiClient.login(email, password);
      
      // Store tokens
      setTokens(response.access_token, response.refresh_token);
      
      // Set user
      setUser(response.user);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  /**
   * Register a new user.
   */
  const register = async (
    email: string,
    username: string,
    password: string,
    fullName?: string
  ): Promise<void> => {
    try {
      const response = await apiClient.register({
        email,
        username,
        password,
        full_name: fullName,
      });
      
      // Store tokens
      setTokens(response.access_token, response.refresh_token);
      
      // Set user
      setUser(response.user);
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  };

  /**
   * Logout and clear tokens.
   */
  const logout = (): void => {
    clearTokens();
    setUser(null);
  };

  /**
   * Refresh user data from API.
   */
  const refreshUser = async (): Promise<void> => {
    try {
      const userData = await apiClient.me();
      setUser(userData);
    } catch (error) {
      console.error('Failed to refresh user:', error);
      // If refresh fails, logout
      logout();
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to access auth context.
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
}
