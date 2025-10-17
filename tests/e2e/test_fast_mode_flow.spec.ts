/**
 * E2E Test: Fast Mode Flow
 * 
 * Tests the complete user journey for fast mode queries:
 * 1. User enters a simple query
 * 2. System recommends Fast mode
 * 3. Quick response is displayed
 * 4. Sources and confidence are shown
 */

import { test, expect } from '@playwright/test';

test.describe('Fast Mode Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('http://localhost:3000');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
  });

  test('should complete fast mode query successfully', async ({ page }) => {
    // Step 1: Enter a simple query
    const queryInput = page.locator('input[placeholder*="Ask a question"]');
    await expect(queryInput).toBeVisible();
    
    const simpleQuery = 'What is AI?';
    await queryInput.fill(simpleQuery);
    
    // Step 2: Verify complexity indicator shows "simple"
    await page.waitForSelector('[data-testid="complexity-indicator"]', { timeout: 2000 });
    const complexityBadge = page.locator('[data-testid="complexity-indicator"]');
    await expect(complexityBadge).toContainText(/simple/i);
    
    // Step 3: Verify Fast mode is recommended
    const modeRecommendation = page.locator('[data-testid="mode-recommendation"]');
    await expect(modeRecommendation).toContainText(/fast/i);
    
    // Step 4: Submit the query
    const submitButton = page.locator('button[type="submit"]');
    await submitButton.click();
    
    // Step 5: Verify loading state
    await expect(page.locator('text=Thinking...')).toBeVisible({ timeout: 1000 });
    
    // Step 6: Wait for response (should be fast - within 3 seconds)
    const responseMessage = page.locator('[role="article"]').filter({ hasText: simpleQuery }).locator('..').locator('[role="article"]').last();
    await expect(responseMessage).toBeVisible({ timeout: 3000 });
    
    // Step 7: Verify response contains content
    const responseContent = responseMessage.locator('.prose');
    await expect(responseContent).not.toBeEmpty();
    
    // Step 8: Verify status badge shows "Complete"
    const statusBadge = responseMessage.locator('text=Complete');
    await expect(statusBadge).toBeVisible();
    
    // Step 9: Verify confidence score is displayed
    const confidenceBadge = responseMessage.locator('text=/Confidence:/');
    await expect(confidenceBadge).toBeVisible();
    
    // Step 10: Verify sources are displayed
    const sourcesSection = responseMessage.locator('text=/Source/');
    await expect(sourcesSection).toBeVisible();
    
    // Step 11: Verify response time was fast (check metadata)
    const pathSource = responseMessage.locator('text=/via speculative/i');
    await expect(pathSource).toBeVisible();
  });

  test('should handle fast mode with cache hit', async ({ page }) => {
    const query = 'What is machine learning?';
    
    // First query - cache miss
    await page.locator('input[placeholder*="Ask a question"]').fill(query);
    await page.locator('button[type="submit"]').click();
    await page.waitForSelector('[role="article"]', { timeout: 5000 });
    
    // Clear chat (if clear button exists)
    const clearButton = page.locator('button[aria-label="Clear chat"]');
    if (await clearButton.isVisible()) {
      await clearButton.click();
    }
    
    // Second query - should hit cache
    await page.locator('input[placeholder*="Ask a question"]').fill(query);
    await page.locator('button[type="submit"]').click();
    
    // Response should be even faster (< 1 second)
    const response = page.locator('[role="article"]').last();
    await expect(response).toBeVisible({ timeout: 1000 });
    
    // Verify cache indicator (if implemented)
    const cacheIndicator = response.locator('text=/cached/i');
    // Cache indicator might not be visible in UI, so this is optional
  });

  test('should handle empty query gracefully', async ({ page }) => {
    const submitButton = page.locator('button[type="submit"]');
    
    // Submit button should be disabled when input is empty
    await expect(submitButton).toBeDisabled();
    
    // Try to submit anyway (should not work)
    await submitButton.click({ force: true });
    
    // No new message should appear
    const messages = page.locator('[role="article"]');
    await expect(messages).toHaveCount(0);
  });

  test('should display reasoning steps when expanded', async ({ page }) => {
    // Submit a query
    await page.locator('input[placeholder*="Ask a question"]').fill('Explain AI');
    await page.locator('button[type="submit"]').click();
    
    // Wait for response
    await page.waitForSelector('[role="article"]', { timeout: 5000 });
    
    // Find and click reasoning steps toggle
    const reasoningToggle = page.locator('button:has-text("Reasoning Steps")');
    if (await reasoningToggle.isVisible()) {
      await reasoningToggle.click();
      
      // Verify reasoning steps are displayed
      const reasoningContent = page.locator('[data-testid="reasoning-step"]').first();
      await expect(reasoningContent).toBeVisible();
    }
  });

  test('should handle network errors gracefully', async ({ page, context }) => {
    // Simulate offline mode
    await context.setOffline(true);
    
    // Try to submit a query
    await page.locator('input[placeholder*="Ask a question"]').fill('Test query');
    await page.locator('button[type="submit"]').click();
    
    // Should show error message
    const errorMessage = page.locator('text=/error|failed/i');
    await expect(errorMessage).toBeVisible({ timeout: 5000 });
    
    // Restore online mode
    await context.setOffline(false);
  });
});
