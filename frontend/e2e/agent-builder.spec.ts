/**
 * E2E Tests for Agent Builder
 * 
 * Tests the complete user flow for creating, testing, and managing agents.
 */

import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const API_URL = process.env.API_URL || 'http://localhost:8000';

// Mock user credentials
const TEST_USER = {
  email: 'test@example.com',
  password: 'testpassword123',
  token: 'mock-jwt-token'
};

// Helper functions
async function login(page: Page) {
  await page.goto(`${BASE_URL}/login`);
  await page.fill('input[name="email"]', TEST_USER.email);
  await page.fill('input[name="password"]', TEST_USER.password);
  await page.click('button[type="submit"]');
  await page.waitForURL(`${BASE_URL}/dashboard`);
}

async function navigateToAgentBuilder(page: Page) {
  await page.goto(`${BASE_URL}/agent-builder`);
  await expect(page.locator('h1')).toContainText('Agent Builder');
}

// Test Suite
test.describe('Agent Builder E2E Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    // Mock API responses
    await page.route(`${API_URL}/api/auth/login`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: TEST_USER.token,
          user: { id: '1', email: TEST_USER.email }
        })
      });
    });
    
    await login(page);
  });

  test.describe('Agent Creation Flow', () => {
    
    test('should create a new agent successfully', async ({ page }) => {
      await navigateToAgentBuilder(page);
      
      // Click "Create Agent" button
      await page.click('button:has-text("Create Agent")');
      
      // Fill agent form
      await page.fill('input[name="name"]', 'Test Agent');
      await page.fill('textarea[name="description"]', 'This is a test agent for E2E testing');
      
      // Select LLM provider
      await page.click('select[name="llm_provider"]');
      await page.click('option[value="openai"]');
      
      // Select model
      await page.click('select[name="llm_model"]');
      await page.click('option[value="gpt-3.5-turbo"]');
      
      // Add prompt template
      await page.fill('textarea[name="prompt_template"]', 
        'You are a helpful assistant. Answer the following question: {query}'
      );
      
      // Select tools
      await page.click('input[type="checkbox"][value="vector_search"]');
      await page.click('input[type="checkbox"][value="web_search"]');
      
      // Mock API response for agent creation
      await page.route(`${API_URL}/api/agent-builder/agents`, async (route) => {
        if (route.request().method() === 'POST') {
          await route.fulfill({
            status: 201,
            contentType: 'application/json',
            body: JSON.stringify({
              id: 'agent_123',
              name: 'Test Agent',
              description: 'This is a test agent for E2E testing',
              llm_provider: 'openai',
              llm_model: 'gpt-3.5-turbo',
              created_at: new Date().toISOString()
            })
          });
        }
      });
      
      // Submit form
      await page.click('button[type="submit"]:has-text("Create Agent")');
      
      // Verify success message
      await expect(page.locator('.toast')).toContainText('Agent created successfully');
      
      // Verify redirect to agent list
      await expect(page).toHaveURL(/\/agent-builder\/agents/);
      
      // Verify agent appears in list
      await expect(page.locator('text=Test Agent')).toBeVisible();
    });

    test('should validate required fields', async ({ page }) => {
      await navigateToAgentBuilder(page);
      
      await page.click('button:has-text("Create Agent")');
      
      // Try to submit without filling required fields
      await page.click('button[type="submit"]:has-text("Create Agent")');
      
      // Verify validation errors
      await expect(page.locator('text=Name is required')).toBeVisible();
      await expect(page.locator('text=Prompt template is required')).toBeVisible();
    });

    test('should show character count for prompt template', async ({ page }) => {
      await navigateToAgentBuilder(page);
      await page.click('button:has-text("Create Agent")');
      
      const promptTextarea = page.locator('textarea[name="prompt_template"]');
      await promptTextarea.fill('Test prompt');
      
      // Verify character count
      await expect(page.locator('text=/\\d+ characters/')).toBeVisible();
    });
  });

  test.describe('Agent Testing', () => {
    
    test('should test agent with sample input', async ({ page }) => {
      await navigateToAgentBuilder(page);
      
      // Mock agent list
      await page.route(`${API_URL}/api/agent-builder/agents`, async (route) => {
        if (route.request().method() === 'GET') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              agents: [{
                id: 'agent_123',
                name: 'Test Agent',
                description: 'Test description',
                llm_provider: 'openai',
                llm_model: 'gpt-3.5-turbo'
              }]
            })
          });
        }
      });
      
      await page.goto(`${BASE_URL}/agent-builder/agents`);
      
      // Click on agent
      await page.click('text=Test Agent');
      
      // Click "Test Agent" button
      await page.click('button:has-text("Test Agent")');
      
      // Fill test input
      await page.fill('textarea[name="query"]', 'What is artificial intelligence?');
      
      // Mock execution response
      await page.route(`${API_URL}/api/agent-builder/executions/agents/*`, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'text/event-stream',
          body: `data: ${JSON.stringify({
            type: 'step',
            step: {
              type: 'llm_call',
              content: 'Artificial intelligence is...',
              duration_ms: 1500
            }
          })}\n\n`
        });
      });
      
      // Run test
      await page.click('button:has-text("Run Test")');
      
      // Verify execution steps appear
      await expect(page.locator('.execution-step')).toBeVisible();
      await expect(page.locator('text=Artificial intelligence is')).toBeVisible();
      
      // Verify metrics
      await expect(page.locator('text=/Duration: \\d+ms/')).toBeVisible();
    });

    test('should display error when test fails', async ({ page }) => {
      await navigateToAgentBuilder(page);
      await page.goto(`${BASE_URL}/agent-builder/agents/agent_123`);
      
      await page.click('button:has-text("Test Agent")');
      await page.fill('textarea[name="query"]', 'Test query');
      
      // Mock error response
      await page.route(`${API_URL}/api/agent-builder/executions/agents/*`, async (route) => {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'LLM service unavailable'
          })
        });
      });
      
      await page.click('button:has-text("Run Test")');
      
      // Verify error message
      await expect(page.locator('.alert-error')).toContainText('LLM service unavailable');
    });
  });

  test.describe('Workflow Designer', () => {
    
    test('should create a workflow with multiple nodes', async ({ page }) => {
      await page.goto(`${BASE_URL}/agent-builder/workflows/new/designer`);
      
      // Verify canvas is loaded
      await expect(page.locator('.react-flow')).toBeVisible();
      
      // Drag agent node from palette
      const agentNode = page.locator('[data-node-type="agent"]');
      const canvas = page.locator('.react-flow__pane');
      
      await agentNode.dragTo(canvas, {
        targetPosition: { x: 200, y: 100 }
      });
      
      // Verify node appears on canvas
      await expect(page.locator('.react-flow__node')).toHaveCount(1);
      
      // Add another node
      const blockNode = page.locator('[data-node-type="block"]');
      await blockNode.dragTo(canvas, {
        targetPosition: { x: 400, y: 100 }
      });
      
      await expect(page.locator('.react-flow__node')).toHaveCount(2);
      
      // Connect nodes
      const sourceHandle = page.locator('.react-flow__handle-right').first();
      const targetHandle = page.locator('.react-flow__handle-left').last();
      
      await sourceHandle.hover();
      await page.mouse.down();
      await targetHandle.hover();
      await page.mouse.up();
      
      // Verify edge is created
      await expect(page.locator('.react-flow__edge')).toHaveCount(1);
      
      // Save workflow
      await page.fill('input[name="workflow_name"]', 'Test Workflow');
      
      await page.route(`${API_URL}/api/agent-builder/workflows`, async (route) => {
        if (route.request().method() === 'POST') {
          await route.fulfill({
            status: 201,
            contentType: 'application/json',
            body: JSON.stringify({
              id: 'workflow_123',
              name: 'Test Workflow'
            })
          });
        }
      });
      
      await page.click('button:has-text("Save Workflow")');
      
      // Verify success
      await expect(page.locator('.toast')).toContainText('Workflow saved successfully');
    });

    test('should validate workflow before saving', async ({ page }) => {
      await page.goto(`${BASE_URL}/agent-builder/workflows/new/designer`);
      
      // Try to save empty workflow
      await page.click('button:has-text("Save Workflow")');
      
      // Verify validation error
      await expect(page.locator('.alert-error')).toContainText('Workflow must have at least one node');
    });
  });

  test.describe('Knowledgebase Management', () => {
    
    test('should create knowledgebase and upload documents', async ({ page }) => {
      await page.goto(`${BASE_URL}/agent-builder/knowledgebases`);
      
      // Create knowledgebase
      await page.click('button:has-text("Create Knowledgebase")');
      await page.fill('input[name="name"]', 'Test KB');
      await page.fill('textarea[name="description"]', 'Test knowledgebase');
      
      await page.route(`${API_URL}/api/agent-builder/knowledgebases`, async (route) => {
        if (route.request().method() === 'POST') {
          await route.fulfill({
            status: 201,
            contentType: 'application/json',
            body: JSON.stringify({
              id: 'kb_123',
              name: 'Test KB'
            })
          });
        }
      });
      
      await page.click('button[type="submit"]:has-text("Create")');
      
      // Upload document
      await page.click('text=Test KB');
      
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles({
        name: 'test.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('Test document content')
      });
      
      // Mock upload response
      await page.route(`${API_URL}/api/agent-builder/knowledgebases/*/documents`, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            document_ids: ['doc_123'],
            processed: 1
          })
        });
      });
      
      // Verify upload progress
      await expect(page.locator('.progress-bar')).toBeVisible();
      
      // Verify success
      await expect(page.locator('text=1 document uploaded')).toBeVisible();
    });

    test('should search knowledgebase', async ({ page }) => {
      await page.goto(`${BASE_URL}/agent-builder/knowledgebases/kb_123`);
      
      // Enter search query
      await page.fill('input[name="search"]', 'artificial intelligence');
      
      // Mock search results
      await page.route(`${API_URL}/api/agent-builder/knowledgebases/*/search*`, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            results: [
              {
                content: 'AI is the simulation of human intelligence...',
                score: 0.95,
                document_id: 'doc_123'
              }
            ]
          })
        });
      });
      
      await page.click('button:has-text("Search")');
      
      // Verify results
      await expect(page.locator('.search-result')).toHaveCount(1);
      await expect(page.locator('text=AI is the simulation')).toBeVisible();
      await expect(page.locator('text=95%')).toBeVisible();
    });
  });

  test.describe('Execution Monitor', () => {
    
    test('should display execution history', async ({ page }) => {
      await page.goto(`${BASE_URL}/agent-builder/executions`);
      
      // Mock executions
      await page.route(`${API_URL}/api/agent-builder/executions*`, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            executions: [
              {
                id: 'exec_123',
                agent_id: 'agent_123',
                agent_name: 'Test Agent',
                status: 'success',
                duration_ms: 1500,
                created_at: new Date().toISOString()
              },
              {
                id: 'exec_124',
                agent_id: 'agent_123',
                agent_name: 'Test Agent',
                status: 'failed',
                duration_ms: 500,
                created_at: new Date().toISOString()
              }
            ],
            total: 2
          })
        });
      });
      
      await page.reload();
      
      // Verify executions are displayed
      await expect(page.locator('.execution-row')).toHaveCount(2);
      
      // Verify status badges
      await expect(page.locator('.badge-success')).toBeVisible();
      await expect(page.locator('.badge-error')).toBeVisible();
      
      // Filter by status
      await page.click('select[name="status"]');
      await page.click('option[value="success"]');
      
      // Verify filtered results
      await expect(page.locator('.execution-row')).toHaveCount(1);
    });

    test('should view execution details', async ({ page }) => {
      await page.goto(`${BASE_URL}/agent-builder/executions`);
      
      // Click on execution
      await page.click('.execution-row:first-child');
      
      // Mock execution details
      await page.route(`${API_URL}/api/agent-builder/executions/*`, async (route) => {
        if (route.request().method() === 'GET') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              id: 'exec_123',
              agent_id: 'agent_123',
              status: 'success',
              steps: [
                {
                  type: 'llm_call',
                  content: 'Response from LLM',
                  duration_ms: 1200
                },
                {
                  type: 'tool_call',
                  tool_name: 'vector_search',
                  duration_ms: 300
                }
              ],
              metrics: {
                total_tokens: 500,
                prompt_tokens: 200,
                completion_tokens: 300
              }
            })
          });
        }
      });
      
      // Verify details are displayed
      await expect(page.locator('.execution-step')).toHaveCount(2);
      await expect(page.locator('text=Response from LLM')).toBeVisible();
      await expect(page.locator('text=vector_search')).toBeVisible();
      
      // Verify metrics
      await expect(page.locator('text=500 tokens')).toBeVisible();
    });
  });

  test.describe('Variables Manager', () => {
    
    test('should create and manage variables', async ({ page }) => {
      await page.goto(`${BASE_URL}/agent-builder/variables`);
      
      // Create variable
      await page.click('button:has-text("Create Variable")');
      await page.fill('input[name="name"]', 'API_KEY');
      await page.click('select[name="scope"]');
      await page.click('option[value="global"]');
      await page.fill('input[name="value"]', 'test-api-key-123');
      
      // Mark as secret
      await page.click('input[type="checkbox"][name="is_secret"]');
      
      await page.route(`${API_URL}/api/agent-builder/variables`, async (route) => {
        if (route.request().method() === 'POST') {
          await route.fulfill({
            status: 201,
            contentType: 'application/json',
            body: JSON.stringify({
              id: 'var_123',
              name: 'API_KEY',
              scope: 'global',
              is_secret: true
            })
          });
        }
      });
      
      await page.click('button[type="submit"]:has-text("Create")');
      
      // Verify variable appears in list
      await expect(page.locator('text=API_KEY')).toBeVisible();
      
      // Verify value is masked
      await expect(page.locator('text=••••••••')).toBeVisible();
    });
  });

  test.describe('Approvals (Human-in-the-Loop)', () => {
    
    test('should display pending approvals', async ({ page }) => {
      await page.goto(`${BASE_URL}/agent-builder/approvals`);
      
      // Mock pending approvals
      await page.route(`${API_URL}/api/agent-builder/approvals/pending`, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            pending_approvals: [
              {
                request_id: 'req_123',
                action: 'Deploy to production',
                priority: 'high',
                created_at: new Date().toISOString(),
                time_remaining_seconds: 3600
              }
            ]
          })
        });
      });
      
      await page.reload();
      
      // Verify approval request is displayed
      await expect(page.locator('text=Deploy to production')).toBeVisible();
      await expect(page.locator('.badge-high')).toBeVisible();
      
      // Click on request
      await page.click('.approval-request:first-child');
      
      // Verify details
      await expect(page.locator('text=Time remaining')).toBeVisible();
      
      // Approve
      await page.fill('textarea[name="comment"]', 'Looks good');
      
      await page.route(`${API_URL}/api/agent-builder/approvals/requests/*/approve`, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Request approved' })
        });
      });
      
      await page.click('button:has-text("Approve")');
      
      // Verify success
      await expect(page.locator('.toast')).toContainText('Request approved');
    });
  });

  test.describe('Performance', () => {
    
    test('should load agent list within 2 seconds', async ({ page }) => {
      const startTime = Date.now();
      
      await page.goto(`${BASE_URL}/agent-builder/agents`);
      await page.waitForSelector('.agent-card');
      
      const loadTime = Date.now() - startTime;
      expect(loadTime).toBeLessThan(2000);
    });

    test('should handle 100 agents without performance degradation', async ({ page }) => {
      // Mock large agent list
      const agents = Array.from({ length: 100 }, (_, i) => ({
        id: `agent_${i}`,
        name: `Agent ${i}`,
        description: `Description ${i}`
      }));
      
      await page.route(`${API_URL}/api/agent-builder/agents*`, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ agents, total: 100 })
        });
      });
      
      const startTime = Date.now();
      await page.goto(`${BASE_URL}/agent-builder/agents`);
      await page.waitForSelector('.agent-card');
      const loadTime = Date.now() - startTime;
      
      expect(loadTime).toBeLessThan(3000);
      
      // Verify virtual scrolling works
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await expect(page.locator('.agent-card')).toHaveCount(100);
    });
  });

  test.describe('Accessibility', () => {
    
    test('should be keyboard navigable', async ({ page }) => {
      await page.goto(`${BASE_URL}/agent-builder/agents`);
      
      // Tab through elements
      await page.keyboard.press('Tab');
      await expect(page.locator(':focus')).toBeVisible();
      
      // Navigate with arrow keys
      await page.keyboard.press('ArrowDown');
      await page.keyboard.press('Enter');
      
      // Verify navigation worked
      await expect(page).toHaveURL(/\/agent-builder\/agents\/.+/);
    });

    test('should have proper ARIA labels', async ({ page }) => {
      await page.goto(`${BASE_URL}/agent-builder/agents`);
      
      // Verify ARIA labels
      await expect(page.locator('[aria-label="Create new agent"]')).toBeVisible();
      await expect(page.locator('[role="navigation"]')).toBeVisible();
      await expect(page.locator('[role="main"]')).toBeVisible();
    });
  });
});
