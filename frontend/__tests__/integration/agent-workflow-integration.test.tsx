/**
 * Integration tests for Agent Builder workflow
 * Tests the complete user journey from agent creation to execution
 */

import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AgentDashboard from '@/app/agent-builder/page';
import { api } from '@/lib/api/agent-builder';

// Mock API
jest.mock('@/lib/api/agent-builder');

const mockApi = api as jest.Mocked<typeof api>;

describe('Agent Builder Integration Tests', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    jest.clearAllMocks();
  });

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    );
  };

  describe('Complete Agent Creation Flow', () => {
    it('should create agent, add blocks, and execute workflow', async () => {
      const user = userEvent.setup();

      // Mock API responses
      mockApi.getAgents.mockResolvedValue({
        agents: [],
        total: 0,
        page: 1,
        page_size: 10,
      });

      mockApi.createAgent.mockResolvedValue({
        id: 'agent-1',
        name: 'Test Agent',
        description: 'Test description',
        llm_provider: 'openai',
        llm_model: 'gpt-4',
        tools: [],
        prompt_template: 'Test prompt',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });

      mockApi.getBlocks.mockResolvedValue({
        blocks: [
          {
            id: 'block-1',
            name: 'Vector Search',
            type: 'tool',
            category: 'search',
            description: 'Search documents',
            config_schema: {},
            created_at: new Date().toISOString(),
          },
        ],
        total: 1,
      });

      mockApi.executeAgent.mockResolvedValue({
        execution_id: 'exec-1',
        status: 'completed',
        result: { answer: 'Test result' },
        duration_ms: 1000,
      });

      // Render dashboard
      renderWithProviders(<AgentDashboard />);

      // Step 1: Create new agent
      const createButton = await screen.findByRole('button', { name: /create agent/i });
      await user.click(createButton);

      // Fill agent form
      const nameInput = screen.getByLabelText(/agent name/i);
      await user.type(nameInput, 'Test Agent');

      const descInput = screen.getByLabelText(/description/i);
      await user.type(descInput, 'Test description');

      const providerSelect = screen.getByLabelText(/llm provider/i);
      await user.selectOptions(providerSelect, 'openai');

      const modelSelect = screen.getByLabelText(/model/i);
      await user.selectOptions(modelSelect, 'gpt-4');

      // Submit form
      const submitButton = screen.getByRole('button', { name: /create/i });
      await user.click(submitButton);

      // Step 2: Verify agent created
      await waitFor(() => {
        expect(mockApi.createAgent).toHaveBeenCalledWith({
          name: 'Test Agent',
          description: 'Test description',
          llm_provider: 'openai',
          llm_model: 'gpt-4',
          tools: [],
          prompt_template: expect.any(String),
        });
      });

      // Step 3: Add blocks to agent
      const agentCard = await screen.findByText('Test Agent');
      await user.click(agentCard);

      const addBlockButton = screen.getByRole('button', { name: /add block/i });
      await user.click(addBlockButton);

      // Select block from palette
      const vectorSearchBlock = await screen.findByText('Vector Search');
      await user.click(vectorSearchBlock);

      // Step 4: Execute agent
      const executeButton = screen.getByRole('button', { name: /execute/i });
      await user.click(executeButton);

      const inputField = screen.getByPlaceholderText(/enter your query/i);
      await user.type(inputField, 'Test query');

      const runButton = screen.getByRole('button', { name: /run/i });
      await user.click(runButton);

      // Step 5: Verify execution
      await waitFor(() => {
        expect(mockApi.executeAgent).toHaveBeenCalledWith('agent-1', {
          input: 'Test query',
        });
      });

      // Verify result displayed
      const result = await screen.findByText(/test result/i);
      expect(result).toBeInTheDocument();
    });
  });

  describe('Workflow Creation and Execution', () => {
    it('should create workflow with multiple blocks and execute', async () => {
      const user = userEvent.setup();

      mockApi.getWorkflows.mockResolvedValue({
        workflows: [],
        total: 0,
      });

      mockApi.createWorkflow.mockResolvedValue({
        id: 'workflow-1',
        name: 'Test Workflow',
        description: 'Test workflow',
        nodes: [],
        edges: [],
        created_at: new Date().toISOString(),
      });

      mockApi.executeWorkflow.mockResolvedValue({
        execution_id: 'exec-1',
        status: 'completed',
        result: {},
        duration_ms: 2000,
      });

      renderWithProviders(<AgentDashboard />);

      // Navigate to workflows
      const workflowsTab = screen.getByRole('tab', { name: /workflows/i });
      await user.click(workflowsTab);

      // Create workflow
      const createButton = screen.getByRole('button', { name: /create workflow/i });
      await user.click(createButton);

      // Add workflow details
      const nameInput = screen.getByLabelText(/workflow name/i);
      await user.type(nameInput, 'Test Workflow');

      // Save workflow
      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(mockApi.createWorkflow).toHaveBeenCalled();
      });

      // Execute workflow
      const executeButton = screen.getByRole('button', { name: /execute/i });
      await user.click(executeButton);

      await waitFor(() => {
        expect(mockApi.executeWorkflow).toHaveBeenCalledWith('workflow-1', {});
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      const user = userEvent.setup();

      mockApi.getAgents.mockRejectedValue(new Error('Network error'));

      renderWithProviders(<AgentDashboard />);

      // Should show error message
      const errorMessage = await screen.findByText(/failed to load/i);
      expect(errorMessage).toBeInTheDocument();

      // Should show retry button
      const retryButton = screen.getByRole('button', { name: /retry/i });
      expect(retryButton).toBeInTheDocument();

      // Retry should work
      mockApi.getAgents.mockResolvedValue({
        agents: [],
        total: 0,
        page: 1,
        page_size: 10,
      });

      await user.click(retryButton);

      await waitFor(() => {
        expect(mockApi.getAgents).toHaveBeenCalledTimes(2);
      });
    });

    it('should handle validation errors', async () => {
      const user = userEvent.setup();

      mockApi.createAgent.mockRejectedValue({
        response: {
          data: {
            detail: 'Agent name already exists',
          },
        },
      });

      renderWithProviders(<AgentDashboard />);

      const createButton = await screen.findByRole('button', { name: /create agent/i });
      await user.click(createButton);

      const submitButton = screen.getByRole('button', { name: /create/i });
      await user.click(submitButton);

      const errorMessage = await screen.findByText(/agent name already exists/i);
      expect(errorMessage).toBeInTheDocument();
    });
  });

  describe('Real-time Updates', () => {
    it('should update execution status in real-time', async () => {
      const user = userEvent.setup();

      mockApi.getExecutions.mockResolvedValue({
        executions: [
          {
            id: 'exec-1',
            agent_id: 'agent-1',
            status: 'running',
            created_at: new Date().toISOString(),
          },
        ],
        total: 1,
      });

      renderWithProviders(<AgentDashboard />);

      // Navigate to executions
      const executionsTab = screen.getByRole('tab', { name: /executions/i });
      await user.click(executionsTab);

      // Should show running status
      const runningStatus = await screen.findByText(/running/i);
      expect(runningStatus).toBeInTheDocument();

      // Simulate status update
      mockApi.getExecutions.mockResolvedValue({
        executions: [
          {
            id: 'exec-1',
            agent_id: 'agent-1',
            status: 'completed',
            created_at: new Date().toISOString(),
          },
        ],
        total: 1,
      });

      // Wait for auto-refresh
      await waitFor(
        () => {
          const completedStatus = screen.getByText(/completed/i);
          expect(completedStatus).toBeInTheDocument();
        },
        { timeout: 6000 }
      );
    });
  });

  describe('Performance', () => {
    it('should handle large lists efficiently', async () => {
      const largeAgentList = Array.from({ length: 100 }, (_, i) => ({
        id: `agent-${i}`,
        name: `Agent ${i}`,
        description: `Description ${i}`,
        llm_provider: 'openai',
        llm_model: 'gpt-4',
        tools: [],
        prompt_template: 'Test',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }));

      mockApi.getAgents.mockResolvedValue({
        agents: largeAgentList,
        total: 100,
        page: 1,
        page_size: 100,
      });

      const startTime = performance.now();
      renderWithProviders(<AgentDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Agent 0')).toBeInTheDocument();
      });

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render in less than 2 seconds
      expect(renderTime).toBeLessThan(2000);
    });
  });
});
