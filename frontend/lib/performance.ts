/**
 * Performance Monitoring Utilities
 * 
 * Tools for measuring and tracking component performance
 */

interface PerformanceMark {
  start: () => void;
  end: () => number;
  measure: () => PerformanceMeasure | null;
}

/**
 * Measure component render performance
 * 
 * @param componentName - Name of the component
 * @returns Object with start, end, and measure methods
 * 
 * @example
 * const perf = measurePerformance('ChatInterface');
 * perf.start();
 * // ... render logic
 * const duration = perf.end();
 * console.log(`Rendered in ${duration}ms`);
 */
export function measurePerformance(componentName: string): PerformanceMark {
  const startMark = `${componentName}-start`;
  const endMark = `${componentName}-end`;
  const measureName = componentName;

  return {
    start: () => {
      performance.mark(startMark);
    },

    end: () => {
      performance.mark(endMark);
      const measure = performance.measure(measureName, startMark, endMark);
      
      // Clean up marks
      performance.clearMarks(startMark);
      performance.clearMarks(endMark);
      
      return Math.round(measure.duration);
    },

    measure: () => {
      try {
        return performance.measure(measureName, startMark, endMark);
      } catch {
        return null;
      }
    },
  };
}

/**
 * Log slow renders to console
 * 
 * @param componentName - Name of the component
 * @param duration - Render duration in ms
 * @param threshold - Threshold for slow render (default: 16ms for 60fps)
 */
export function logSlowRender(
  componentName: string,
  duration: number,
  threshold = 16
): void {
  if (duration > threshold) {
    console.warn(
      `[Performance] ${componentName} took ${duration}ms to render (threshold: ${threshold}ms)`
    );
  }
}

/**
 * Measure async operation performance
 * 
 * @param operationName - Name of the operation
 * @param operation - Async operation to measure
 * @returns Result of the operation
 */
export async function measureAsync<T>(
  operationName: string,
  operation: () => Promise<T>
): Promise<T> {
  const perf = measurePerformance(operationName);
  
  perf.start();
  try {
    const result = await operation();
    const duration = perf.end();
    
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Performance] ${operationName} completed in ${duration}ms`);
    }
    
    return result;
  } catch (error) {
    perf.end();
    throw error;
  }
}

/**
 * Get Web Vitals metrics
 */
export function getWebVitals(): void {
  if (typeof window === 'undefined') return;

  // First Contentful Paint
  const paintEntries = performance.getEntriesByType('paint');
  const fcp = paintEntries.find((entry) => entry.name === 'first-contentful-paint');
  
  if (fcp) {
    console.log(`[Web Vitals] FCP: ${Math.round(fcp.startTime)}ms`);
  }

  // Largest Contentful Paint
  const observer = new PerformanceObserver((list) => {
    const entries = list.getEntries();
    const lastEntry = entries[entries.length - 1];
    if (lastEntry) {
      console.log(`[Web Vitals] LCP: ${Math.round(lastEntry.startTime)}ms`);
    }
  });

  observer.observe({ entryTypes: ['largest-contentful-paint'] });
}
