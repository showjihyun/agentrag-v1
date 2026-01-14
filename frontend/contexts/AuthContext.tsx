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
  const [mounted, setMounted] = useState(false);
  const { toast } = useToast();

  const isAuthenticated = user !== null;

  // Handle mounting to prevent hydration issues
  useEffect(() => {
    setMounted(true);
  }, []);

  /**
   * Load user from token on mount.
   */
  useEffect(() => {
    if (!mounted) return;

    const loadUser = async () => {
      const token = getAccessToken();
      const isDevelopment = process.env.NODE_ENV === 'development';
      
      // Development mode: Create fake user and token if none exists
      if (isDevelopment && !token) {
        console.log('🔧 Development mode: Creating fake user and token using backend test account');
        
        // Create fake token (not a real JWT, just for development)
        const fakeToken = 'dev-fake-token-12345';
        const fakeRefreshToken = 'dev-fake-refresh-token-12345';
        
        // Store fake tokens
        setTokens(fakeToken, fakeRefreshToken);
        
        // Create fake user matching backend test account
        const fakeUser: UserResponse = {
          id: 'dev-user-id',
          email: 'test@example.com',  // Same as backend test account
          username: 'testuser',       // Same as backend test account
          full_name: 'Test User (Dev Mode)',
          role: 'admin',              // Same as backend test account
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          query_count: 0,             // Added field
          storage_used_bytes: 0,
        };
        
        setUser(fakeUser);
        setIsLoading(false);
        
        toast({
          title: 'Development Mode Auto Login',
          description: 'Automatically logged in with test@example.com test account.',
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
            email: 'test@example.com',  // Same as backend test account
            username: 'testuser',       // Same as backend test account
            full_name: 'Test User (Dev Mode)',
            role: 'admin',              // Same as backend test account
            is_active: true,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
            query_count: 0,             // Added field
            storage_used_bytes: 0,
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
  }, [mounted, toast]);

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
        full_name: fullName || '',
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
