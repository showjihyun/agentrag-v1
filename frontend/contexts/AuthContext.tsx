'use client';

/**
 * Authentication Context for managing user authentication state.
 * Provides login, register, logout, and user refresh functionality.
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { UserResponse } from '@/lib/types';
import { apiClient } from '@/lib/api-client';
import { setTokens, clearTokens, getAccessToken, isTokenExpired } from '@/lib/auth';
import { useToast } from '@/hooks/use-toast';

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
  const { toast } = useToast();

  const isAuthenticated = user !== null;

  /**
   * Load user from token on mount.
   */
  useEffect(() => {
    const loadUser = async () => {
      const token = getAccessToken();
      const isDevelopment = process.env.NODE_ENV === 'development';
      
      // Development mode: Create fake user and token if none exists
      if (isDevelopment && !token) {
        console.log('🔧 Development mode: Creating fake user and token using backend test account');
        
        // Create fake token (not a real JWT, just for development)
        const fakeToken = 'dev-fake-token-' + Date.now();
        const fakeRefreshToken = 'dev-fake-refresh-token-' + Date.now();
        
        // Store fake tokens
        setTokens(fakeToken, fakeRefreshToken);
        
        // Create fake user matching backend test account
        const fakeUser: UserResponse = {
          id: 'dev-user-id',
          email: 'test@example.com',  // 백엔드 테스트 계정과 동일
          username: 'testuser',       // 백엔드 테스트 계정과 동일
          full_name: 'Test User (Dev Mode)',
          role: 'admin',              // 백엔드 테스트 계정과 동일
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          storage_used_bytes: 0,
          storage_limit_bytes: 1073741824, // 1GB
        };
        
        setUser(fakeUser);
        setIsLoading(false);
        
        toast({
          title: '개발 모드 자동 로그인',
          description: 'test@example.com 테스트 계정으로 자동 로그인되었습니다.',
        });
        
        return;
      }
      
      if (!token) {
        setIsLoading(false);
        return;
      }

      // Check if token is expired (skip for fake tokens)
      if (!token.startsWith('dev-fake-token-') && isTokenExpired(token)) {
        clearTokens();
        setIsLoading(false);
        return;
      }

      try {
        // Skip API call for fake tokens in development
        if (isDevelopment && token.startsWith('dev-fake-token-')) {
          console.log('🔧 Development mode: Using fake user matching backend test account');
          const fakeUser: UserResponse = {
            id: 'dev-user-id',
            email: 'test@example.com',  // 백엔드 테스트 계정과 동일
            username: 'testuser',       // 백엔드 테스트 계정과 동일
            full_name: 'Test User (Dev Mode)',
            role: 'admin',              // 백엔드 테스트 계정과 동일
            is_active: true,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            storage_used_bytes: 0,
            storage_limit_bytes: 1073741824, // 1GB
          };
          setUser(fakeUser);
        } else {
          // Fetch user info from API for real tokens
          const userData = await apiClient.me();
          setUser(userData);
        }
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
