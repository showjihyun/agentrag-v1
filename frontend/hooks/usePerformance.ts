/**
 * Performance monitoring hooks
 */

import { useEffect, useRef, useCallback } from 'react';

/**
 * Measure component render time
 */
export function useRenderTime(componentName: string, enabled = process.env.NODE_ENV === 'development') {
  const renderCountRef = useRef(0);
  const startTimeRef = useRef(0);

  useEffect(() => {
    if (!enabled) return;

    renderCountRef.current++;
    const renderTime = performance.now() - startTimeRef.current;

    if (renderCountRef.current > 1) {
      console.log(
        `[Performance] ${componentName} render #${renderCountRef.current}: ${renderTime.toFixed(2)}ms`
      );
    }
  });

  startTimeRef.current = performance.now();
}

/**
 * Track component mount/unmount
 */
export function useComponentLifecycle(componentName: string, enabled = process.env.NODE_ENV === 'development') {
  useEffect(() => {
    if (!enabled) return;

    const mountTime = performance.now();
    console.log(`[Lifecycle] ${componentName} mounted at ${mountTime.toFixed(2)}ms`);

    return () => {
      const unmountTime = performance.now();
      const lifetime = unmountTime - mountTime;
      console.log(
        `[Lifecycle] ${componentName} unmounted after ${lifetime.toFixed(2)}ms`
      );
    };
  }, [componentName, enabled]);
}

/**
 * Measure function execution time
 */
export function useMeasure() {
  const measure = useCallback(<T extends (...args: any[]) => any>(
    fn: T,
    label: string
  ): T => {
    return ((...args: Parameters<T>) => {
      const start = performance.now();
      const result = fn(...args);
      const end = performance.now();
      
      console.log(`[Measure] ${label}: ${(end - start).toFixed(2)}ms`);
      
      return result;
    }) as T;
  }, []);

  const measureAsync = useCallback(<T extends (...args: any[]) => Promise<any>>(
    fn: T,
    label: string
  ): T => {
    return (async (...args: Parameters<T>) => {
      const start = performance.now();
      const result = await fn(...args);
      const end = performance.now();
      
      console.log(`[Measure] ${label}: ${(end - start).toFixed(2)}ms`);
      
      return result;
    }) as T;
  }, []);

  return { measure, measureAsync };
}

/**
 * Track Web Vitals
 */
export function useWebVitals(onReport?: (metric: any) => void) {
  useEffect(() => {
    if (typeof window === 'undefined') return;

    // Import web-vitals dynamically
    import('web-vitals').then(({ onCLS, onFID, onFCP, onLCP, onTTFB }) => {
      const reportHandler = (metric: any) => {
        console.log(`[Web Vitals] ${metric.name}:`, metric.value);
        onReport?.(metric);

        // Send to analytics in production
        if (process.env.NODE_ENV === 'production') {
          // TODO: Send to analytics service
          // analytics.track('web-vital', metric);
        }
      };

      onCLS(reportHandler);
      onFID(reportHandler);
      onFCP(reportHandler);
      onLCP(reportHandler);
      onTTFB(reportHandler);
    });
  }, [onReport]);
}

/**
 * Monitor memory usage
 */
export function useMemoryMonitor(interval = 5000) {
  useEffect(() => {
    if (typeof window === 'undefined' || !('memory' in performance)) return;

    const checkMemory = () => {
      const memory = (performance as any).memory;
      const used = (memory.usedJSHeapSize / 1048576).toFixed(2);
      const total = (memory.totalJSHeapSize / 1048576).toFixed(2);
      const limit = (memory.jsHeapSizeLimit / 1048576).toFixed(2);

      console.log(
        `[Memory] Used: ${used}MB / Total: ${total}MB / Limit: ${limit}MB`
      );

      // Warn if memory usage is high
      if (memory.usedJSHeapSize / memory.jsHeapSizeLimit > 0.9) {
        console.warn('[Memory] High memory usage detected!');
      }
    };

    const intervalId = setInterval(checkMemory, interval);
    return () => clearInterval(intervalId);
  }, [interval]);
}

/**
 * Track long tasks (> 50ms)
 */
export function useLongTaskMonitor() {
  useEffect(() => {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) return;

    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          console.warn(
            `[Long Task] Duration: ${entry.duration.toFixed(2)}ms`,
            entry
          );
        }
      });

      observer.observe({ entryTypes: ['longtask'] });

      return () => observer.disconnect();
    } catch (e) {
      // PerformanceObserver not supported
    }
  }, []);
}

/**
 * Detect render blocking resources
 */
export function useRenderBlockingResources() {
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const checkResources = () => {
      const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[];
      
      const blocking = resources.filter(
        (resource) =>
          resource.renderBlockingStatus === 'blocking' ||
          (resource.initiatorType === 'script' && !resource.name.includes('async')) ||
          (resource.initiatorType === 'link' && resource.name.includes('.css'))
      );

      if (blocking.length > 0) {
        console.warn('[Render Blocking] Found blocking resources:', blocking);
      }
    };

    // Check after page load
    if (document.readyState === 'complete') {
      checkResources();
    } else {
      window.addEventListener('load', checkResources);
      return () => window.removeEventListener('load', checkResources);
    }
  }, []);
}

/**
 * Performance budget checker
 */
export function usePerformanceBudget(budgets: {
  fcp?: number; // First Contentful Paint
  lcp?: number; // Largest Contentful Paint
  fid?: number; // First Input Delay
  cls?: number; // Cumulative Layout Shift
  ttfb?: number; // Time to First Byte
}) {
  useEffect(() => {
    if (typeof window === 'undefined') return;

    import('web-vitals').then(({ onCLS, onFID, onFCP, onLCP, onTTFB }) => {
      const checkBudget = (metric: any) => {
        const budget = budgets[metric.name.toLowerCase() as keyof typeof budgets];
        
        if (budget && metric.value > budget) {
          console.warn(
            `[Performance Budget] ${metric.name} exceeded budget:`,
            `${metric.value.toFixed(2)} > ${budget}`
          );
        }
      };

      if (budgets.cls) onCLS(checkBudget);
      if (budgets.fid) onFID(checkBudget);
      if (budgets.fcp) onFCP(checkBudget);
      if (budgets.lcp) onLCP(checkBudget);
      if (budgets.ttfb) onTTFB(checkBudget);
    });
  }, [budgets]);
}
