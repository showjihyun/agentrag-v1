import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ExecutionMonitorPage from '@/app/agent-builder/executions/page';
import { agentBuilderAPI } from '@/lib/api/agent-builder';

// Mock the API
vi.mock('@/lib/api/agent-builder', () => ({
  agentBuilderAPI: {
    getExecutions: vi.fn(),
    getExecutionStats: vi.fn(),
    getAgents: vi.fn(),
    cancelExecution: vi.fn(),
    replayExecution: vi.fn(),
  },
}));

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

// Mock toast
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

describe('ExecutionMonitorPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mock responses
    (agentBuilderAPI.getExecutions as any).mockResolvedValue({
      executions: [
        {
          id: 'exec-1',
          agent_id: 'agent-1',
          agent_name: 'Test Agent',
          user_id: 'user-1',
          status: 'completed',
          duration_ms: 1500,
          started_at: new Date().toISOString(),
        },
      ],
      total: 1,
    });

    (agentBuilderAPI.getExecutionStats as any).mockResolvedValue({
      active: 2,
      total: 100,
      successRate: 95,
      avgDuration: 2.5,
    });

    (agentBuilderAPI.getAgents as any).mockResolvedValue({
      agents: [
        {
          id: 'agent-1',
          name: 'Test Agent',
          agent_type: 'custom',
          llm_provider: 'ollama',
          llm_model: 'llama3.1',
        },
      ],
      total: 1,
    });
  });

  it('renders execution monitor page with stats', async () => {
    render(<ExecutionMonitorPage />);

    await waitFor(() => {
      expect(screen.getByText('Execution Monitor')).toBeInTheDocument();
    });

    // Check stats cards are rendered
    expect(screen.getByText('Active Executions')).toBeInTheDocument();
    expect(screen.getByText('Success Rate')).toBeInTheDocument();
    expect(screen.getByText('Avg Duration')).toBeInTheDocument();
    expect(screen.getByText('Total Executions')).toBeInTheDocument();
  });

  it('displays execution list with filtering', async () => {
    render(<ExecutionMonitorPage />);

    await waitFor(() => {
      expect(screen.getByText('Recent Executions')).toBeInTheDocument();
    });

    // Check filters are present
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Agent')).toBeInTheDocument();
    expect(screen.getByText('Time Range')).toBeInTheDocument();
  });

  it('shows execution data in table', async () => {
    render(<ExecutionMonitorPage />);

    await waitFor(() => {
      expect(screen.getByText('Test Agent')).toBeInTheDocument();
    });

    // Check execution details are displayed
    expect(screen.getByText('completed')).toBeInTheDocument();
  });
});
