/**
 * Optimistic Updates Hook
 * 
 * Provides optimistic UI updates for better UX
 */

import { useState, useCallback, useRef } from 'react';

interface UseOptimisticOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: Error, rollback: () => void) => void;
  timeout?: number;
}

interface OptimisticUpdate<T> {
  id: string;
  data: T;
  timestamp: number;
}

export const useOptimistic = <T,>(
  initialData: T,
  options: UseOptimisticOptions<T> = {}
) => {
  const [data, setData] = useState<T>(initialData);
  const [isOptimistic, setIsOptimistic] = useState(false);
  const previousDataRef = useRef<T>(initialData);
  const pendingUpdatesRef = useRef<Map<string, OptimisticUpdate<T>>>(new Map());
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Apply optimistic update
  const applyOptimistic = useCallback((updateId: string, newData: T) => {
    // Store previous data for rollback
    previousDataRef.current = data;
    
    // Store pending update
    pendingUpdatesRef.current.set(updateId, {
      id: updateId,
      data: newData,
      timestamp: Date.now(),
    });

    // Apply update
    setData(newData);
    setIsOptimistic(true);

    // Set timeout for automatic rollback
    if (options.timeout) {
      timeoutRef.current = setTimeout(() => {
        rollback(updateId);
      }, options.timeout);
    }
  }, [data, options.timeout]);

  // Confirm optimistic update
  const confirm = useCallback((updateId: string, confirmedData?: T) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    pendingUpdatesRef.current.delete(updateId);
    
    if (confirmedData) {
      setData(confirmedData);
    }

    if (pendingUpdatesRef.current.size === 0) {
      setIsOptimistic(false);
    }

    options.onSuccess?.(confirmedData || data);
  }, [data, options]);

  // Rollback optimistic update
  const rollback = useCallback((updateId?: string) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    if (updateId) {
      pendingUpdatesRef.current.delete(updateId);
    } else {
      pendingUpdatesRef.current.clear();
    }

    setData(previousDataRef.current);
    setIsOptimistic(false);

    const error = new Error('Optimistic update failed');
    options.onError?.(error, () => rollback(updateId));
  }, [options]);

  // Clear all pending updates
  const clear = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    pendingUpdatesRef.current.clear();
    setIsOptimistic(false);
  }, []);

  return {
    data,
    isOptimistic,
    applyOptimistic,
    confirm,
    rollback,
    clear,
  };
};

/**
 * Optimistic list operations
 */
export const useOptimisticList = <T extends { id: string }>(
  initialList: T[],
  options: UseOptimisticOptions<T[]> = {}
) => {
  const {
    data: list,
    isOptimistic,
    applyOptimistic,
    confirm,
    rollback,
  } = useOptimistic<T[]>(initialList, options);

  // Add item optimistically
  const addOptimistic = useCallback((item: T) => {
    const updateId = `add-${item.id}`;
    const newList = [...list, item];
    applyOptimistic(updateId, newList);
    return updateId;
  }, [list, applyOptimistic]);

  // Update item optimistically
  const updateOptimistic = useCallback((itemId: string, updates: Partial<T>) => {
    const updateId = `update-${itemId}`;
    const newList = list.map(item =>
      item.id === itemId ? { ...item, ...updates } : item
    );
    applyOptimistic(updateId, newList);
    return updateId;
  }, [list, applyOptimistic]);

  // Remove item optimistically
  const removeOptimistic = useCallback((itemId: string) => {
    const updateId = `remove-${itemId}`;
    const newList = list.filter(item => item.id !== itemId);
    applyOptimistic(updateId, newList);
    return updateId;
  }, [list, applyOptimistic]);

  return {
    list,
    isOptimistic,
    addOptimistic,
    updateOptimistic,
    removeOptimistic,
    confirm,
    rollback,
  };
};
