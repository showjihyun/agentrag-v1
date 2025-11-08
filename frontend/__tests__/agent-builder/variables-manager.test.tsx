import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import VariablesManagerPage from '@/app/agent-builder/variables/page';
import { agentBuilderAPI } from '@/lib/api/agent-builder';

// Mock the API
vi.mock('@/lib/api/agent-builder', () => ({
  agentBuilderAPI: {
    getVariables: vi.fn(),
    createVariable: vi.fn(),
    updateVariable: vi.fn(),
    deleteVariable: vi.fn(),
    revealSecret: vi.fn(),
  },
}));

// Mock toast
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

describe('VariablesManagerPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Setup default mock responses
    (agentBuilderAPI.getVariables as any).mockResolvedValue([
      {
        id: 'var-1',
        name: 'API_KEY',
        scope: 'user',
        value_type: 'string',
        value: 'test-key',
        is_secret: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: 'var-2',
        name: 'SECRET_TOKEN',
        scope: 'global',
        value_type: 'string',
        value: '••••••••',
        is_secret: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]);
  });

  it('renders variables manager page', async () => {
    render(<VariablesManagerPage />);

    await waitFor(() => {
      expect(screen.getByText('Variables')).toBeInTheDocument();
    });

    expect(screen.getByText('Manage global variables and secrets')).toBeInTheDocument();
  });

  it('displays variables with different scopes', async () => {
    render(<VariablesManagerPage />);

    await waitFor(() => {
      expect(screen.getByText('API_KEY')).toBeInTheDocument();
    });

    expect(screen.getByText('SECRET_TOKEN')).toBeInTheDocument();
  });

  it('masks secret variable values', async () => {
    render(<VariablesManagerPage />);

    await waitFor(() => {
      expect(screen.getByText('SECRET_TOKEN')).toBeInTheDocument();
    });

    // Secret should be masked
    const maskedValues = screen.getAllByText('••••••••');
    expect(maskedValues.length).toBeGreaterThan(0);
  });

  it('shows create variable button', async () => {
    render(<VariablesManagerPage />);

    await waitFor(() => {
      const createButtons = screen.getAllByText('Create Variable');
      expect(createButtons.length).toBeGreaterThan(0);
    });
  });

  it('displays variable types as badges', async () => {
    render(<VariablesManagerPage />);

    await waitFor(() => {
      const stringBadges = screen.getAllByText('string');
      expect(stringBadges.length).toBeGreaterThan(0);
    });
  });
});
