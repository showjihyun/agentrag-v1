/**
 * Optimistic UI update hooks for better UX
 */

import { useQueryClient, useMutation } from '@tanstack/react-query';
import { useCallback } from 'react';

/**
 * Generic optimistic update hook
 */
export function useOptimisticUpdate<TData, TVariables>(
  queryKey: any[],
  mutationFn: (variables: TVariables) => Promise<TData>,
  options?: {
    onSuccess?: (data: TData, variables: TVariables) => void;
    onError?: (error: Error, variables: TVariables, context: any) => void;
    updateFn?: (oldData: any, variables: TVariables) => any;
  }
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn,
    onMutate: async (variables) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey });

      // Snapshot previous value
      const previousData = queryClient.getQueryData(queryKey);

      // Optimistically update
      if (options?.updateFn) {
        queryClient.setQueryData(queryKey, (old: any) =>
          options.updateFn!(old, variables)
        );
      }

      return { previousData };
    },
    onError: (error, variables, context: any) => {
      // Rollback on error
      if (context?.previousData) {
        queryClient.setQueryData(queryKey, context.previousData);
      }
      options?.onError?.(error as Error, variables, context);
    },
    onSuccess: (data, variables) => {
      options?.onSuccess?.(data, variables);
    },
    onSettled: () => {
      // Refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey });
    },
  });
}

/**
 * Optimistic create
 */
export function useOptimisticCreate<TItem, TCreate>(
  queryKey: any[],
  createFn: (data: TCreate) => Promise<TItem>,
  options?: {
    generateTempId?: () => string;
    onSuccess?: (data: TItem) => void;
    onError?: (error: Error) => void;
  }
) {
  const generateTempId = options?.generateTempId || (() => `temp-${Date.now()}`);

  return useOptimisticUpdate<TItem, TCreate>(queryKey, createFn, {
    updateFn: (oldData: any, variables) => {
      if (Array.isArray(oldData)) {
        // Add temporary item to list
        return [
          ...oldData,
          {
            ...variables,
            id: generateTempId(),
            _optimistic: true,
          },
        ];
      }
      return oldData;
    },
    onSuccess: options?.onSuccess,
    onError: options?.onError,
  });
}

/**
 * Optimistic update
 */
export function useOptimisticEdit<TItem, TUpdate>(
  queryKey: any[],
  updateFn: (id: string, data: TUpdate) => Promise<TItem>,
  options?: {
    onSuccess?: (data: TItem) => void;
    onError?: (error: Error) => void;
  }
) {
  return useOptimisticUpdate<TItem, { id: string; data: TUpdate }>(
    queryKey,
    ({ id, data }) => updateFn(id, data),
    {
      updateFn: (oldData: any, variables) => {
        if (Array.isArray(oldData)) {
          // Update item in list
          return oldData.map((item: any) =>
            item.id === variables.id
              ? { ...item, ...variables.data, _optimistic: true }
              : item
          );
        } else if (oldData?.id === variables.id) {
          // Update single item
          return { ...oldData, ...variables.data, _optimistic: true };
        }
        return oldData;
      },
      onSuccess: options?.onSuccess,
      onError: options?.onError,
    }
  );
}

/**
 * Optimistic delete
 */
export function useOptimisticDelete<TItem = void>(
  queryKey: any[],
  deleteFn: (id: string) => Promise<TItem>,
  options?: {
    onSuccess?: (data: TItem) => void;
    onError?: (error: Error) => void;
  }
) {
  return useOptimisticUpdate<TItem, string>(queryKey, deleteFn, {
    updateFn: (oldData: any, id) => {
      if (Array.isArray(oldData)) {
        // Remove item from list
        return oldData.filter((item: any) => item.id !== id);
      }
      return oldData;
    },
    onSuccess: options?.onSuccess,
    onError: options?.onError,
  });
}

/**
 * Optimistic toggle (e.g., favorite, like)
 */
export function useOptimisticToggle<TItem>(
  queryKey: any[],
  toggleFn: (id: string, value: boolean) => Promise<TItem>,
  field: string,
  options?: {
    onSuccess?: (data: TItem) => void;
    onError?: (error: Error) => void;
  }
) {
  return useOptimisticUpdate<TItem, { id: string; value: boolean }>(
    queryKey,
    ({ id, value }) => toggleFn(id, value),
    {
      updateFn: (oldData: any, variables) => {
        if (Array.isArray(oldData)) {
          return oldData.map((item: any) =>
            item.id === variables.id
              ? { ...item, [field]: variables.value, _optimistic: true }
              : item
          );
        } else if (oldData?.id === variables.id) {
          return { ...oldData, [field]: variables.value, _optimistic: true };
        }
        return oldData;
      },
      onSuccess: options?.onSuccess,
      onError: options?.onError,
    }
  );
}

/**
 * Hook for agent builder optimistic updates
 */
export function useAgentBuilderOptimistic() {
  const queryClient = useQueryClient();

  const createAgent = useOptimisticCreate(
    ['agent-builder-agents'],
    async (data: any) => {
      const { agentBuilderAPI } = await import('@/lib/api/agent-builder');
      return agentBuilderAPI.createAgent(data);
    }
  );

  const updateAgent = useOptimisticEdit(
    ['agent-builder-agents'],
    async (id: string, data: any) => {
      const { agentBuilderAPI } = await import('@/lib/api/agent-builder');
      return agentBuilderAPI.updateAgent(id, data);
    }
  );

  const deleteAgent = useOptimisticDelete(
    ['agent-builder-agents'],
    async (id: string) => {
      const { agentBuilderAPI } = await import('@/lib/api/agent-builder');
      return agentBuilderAPI.deleteAgent(id);
    }
  );

  const toggleFavorite = useOptimisticToggle(
    ['agent-builder-agents'],
    async (id: string, value: boolean) => {
      // Implement favorite toggle API
      return { id, isFavorite: value } as any;
    },
    'isFavorite'
  );

  return {
    createAgent,
    updateAgent,
    deleteAgent,
    toggleFavorite,
  };
}
