/**
 * Custom hook for handling async operations with loading, error, and data states
 * 
 * @param asyncFunction - Async function to execute
 * @param immediate - Whether to execute immediately (default: true)
 * @returns Object with execute function and state
 * 
 * @example
 * const { execute, status, data, error } = useAsync(fetchData);
 */

import { useState, useEffect, useCallback } from 'react';

type AsyncStatus = 'idle' | 'pending' | 'success' | 'error';

interface UseAsyncReturn<T> {
  execute: () => Promise<void>;
  status: AsyncStatus;
  data: T | null;
  error: Error | null;
  isLoading: boolean;
  isError: boolean;
  isSuccess: boolean;
}

export function useAsync<T>(
  asyncFunction: () => Promise<T>,
  immediate = true
): UseAsyncReturn<T> {
  const [status, setStatus] = useState<AsyncStatus>('idle');
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const execute = useCallback(async () => {
    setStatus('pending');
    setData(null);
    setError(null);

    try {
      const response = await asyncFunction();
      setData(response);
      setStatus('success');
    } catch (err) {
      const error = err instanceof Error ? err : new Error('An unknown error occurred');
      setError(error);
      setStatus('error');
    }
  }, [asyncFunction]);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [execute, immediate]);

  return {
    execute,
    status,
    data,
    error,
    isLoading: status === 'pending',
    isError: status === 'error',
    isSuccess: status === 'success',
  };
}
