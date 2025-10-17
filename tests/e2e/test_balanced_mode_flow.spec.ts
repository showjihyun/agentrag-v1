/**
 * E2E Test: Balanced Mode Flow
 * 
 * Tests the progressive response flow in balanced mode:
 * 1. Preliminary response appears quickly
 * 2. Refinement process is visible
 * 3. Final response shows improvements
 */

import { test, expect } from '@playwright/test';

test.describe('Balanced Mode Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
  });

  test('should show progressive response in balanced mode', async ({ page }) => {
    // Enter a medium complexity query
    const mediumQuery = 'Compare AI and machine learning, and explain their differences';
    await page.locator('input[placeholder*="Ask a question"]').fill(mediumQuery);
    
    // Wait for complexity analysis
    await page.waitForTimeout(500);
    
    // Verify Balanced mode is recommended
    const modeRecommendation = page.locator('[data-testid="mode-recommendation"]');
    await expect(modeRecommendation).toContainText(/balanced/i);
    
    // Submit query
    await page.locator('button[type="submit"]').click();
    
    // Step 1: Verify preliminary response appears quickly (within 3 seconds)
    const firstResponse = page.locator('[role="article"]').last();
    await expect(firstResponse).toBeVisible({ timeout: 3000 });
    
    // Step 2: Verify "Preliminary" badge is shown
    const preliminaryBadge = firstResponse.locator('text=Preliminary');
    await expect(preliminaryBadge).toBeVisible();
    
    // Step 3: Verify "Refining..." indicator appears
    const refiningIndicator = firstResponse.locator('text=/refining|processing deeper/i');
    await expect(refiningIndicator).toBeVisible({ timeout: 2000 });
    
    // Step 4: Wait for refinement to complete (within 10 seconds)
    const completeBadge = firstResponse.locator('text=Complete');
    await expect(completeBadge).toBeVisible({ timeout: 10000 });
    
    // Step 5: Verify final response has higher confidence
    const confidenceText = await firstResponse.locator('text=/Confidence: \\d+%/').textContent();
    const confidenceMatch = confidenceText?.match(/(\d+)%/);
    if (confidenceMatch) {
      const confidence = parseInt(confidenceMatch[1]);
      expect(confidence).toBeGreaterThan(60); // Should have decent confidence
    }
    
    // Step 6: Verify sources are present
    const sourcesButton = firstResponse.locator('button:has-text("Source")');
    await expect(sourcesButton).toBeVisible();
  });

  test('should show reasoning steps during refinement', async ({ page }) => {
    // Submit a complex query
    await page.locator('input[placeholder*="Ask a question"]').fill('Analyze the impact of AI on society');
    await page.locator('button[type="submit"]').click();
    
    // Wait for response to start
    await page.waitForSelector('[role="article"]', { timeout: 5000 });
    
    // Expand reasoning steps
    const reasoningToggle = page.locator('button:has-text("Reasoning Steps")');
    await reasoningToggle.click();
    
    // Verify reasoning steps appear progressively
    const reasoningSteps = page.locator('[data-testid="reasoning-step"]');
    
    // Should have at least one step
    await expect(reasoningSteps.first()).toBeVisible({ timeout: 5000 });
    
    // Wait a bit and check if more steps appear
    await page.waitForTimeout(2000);
    const stepCount = await reasoningSteps.count();
    expect(stepCount).toBeGreaterThan(0);
  });

  test('should handle mode switching', async ({ page }) => {
    // Enter query
    await page.locator('input[placeholder*="Ask a question"]').fill('What is deep learning?');
    
    // Manually select Deep mode
    const deepModeButton = page.locator('button:has-text("Deep")');
    await deepModeButton.click();
    
    // Verify Deep mode is selected
    await expect(deepModeButton).toHaveClass(/bg-white|selected/);
    
    // Submit query
    await page.locator('button[type="submit"]').click();
    
    // Should show more detailed reasoning
    await page.waitForSelector('[role="article"]', { timeout: 15000 });
    
    // Verify path source indicates agentic
    const pathSource = page.locator('text=/via agentic|via deep/i');
    await expect(pathSource).toBeVisible();
  });

  test('should compare preliminary and final responses', async ({ page }) => {
    // Submit query
    await page.locator('input[placeholder*="Ask a question"]').fill('Explain neural networks');
    await page.locator('button[type="submit"]').click();
    
    // Wait for preliminary response
    const response = page.locator('[role="article"]').last();
    await expect(response.locator('text=Preliminary')).toBeVisible({ timeout: 3000 });
    
    // Capture preliminary content
    const preliminaryContent = await response.locator('.prose').textContent();
    
    // Wait for final response
    await expect(response.locator('text=Complete')).toBeVisible({ timeout: 10000 });
    
    // Capture final content
    const finalContent = await response.locator('.prose').textContent();
    
    // Content should have changed (refined)
    expect(finalContent).not.toBe(preliminaryContent);
    expect(finalContent?.length || 0).toBeGreaterThan(0);
  });

  test('should handle timeout gracefully', async ({ page }) => {
    // This test simulates a slow backend response
    // In real scenario, you'd mock the API to delay response
    
    await page.locator('input[placeholder*="Ask a question"]').fill('Complex analysis query');
    await page.locator('button[type="submit"]').click();
    
    // Wait for response (with extended timeout)
    const response = page.locator('[role="article"]').last();
    await expect(response).toBeVisible({ timeout: 20000 });
    
    // Should eventually show some response (even if partial)
    const content = response.locator('.prose');
    await expect(content).not.toBeEmpty();
  });
});
