/**
 * Route and data prefetching utilities
 */

import { queryKeys, STALE_TIMES } from '../queryKeys';
import { queryClient } from '../queryClient';

/**
 * Prefetch strategies
 */
export type PrefetchStrategy = 'hover' | 'visible' | 'idle' | 'immediate';

/**
 * Prefetch route data on hover
 */
export function prefetchOnHover(
  prefetchFn: () => Promise<void>
): { onMouseEnter: () => void } {
  let prefetched = false;

  return {
    onMouseEnter: () => {
      if (!prefetched) {
        prefetched = true;
        prefetchFn().catch(console.error);
      }
    },
  };
}

/**
 * Prefetch when element becomes visible
 */
export function prefetchOnVisible(
  element: HTMLElement | null,
  prefetchFn: () => Promise<void>
): () => void {
  if (!element || typeof IntersectionObserver === 'undefined') {
    return () => {};
  }

  let prefetched = false;
  
  const observer = new IntersectionObserver(
    (entries) => {
      const entry = entries[0];
      if (entry && entry.isIntersecting && !prefetched) {
        prefetched = true;
        prefetchFn().catch(console.error);
        observer.disconnect();
      }
    },
    { threshold: 0.1 }
  );

  observer.observe(element);
  
  return () => observer.disconnect();
}

/**
 * Prefetch during browser idle time
 */
export function prefetchOnIdle(prefetchFn: () => Promise<void>): void {
  if ('requestIdleCallback' in window) {
    (window as any).requestIdleCallback(() => {
      prefetchFn().catch(console.error);
    });
  } else {
    // Fallback for Safari
    setTimeout(() => {
      prefetchFn().catch(console.error);
    }, 200);
  }
}

/**
 * Common route prefetch functions
 */
export const routePrefetchers = {
  // Prefetch workflow detail
  workflowDetail: async (id: string, fetchFn: (id: string) => Promise<any>) => {
    await queryClient.prefetchQuery({
      queryKey: queryKeys.workflows.detail(id),
      queryFn: () => fetchFn(id),
      staleTime: STALE_TIMES.MEDIUM,
    });
  },

  // Prefetch agent detail
  agentDetail: async (id: string, fetchFn: (id: string) => Promise<any>) => {
    await queryClient.prefetchQuery({
      queryKey: queryKeys.agents.detail(id),
      queryFn: () => fetchFn(id),
      staleTime: STALE_TIMES.MEDIUM,
    });
  },

  // Prefetch document list
  documentList: async (fetchFn: () => Promise<any>) => {
    await queryClient.prefetchQuery({
      queryKey: queryKeys.documents.lists(),
      queryFn: fetchFn,
      staleTime: STALE_TIMES.SHORT,
    });
  },

  // Prefetch conversation messages
  conversationMessages: async (id: string, fetchFn: (id: string) => Promise<any>) => {
    await queryClient.prefetchQuery({
      queryKey: queryKeys.conversations.messages(id),
      queryFn: () => fetchFn(id),
      staleTime: STALE_TIMES.SHORT,
    });
  },
};

/**
 * Preload critical resources
 */
export function preloadCriticalResources() {
  // Preload fonts
  const fonts = [
    '/fonts/inter-var.woff2',
  ];

  fonts.forEach(font => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'font';
    link.type = 'font/woff2';
    link.href = font;
    link.crossOrigin = 'anonymous';
    document.head.appendChild(link);
  });
}

/**
 * Preconnect to external origins
 */
export function preconnectOrigins(origins: string[]) {
  origins.forEach(origin => {
    const link = document.createElement('link');
    link.rel = 'preconnect';
    link.href = origin;
    document.head.appendChild(link);
  });
}

/**
 * DNS prefetch for external resources
 */
export function dnsPrefetch(domains: string[]) {
  domains.forEach(domain => {
    const link = document.createElement('link');
    link.rel = 'dns-prefetch';
    link.href = domain;
    document.head.appendChild(link);
  });
}
