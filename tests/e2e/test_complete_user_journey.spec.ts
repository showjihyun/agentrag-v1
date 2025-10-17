/**
 * E2E Test: Complete User Journey
 * 
 * Tests the full user workflow from document upload to query
 */

import { test, expect } from '@playwright/test';

test.describe('Complete User Journey', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
  });

  test('should complete full workflow: upload → query → response', async ({ page }) => {
    // Step 1: Upload a document
    const fileInput = page.locator('input[type="file"]');
    if (await fileInput.isVisible()) {
      // Create a test file
      await fileInput.setInputFiles({
        name: 'test-document.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('This is a test document about artificial intelligence and machine learning.')
      });
      
      // Wait for upload to complete
      await expect(page.locator('text=/uploaded|success/i')).toBeVisible({ timeout: 10000 });
    }
    
    // Step 2: Enter a query related to the document
    await page.locator('input[placeholder*="Ask a question"]').fill('What is this document about?');
    await page.locator('button[type="submit"]').click();
    
    // Step 3: Verify response appears
    const response = page.locator('[role="article"]').last();
    await expect(response).toBeVisible({ timeout: 10000 });
    
    // Step 4: Verify response mentions the document content
    const content = await response.textContent();
    expect(content?.toLowerCase()).toMatch(/artificial intelligence|machine learning/);
  });

  test('should handle authentication flow', async ({ page }) => {
    // Check if login is required
    const loginButton = page.locator('button:has-text("Login")');
    
    if (await loginButton.isVisible()) {
      await loginButton.click();
      
      // Fill login form
      await page.locator('input[type="email"]').fill('test@example.com');
      await page.locator('input[type="password"]').fill('testpassword123');
      await page.locator('button[type="submit"]').click();
      
      // Should redirect to main page or show user menu
      await expect(page.locator('[data-testid="user-menu"]')).toBeVisible({ timeout: 5000 });
    }
  });

  test('should navigate between conversations', async ({ page }) => {
    // Submit first query
    await page.locator('input[placeholder*="Ask a question"]').fill('First question');
    await page.locator('button[type="submit"]').click();
    await page.waitForSelector('[role="article"]', { timeout: 5000 });
    
    // Start new conversation
    const newChatButton = page.locator('button:has-text("New Chat")');
    if (await newChatButton.isVisible()) {
      await newChatButton.click();
      
      // Submit second query
      await page.locator('input[placeholder*="Ask a question"]').fill('Second question');
      await page.locator('button[type="submit"]').click();
      await page.waitForSelector('[role="article"]', { timeout: 5000 });
      
      // Navigate back to first conversation
      const conversationList = page.locator('[data-testid="conversation-item"]');
      if (await conversationList.first().isVisible()) {
        await conversationList.first().click();
        
        // Should show first question
        await expect(page.locator('text=First question')).toBeVisible();
      }
    }
  });

  test('should handle batch document upload', async ({ page }) => {
    const batchUploadButton = page.locator('button:has-text("Batch Upload")');
    
    if (await batchUploadButton.isVisible()) {
      await batchUploadButton.click();
      
      // Upload multiple files
      const fileInput = page.locator('input[type="file"][multiple]');
      await fileInput.setInputFiles([
        {
          name: 'doc1.txt',
          mimeType: 'text/plain',
          buffer: Buffer.from('Document 1 content')
        },
        {
          name: 'doc2.txt',
          mimeType: 'text/plain',
          buffer: Buffer.from('Document 2 content')
        }
      ]);
      
      // Verify progress indicators
      await expect(page.locator('[data-testid="upload-progress"]')).toBeVisible({ timeout: 2000 });
      
      // Wait for completion
      await expect(page.locator('text=/2.*uploaded/i')).toBeVisible({ timeout: 15000 });
    }
  });

  test('should display user dashboard with statistics', async ({ page }) => {
    const dashboardLink = page.locator('a[href="/dashboard"]');
    
    if (await dashboardLink.isVisible()) {
      await dashboardLink.click();
      
      // Verify dashboard elements
      await expect(page.locator('text=/documents|queries|storage/i')).toBeVisible({ timeout: 5000 });
      
      // Check for statistics cards
      const statsCards = page.locator('[data-testid="stat-card"]');
      expect(await statsCards.count()).toBeGreaterThan(0);
    }
  });
});
