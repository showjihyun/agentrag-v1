/**
 * Performance monitoring utilities
 */

interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
  metadata?: Record<string, any>;
}

class PerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private observers: PerformanceObserver[] = [];

  /**
   * Initialize performance monitoring
   */
  init() {
    if (typeof window === 'undefined') return;

    // Monitor Long Tasks
    if ('PerformanceObserver' in window) {
      try {
        const longTaskObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            this.recordMetric('long-task', entry.duration, {
              name: entry.name,
              startTime: entry.startTime,
            });
          }
        });
        longTaskObserver.observe({ entryTypes: ['longtask'] });
        this.observers.push(longTaskObserver);
      } catch (e) {
        console.warn('[Performance] Long task monitoring not supported');
      }

      // Monitor Layout Shifts
      try {
        const clsObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if ((entry as any).hadRecentInput) continue;
            
            this.recordMetric('layout-shift', (entry as any).value, {
              sources: (entry as any).sources,
            });
          }
        });
        clsObserver.observe({ entryTypes: ['layout-shift'] });
        this.observers.push(clsObserver);
      } catch (e) {
        console.warn('[Performance] Layout shift monitoring not supported');
      }

      // Monitor First Input Delay
      try {
        const fidObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            const firstInputEntry = entry as any;
            this.recordMetric('first-input-delay', firstInputEntry.processingStart - firstInputEntry.startTime, {
              name: entry.name,
            });
          }
        });
        fidObserver.observe({ entryTypes: ['first-input'] });
        this.observers.push(fidObserver);
      } catch (e) {
        console.warn('[Performance] First input delay monitoring not supported');
      }
    }

    // Monitor Core Web Vitals
    this.monitorWebVitals();

    console.log('[Performance] Monitoring initialized');
  }

  /**
   * Monitor Core Web Vitals
   */
  private monitorWebVitals() {
    if (typeof window === 'undefined') return;

    // LCP - Largest Contentful Paint
    if ('PerformanceObserver' in window) {
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          if (lastEntry) {
            this.recordMetric('lcp', lastEntry.startTime, {
              element: (lastEntry as any).element?.tagName,
            });
          }
        });
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        this.observers.push(lcpObserver);
      } catch (e) {
        console.warn('[Performance] LCP monitoring not supported');
      }
    }

    // FCP - First Contentful Paint
    window.addEventListener('load', () => {
      const perfData = performance.getEntriesByType('paint');
      const fcp = perfData.find((entry) => entry.name === 'first-contentful-paint');
      if (fcp) {
        this.recordMetric('fcp', fcp.startTime);
      }
    });

    // TTFB - Time to First Byte
    window.addEventListener('load', () => {
      const navTiming = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      if (navTiming) {
        this.recordMetric('ttfb', navTiming.responseStart - navTiming.requestStart);
      }
    });
  }

  /**
   * Record a performance metric
   */
  recordMetric(name: string, value: number, metadata?: Record<string, any>) {
    const metric: PerformanceMetric = {
      name,
      value,
      timestamp: Date.now(),
      metadata: metadata || {},
    };

    this.metrics.push(metric);

    // Log in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Performance] ${name}:`, value.toFixed(2), 'ms', metadata);
    }

    // Send to analytics in production
    if (process.env.NODE_ENV === 'production') {
      this.sendToAnalytics(metric);
    }

    // Keep only last 100 metrics
    if (this.metrics.length > 100) {
      this.metrics.shift();
    }
  }

  /**
   * Send metric to analytics
   */
  private sendToAnalytics(metric: PerformanceMetric) {
    // Send to your analytics service
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', 'performance_metric', {
        metric_name: metric.name,
        metric_value: metric.value,
        ...metric.metadata,
      });
    }
  }

  /**
   * Measure function execution time
   */
  measure<T>(name: string, fn: () => T): T {
    const startTime = performance.now();
    const result = fn();
    const endTime = performance.now();
    
    this.recordMetric(name, endTime - startTime);
    
    return result;
  }

  /**
   * Measure async function execution time
   */
  async measureAsync<T>(name: string, fn: () => Promise<T>): Promise<T> {
    const startTime = performance.now();
    const result = await fn();
    const endTime = performance.now();
    
    this.recordMetric(name, endTime - startTime);
    
    return result;
  }

  /**
   * Start a performance mark
   */
  mark(name: string) {
    if (typeof performance !== 'undefined' && performance.mark) {
      performance.mark(name);
    }
  }

  /**
   * Measure between two marks
   */
  measureBetween(name: string, startMark: string, endMark: string) {
    if (typeof performance !== 'undefined' && performance.measure) {
      try {
        performance.measure(name, startMark, endMark);
        const measure = performance.getEntriesByName(name)[0];
        if (measure) {
          this.recordMetric(name, measure.duration);
        }
      } catch (e) {
        console.warn('[Performance] Failed to measure:', e);
      }
    }
  }

  /**
   * Get all metrics
   */
  getMetrics(): PerformanceMetric[] {
    return [...this.metrics];
  }

  /**
   * Get metrics by name
   */
  getMetricsByName(name: string): PerformanceMetric[] {
    return this.metrics.filter((m) => m.name === name);
  }

  /**
   * Get average metric value
   */
  getAverageMetric(name: string): number {
    const metrics = this.getMetricsByName(name);
    if (metrics.length === 0) return 0;
    
    const sum = metrics.reduce((acc, m) => acc + m.value, 0);
    return sum / metrics.length;
  }

  /**
   * Clear all metrics
   */
  clearMetrics() {
    this.metrics = [];
  }

  /**
   * Cleanup observers
   */
  cleanup() {
    this.observers.forEach((observer) => observer.disconnect());
    this.observers = [];
  }
}

// Singleton instance
export const performanceMonitor = new PerformanceMonitor();

/**
 * React hook for performance monitoring
 */
export function usePerformanceMonitoring(componentName: string) {
  if (typeof window === 'undefined') return;

  const mountTime = performance.now();

  // Record mount time
  performanceMonitor.recordMetric(`${componentName}-mount`, mountTime);

  // Cleanup on unmount
  return () => {
    const unmountTime = performance.now();
    const lifetime = unmountTime - mountTime;
    performanceMonitor.recordMetric(`${componentName}-lifetime`, lifetime);
  };
}

/**
 * Measure component render time
 */
export function measureRender(componentName: string) {
  return {
    onRenderStart: () => {
      performanceMonitor.mark(`${componentName}-render-start`);
    },
    onRenderEnd: () => {
      performanceMonitor.mark(`${componentName}-render-end`);
      performanceMonitor.measureBetween(
        `${componentName}-render`,
        `${componentName}-render-start`,
        `${componentName}-render-end`
      );
    },
  };
}

/**
 * Report Web Vitals
 */
export function reportWebVitals(metric: any) {
  performanceMonitor.recordMetric(metric.name, metric.value, {
    id: metric.id,
    label: metric.label,
  });
}
