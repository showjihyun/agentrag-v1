/**
 * End-to-end tests for Agent Builder
 */

import { test, expect } from '@playwright/test';

test.describe('Agent Builder E2E', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/agent-builder');
  });

  test('should create and execute an agent', async ({ page }) => {
    // Click create agent button
    await page.click('button:has-text("Create Agent")');

    // Fill agent form
    await page.fill('input[name="name"]', 'Test Agent');
    await page.fill('textarea[name="description"]', 'E2E Test Agent');
    await page.selectOption('select[name="llm_provider"]', 'openai');
    await page.selectOption('select[name="llm_model"]', 'gpt-4');

    // Submit form
    await page.click('button:has-text("Create")');

    // Wait for success message
    await expect(page.locator('text=Agent created successfully')).toBeVisible();

    // Execute agent
    await page.click('button:has-text("Execute")');
    await page.fill('input[placeholder*="query"]', 'Test query');
    await page.click('button:has-text("Run")');

    // Wait for result
    await expect(page.locator('[data-testid="execution-result"]')).toBeVisible({
      timeout: 10000,
    });
  });

  test('should create a workflow', async ({ page }) => {
    // Navigate to workflows
    await page.click('text=Workflows');

    // Create workflow
    await page.click('button:has-text("Create Workflow")');
    await page.fill('input[name="name"]', 'Test Workflow');

    // Add blocks to workflow
    await page.dragAndDrop('[data-block-type="agent"]', '[data-testid="workflow-canvas"]');

    // Save workflow
    await page.click('button:has-text("Save")');

    // Verify success
    await expect(page.locator('text=Workflow saved')).toBeVisible();
  });

  test('should handle offline mode', async ({ page, context }) => {
    // Go offline
    await context.setOffline(true);

    // Try to load page
    await page.goto('/agent-builder');

    // Should show offline message
    await expect(page.locator('text=You are offline')).toBeVisible();

    // Go back online
    await context.setOffline(false);
    await page.reload();

    // Should work normally
    await expect(page.locator('text=Agent Builder')).toBeVisible();
  });

  test('should be accessible', async ({ page }) => {
    // Check for proper heading structure
    const h1 = await page.locator('h1').count();
    expect(h1).toBeGreaterThan(0);

    // Check for ARIA labels
    const buttons = await page.locator('button').all();
    for (const button of buttons) {
      const ariaLabel = await button.getAttribute('aria-label');
      const text = await button.textContent();
      expect(ariaLabel || text).toBeTruthy();
    }

    // Check for keyboard navigation
    await page.keyboard.press('Tab');
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeTruthy();
  });
});
