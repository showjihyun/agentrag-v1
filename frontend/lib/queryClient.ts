import { QueryClient, QueryCache, MutationCache } from '@tanstack/react-query';

/**
 * Cache time constants (in milliseconds)
 */
export const CACHE_TIMES = {
  // Short-lived data (1 minute)
  SHORT: 1 * 60 * 1000,
  // Medium-lived data (5 minutes)
  MEDIUM: 5 * 60 * 1000,
  // Long-lived data (30 minutes)
  LONG: 30 * 60 * 1000,
  // Static data (1 hour)
  STATIC: 60 * 60 * 1000,
  // Infinite (until manual invalidation)
  INFINITE: Infinity,
} as const;

/**
 * Stale time constants
 */
export const STALE_TIMES = {
  // Immediately stale (always refetch)
  IMMEDIATE: 0,
  // Short stale time (30 seconds)
  SHORT: 30 * 1000,
  // Medium stale time (2 minutes)
  MEDIUM: 2 * 60 * 1000,
  // Long stale time (10 minutes)
  LONG: 10 * 60 * 1000,
} as const;

/**
 * Query client with optimized caching strategy
 */
export const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error, query) => {
      // Log errors for debugging (only in development)
      if (process.env.NODE_ENV === 'development') {
        console.error(`Query error [${query.queryKey}]:`, error);
      }
    },
  }),
  mutationCache: new MutationCache({
    onError: (error, _variables, _context, mutation) => {
      if (process.env.NODE_ENV === 'development') {
        console.error(`Mutation error [${mutation.options.mutationKey}]:`, error);
      }
    },
  }),
  defaultOptions: {
    queries: {
      // Default stale time: 2 minutes
      staleTime: STALE_TIMES.MEDIUM,
      // Default cache time: 10 minutes
      gcTime: CACHE_TIMES.MEDIUM * 2,
      // Retry failed requests 3 times
      retry: 3,
      // Retry delay with exponential backoff
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      // Refetch on window focus (only if stale)
      refetchOnWindowFocus: 'always',
      // Refetch on reconnect
      refetchOnReconnect: true,
      // Don't refetch on mount if data is fresh
      refetchOnMount: true,
      // Network mode
      networkMode: 'offlineFirst',
      // Structural sharing for better performance
      structuralSharing: true,
    },
    mutations: {
      // Retry failed mutations once
      retry: 1,
      // Retry delay
      retryDelay: 1000,
      // Network mode
      networkMode: 'offlineFirst',
    },
  },
});

/**
 * Query keys factory for consistent key management
 */
export const queryKeys = {
  // Workflows
  workflows: {
    all: ['workflows'] as const,
    lists: () => [...queryKeys.workflows.all, 'list'] as const,
    list: (filters: string) => [...queryKeys.workflows.lists(), { filters }] as const,
    details: () => [...queryKeys.workflows.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.workflows.details(), id] as const,
    executions: (id: string) => [...queryKeys.workflows.detail(id), 'executions'] as const,
    status: (id: string) => [...queryKeys.workflows.detail(id), 'status'] as const,
  },

  // Agents
  agents: {
    all: ['agents'] as const,
    lists: () => [...queryKeys.agents.all, 'list'] as const,
    list: (filters: string) => [...queryKeys.agents.lists(), { filters }] as const,
    details: () => [...queryKeys.agents.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.agents.details(), id] as const,
    tools: (id: string) => [...queryKeys.agents.detail(id), 'tools'] as const,
  },

  // Tools
  tools: {
    all: ['tools'] as const,
    lists: () => [...queryKeys.tools.all, 'list'] as const,
    list: (filters: string) => [...queryKeys.tools.lists(), { filters }] as const,
    details: () => [...queryKeys.tools.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.tools.details(), id] as const,
  },

  // AI Assistant
  aiAssistant: {
    all: ['ai-assistant'] as const,
    breakpoints: (workflowId: string) => 
      [...queryKeys.aiAssistant.all, 'breakpoints', workflowId] as const,
    optimizations: (workflowId: string) => 
      [...queryKeys.aiAssistant.all, 'optimizations', workflowId] as const,
    diagnosis: (workflowId: string) => 
      [...queryKeys.aiAssistant.all, 'diagnosis', workflowId] as const,
  },

  // Monitoring
  monitoring: {
    all: ['monitoring'] as const,
    health: () => [...queryKeys.monitoring.all, 'health'] as const,
    metrics: (workflowId: string) => 
      [...queryKeys.monitoring.all, 'metrics', workflowId] as const,
    alerts: () => [...queryKeys.monitoring.all, 'alerts'] as const,
  },

  // Documents
  documents: {
    all: ['documents'] as const,
    lists: () => [...queryKeys.documents.all, 'list'] as const,
    list: (filters?: { status?: string }) => [...queryKeys.documents.lists(), filters] as const,
    details: () => [...queryKeys.documents.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.documents.details(), id] as const,
  },

  // Conversations
  conversations: {
    all: ['conversations'] as const,
    lists: () => [...queryKeys.conversations.all, 'list'] as const,
    list: (filters?: { limit?: number }) => [...queryKeys.conversations.lists(), filters] as const,
    details: () => [...queryKeys.conversations.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.conversations.details(), id] as const,
    messages: (id: string) => [...queryKeys.conversations.detail(id), 'messages'] as const,
  },

  // User
  user: {
    all: ['user'] as const,
    current: () => [...queryKeys.user.all, 'current'] as const,
    settings: () => [...queryKeys.user.all, 'settings'] as const,
  },
} as const;

/**
 * Query options presets for common use cases
 */
export const queryOptions = {
  // For data that rarely changes (e.g., user settings, static configs)
  static: {
    staleTime: STALE_TIMES.LONG,
    gcTime: CACHE_TIMES.STATIC,
    refetchOnWindowFocus: false,
  },
  // For data that changes frequently (e.g., execution status)
  realtime: {
    staleTime: STALE_TIMES.IMMEDIATE,
    gcTime: CACHE_TIMES.SHORT,
    refetchInterval: 5000,
  },
  // For list data with pagination
  list: {
    staleTime: STALE_TIMES.SHORT,
    gcTime: CACHE_TIMES.MEDIUM,
    keepPreviousData: true,
  },
  // For detail views
  detail: {
    staleTime: STALE_TIMES.MEDIUM,
    gcTime: CACHE_TIMES.LONG,
  },
} as const;

/**
 * Prefetch helper for route transitions
 */
export async function prefetchQuery<T>(
  queryKey: readonly unknown[],
  queryFn: () => Promise<T>,
  options?: { staleTime?: number }
) {
  return queryClient.prefetchQuery({
    queryKey,
    queryFn,
    staleTime: options?.staleTime ?? STALE_TIMES.MEDIUM,
  });
}

/**
 * Invalidate queries by key prefix
 */
export function invalidateQueries(keyPrefix: readonly unknown[]) {
  return queryClient.invalidateQueries({ queryKey: keyPrefix });
}
