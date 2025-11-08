/**
 * Web Worker Hook
 * 
 * Offload heavy computations to Web Workers
 */

import { useEffect, useRef, useState, useCallback } from 'react';

interface UseWebWorkerOptions<T, R> {
  workerFunction: (data: T) => R;
  onSuccess?: (result: R) => void;
  onError?: (error: Error) => void;
}

export const useWebWorker = <T, R>({
  workerFunction,
  onSuccess,
  onError,
}: UseWebWorkerOptions<T, R>) => {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<R | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const workerRef = useRef<Worker | null>(null);

  useEffect(() => {
    // Create worker from function
    const workerCode = `
      self.onmessage = function(e) {
        try {
          const fn = ${workerFunction.toString()};
          const result = fn(e.data);
          self.postMessage({ type: 'success', result });
        } catch (error) {
          self.postMessage({ 
            type: 'error', 
            error: error.message || 'Worker error' 
          });
        }
      };
    `;

    const blob = new Blob([workerCode], { type: 'application/javascript' });
    const workerUrl = URL.createObjectURL(blob);
    workerRef.current = new Worker(workerUrl);

    // Cleanup
    return () => {
      if (workerRef.current) {
        workerRef.current.terminate();
        URL.revokeObjectURL(workerUrl);
      }
    };
  }, [workerFunction]);

  const execute = useCallback((data: T) => {
    if (!workerRef.current) {
      const error = new Error('Worker not initialized');
      setError(error);
      onError?.(error);
      return;
    }

    setIsLoading(true);
    setError(null);

    workerRef.current.onmessage = (e) => {
      setIsLoading(false);
      
      if (e.data.type === 'success') {
        setResult(e.data.result);
        onSuccess?.(e.data.result);
      } else if (e.data.type === 'error') {
        const error = new Error(e.data.error);
        setError(error);
        onError?.(error);
      }
    };

    workerRef.current.onerror = (e) => {
      setIsLoading(false);
      const error = new Error(e.message || 'Worker error');
      setError(error);
      onError?.(error);
    };

    workerRef.current.postMessage(data);
  }, [onSuccess, onError]);

  const terminate = useCallback(() => {
    if (workerRef.current) {
      workerRef.current.terminate();
      workerRef.current = null;
    }
  }, []);

  return {
    execute,
    terminate,
    isLoading,
    result,
    error,
  };
};

/**
 * Predefined worker for text processing
 */
export const useTextProcessingWorker = () => {
  return useWebWorker({
    workerFunction: (text: string) => {
      // Heavy text processing
      const words = text.split(/\s+/);
      const wordCount = words.length;
      const charCount = text.length;
      const uniqueWords = new Set(words.map(w => w.toLowerCase()));
      
      return {
        wordCount,
        charCount,
        uniqueWordCount: uniqueWords.size,
        averageWordLength: charCount / wordCount,
      };
    },
  });
};

/**
 * Predefined worker for data sorting
 */
export const useSortingWorker = <T,>() => {
  return useWebWorker<{ data: T[]; key: keyof T }, T[]>({
    workerFunction: ({ data, key }) => {
      return [...data].sort((a, b) => {
        if (a[key] < b[key]) return -1;
        if (a[key] > b[key]) return 1;
        return 0;
      });
    },
  });
};
