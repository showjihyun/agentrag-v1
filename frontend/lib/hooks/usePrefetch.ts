/**
 * Prefetch Hook
 * 
 * Predictive data prefetching for better UX
 */

import { useEffect, useCallback, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';

interface UsePrefetchOptions {
  enabled?: boolean;
  delay?: number;
  priority?: 'high' | 'low';
}

export const usePrefetch = (
  queryKey: any[],
  queryFn: () => Promise<any>,
  options: UsePrefetchOptions = {}
) => {
  const queryClient = useQueryClient();
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const { enabled = true, delay = 0, priority = 'low' } = options;

  const prefetch = useCallback(() => {
    if (!enabled) return;

    if (delay > 0) {
      timeoutRef.current = setTimeout(() => {
        queryClient.prefetchQuery({
          queryKey,
          queryFn,
        });
      }, delay);
    } else {
      queryClient.prefetchQuery({
        queryKey,
        queryFn,
      });
    }
  }, [queryClient, queryKey, queryFn, enabled, delay]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return { prefetch };
};

/**
 * Prefetch on hover
 */
export const usePrefetchOnHover = (
  queryKey: any[],
  queryFn: () => Promise<any>,
  options: UsePrefetchOptions = {}
) => {
  const { prefetch } = usePrefetch(queryKey, queryFn, options);

  const onMouseEnter = useCallback(() => {
    prefetch();
  }, [prefetch]);

  return { onMouseEnter };
};

/**
 * Prefetch on intersection (when element becomes visible)
 */
export const usePrefetchOnIntersection = (
  queryKey: any[],
  queryFn: () => Promise<any>,
  options: UsePrefetchOptions & { threshold?: number } = {}
) => {
  const { prefetch } = usePrefetch(queryKey, queryFn, options);
  const elementRef = useRef<HTMLElement>(null);
  const { threshold = 0.1 } = options;

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            prefetch();
          }
        });
      },
      { threshold }
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [prefetch, threshold]);

  return { elementRef };
};

/**
 * Prefetch related data based on user behavior
 */
export const useSmartPrefetch = () => {
  const queryClient = useQueryClient();

  const prefetchRelated = useCallback(
    (currentId: string, relatedIds: string[], queryFn: (id: string) => Promise<any>) => {
      relatedIds.forEach((id) => {
        if (id !== currentId) {
          queryClient.prefetchQuery({
            queryKey: ['item', id],
            queryFn: () => queryFn(id),
          });
        }
      });
    },
    [queryClient]
  );

  return { prefetchRelated };
};
