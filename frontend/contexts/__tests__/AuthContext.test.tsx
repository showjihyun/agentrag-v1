/**
 * Tests for AuthContext
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../AuthContext';
import { apiClient } from '@/lib/api-client';
import * as authUtils from '@/lib/auth';

// Mock the API client
jest.mock('@/lib/api-client', () => ({
  apiClient: {
    login: jest.fn(),
    register: jest.fn(),
    me: jest.fn(),
  },
}));

// Mock auth utilities
jest.mock('@/lib/auth', () => ({
  setTokens: jest.fn(),
  clearTokens: jest.fn(),
  getAccessToken: jest.fn(),
  isTokenExpired: jest.fn(),
}));

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (authUtils.getAccessToken as jest.Mock).mockReturnValue(null);
    (authUtils.isTokenExpired as jest.Mock).mockReturnValue(false);
  });

  it('should initialize with no user and not loading after mount', async () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('should load user from token on mount', async () => {
    const mockUser = {
      id: '123',
      email: 'test@example.com',
      username: 'testuser',
      role: 'user',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      query_count: 0,
      storage_used_bytes: 0,
    };

    (authUtils.getAccessToken as jest.Mock).mockReturnValue('mock-token');
    (apiClient.me as jest.Mock).mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('should handle login successfully', async () => {
    const mockResponse = {
      access_token: 'access-token',
      refresh_token: 'refresh-token',
      token_type: 'bearer',
      expires_in: 86400,
      user: {
        id: '123',
        email: 'test@example.com',
        username: 'testuser',
        role: 'user',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        query_count: 0,
        storage_used_bytes: 0,
      },
    };

    (apiClient.login as jest.Mock).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.login('test@example.com', 'password123');
    });

    expect(authUtils.setTokens).toHaveBeenCalledWith('access-token', 'refresh-token');
    expect(result.current.user).toEqual(mockResponse.user);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('should handle register successfully', async () => {
    const mockResponse = {
      access_token: 'access-token',
      refresh_token: 'refresh-token',
      token_type: 'bearer',
      expires_in: 86400,
      user: {
        id: '123',
        email: 'new@example.com',
        username: 'newuser',
        role: 'user',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        query_count: 0,
        storage_used_bytes: 0,
      },
    };

    (apiClient.register as jest.Mock).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.register('new@example.com', 'newuser', 'password123', 'New User');
    });

    expect(apiClient.register).toHaveBeenCalledWith({
      email: 'new@example.com',
      username: 'newuser',
      password: 'password123',
      full_name: 'New User',
    });
    expect(authUtils.setTokens).toHaveBeenCalledWith('access-token', 'refresh-token');
    expect(result.current.user).toEqual(mockResponse.user);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('should handle logout', async () => {
    const mockUser = {
      id: '123',
      email: 'test@example.com',
      username: 'testuser',
      role: 'user',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      query_count: 0,
      storage_used_bytes: 0,
    };

    (authUtils.getAccessToken as jest.Mock).mockReturnValue('mock-token');
    (apiClient.me as jest.Mock).mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser);
    });

    act(() => {
      result.current.logout();
    });

    expect(authUtils.clearTokens).toHaveBeenCalled();
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('should refresh user data', async () => {
    const initialUser = {
      id: '123',
      email: 'test@example.com',
      username: 'testuser',
      role: 'user',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      query_count: 0,
      storage_used_bytes: 0,
    };

    const updatedUser = {
      ...initialUser,
      query_count: 10,
      storage_used_bytes: 1024,
    };

    (authUtils.getAccessToken as jest.Mock).mockReturnValue('mock-token');
    (apiClient.me as jest.Mock)
      .mockResolvedValueOnce(initialUser)
      .mockResolvedValueOnce(updatedUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await waitFor(() => {
      expect(result.current.user).toEqual(initialUser);
    });

    await act(async () => {
      await result.current.refreshUser();
    });

    expect(result.current.user).toEqual(updatedUser);
  });

  it('should clear tokens if token is expired on mount', async () => {
    (authUtils.getAccessToken as jest.Mock).mockReturnValue('expired-token');
    (authUtils.isTokenExpired as jest.Mock).mockReturnValue(true);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(authUtils.clearTokens).toHaveBeenCalled();
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('should logout if refreshUser fails', async () => {
    const mockUser = {
      id: '123',
      email: 'test@example.com',
      username: 'testuser',
      role: 'user',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      query_count: 0,
      storage_used_bytes: 0,
    };

    (authUtils.getAccessToken as jest.Mock).mockReturnValue('mock-token');
    (apiClient.me as jest.Mock)
      .mockResolvedValueOnce(mockUser)
      .mockRejectedValueOnce(new Error('Unauthorized'));

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser);
    });

    await act(async () => {
      try {
        await result.current.refreshUser();
      } catch (error) {
        // Expected to throw
      }
    });

    expect(authUtils.clearTokens).toHaveBeenCalled();
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });
});
