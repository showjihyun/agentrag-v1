// Performance monitoring utilities

export interface PerformanceMetrics {
  componentName: string;
  renderTime: number;
  renderCount: number;
  timestamp: number;
}

class PerformanceMonitor {
  private metrics: PerformanceMetrics[] = [];
  private observers: PerformanceObserver[] = [];

  constructor() {
    this.setupPerformanceObservers();
  }

  private setupPerformanceObservers() {
    if (typeof window === 'undefined') return;

    // Observe long tasks
    if ('PerformanceObserver' in window) {
      const longTaskObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.duration > 50) { // Tasks longer than 50ms
            console.warn('Long task detected:', {
              name: entry.name,
              duration: entry.duration,
              startTime: entry.startTime,
            });
          }
        }
      });

      try {
        longTaskObserver.observe({ entryTypes: ['longtask'] });
        this.observers.push(longTaskObserver);
      } catch (e) {
        console.warn('Long task observer not supported');
      }

      // Observe layout shifts
      const layoutShiftObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if ((entry as any).value > 0.1) { // CLS threshold
            console.warn('Layout shift detected:', {
              value: (entry as any).value,
              sources: (entry as any).sources,
            });
          }
        }
      });

      try {
        layoutShiftObserver.observe({ entryTypes: ['layout-shift'] });
        this.observers.push(layoutShiftObserver);
      } catch (e) {
        console.warn('Layout shift observer not supported');
      }
    }
  }

  recordComponentRender(componentName: string, renderTime: number) {
    this.metrics.push({
      componentName,
      renderTime,
      renderCount: this.getComponentRenderCount(componentName) + 1,
      timestamp: Date.now(),
    });

    // Keep only last 100 metrics
    if (this.metrics.length > 100) {
      this.metrics = this.metrics.slice(-100);
    }
  }

  getComponentRenderCount(componentName: string): number {
    return this.metrics.filter(m => m.componentName === componentName).length;
  }

  getAverageRenderTime(componentName: string): number {
    const componentMetrics = this.metrics.filter(m => m.componentName === componentName);
    if (componentMetrics.length === 0) return 0;
    
    const totalTime = componentMetrics.reduce((sum, m) => sum + m.renderTime, 0);
    return totalTime / componentMetrics.length;
  }

  getSlowComponents(threshold: number = 16): PerformanceMetrics[] {
    const componentAverages = new Map<string, number>();
    
    this.metrics.forEach(metric => {
      const current = componentAverages.get(metric.componentName) || 0;
      componentAverages.set(metric.componentName, current + metric.renderTime);
    });

    return Array.from(componentAverages.entries())
      .map(([componentName, totalTime]) => ({
        componentName,
        renderTime: totalTime / this.getComponentRenderCount(componentName),
        renderCount: this.getComponentRenderCount(componentName),
        timestamp: Date.now(),
      }))
      .filter(metric => metric.renderTime > threshold);
  }

  exportMetrics(): PerformanceMetrics[] {
    return [...this.metrics];
  }

  clearMetrics() {
    this.metrics = [];
  }

  disconnect() {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
  }
}

export const performanceMonitor = new PerformanceMonitor();

// React Profiler callback
export const onRenderCallback = (
  id: string,
  phase: 'mount' | 'update' | 'nested-update',
  actualDuration: number,
  baseDuration: number,
  startTime: number,
  commitTime: number
) => {
  if (process.env.NODE_ENV === 'development') {
    performanceMonitor.recordComponentRender(id, actualDuration);
    
    // Log slow renders
    if (actualDuration > 16) {
      console.warn(`Slow render detected in ${id}:`, {
        phase,
        actualDuration,
        baseDuration,
        startTime,
        commitTime,
      });
    }
  }
};

// Custom hook for measuring component performance
export function usePerformanceProfiler(componentName: string) {
  const startTime = performance.now();
  
  return {
    measure: () => {
      const endTime = performance.now();
      const duration = endTime - startTime;
      performanceMonitor.recordComponentRender(componentName, duration);
      return duration;
    },
  };
}

// Web Vitals measurement (optional dependency)
export function measureWebVitals() {
  if (typeof window === 'undefined') return;

  // Simple performance measurement without external dependencies
  try {
    // Use built-in Performance API
    if ('performance' in window && 'PerformanceObserver' in window) {
      // Measure paint timings
      const paintObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          console.log(`${entry.name}: ${entry.startTime}ms`);
        }
      });
      
      try {
        paintObserver.observe({ entryTypes: ['paint'] });
      } catch (e) {
        console.warn('Paint observer not supported');
      }

      // Measure navigation timing
      window.addEventListener('load', () => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        if (navigation) {
          console.log('Navigation Timing:', {
            domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
            loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
            firstByte: navigation.responseStart - navigation.requestStart,
          });
        }
      });
    }
  } catch (error) {
    console.warn('Performance measurement failed:', error);
  }
}