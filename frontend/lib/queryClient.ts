import { QueryClient } from '@tanstack/react-query';

/**
 * Default query client configuration
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Stale time: 5 minutes
      staleTime: 5 * 60 * 1000,
      // Cache time: 10 minutes
      gcTime: 10 * 60 * 1000,
      // Retry failed requests 3 times
      retry: 3,
      // Retry delay with exponential backoff
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      // Refetch on window focus
      refetchOnWindowFocus: true,
      // Refetch on reconnect
      refetchOnReconnect: true,
      // Don't refetch on mount if data is fresh
      refetchOnMount: false,
    },
    mutations: {
      // Retry failed mutations once
      retry: 1,
      // Retry delay
      retryDelay: 1000,
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
} as const;
