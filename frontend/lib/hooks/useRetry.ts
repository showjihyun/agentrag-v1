import { useState, useCallback } from 'react';

interface RetryOptions {
  maxAttempts?: number;
  delay?: number;
  backoff?: boolean;
  onRetry?: (attempt: number) => void;
}

/**
 * Retry Hook
 * 
 * Provides retry logic with exponential backoff
 */
export function useRetry<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
) {
  const {
    maxAttempts = 3,
    delay = 1000,
    backoff = true,
    onRetry,
  } = options;

  const [isRetrying, setIsRetrying] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [error, setError] = useState<Error | null>(null);

  const execute = useCallback(async (): Promise<T> => {
    setError(null);
    let lastError: Error | null = null;

    for (let i = 0; i < maxAttempts; i++) {
      try {
        setAttempt(i + 1);
        
        if (i > 0) {
          setIsRetrying(true);
          onRetry?.(i);
          
          // Calculate delay with exponential backoff
          const waitTime = backoff ? delay * Math.pow(2, i - 1) : delay;
          await new Promise(resolve => setTimeout(resolve, waitTime));
        }

        const result = await fn();
        setIsRetrying(false);
        setAttempt(0);
        return result;
      } catch (err) {
        lastError = err instanceof Error ? err : new Error(String(err));
        console.warn(`Attempt ${i + 1}/${maxAttempts} failed:`, lastError.message);
        
        // If this was the last attempt, throw the error
        if (i === maxAttempts - 1) {
          setError(lastError);
          setIsRetrying(false);
          throw lastError;
        }
      }
    }

    // This should never be reached, but TypeScript needs it
    throw lastError || new Error('All retry attempts failed');
  }, [fn, maxAttempts, delay, backoff, onRetry]);

  const reset = useCallback(() => {
    setIsRetrying(false);
    setAttempt(0);
    setError(null);
  }, []);

  return {
    execute,
    reset,
    isRetrying,
    attempt,
    error,
  };
}
