import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AgentBuilderDashboard from '@/app/agent-builder/page';
import { agentBuilderAPI } from '@/lib/api/agent-builder';

jest.mock('@/lib/api/agent-builder');
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('AgentBuilderDashboard', () => {
  const mockStats = {
    executions: {
      total: 100,
      last_24h: 10,
      success_rate: 95,
      running: 2,
      avg_duration_seconds: 5.5,
    },
    resources: {
      agents: 5,
      blocks: 10,
      workflows: 3,
    },
  };

  const mockActivity = {
    activities: [
      {
        id: '1',
        agent_name: 'Test Agent',
        status: 'completed',
        duration: 5,
        started_at: new Date().toISOString(),
      },
    ],
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (agentBuilderAPI.getDashboardStats as jest.Mock).mockResolvedValue(mockStats);
    (agentBuilderAPI.getRecentActivity as jest.Mock).mockResolvedValue(mockActivity);
    (agentBuilderAPI.getFavoriteAgents as jest.Mock).mockResolvedValue({ agents: [] });
    (agentBuilderAPI.getExecutionTrend as jest.Mock).mockResolvedValue({ trend: [] });
    (agentBuilderAPI.getSystemStatus as jest.Mock).mockResolvedValue({ status: 'ok' });
  });

  it('should render dashboard with stats', async () => {
    render(<AgentBuilderDashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Agent Builder Dashboard')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText('Total Executions')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
    });
  });

  it('should display success rate', async () => {
    render(<AgentBuilderDashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Success Rate')).toBeInTheDocument();
      expect(screen.getByText('95%')).toBeInTheDocument();
    });
  });

  it('should show recent activity', async () => {
    render(<AgentBuilderDashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Recent Activity')).toBeInTheDocument();
      expect(screen.getByText('Test Agent')).toBeInTheDocument();
    });
  });

  it('should display system warning when status is warning', async () => {
    (agentBuilderAPI.getSystemStatus as jest.Mock).mockResolvedValue({
      status: 'warning',
      stuck_executions: 2,
    });

    render(<AgentBuilderDashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/2 execution\(s\) have been running/i)).toBeInTheDocument();
    });
  });

  it('should handle API errors gracefully', async () => {
    (agentBuilderAPI.getDashboardStats as jest.Mock).mockRejectedValue(
      new Error('API Error')
    );

    render(<AgentBuilderDashboard />, { wrapper: createWrapper() });

    // Should show loading state and not crash
    expect(screen.getByText('Agent Builder Dashboard')).toBeInTheDocument();
  });

  it('should refresh stats on interval', async () => {
    jest.useFakeTimers();
    render(<AgentBuilderDashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(agentBuilderAPI.getDashboardStats).toHaveBeenCalledTimes(1);
    });

    // Fast-forward 30 seconds
    jest.advanceTimersByTime(30000);

    await waitFor(() => {
      expect(agentBuilderAPI.getDashboardStats).toHaveBeenCalledTimes(2);
    });

    jest.useRealTimers();
  });
});
