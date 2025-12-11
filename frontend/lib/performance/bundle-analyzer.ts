/**
 * Bundle size analysis utilities
 * 
 * These utilities help identify and optimize large dependencies
 */

/**
 * Track component render time in development
 */
export function measureRenderTime(componentName: string) {
  if (process.env.NODE_ENV !== 'development') {
    return { start: () => {}, end: () => {} };
  }

  let startTime: number;

  return {
    start: () => {
      startTime = performance.now();
    },
    end: () => {
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      if (duration > 16) { // More than one frame (60fps)
        console.warn(
          `[Performance] ${componentName} took ${duration.toFixed(2)}ms to render`
        );
      }
    },
  };
}

/**
 * Report Web Vitals metrics
 */
export function reportWebVitals(metric: {
  id: string;
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
}) {
  // Log in development
  if (process.env.NODE_ENV === 'development') {
    console.log(`[Web Vitals] ${metric.name}: ${metric.value} (${metric.rating})`);
  }

  // In production, send to analytics
  if (process.env.NODE_ENV === 'production') {
    // TODO: Send to analytics service
    // analytics.track('web_vitals', metric);
  }
}

/**
 * Measure and log bundle chunk sizes
 */
export function logChunkSizes() {
  if (typeof window === 'undefined') return;

  const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[];
  const jsChunks = resources.filter(r => r.name.endsWith('.js'));
  
  const totalSize = jsChunks.reduce((acc, chunk) => acc + (chunk.transferSize || 0), 0);
  
  console.log('[Bundle Analysis]');
  console.log(`Total JS size: ${(totalSize / 1024).toFixed(2)} KB`);
  
  // Log large chunks
  jsChunks
    .filter(chunk => (chunk.transferSize || 0) > 50 * 1024) // > 50KB
    .sort((a, b) => (b.transferSize || 0) - (a.transferSize || 0))
    .forEach(chunk => {
      const name = chunk.name.split('/').pop();
      console.log(`  ${name}: ${((chunk.transferSize || 0) / 1024).toFixed(2)} KB`);
    });
}

/**
 * Performance budget checker
 */
export const PERFORMANCE_BUDGETS = {
  // Time to First Byte
  TTFB: 800,
  // First Contentful Paint
  FCP: 1800,
  // Largest Contentful Paint
  LCP: 2500,
  // First Input Delay
  FID: 100,
  // Cumulative Layout Shift
  CLS: 0.1,
  // Total Blocking Time
  TBT: 200,
  // Total JS bundle size (KB)
  JS_BUNDLE_SIZE: 300,
} as const;

export function checkPerformanceBudget(
  metric: keyof typeof PERFORMANCE_BUDGETS,
  value: number
): boolean {
  const budget = PERFORMANCE_BUDGETS[metric];
  const passed = value <= budget;
  
  if (!passed && process.env.NODE_ENV === 'development') {
    console.warn(
      `[Performance Budget] ${metric} exceeded: ${value} > ${budget}`
    );
  }
  
  return passed;
}
