/**
 * Code splitting utilities for lazy loading components
 */

import dynamic from 'next/dynamic';
import { Skeleton } from '@/components/ui/skeleton';
import { Loader2 } from 'lucide-react';

/**
 * Loading fallback components
 */
export const LoadingFallbacks = {
  // Small component loading
  small: () => <Skeleton className="h-[100px] w-full" />,
  
  // Medium component loading
  medium: () => <Skeleton className="h-[300px] w-full" />,
  
  // Large component loading (full page)
  large: () => (
    <div className="flex items-center justify-center h-screen">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
    </div>
  ),
  
  // Form loading
  form: () => (
    <div className="space-y-4">
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-32 w-full" />
      <Skeleton className="h-10 w-32" />
    </div>
  ),
  
  // Chart loading
  chart: () => <Skeleton className="h-[400px] w-full" />,
  
  // Editor loading
  editor: () => <Skeleton className="h-[500px] w-full" />,
};

/**
 * Create a dynamically imported component with loading state
 */
export function createDynamicComponent<T = any>(
  importFn: () => Promise<{ default: React.ComponentType<T> }>,
  options?: {
    loading?: () => React.ReactNode;
    ssr?: boolean;
  }
) {
  return dynamic(importFn, {
    loading: options?.loading || LoadingFallbacks.medium,
    ssr: options?.ssr ?? false,
  });
}

/**
 * Preload a dynamic component
 */
export function preloadComponent(
  importFn: () => Promise<any>
): void {
  // Trigger the import but don't wait for it
  importFn().catch(err => {
    console.error('Failed to preload component:', err);
  });
}

/**
 * Lazy load component on interaction
 */
export function useLazyLoad<T = any>(
  importFn: () => Promise<{ default: React.ComponentType<T> }>
) {
  const [Component, setComponent] = React.useState<React.ComponentType<T> | null>(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);

  const load = React.useCallback(async () => {
    if (Component) return; // Already loaded
    
    setIsLoading(true);
    setError(null);
    
    try {
      const module = await importFn();
      setComponent(() => module.default);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to load component'));
    } finally {
      setIsLoading(false);
    }
  }, [Component, importFn]);

  return { Component, isLoading, error, load };
}

/**
 * Prefetch component on hover
 */
export function usePrefetchOnHover(
  importFn: () => Promise<any>
) {
  const prefetchedRef = React.useRef(false);

  const handleMouseEnter = React.useCallback(() => {
    if (!prefetchedRef.current) {
      prefetchedRef.current = true;
      preloadComponent(importFn);
    }
  }, [importFn]);

  return { onMouseEnter: handleMouseEnter };
}

/**
 * Common dynamic imports for Agent Builder
 */
export const DynamicComponents = {
  // Heavy editors
  MonacoEditor: createDynamicComponent(
    () => import('@monaco-editor/react'),
    { loading: LoadingFallbacks.editor }
  ),
  
  // Workflow canvas (React Flow)
  WorkflowCanvas: createDynamicComponent(
    () => import('@/components/agent-builder/workflow-nodes/WorkflowCanvas'),
    { loading: LoadingFallbacks.large }
  ),
  
  // Charts
  ExecutionChart: createDynamicComponent(
    () => import('@/components/agent-builder/ExecutionMetrics'),
    { loading: LoadingFallbacks.chart }
  ),
  
  // Complex forms
  BlockEditor: createDynamicComponent(
    () => import('@/components/agent-builder/BlockEditor'),
    { loading: LoadingFallbacks.form }
  ),
  
  // Test panels
  AgentTestPanel: createDynamicComponent(
    () => import('@/components/agent-builder/AgentTestPanel'),
    { loading: LoadingFallbacks.medium }
  ),
  
  BlockTestPanel: createDynamicComponent(
    () => import('@/components/agent-builder/BlockTestPanel'),
    { loading: LoadingFallbacks.medium }
  ),
};

/**
 * Route-based code splitting helper
 */
export function createRouteComponent(
  importFn: () => Promise<{ default: React.ComponentType<any> }>
) {
  return dynamic(importFn, {
    loading: LoadingFallbacks.large,
    ssr: true, // Enable SSR for routes
  });
}
