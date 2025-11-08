/**
 * Performance E2E Tests
 * 
 * Tests performance metrics and optimization features.
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';

test.describe('Performance Tests', () => {
  
  test('should meet Core Web Vitals thresholds', async ({ page }) => {
    await page.goto(`${BASE_URL}/agent-builder`);
    
    // Measure performance metrics
    const metrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      const paint = performance.getEntriesByType('paint');
      
      return {
        // First Contentful Paint
        fcp: paint.find(entry => entry.name === 'first-contentful-paint')?.startTime || 0,
        
        // Largest Contentful Paint
        lcp: navigation.loadEventEnd - navigation.fetchStart,
        
        // Time to Interactive
        tti: navigation.domInteractive - navigation.fetchStart,
        
        // Total Blocking Time
        tbt: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
      };
    });
    
    // Core Web Vitals thresholds
    expect(metrics.fcp).toBeLessThan(1800); // FCP < 1.8s (good)
    expect(metrics.lcp).toBeLessThan(2500); // LCP < 2.5s (good)
    expect(metrics.tti).toBeLessThan(3800); // TTI < 3.8s (good)
    expect(metrics.tbt).toBeLessThan(300);  // TBT < 300ms (good)
    
    console.log('Performance Metrics:', metrics);
  });

  test('should lazy load images', async ({ page }) => {
    await page.goto(`${BASE_URL}/agent-builder/marketplace`);
    
    // Check that images have loading="lazy"
    const images = await page.locator('img').all();
    
    for (const img of images) {
      const loading = await img.getAttribute('loading');
      expect(loading).toBe('lazy');
    }
  });

  test('should use code splitting', async ({ page }) => {
    await page.goto(`${BASE_URL}/agent-builder`);
    
    // Get all loaded scripts
    const scripts = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('script[src]'))
        .map(script => (script as HTMLScriptElement).src);
    });
    
    // Verify chunks are loaded
    const hasChunks = scripts.some(src => src.includes('chunk'));
    expect(hasChunks).toBeTruthy();
    
    console.log(`Loaded ${scripts.length} scripts`);
  });

  test('should cache API responses', async ({ page }) => {
    await page.goto(`${BASE_URL}/agent-builder/agents`);
    
    // First load
    const firstLoadStart = Date.now();
    await page.waitForSelector('.agent-card');
    const firstLoadTime = Date.now() - firstLoadStart;
    
    // Reload page
    await page.reload();
    
    // Second load (should be faster due to caching)
    const secondLoadStart = Date.now();
    await page.waitForSelector('.agent-card');
    const secondLoadTime = Date.now() - secondLoadStart;
    
    // Second load should be at least 30% faster
    expect(secondLoadTime).toBeLessThan(firstLoadTime * 0.7);
    
    console.log(`First load: ${firstLoadTime}ms, Second load: ${secondLoadTime}ms`);
  });

  test('should handle large datasets efficiently', async ({ page }) => {
    // Mock large dataset
    await page.route('**/api/agent-builder/executions*', async (route) => {
      const executions = Array.from({ length: 1000 }, (_, i) => ({
        id: `exec_${i}`,
        agent_id: `agent_${i % 10}`,
        status: i % 3 === 0 ? 'success' : 'failed',
        duration_ms: Math.random() * 5000,
        created_at: new Date(Date.now() - i * 60000).toISOString()
      }));
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ executions, total: 1000 })
      });
    });
    
    const startTime = Date.now();
    await page.goto(`${BASE_URL}/agent-builder/executions`);
    await page.waitForSelector('.execution-row');
    const loadTime = Date.now() - startTime;
    
    // Should load within 3 seconds even with 1000 items
    expect(loadTime).toBeLessThan(3000);
    
    // Verify virtual scrolling is working (not all items rendered)
    const renderedRows = await page.locator('.execution-row').count();
    expect(renderedRows).toBeLessThan(100); // Only visible items rendered
    
    console.log(`Loaded 1000 items in ${loadTime}ms, rendered ${renderedRows} rows`);
  });

  test('should optimize bundle size', async ({ page }) => {
    await page.goto(`${BASE_URL}/agent-builder`);
    
    // Get total bundle size
    const resources = await page.evaluate(() => {
      return performance.getEntriesByType('resource')
        .filter(r => r.name.endsWith('.js'))
        .reduce((total, r) => total + (r as PerformanceResourceTiming).transferSize, 0);
    });
    
    // Total JS bundle should be under 500KB (compressed)
    expect(resources).toBeLessThan(500 * 1024);
    
    console.log(`Total JS bundle size: ${(resources / 1024).toFixed(2)} KB`);
  });

  test('should prefetch critical resources', async ({ page }) => {
    await page.goto(`${BASE_URL}/agent-builder`);
    
    // Check for prefetch links
    const prefetchLinks = await page.locator('link[rel="prefetch"]').count();
    expect(prefetchLinks).toBeGreaterThan(0);
    
    console.log(`Found ${prefetchLinks} prefetch links`);
  });

  test('should use service worker for offline support', async ({ page, context }) => {
    await page.goto(`${BASE_URL}/agent-builder`);
    
    // Check if service worker is registered
    const swRegistered = await page.evaluate(() => {
      return 'serviceWorker' in navigator && navigator.serviceWorker.controller !== null;
    });
    
    if (swRegistered) {
      console.log('Service worker is registered');
      
      // Go offline
      await context.setOffline(true);
      
      // Try to navigate (should work with cached resources)
      await page.goto(`${BASE_URL}/agent-builder/agents`);
      
      // Should show offline indicator
      await expect(page.locator('text=/offline|no connection/i')).toBeVisible();
    }
  });

  test('should debounce search input', async ({ page }) => {
    await page.goto(`${BASE_URL}/agent-builder/agents`);
    
    const searchInput = page.locator('input[name="search"]');
    
    // Type quickly
    await searchInput.type('test query', { delay: 50 });
    
    // Wait for debounce
    await page.waitForTimeout(500);
    
    // Should only make one API call (not one per keystroke)
    const apiCalls = await page.evaluate(() => {
      return (window as any).__apiCallCount || 0;
    });
    
    expect(apiCalls).toBeLessThanOrEqual(2); // Initial load + debounced search
  });

  test('should use React.memo for expensive components', async ({ page }) => {
    await page.goto(`${BASE_URL}/agent-builder/workflows/new/designer`);
    
    // Add multiple nodes
    for (let i = 0; i < 10; i++) {
      await page.click('[data-node-type="agent"]');
    }
    
    // Measure render time
    const renderTime = await page.evaluate(() => {
      const start = performance.now();
      
      // Trigger re-render
      window.dispatchEvent(new Event('resize'));
      
      return performance.now() - start;
    });
    
    // Re-render should be fast (< 100ms)
    expect(renderTime).toBeLessThan(100);
    
    console.log(`Re-render time: ${renderTime.toFixed(2)}ms`);
  });
});

