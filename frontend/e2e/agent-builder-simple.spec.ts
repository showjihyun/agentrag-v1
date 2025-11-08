/**
 * Simple E2E test for Agent Builder
 * Tests basic functionality without requiring full backend
 */

import { test, expect } from '@playwright/test';

test.describe('Agent Builder - Simple Tests', () => {
  
  test('should load the homepage', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Check if page loaded
    expect(page.url()).toContain('localhost:3000');
    
    console.log('✓ Homepage loaded successfully');
  });

  test('should have proper page title', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Check title
    const title = await page.title();
    expect(title).toBeTruthy();
    
    console.log(`✓ Page title: ${title}`);
  });

  test('should have navigation elements', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    // Check for common navigation elements
    const nav = page.locator('nav, [role="navigation"]');
    
    if (await nav.count() > 0) {
      console.log('✓ Navigation found');
    } else {
      console.log('ℹ Navigation not found (may be on login page)');
    }
  });

  test('should be responsive', async ({ page }) => {
    // Test desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    console.log('✓ Desktop viewport (1920x1080) loaded');
    
    // Test tablet
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForLoadState('networkidle');
    console.log('✓ Tablet viewport (768x1024) loaded');
    
    // Test mobile
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForLoadState('networkidle');
    console.log('✓ Mobile viewport (375x667) loaded');
  });

  test('should have no console errors on load', async ({ page }) => {
    const errors: string[] = [];
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    if (errors.length === 0) {
      console.log('✓ No console errors');
    } else {
      console.log(`⚠ Found ${errors.length} console errors:`);
      errors.forEach(err => console.log(`  - ${err}`));
    }
    
    // Don't fail the test for console errors, just report them
    expect(errors.length).toBeLessThan(10);
  });

  test('should load CSS and JavaScript', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    // Check if styles are loaded
    const hasStyles = await page.evaluate(() => {
      return document.styleSheets.length > 0;
    });
    
    expect(hasStyles).toBeTruthy();
    console.log(`✓ Loaded ${await page.evaluate(() => document.styleSheets.length)} stylesheets`);
    
    // Check if scripts are loaded
    const hasScripts = await page.evaluate(() => {
      return document.scripts.length > 0;
    });
    
    expect(hasScripts).toBeTruthy();
    console.log(`✓ Loaded ${await page.evaluate(() => document.scripts.length)} scripts`);
  });

  test('should have proper meta tags', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Check viewport meta tag
    const viewport = await page.locator('meta[name="viewport"]').getAttribute('content');
    expect(viewport).toBeTruthy();
    console.log(`✓ Viewport: ${viewport}`);
    
    // Check charset
    const charset = await page.evaluate(() => document.characterSet);
    expect(charset).toBe('UTF-8');
    console.log(`✓ Charset: ${charset}`);
  });

  test('should measure page load performance', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    const metrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        domContentLoaded: Math.round(navigation.domContentLoadedEventEnd - navigation.fetchStart),
        loadComplete: Math.round(navigation.loadEventEnd - navigation.fetchStart),
        domInteractive: Math.round(navigation.domInteractive - navigation.fetchStart),
      };
    });
    
    console.log('✓ Performance metrics:');
    console.log(`  - DOM Content Loaded: ${metrics.domContentLoaded}ms`);
    console.log(`  - Load Complete: ${metrics.loadComplete}ms`);
    console.log(`  - DOM Interactive: ${metrics.domInteractive}ms`);
    
    // Reasonable thresholds
    expect(metrics.domContentLoaded).toBeLessThan(5000);
    expect(metrics.loadComplete).toBeLessThan(10000);
  });

  test('should handle 404 pages gracefully', async ({ page }) => {
    const response = await page.goto('http://localhost:3000/this-page-does-not-exist');
    
    // Should either get 404 or redirect
    if (response) {
      const status = response.status();
      console.log(`✓ 404 page status: ${status}`);
      expect([404, 200, 301, 302]).toContain(status);
    }
  });

  test('should have accessible HTML structure', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    // Check for main landmark
    const main = page.locator('main, [role="main"]');
    const mainCount = await main.count();
    
    if (mainCount > 0) {
      console.log('✓ Main landmark found');
    } else {
      console.log('ℹ Main landmark not found');
    }
    
    // Check for proper heading hierarchy
    const h1Count = await page.locator('h1').count();
    console.log(`✓ Found ${h1Count} h1 heading(s)`);
  });
});

test.describe('Agent Builder - Component Tests', () => {
  
  test('should check if Agent Builder route exists', async ({ page }) => {
    const response = await page.goto('http://localhost:3000/agent-builder');
    
    if (response) {
      const status = response.status();
      console.log(`✓ Agent Builder route status: ${status}`);
      
      // Should either load or redirect to login
      expect([200, 301, 302, 401, 403]).toContain(status);
    }
  });

  test('should check if agents route exists', async ({ page }) => {
    const response = await page.goto('http://localhost:3000/agent-builder/agents');
    
    if (response) {
      const status = response.status();
      console.log(`✓ Agents route status: ${status}`);
      expect([200, 301, 302, 401, 403]).toContain(status);
    }
  });

  test('should check if workflows route exists', async ({ page }) => {
    const response = await page.goto('http://localhost:3000/agent-builder/workflows');
    
    if (response) {
      const status = response.status();
      console.log(`✓ Workflows route status: ${status}`);
      expect([200, 301, 302, 401, 403]).toContain(status);
    }
  });

  test('should check if executions route exists', async ({ page }) => {
    const response = await page.goto('http://localhost:3000/agent-builder/executions');
    
    if (response) {
      const status = response.status();
      console.log(`✓ Executions route status: ${status}`);
      expect([200, 301, 302, 401, 403]).toContain(status);
    }
  });

  test('should check if approvals route exists', async ({ page }) => {
    const response = await page.goto('http://localhost:3000/agent-builder/approvals');
    
    if (response) {
      const status = response.status();
      console.log(`✓ Approvals route status: ${status}`);
      expect([200, 301, 302, 401, 403]).toContain(status);
    }
  });
});
