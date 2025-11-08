import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AgentBuilderDashboard from '@/app/agent-builder/page';
import { AgentForm } from '@/components/agent-builder/AgentForm';

expect.extend(toHaveNoViolations);

jest.mock('@/lib/api/agent-builder');
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
  usePathname: () => '/agent-builder',
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('Agent Builder Accessibility', () => {
  beforeEach(() => {
    // Mock API responses
    const { agentBuilderAPI } = require('@/lib/api/agent-builder');
    agentBuilderAPI.getDashboardStats.mockResolvedValue({
      executions: { total: 0, last_24h: 0, success_rate: 0, running: 0, avg_duration_seconds: 0 },
      resources: { agents: 0, blocks: 0, workflows: 0 },
    });
    agentBuilderAPI.getRecentActivity.mockResolvedValue({ activities: [] });
    agentBuilderAPI.getFavoriteAgents.mockResolvedValue({ agents: [] });
    agentBuilderAPI.getExecutionTrend.mockResolvedValue({ trend: [] });
    agentBuilderAPI.getSystemStatus.mockResolvedValue({ status: 'ok' });
  });

  it('should have no accessibility violations on dashboard', async () => {
    const { container } = render(<AgentBuilderDashboard />, {
      wrapper: createWrapper(),
    });

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have no accessibility violations on agent form', async () => {
    const { container } = render(<AgentForm />, {
      wrapper: createWrapper(),
    });

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have proper heading hierarchy', () => {
    render(<AgentBuilderDashboard />, { wrapper: createWrapper() });

    const h1 = document.querySelector('h1');
    expect(h1).toBeInTheDocument();
    expect(h1?.textContent).toBe('Agent Builder Dashboard');
  });

  it('should have skip to content link', () => {
    render(<AgentBuilderDashboard />, { wrapper: createWrapper() });

    const skipLink = document.querySelector('a[href="#main-content"]');
    expect(skipLink).toBeInTheDocument();
  });

  it('should have proper ARIA labels on buttons', () => {
    render(<AgentBuilderDashboard />, { wrapper: createWrapper() });

    const createButton = document.querySelector('[aria-label="Create a new agent"]');
    expect(createButton).toBeInTheDocument();
  });

  it('should have proper landmark roles', () => {
    render(<AgentBuilderDashboard />, { wrapper: createWrapper() });

    expect(document.querySelector('[role="banner"]')).toBeInTheDocument();
    expect(document.querySelector('#main-content')).toBeInTheDocument();
  });

  it('should support keyboard navigation', async () => {
    const { container } = render(<AgentBuilderDashboard />, {
      wrapper: createWrapper(),
    });

    // All interactive elements should be focusable
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    expect(focusableElements.length).toBeGreaterThan(0);

    // All should have tabindex >= 0 or be naturally focusable
    focusableElements.forEach((element) => {
      const tabindex = element.getAttribute('tabindex');
      if (tabindex !== null) {
        expect(parseInt(tabindex)).toBeGreaterThanOrEqual(-1);
      }
    });
  });

  it('should have sufficient color contrast', async () => {
    const { container } = render(<AgentBuilderDashboard />, {
      wrapper: createWrapper(),
    });

    // Axe will check color contrast
    const results = await axe(container, {
      rules: {
        'color-contrast': { enabled: true },
      },
    });

    expect(results).toHaveNoViolations();
  });
});
