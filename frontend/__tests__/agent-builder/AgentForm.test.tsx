import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AgentForm } from '@/components/agent-builder/AgentForm';
import { agentBuilderAPI } from '@/lib/api/agent-builder';

// Mock the API
jest.mock('@/lib/api/agent-builder');
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    back: jest.fn(),
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

describe('AgentForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render form fields', () => {
    render(<AgentForm />, { wrapper: createWrapper() });

    expect(screen.getByLabelText(/agent name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/llm provider/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/model/i)).toBeInTheDocument();
  });

  it('should validate required fields', async () => {
    const user = userEvent.setup();
    render(<AgentForm />, { wrapper: createWrapper() });

    const submitButton = screen.getByRole('button', { name: /create agent/i });
    await user.click(submitButton);

    expect(await screen.findByText(/name is required/i)).toBeInTheDocument();
  });

  it('should submit form with valid data', async () => {
    const user = userEvent.setup();
    const mockCreate = jest.fn().mockResolvedValue({
      id: '123',
      name: 'Test Agent',
    });
    (agentBuilderAPI.createAgent as jest.Mock) = mockCreate;

    const onSuccess = jest.fn();
    render(<AgentForm onSuccess={onSuccess} />, { wrapper: createWrapper() });

    // Fill form
    await user.type(screen.getByLabelText(/agent name/i), 'Test Agent');
    await user.type(screen.getByLabelText(/description/i), 'Test Description');

    // Submit
    const submitButton = screen.getByRole('button', { name: /create agent/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'Test Agent',
          description: 'Test Description',
        })
      );
    });
  });

  it('should handle API errors', async () => {
    const user = userEvent.setup();
    const mockCreate = jest.fn().mockRejectedValue(new Error('API Error'));
    (agentBuilderAPI.createAgent as jest.Mock) = mockCreate;

    render(<AgentForm />, { wrapper: createWrapper() });

    // Fill and submit form
    await user.type(screen.getByLabelText(/agent name/i), 'Test Agent');
    const submitButton = screen.getByRole('button', { name: /create agent/i });
    await user.click(submitButton);

    // Should show error toast (you may need to adjust based on your toast implementation)
    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalled();
    });
  });

  it('should populate form with initial data in edit mode', () => {
    const initialData = {
      name: 'Existing Agent',
      description: 'Existing Description',
      agent_type: 'custom',
      llm_provider: 'ollama',
      llm_model: 'llama3.1',
    };

    render(<AgentForm initialData={initialData} agentId="123" />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByDisplayValue('Existing Agent')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Existing Description')).toBeInTheDocument();
  });
});
