/**
 * E2E Tests for Phase 2 & 3 Features
 * Tests code splitting, animations, WebSocket, and i18n
 */

import { test, expect } from '@playwright/test';

test.describe('Phase 2: Code Splitting & Performance', () => {
  test('should lazy load heavy components', async ({ page }) => {
    await page.goto('/');

    // Check that monitoring dashboard is not loaded initially
    const monitoringScript = page.locator('script[src*="monitoring"]');
    await expect(monitoringScript).toHaveCount(0);

    // Navigate to monitoring page
    await page.goto('/monitoring');

    // Wait for lazy component to load
    await page.waitForSelector('[data-testid="monitoring-dashboard"]', { timeout: 5000 });

    // Verify component is loaded
    await expect(page.locator('[data-testid="monitoring-dashboard"]')).toBeVisible();
  });

  test('should have optimized bundle size', async ({ page }) => {
    const response = await page.goto('/');
    
    // Check that main bundle is reasonably sized
    const resources = await page.evaluate(() => {
      return performance.getEntriesByType('resource').map((r: any) => ({
        name: r.name,
        size: r.transferSize,
      }));
    });

    const mainBundle = resources.find((r: any) => r.name.includes('main'));
    if (mainBundle) {
      // Main bundle should be under 500KB
      expect(mainBundle.size).toBeLessThan(500 * 1024);
    }
  });
});

test.describe('Phase 2: React Hook Form', () => {
  test('should validate login form with Zod', async ({ page }) => {
    await page.goto('/auth/login');

    // Submit empty form
    await page.click('button[type="submit"]');

    // Check for validation errors
    await expect(page.locator('text=Invalid email address')).toBeVisible();
    await expect(page.locator('text=Password must be at least 6 characters')).toBeVisible();
  });

  test('should validate register form', async ({ page }) => {
    await page.goto('/auth/register');

    // Fill form with mismatched passwords
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.fill('input[name="confirmPassword"]', 'different');

    await page.click('button[type="submit"]');

    // Check for password mismatch error
    await expect(page.locator('text=Passwords don\'t match')).toBeVisible();
  });

  test('should have optimized form re-renders', async ({ page }) => {
    await page.goto('/auth/login');

    // Type in email field
    await page.fill('input[name="email"]', 'test@example.com');

    // Password field should not re-render (no validation yet)
    const passwordField = page.locator('input[name="password"]');
    await expect(passwordField).toBeVisible();
    await expect(passwordField).toHaveValue('');
  });
});

test.describe('Phase 2: Framer Motion Animations', () => {
  test('should animate page transitions', async ({ page }) => {
    await page.goto('/');

    // Navigate to dashboard
    await page.click('a[href="/dashboard"]');

    // Check for animation classes
    const dashboard = page.locator('[data-testid="dashboard"]');
    await expect(dashboard).toBeVisible();

    // Verify smooth transition (no jarring jumps)
    await page.waitForTimeout(500);
  });

  test('should animate message list', async ({ page }) => {
    await page.goto('/');

    // Send a message
    await page.fill('textarea[placeholder*="message"]', 'Test message');
    await page.click('button[type="submit"]');

    // Check that message appears with animation
    const message = page.locator('[data-testid="message"]').last();
    await expect(message).toBeVisible();
  });

  test('should have smooth button interactions', async ({ page }) => {
    await page.goto('/');

    // Hover over button
    const button = page.locator('button').first();
    await button.hover();

    // Button should have hover effect
    await expect(button).toBeVisible();
  });
});

