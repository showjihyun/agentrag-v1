/**
 * Performance Monitoring System
 * 
 * Tracks Web Vitals and custom performance metrics
 */

import { useEffect } from 'react';

// Web Vitals types
export interface WebVitalsMetric {
  name: 'CLS' | 'FID' | 'FCP' | 'LCP' | 'TTFB' | 'INP';
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  delta: number;
  id: string;
  navigationType: string;
}

// Custom metric types
export interface CustomMetric {
  name: string;
  value: number;
  timestamp: number;
  metadata?: Record<string, any>;
}

/**
 * Performance Monitor class
 */
class PerformanceMonitor {
  private metrics: CustomMetric[] = [];
  private webVitals: WebVitalsMetric[] = [];
  private enabled: boolean = true;

  constructor() {
    if (typeof window !== 'undefined') {
      this.initWebVitals();
    }
  }

  /**
   * Initialize Web Vitals tracking
   */
  private async initWebVitals() {
    try {
      const { onCLS, onFID, onFCP, onLCP, onTTFB, onINP } = await import('web-vitals');

      onCLS(this.handleWebVital.bind(this));
      onFID(this.handleWebVital.bind(this));
      onFCP(this.handleWebVital.bind(this));
      onLCP(this.handleWebVital.bind(this));
      onTTFB(this.handleWebVital.bind(this));
      onINP(this.handleWebVital.bind(this));
    } catch (error) {
      console.warn('Web Vitals not available:', error);
    }
  }

  /**
   * Handle Web Vital metric
   */
  private handleWebVital(metric: WebVitalsMetric) {
    this.webVitals.push(metric);
    
    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Web Vital] ${metric.name}:`, {
        value: metric.value,
        rating: metric.rating,
      });
    }

    // Send to analytics (implement your analytics service)
    this.sendToAnalytics('web-vital', metric);
  }

  /**
   * Track custom metric
   */
  trackMetric(name: string, value: number, metadata?: Record<string, any>) {
    if (!this.enabled) return;

    const metric: CustomMetric = {
      name,
      value,
      timestamp: Date.now(),
      metadata,
    };

    this.metrics.push(metric);

    if (process.env.NODE_ENV === 'development') {
      console.log(`[Metric] ${name}:`, value, metadata);
    }

    this.sendToAnalytics('custom-metric', metric);
  }

  /**
   * Track page load time
   */
  trackPageLoad(pageName: string) {
    if (typeof window === 'undefined') return;

    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    
    if (navigation) {
      this.trackMetric('page-load', navigation.loadEventEnd - navigation.fetchStart, {
        page: pageName,
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.fetchStart,
        domInteractive: navigation.domInteractive - navigation.fetchStart,
      });
    }
  }

  /**
   * Track API call performance
   */
  trackAPICall(endpoint: string, duration: number, status: number) {
    this.trackMetric('api-call', duration, {
      endpoint,
      status,
      success: status >= 200 && status < 300,
    });
  }

  /**
   * Track component render time
   */
  trackComponentRender(componentName: string, duration: number) {
    this.trackMetric('component-render', duration, {
      component: componentName,
    });
  }

  /**
   * Track user interaction
   */
  trackInteraction(action: string, duration?: number) {
    this.trackMetric('user-interaction', duration || 0, {
      action,
    });
  }

  /**
   * Get all metrics
   */
  getMetrics() {
    return {
      webVitals: this.webVitals,
      custom: this.metrics,
    };
  }

  /**
   * Get Web Vitals summary
   */
  getWebVitalsSummary() {
    const summary: Record<string, any> = {};

    this.webVitals.forEach(metric => {
      if (!summary[metric.name]) {
        summary[metric.name] = {
          value: metric.value,
          rating: metric.rating,
        };
      }
    });

    return summary;
  }

  /**
   * Clear all metrics
   */
  clearMetrics() {
    this.metrics = [];
    this.webVitals = [];
  }

  /**
   * Enable/disable monitoring
   */
  setEnabled(enabled: boolean) {
    this.enabled = enabled;
  }

  /**
   * Send to analytics service
   */
  private sendToAnalytics(type: string, data: any) {
    // Implement your analytics service here
    // Examples: Google Analytics, Mixpanel, Custom API
    
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', type, data);
    }
  }
}

// Global instance
const performanceMonitor = new PerformanceMonitor();

export default performanceMonitor;

/**
 * Hook for tracking component performance
 */
export function usePerformanceTracking(componentName: string) {
  useEffect(() => {
    const startTime = performance.now();

    return () => {
      const duration = performance.now() - startTime;
      performanceMonitor.trackComponentRender(componentName, duration);
    };
  }, [componentName]);
}

/**
 * Hook for tracking page load
 */
export function usePageLoadTracking(pageName: string) {
  useEffect(() => {
    performanceMonitor.trackPageLoad(pageName);
  }, [pageName]);
}

/**
 * Measure function execution time
 */
export function measurePerformance<T extends (...args: any[]) => any>(
  fn: T,
  name: string
): T {
  return ((...args: Parameters<T>) => {
    const start = performance.now();
    const result = fn(...args);
    const duration = performance.now() - start;
    
    performanceMonitor.trackMetric(`function-${name}`, duration);
    
    return result;
  }) as T;
}

/**
 * Measure async function execution time
 */
export function measureAsyncPerformance<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  name: string
): T {
  return (async (...args: Parameters<T>) => {
    const start = performance.now();
    const result = await fn(...args);
    const duration = performance.now() - start;
    
    performanceMonitor.trackMetric(`async-function-${name}`, duration);
    
    return result;
  }) as T;
}
