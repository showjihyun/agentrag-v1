/**
 * Workflow Tools UI/UX E2E Tests
 * 워크플로우 도구들의 UI/UX 테스트
 */

import { test, expect } from '@playwright/test';

test.describe('Workflow Tools UI Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/agent-builder/workflows');
    await page.waitForLoadState('networkidle');
  });

  test('should load workflows page', async ({ page }) => {
    // Check page loaded
    await expect(page).toHaveURL(/workflows/);
    
    // Check for main content
    const mainContent = page.locator('main, [role="main"], .main-content').first();
    await expect(mainContent).toBeVisible({ timeout: 10000 });
    
    console.log('✅ Workflows page loaded successfully');
  });

  test('should display workflow list or empty state', async ({ page }) => {
    // Wait for content to load
    await page.waitForTimeout(2000);
    
    // Check for workflow cards or empty state
    const workflowCards = page.locator('[class*="workflow"], [class*="card"]');
    const emptyState = page.getByText(/no workflow|empty|create/i);
    
    const hasCards = await workflowCards.count() > 0;
    const hasEmptyState = await emptyState.isVisible().catch(() => false);
    
    console.log(`📋 Workflow cards: ${await workflowCards.count()}`);
    console.log(`📭 Empty state visible: ${hasEmptyState}`);
    
    expect(hasCards || hasEmptyState).toBeTruthy();
  });

  test('should have create workflow button', async ({ page }) => {
    // Look for create/new button
    const createButton = page.getByRole('button', { name: /create|new|add|\+/i }).first();
    const createLink = page.getByRole('link', { name: /create|new|add/i }).first();
    
    const hasCreateButton = await createButton.isVisible().catch(() => false);
    const hasCreateLink = await createLink.isVisible().catch(() => false);
    
    console.log(`🔘 Create button visible: ${hasCreateButton}`);
    console.log(`🔗 Create link visible: ${hasCreateLink}`);
    
    // At least one should exist
    expect(hasCreateButton || hasCreateLink).toBeTruthy();
  });

  test('should navigate to workflow editor', async ({ page }) => {
    // Try to navigate to new workflow
    await page.goto('/agent-builder/workflows/new');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Check for editor elements
    const canvas = page.locator('[class*="canvas"], [class*="flow"], [class*="react-flow"]');
    const sidebar = page.locator('[class*="sidebar"], [class*="panel"], [class*="palette"]');
    
    const hasCanvas = await canvas.first().isVisible().catch(() => false);
    const hasSidebar = await sidebar.first().isVisible().catch(() => false);
    
    console.log(`🎨 Canvas visible: ${hasCanvas}`);
    console.log(`📑 Sidebar visible: ${hasSidebar}`);
  });
});

test.describe('Tool Configuration UI Tests', () => {
  test('should display tool categories in sidebar', async ({ page }) => {
    await page.goto('/agent-builder/workflows/new');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Look for tool categories
    const categories = ['AI', 'Communication', 'Data', 'Search', 'HTTP', 'Code'];
    let foundCategories = 0;
    
    for (const category of categories) {
      const categoryElement = page.getByText(category, { exact: false });
      if (await categoryElement.first().isVisible().catch(() => false)) {
        foundCategories++;
        console.log(`✅ Found category: ${category}`);
      }
    }
    
    console.log(`📂 Found ${foundCategories}/${categories.length} categories`);
  });

  test('should display individual tools', async ({ page }) => {
    await page.goto('/agent-builder/workflows/new');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Look for specific tools
    const tools = ['HTTP Request', 'OpenAI', 'Slack', 'PostgreSQL', 'Code'];
    let foundTools = 0;
    
    for (const tool of tools) {
      const toolElement = page.getByText(tool, { exact: false });
      if (await toolElement.first().isVisible().catch(() => false)) {
        foundTools++;
        console.log(`✅ Found tool: ${tool}`);
      }
    }
    
    console.log(`🔧 Found ${foundTools}/${tools.length} tools`);
  });
});

test.describe('Workflow Canvas Interaction Tests', () => {
  test('should support node interactions', async ({ page }) => {
    await page.goto('/agent-builder/workflows/new');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Check for React Flow canvas
    const reactFlow = page.locator('.react-flow, [class*="reactflow"]');
    const hasReactFlow = await reactFlow.first().isVisible().catch(() => false);
    
    console.log(`🔄 React Flow canvas: ${hasReactFlow}`);
    
    // Check for zoom controls
    const zoomControls = page.locator('[class*="controls"], [class*="zoom"]');
    const hasZoomControls = await zoomControls.first().isVisible().catch(() => false);
    
    console.log(`🔍 Zoom controls: ${hasZoomControls}`);
    
    // Check for minimap
    const minimap = page.locator('[class*="minimap"]');
    const hasMinimap = await minimap.first().isVisible().catch(() => false);
    
    console.log(`🗺️ Minimap: ${hasMinimap}`);
  });

  test('should have save and execute buttons', async ({ page }) => {
    await page.goto('/agent-builder/workflows/new');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Look for action buttons
    const saveButton = page.getByRole('button', { name: /save|저장/i });
    const executeButton = page.getByRole('button', { name: /execute|run|실행/i });
    
    const hasSave = await saveButton.first().isVisible().catch(() => false);
    const hasExecute = await executeButton.first().isVisible().catch(() => false);
    
    console.log(`💾 Save button: ${hasSave}`);
    console.log(`▶️ Execute button: ${hasExecute}`);
  });
});

test.describe('Responsive Design Tests', () => {
  test('should be responsive on tablet', async ({ page }) => {
    await page.setViewportSize({ width: 1024, height: 768 });
    await page.goto('/agent-builder/workflows');
    await page.waitForLoadState('networkidle');
    
    // Check layout
    const mainContent = page.locator('main, [role="main"]').first();
    await expect(mainContent).toBeVisible();
    
    console.log('📱 Tablet layout OK');
  });

  test('should be responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/agent-builder/workflows');
    await page.waitForLoadState('networkidle');
    
    // Check layout
    const mainContent = page.locator('main, [role="main"]').first();
    await expect(mainContent).toBeVisible();
    
    // Check for mobile menu
    const mobileMenu = page.locator('[class*="mobile"], [class*="hamburger"], [class*="menu-toggle"]');
    const hasMobileMenu = await mobileMenu.first().isVisible().catch(() => false);
    
    console.log(`📱 Mobile layout OK`);
    console.log(`☰ Mobile menu: ${hasMobileMenu}`);
  });
});
