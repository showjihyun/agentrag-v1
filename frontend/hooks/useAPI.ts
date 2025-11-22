import { useState, useCallback } from 'react';
import { toast } from 'sonner';

export interface UseAPIOptions extends RequestInit {
  showErrorToast?: boolean;
  errorMessage?: string;
}

export interface UseAPIResult<T> {
  data: T | null;
  error: Error | null;
  isLoading: boolean;
  execute: () => Promise<T>;
  reset: () => void;
}

/**
 * Reusable hook for API calls with loading, error handling, and toast notifications
 */
export function useAPI<T>(
  url: string,
  options: UseAPIOptions = {}
): UseAPIResult<T> {
  const { showErrorToast = true, errorMessage, ...fetchOptions } = options;
  
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const execute = useCallback(async (): Promise<T> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(url, fetchOptions);

      if (!response.ok) {
        throw new Error(
          `HTTP ${response.status}: ${response.statusText}`
        );
      }

      const result = await response.json();
      setData(result);
      return result;
    } catch (err) {
      const apiError = err instanceof Error ? err : new Error('Unknown error');
      setError(apiError);
      
      if (showErrorToast) {
        toast.error(errorMessage || apiError.message);
      }
      
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  }, [url, fetchOptions, showErrorToast, errorMessage]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setIsLoading(false);
  }, []);

  return { data, error, isLoading, execute, reset };
}