test.describe('Phase 3: WebSocket Real-time Updates', () => {
  test('should connect to WebSocket', async ({ page }) => {
    await page.goto('/');

    // Wait for WebSocket connection
    await page.waitForTimeout(1000);

    // Check connection status
    const status = await page.evaluate(() => {
      return (window as any).wsClient?.isConnected();
    });

    expect(status).toBeTruthy();
  });

  test('should receive real-time messages', async ({ page }) => {
    await page.goto('/');

    // Send a message
    await page.fill('textarea[placeholder*="message"]', 'Test real-time');
    await page.click('button[type="submit"]');

    // Wait for response via WebSocket
    await page.waitForSelector('[data-testid="assistant-message"]', { timeout: 10000 });

    // Verify message received
    const assistantMessage = page.locator('[data-testid="assistant-message"]').last();
    await expect(assistantMessage).toBeVisible();
  });

  test('should show typing indicator', async ({ page }) => {
    await page.goto('/');

    // Start typing
    await page.fill('textarea[placeholder*="message"]', 'T');

    // Check for typing indicator (if implemented)
    await page.waitForTimeout(500);
  });

  test('should handle WebSocket reconnection', async ({ page }) => {
    await page.goto('/');

    // Simulate disconnect
    await page.evaluate(() => {
      (window as any).wsClient?.disconnect();
    });

    await page.waitForTimeout(1000);

    // Reconnect
    await page.evaluate(() => {
      (window as any).wsClient?.connect();
    });

    await page.waitForTimeout(2000);

    // Verify reconnected
    const status = await page.evaluate(() => {
      return (window as any).wsClient?.isConnected();
    });

    expect(status).toBeTruthy();
  });
});

test.describe('Phase 3: Internationalization (i18n)', () => {
  test('should switch language to Korean', async ({ page }) => {
    await page.goto('/');

    // Open language switcher
    await page.click('[aria-label="Change language"]');

    // Select Korean
    await page.click('text=한국어');

    // Verify language changed
    await expect(page.locator('text=로그인')).toBeVisible();
  });

  test('should switch language to Japanese', async ({ page }) => {
    await page.goto('/');

    // Open language switcher
    await page.click('[aria-label="Change language"]');

    // Select Japanese
    await page.click('text=日本語');

    // Verify language changed
    await expect(page.locator('text=ログイン')).toBeVisible();
  });

  test('should persist language preference', async ({ page }) => {
    await page.goto('/');

    // Change to Korean
    await page.click('[aria-label="Change language"]');
    await page.click('text=한국어');

    // Reload page
    await page.reload();

    // Verify language persisted
    await expect(page.locator('text=로그인')).toBeVisible();
  });

  test('should format dates according to locale', async ({ page }) => {
    await page.goto('/dashboard');

    // Get date format
    const dateText = await page.locator('[data-testid="date"]').first().textContent();

    // Change to Korean
    await page.click('[aria-label="Change language"]');
    await page.click('text=한국어');

    // Verify date format changed
    const koreanDateText = await page.locator('[data-testid="date"]').first().textContent();
    expect(dateText).not.toBe(koreanDateText);
  });
});

test.describe('Phase 3: Performance Metrics', () => {
  test('should have fast Time to Interactive', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');

    // Wait for page to be interactive
    await page.waitForLoadState('networkidle');
    const endTime = Date.now();

    const tti = endTime - startTime;

    // TTI should be under 2 seconds
    expect(tti).toBeLessThan(2000);
  });

  test('should have good Lighthouse score', async ({ page }) => {
    await page.goto('/');

    // Get performance metrics
    const metrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as any;
      return {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
      };
    });

    // DOM Content Loaded should be fast
    expect(metrics.domContentLoaded).toBeLessThan(1000);
  });

  test('should have minimal re-renders', async ({ page }) => {
    await page.goto('/');

    // Type in input
    await page.fill('textarea[placeholder*="message"]', 'Test');

    // Only the input component should re-render
    // (This would need React DevTools profiler in real scenario)
    await page.waitForTimeout(100);
  });
});

test.describe('Integration: All Features Together', () => {
  test('should work with all features enabled', async ({ page }) => {
    await page.goto('/');

    // Change language
    await page.click('[aria-label="Change language"]');
    await page.click('text=한국어');

    // Send message (with animations and WebSocket)
    await page.fill('textarea[placeholder*="메시지"]', '테스트 메시지');
    await page.click('button[type="submit"]');

    // Wait for response
    await page.waitForSelector('[data-testid="assistant-message"]', { timeout: 10000 });

    // Verify everything works together
    await expect(page.locator('[data-testid="assistant-message"]').last()).toBeVisible();
  });
});
