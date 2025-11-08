/**
 * React Query Configuration
 * 
 * Centralized configuration for TanStack Query
 */

import { QueryClient, DefaultOptions } from '@tanstack/react-query';

// Default options for all queries
const queryConfig: DefaultOptions = {
  queries: {
    // Stale time: 5 minutes
    staleTime: 5 * 60 * 1000,
    
    // Cache time: 10 minutes
    gcTime: 10 * 60 * 1000,
    
    // Retry failed requests
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    
    // Refetch on window focus
    refetchOnWindowFocus: false,
    
    // Refetch on reconnect
    refetchOnReconnect: true,
    
    // Refetch on mount
    refetchOnMount: true,
  },
  mutations: {
    // Retry mutations once
    retry: 1,
  },
};

// Create query client
export const queryClient = new QueryClient({
  defaultOptions: queryConfig,
});

// Query keys factory
export const queryKeys = {
  // Chat
  chat: {
    all: ['chat'] as const,
    sessions: () => [...queryKeys.chat.all, 'sessions'] as const,
    session: (id: string) => [...queryKeys.chat.all, 'session', id] as const,
    messages: (sessionId: string) => [...queryKeys.chat.all, 'messages', sessionId] as const,
  },
  
  // Documents
  documents: {
    all: ['documents'] as const,
    list: (filters?: Record<string, unknown>) => [...queryKeys.documents.all, 'list', filters] as const,
    detail: (id: string) => [...queryKeys.documents.all, 'detail', id] as const,
    search: (query: string) => [...queryKeys.documents.all, 'search', query] as const,
  },
  
  // User
  user: {
    all: ['user'] as const,
    profile: () => [...queryKeys.user.all, 'profile'] as const,
    settings: () => [...queryKeys.user.all, 'settings'] as const,
    usage: () => [...queryKeys.user.all, 'usage'] as const,
  },
} as const;
