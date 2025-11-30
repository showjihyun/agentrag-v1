/**
 * Optimistic UI update hooks for better UX
 */

import { useQueryClient, useMutation, QueryKey } from '@tanstack/react-query';

/**
 * Generic optimistic update hook
 */
export function useOptimisticUpdate<TData, TVariables, TContext = unknown>(
  queryKey: QueryKey,
  mutationFn: (variables: TVariables) => Promise<TData>,
  options?: {
    onSuccess?: (data: TData, variables: TVariables) => void;
    onError?: (error: Error, variables: TVariables, context: TContext | undefined) => void;
    updateFn?: (oldData: TData | undefined, variables: TVariables) => TData;
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
        queryClient.setQueryData<TData>(queryKey, (old) =>
          options.updateFn!(old, variables)
        );
      }

      return { previousData };
    },
    onError: (error, variables, context) => {
      // Rollback on error
      const ctx = context as { previousData?: TData } | undefined;
      if (ctx?.previousData) {
        queryClient.setQueryData(queryKey, ctx.previousData);
      }
      options?.onError?.(error as Error, variables, context as TContext | undefined);
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
export function useOptimisticCreate<TItem extends { id?: string }, TCreate>(
  queryKey: QueryKey,
  createFn: (data: TCreate) => Promise<TItem>,
  options?: {
    generateTempId?: () => string;
    onSuccess?: (data: TItem) => void;
    onError?: (error: Error) => void;
  }
) {
  const generateTempId = options?.generateTempId || (() => `temp-${Date.now()}`);

  return useOptimisticUpdate<TItem, TCreate>(queryKey, createFn, {
    updateFn: (oldData, variables) => {
      if (Array.isArray(oldData)) {
        // Add temporary item to list
        return [
          ...oldData,
          {
            ...variables,
            id: generateTempId(),
            _optimistic: true,
          },
        ] as unknown as TItem;
      }
      return oldData as TItem;
    },
    onSuccess: options?.onSuccess,
    onError: options?.onError,
  });
}

/**
 * Optimistic update
 */
export function useOptimisticEdit<TItem extends { id?: string }, TUpdate>(
  queryKey: QueryKey,
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
      updateFn: (oldData, variables) => {
        if (Array.isArray(oldData)) {
          // Update item in list
          return oldData.map((item) =>
            (item as { id?: string }).id === variables.id
              ? { ...item, ...variables.data, _optimistic: true }
              : item
          ) as unknown as TItem;
        } else if ((oldData as { id?: string })?.id === variables.id) {
          // Update single item
          return { ...oldData, ...variables.data, _optimistic: true } as TItem;
        }
        return oldData as TItem;
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
  queryKey: QueryKey,
  deleteFn: (id: string) => Promise<TItem>,
  options?: {
    onSuccess?: (data: TItem) => void;
    onError?: (error: Error) => void;
  }
) {
  return useOptimisticUpdate<TItem, string>(queryKey, deleteFn, {
    updateFn: (oldData, id) => {
      if (Array.isArray(oldData)) {
        // Remove item from list
        return oldData.filter((item) => (item as { id?: string }).id !== id) as unknown as TItem;
      }
      return oldData as TItem;
    },
    onSuccess: options?.onSuccess,
    onError: options?.onError,
  });
}

/**
 * Optimistic toggle (e.g., favorite, like)
 */
export function useOptimisticToggle<TItem extends { id?: string }>(
  queryKey: QueryKey,
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
      updateFn: (oldData, variables) => {
        if (Array.isArray(oldData)) {
          return oldData.map((item) =>
            (item as { id?: string }).id === variables.id
              ? { ...item, [field]: variables.value, _optimistic: true }
              : item
          ) as unknown as TItem;
        } else if ((oldData as { id?: string })?.id === variables.id) {
          return { ...oldData, [field]: variables.value, _optimistic: true } as TItem;
        }
        return oldData as TItem;
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
