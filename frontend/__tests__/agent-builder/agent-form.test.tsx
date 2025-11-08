import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { AgentForm } from '@/components/agent-builder/AgentForm';
import { agentBuilderAPI } from '@/lib/api/agent-builder';

// Mock the API
jest.mock('@/lib/api/agent-builder', () => ({
  agentBuilderAPI: {
    createAgent: jest.fn(),
    updateAgent: jest.fn(),
    listTools: jest.fn(),
  },
}));

// Mock toast
jest.mock('@/components/ui/toast', () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}));

// Mock router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    back: jest.fn(),
  }),
}));

describe('AgentForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (agentBuilderAPI.listTools as jest.Mock).mockResolvedValue([
      {
        id: 'tool1',
        name: 'Vector Search',
        category: 'search',
        description: 'Search documents',
      },
      {
        id: 'tool2',
        name: 'Web Search',
        category: 'search',
        description: 'Search the web',
      },
    ]);
  });

  describe('Validation', () => {
    it('should show validation error when name is empty', async () => {
      render(<AgentForm mode="create" />);

      const submitButton = screen.getByRole('button', { name: /create agent/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/name is required/i)).toBeInTheDocument();
      });
    });

    it('should show validation error when name is too short', async () => {
      render(<AgentForm mode="create" />);

      const nameInput = screen.getByLabelText(/agent name/i);
      fireEvent.change(nameInput, { target: { value: 'ab' } });

      const submitButton = screen.getByRole('button', { name: /create agent/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/name must be at least 3 characters/i)).toBeInTheDocument();
      });
    });

    it('should show validation error when LLM provider is not selected', async () => {
      render(<AgentForm mode="create" />);

      const nameInput = screen.getByLabelText(/agent name/i);
      fireEvent.change(nameInput, { target: { value: 'Test Agent' } });

      const submitButton = screen.getByRole('button', { name: /create agent/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/llm provider is required/i)).toBeInTheDocument();
      });
    });

    it('should show validation error when prompt template is empty', async () => {
      render(<AgentForm mode="create" />);

      const nameInput = screen.getByLabelText(/agent name/i);
      fireEvent.change(nameInput, { target: { value: 'Test Agent' } });

      const submitButton = screen.getByRole('button', { name: /create agent/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/prompt template is required/i)).toBeInTheDocument();
      });
    });
  });

  describe('Form Submission', () => {
    it('should successfully create agent with valid data', async () => {
      const mockAgent = {
        id: 'agent1',
        name: 'Test Agent',
        description: 'Test description',
        agent_type: 'custom',
        llm_provider: 'ollama',
        llm_model: 'llama3.1',
      };

      (agentBuilderAPI.createAgent as jest.Mock).mockResolvedValue(mockAgent);

      render(<AgentForm mode="create" />);

      // Fill in form
      const nameInput = screen.getByLabelText(/agent name/i);
      fireEvent.change(nameInput, { target: { value: 'Test Agent' } });

      const descriptionInput = screen.getByLabelText(/description/i);
      fireEvent.change(descriptionInput, { target: { value: 'Test description' } });

      // Submit form
      const submitButton = screen.getByRole('button', { name: /create agent/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(agentBuilderAPI.createAgent).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'Test Agent',
            description: 'Test description',
          })
        );
      });
    });

    it('should handle API errors gracefully', async () => {
      (agentBuilderAPI.createAgent as jest.Mock).mockRejectedValue(
        new Error('API Error')
      );

      render(<AgentForm mode="create" />);

      // Fill in form
      const nameInput = screen.getByLabelText(/agent name/i);
      fireEvent.change(nameInput, { target: { value: 'Test Agent' } });

      // Submit form
      const submitButton = screen.getByRole('button', { name: /create agent/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/failed to create agent/i)).toBeInTheDocument();
      });
    });
  });

  describe('Tool Selection', () => {
    it('should load and display available tools', async () => {
      render(<AgentForm mode="create" />);

      await waitFor(() => {
        expect(screen.getByText('Vector Search')).toBeInTheDocument();
        expect(screen.getByText('Web Search')).toBeInTheDocument();
      });
    });

    it('should allow selecting and deselecting tools', async () => {
      render(<AgentForm mode="create" />);

      await waitFor(() => {
        const vectorSearchToggle = screen.getByRole('switch', { name: /vector search/i });
        expect(vectorSearchToggle).not.toBeChecked();

        fireEvent.click(vectorSearchToggle);
        expect(vectorSearchToggle).toBeChecked();

        fireEvent.click(vectorSearchToggle);
        expect(vectorSearchToggle).not.toBeChecked();
      });
    });
  });

  describe('Edit Mode', () => {
    it('should populate form with existing agent data', async () => {
      const existingAgent = {
        id: 'agent1',
        name: 'Existing Agent',
        description: 'Existing description',
        agent_type: 'custom',
        llm_provider: 'ollama',
        llm_model: 'llama3.1',
        tools: ['tool1'],
      };

      render(<AgentForm mode="edit" agent={existingAgent} />);

      await waitFor(() => {
        const nameInput = screen.getByLabelText(/agent name/i) as HTMLInputElement;
        expect(nameInput.value).toBe('Existing Agent');

        const descriptionInput = screen.getByLabelText(/description/i) as HTMLTextAreaElement;
        expect(descriptionInput.value).toBe('Existing description');
      });
    });

    it('should call updateAgent API when editing', async () => {
      const existingAgent = {
        id: 'agent1',
        name: 'Existing Agent',
        description: 'Existing description',
        agent_type: 'custom',
        llm_provider: 'ollama',
        llm_model: 'llama3.1',
      };

      (agentBuilderAPI.updateAgent as jest.Mock).mockResolvedValue(existingAgent);

      render(<AgentForm mode="edit" agent={existingAgent} />);

      const nameInput = screen.getByLabelText(/agent name/i);
      fireEvent.change(nameInput, { target: { value: 'Updated Agent' } });

      const submitButton = screen.getByRole('button', { name: /update agent/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(agentBuilderAPI.updateAgent).toHaveBeenCalledWith(
          'agent1',
          expect.objectContaining({
            name: 'Updated Agent',
          })
        );
      });
    });
  });

  describe('Prompt Template', () => {
    it('should validate prompt template is not empty', async () => {
      render(<AgentForm mode="create" />);

      const nameInput = screen.getByLabelText(/agent name/i);
      fireEvent.change(nameInput, { target: { value: 'Test Agent' } });

      const promptInput = screen.getByLabelText(/prompt template/i);
      fireEvent.change(promptInput, { target: { value: '' } });

      const submitButton = screen.getByRole('button', { name: /create agent/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/prompt template is required/i)).toBeInTheDocument();
      });
    });

    it('should accept valid prompt template with variables', async () => {
      render(<AgentForm mode="create" />);

      const promptInput = screen.getByLabelText(/prompt template/i);
      fireEvent.change(promptInput, {
        target: { value: 'Answer the question: ${query}' },
      });

      // Should not show validation error
      await waitFor(() => {
        expect(screen.queryByText(/prompt template is required/i)).not.toBeInTheDocument();
      });
    });
  });
});
