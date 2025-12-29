/**
 * Performance Monitoring Utilities
 * 
 * Monitor and report performance metrics
 */

interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
  metadata?: Record<string, any>;
}

class PerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private observers: Map<string, PerformanceObserver> = new Map();

  constructor() {
    if (typeof window !== 'undefined') {
      this.initializeObservers();
    }
  }

  private initializeObservers() {
    // Observe Long Tasks
    if ('PerformanceObserver' in window) {
      try {
        const longTaskObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            this.recordMetric({
              name: 'long-task',
              value: entry.duration,
              timestamp: entry.startTime,
              metadata: {
                type: entry.entryType,
              },
            });
          }
        });
        longTaskObserver.observe({ entryTypes: ['longtask'] });
        this.observers.set('longtask', longTaskObserver);
      } catch (e) {
        // Long tasks not supported
      }

      // Observe Layout Shifts
      try {
        const clsObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if ('value' in entry) {
              this.recordMetric({
                name: 'cumulative-layout-shift',
                value: (entry as any).value,
                timestamp: entry.startTime,
              });
            }
          }
        });
        clsObserver.observe({ entryTypes: ['layout-shift'] });
        this.observers.set('layout-shift', clsObserver);
      } catch (e) {
        // Layout shift not supported
      }

      // Observe First Input Delay
      try {
        const fidObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            const fid = (entry as any).processingStart - entry.startTime;
            this.recordMetric({
              name: 'first-input-delay',
              value: fid,
              timestamp: entry.startTime,
            });
          }
        });
        fidObserver.observe({ entryTypes: ['first-input'] });
        this.observers.set('first-input', fidObserver);
      } catch (e) {
        // First input not supported
      }
    }
  }

  recordMetric(metric: PerformanceMetric) {
    this.metrics.push(metric);

    // Keep only last 100 metrics
    if (this.metrics.length > 100) {
      this.metrics.shift();
    }

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Performance] ${metric.name}:`, metric.value, 'ms');
    }
  }

  getMetrics(name?: string): PerformanceMetric[] {
    if (name) {
      return this.metrics.filter((m) => m.name === name);
    }
    return this.metrics;
  }

  getAverageMetric(name: string): number {
    const metrics = this.getMetrics(name);
    if (metrics.length === 0) return 0;
    const sum = metrics.reduce((acc, m) => acc + m.value, 0);
    return sum / metrics.length;
  }

  clearMetrics() {
    this.metrics = [];
  }

  disconnect() {
    this.observers.forEach((observer) => observer.disconnect());
    this.observers.clear();
  }

  // Core Web Vitals
  getCoreWebVitals() {
    return {
      lcp: this.getAverageMetric('largest-contentful-paint'),
      fid: this.getAverageMetric('first-input-delay'),
      cls: this.getAverageMetric('cumulative-layout-shift'),
    };
  }

  // Report to analytics
  reportToAnalytics() {
    const vitals = this.getCoreWebVitals();
    
    // Send to your analytics service
    if (typeof window !== 'undefined' && 'gtag' in window) {
      (window as any).gtag('event', 'web_vitals', {
        event_category: 'Performance',
        lcp: vitals.lcp,
        fid: vitals.fid,
        cls: vitals.cls,
      });
    }

    return vitals;
  }
}

// Singleton instance
export const performanceMonitor = new PerformanceMonitor();

// React hook for performance monitoring
export const usePerformanceMonitor = () => {
  return {
    recordMetric: (name: string, value: number, metadata?: Record<string, any>) => {
      performanceMonitor.recordMetric({
        name,
        value,
        timestamp: Date.now(),
        ...(metadata && { metadata }),
      });
    },
    getMetrics: performanceMonitor.getMetrics.bind(performanceMonitor),
    getCoreWebVitals: performanceMonitor.getCoreWebVitals.bind(performanceMonitor),
  };
};

// Measure component render time
export const measureRender = (componentName: string) => {
  const start = performance.now();
  
  return () => {
    const duration = performance.now() - start;
    performanceMonitor.recordMetric({
      name: 'component-render',
      value: duration,
      timestamp: start,
      metadata: { component: componentName },
    });
  };
};

// Measure async operation
export const measureAsync = async <T,>(
  name: string,
  fn: () => Promise<T>
): Promise<T> => {
  const start = performance.now();
  try {
    const result = await fn();
    const duration = performance.now() - start;
    performanceMonitor.recordMetric({
      name,
      value: duration,
      timestamp: start,
      metadata: { success: true },
    });
    return result;
  } catch (error) {
    const duration = performance.now() - start;
    performanceMonitor.recordMetric({
      name,
      value: duration,
      timestamp: start,
      metadata: { success: false, error: String(error) },
    });
    throw error;
  }
};
