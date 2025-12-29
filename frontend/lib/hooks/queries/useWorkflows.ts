// React Query hooks for Workflows/Flows

import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { flowsAPI } from '@/lib/api/flows';
import { queryKeys } from '@/lib/queryKeys';
import {
  Agentflow,
  Chatflow,
  CreateAgentflowRequest,
  CreateChatflowRequest,
  UpdateFlowRequest,
  FlowFilters,
  FlowListResponse,
  FlowExecution,
} from '@/lib/types/flows';

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Get all flows (both Agentflow and Chatflow)
 */
export function useFlows(
  filters?: FlowFilters,
  options?: Omit<UseQueryOptions<FlowListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.workflows.list(filters || {}),
    queryFn: () => flowsAPI.getFlows(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (replaces cacheTime)
    ...options,
  });
}

/**
 * Get Agentflows only
 */
export function useAgentflows(
  filters?: FlowFilters,
  options?: Omit<UseQueryOptions<FlowListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.agentflows.list(filters || {}),
    queryFn: () => flowsAPI.getAgentflows(filters),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000, // 10 minutes (replaces cacheTime)
    ...options,
  });
}

/**
 * Get Chatflows only
 */
export function useChatflows(
  filters?: FlowFilters,
  options?: Omit<UseQueryOptions<FlowListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.chatflows.list(filters || {}),
    queryFn: () => flowsAPI.getChatflows(filters),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000, // 10 minutes (replaces cacheTime)
    ...options,
  });
}

/**
 * Get a specific flow by ID
 */
export function useFlow(
  id: string,
  options?: Omit<UseQueryOptions<Agentflow | Chatflow>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.workflows.detail(id),
    queryFn: () => flowsAPI.getFlow(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
    ...options,
  });
}

/**
 * Get execution history for a flow
 */
export function useFlowExecutions(
  flowId: string,
  limit: number = 20,
  offset: number = 0,
  options?: Omit<UseQueryOptions<{ executions: FlowExecution[]; total: number }>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.executions.list(flowId),
    queryFn: () => flowsAPI.getExecutions(flowId, limit, offset),
    enabled: !!flowId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    ...options,
  });
}

/**
 * Get a specific execution
 */
export function useExecution(
  executionId: string,
  options?: Omit<UseQueryOptions<FlowExecution>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.executions.detail(executionId),
    queryFn: () => flowsAPI.getExecution(executionId),
    enabled: !!executionId,
    staleTime: 1 * 60 * 1000, // 1 minute
    refetchInterval: (query) => {
      // Auto-refetch if execution is running
      const data = query?.state?.data as FlowExecution | undefined;
      if (data?.status === 'running' || data?.status === 'pending') {
        return 2000; // 2 seconds
      }
      return false;
    },
    ...options,
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Create a new Agentflow
 */
export function useCreateAgentflow() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: CreateAgentflowRequest) => flowsAPI.createAgentflow(data),
    onSuccess: () => {
      // Invalidate all flow lists
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.agentflows.lists() });
    },
  });
}

/**
 * Create a new Chatflow
 */
export function useCreateChatflow() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: CreateChatflowRequest) => flowsAPI.createChatflow(data),
    onSuccess: () => {
      // Invalidate all flow lists
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.chatflows.lists() });
    },
  });
}

/**
 * Update a flow
 */
export function useUpdateFlow() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateFlowRequest }) =>
      flowsAPI.updateFlow(id, data),
    onSuccess: (_, variables) => {
      // Invalidate specific flow and all lists
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.agentflows.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.chatflows.lists() });
    },
  });
}

/**
 * Delete a flow
 */
export function useDeleteFlow() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => flowsAPI.deleteFlow(id),
    onSuccess: (_, id) => {
      // Remove from cache and invalidate lists
      queryClient.removeQueries({ queryKey: queryKeys.workflows.detail(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.agentflows.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.chatflows.lists() });
    },
  });
}

/**
 * Execute a flow
 */
export function useExecuteFlow() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, inputData }: { id: string; inputData: Record<string, any> }) =>
      flowsAPI.executeFlow(id, inputData),
    onSuccess: (_, variables) => {
      // Invalidate execution list for this flow
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.executions.list(variables.id) 
      });
    },
  });
}

/**
 * Cancel a running execution
 */
export function useCancelExecution() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (executionId: string) => flowsAPI.cancelExecution(executionId),
    onSuccess: (_, executionId) => {
      // Invalidate specific execution
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.executions.detail(executionId) 
      });
    },
  });
}

// ============================================================================
// Optimistic Update Hooks
// ============================================================================

/**
 * Update flow with optimistic update
 */
export function useOptimisticUpdateFlow() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateFlowRequest }) =>
      flowsAPI.updateFlow(id, data),
    
    // Optimistic update
    onMutate: async ({ id, data }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.workflows.detail(id) });
      
      // Snapshot previous value
      const previousFlow = queryClient.getQueryData(queryKeys.workflows.detail(id));
      
      // Optimistically update
      queryClient.setQueryData(queryKeys.workflows.detail(id), (old: any) => ({
        ...old,
        ...data,
      }));
      
      return { previousFlow };
    },
    
    // Rollback on error
    onError: (err, variables, context) => {
      if (context?.previousFlow) {
        queryClient.setQueryData(
          queryKeys.workflows.detail(variables.id),
          context.previousFlow
        );
      }
    },
    
    // Refetch on success or error
    onSettled: (_, __, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.detail(variables.id) });
    },
  });
}

// ============================================================================
// Prefetch Hooks
// ============================================================================

/**
 * Prefetch flow details (for hover/navigation)
 */
export function usePrefetchFlow() {
  const queryClient = useQueryClient();
  
  return (id: string) => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.workflows.detail(id),
      queryFn: () => flowsAPI.getFlow(id),
      staleTime: 5 * 60 * 1000,
    });
  };
}