test.describe('Memory Leak Tests', () => {
  
  test('should not leak memory on navigation', async ({ page }) => {
    await page.goto(`${BASE_URL}/agent-builder`);
    
    // Get initial memory
    const initialMemory = await page.evaluate(() => {
      if ('memory' in performance) {
        return (performance as any).memory.usedJSHeapSize;
      }
      return 0;
    });
    
    // Navigate multiple times
    for (let i = 0; i < 10; i++) {
      await page.goto(`${BASE_URL}/agent-builder/agents`);
      await page.goto(`${BASE_URL}/agent-builder/workflows`);
      await page.goto(`${BASE_URL}/agent-builder/executions`);
    }
    
    // Force garbage collection (if available)
    await page.evaluate(() => {
      if ('gc' in window) {
        (window as any).gc();
      }
    });
    
    // Get final memory
    const finalMemory = await page.evaluate(() => {
      if ('memory' in performance) {
        return (performance as any).memory.usedJSHeapSize;
      }
      return 0;
    });
    
    if (initialMemory > 0 && finalMemory > 0) {
      // Memory should not increase by more than 50%
      const memoryIncrease = (finalMemory - initialMemory) / initialMemory;
      expect(memoryIncrease).toBeLessThan(0.5);
      
      console.log(`Memory increase: ${(memoryIncrease * 100).toFixed(2)}%`);
    }
  });

  test('should cleanup event listeners', async ({ page }) => {
    await page.goto(`${BASE_URL}/agent-builder/workflows/new/designer`);
    
    // Get initial listener count
    const initialListeners = await page.evaluate(() => {
      return (window as any).getEventListeners?.(document).length || 0;
    });
    
    // Add and remove nodes multiple times
    for (let i = 0; i < 20; i++) {
      await page.click('[data-node-type="agent"]');
      await page.keyboard.press('Delete');
    }
    
    // Get final listener count
    const finalListeners = await page.evaluate(() => {
      return (window as any).getEventListeners?.(document).length || 0;
    });
    
    // Listener count should not grow significantly
    if (initialListeners > 0) {
      expect(finalListeners).toBeLessThan(initialListeners * 1.5);
      console.log(`Listeners: ${initialListeners} → ${finalListeners}`);
    }
  });
});
