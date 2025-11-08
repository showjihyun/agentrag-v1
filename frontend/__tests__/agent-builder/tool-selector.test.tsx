import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ToolSelector } from '@/components/agent-builder/ToolSelector';
import { agentBuilderAPI } from '@/lib/api/agent-builder';

// Mock the API
jest.mock('@/lib/api/agent-builder', () => ({
  agentBuilderAPI: {
    listTools: jest.fn(),
  },
}));

const mockTools = [
  {
    id: 'tool1',
    name: 'Vector Search',
    category: 'search',
    description: 'Search documents using semantic similarity',
    input_schema: { type: 'object' },
    output_schema: { type: 'object' },
  },
  {
    id: 'tool2',
    name: 'Web Search',
    category: 'search',
    description: 'Search the web using DuckDuckGo',
    input_schema: { type: 'object' },
    output_schema: { type: 'object' },
  },
  {
    id: 'tool3',
    name: 'Database Query',
    category: 'database',
    description: 'Execute SQL queries',
    input_schema: { type: 'object' },
    output_schema: { type: 'object' },
  },
  {
    id: 'tool4',
    name: 'HTTP API Call',
    category: 'api',
    description: 'Make HTTP requests to external APIs',
    input_schema: { type: 'object' },
    output_schema: { type: 'object' },
  },
];

describe('ToolSelector', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (agentBuilderAPI.listTools as jest.Mock).mockResolvedValue(mockTools);
  });

  describe('Tool Loading', () => {
    it('should load and display tools', async () => {
      render(<ToolSelector selectedTools={[]} onToolsChange={jest.fn()} />);

      await waitFor(() => {
        expect(screen.getByText('Vector Search')).toBeInTheDocument();
        expect(screen.getByText('Web Search')).toBeInTheDocument();
        expect(screen.getByText('Database Query')).toBeInTheDocument();
        expect(screen.getByText('HTTP API Call')).toBeInTheDocument();
      });
    });

    it('should show loading state while fetching tools', () => {
      render(<ToolSelector selectedTools={[]} onToolsChange={jest.fn()} />);

      expect(screen.getByText(/loading tools/i)).toBeInTheDocument();
    });

    it('should handle API errors gracefully', async () => {
      (agentBuilderAPI.listTools as jest.Mock).mockRejectedValue(
        new Error('Failed to load tools')
      );

      render(<ToolSelector selectedTools={[]} onToolsChange={jest.fn()} />);

      await waitFor(() => {
        expect(screen.getByText(/failed to load tools/i)).toBeInTheDocument();
      });
    });
  });

  describe('Tool Selection', () => {
    it('should allow selecting a tool', async () => {
      const onToolsChange = jest.fn();
      render(<ToolSelector selectedTools={[]} onToolsChange={onToolsChange} />);

      await waitFor(() => {
        const vectorSearchToggle = screen.getByRole('switch', { name: /vector search/i });
        fireEvent.click(vectorSearchToggle);
      });

      expect(onToolsChange).toHaveBeenCalledWith(['tool1']);
    });

    it('should allow deselecting a tool', async () => {
      const onToolsChange = jest.fn();
      render(<ToolSelector selectedTools={['tool1']} onToolsChange={onToolsChange} />);

      await waitFor(() => {
        const vectorSearchToggle = screen.getByRole('switch', { name: /vector search/i });
        expect(vectorSearchToggle).toBeChecked();

        fireEvent.click(vectorSearchToggle);
      });

      expect(onToolsChange).toHaveBeenCalledWith([]);
    });

    it('should allow selecting multiple tools', async () => {
      const onToolsChange = jest.fn();
      render(<ToolSelector selectedTools={[]} onToolsChange={onToolsChange} />);

      await waitFor(async () => {
        const vectorSearchToggle = screen.getByRole('switch', { name: /vector search/i });
        fireEvent.click(vectorSearchToggle);

        await waitFor(() => {
          expect(onToolsChange).toHaveBeenCalledWith(['tool1']);
        });

        const webSearchToggle = screen.getByRole('switch', { name: /web search/i });
        fireEvent.click(webSearchToggle);

        await waitFor(() => {
          expect(onToolsChange).toHaveBeenCalledWith(['tool1', 'tool2']);
        });
      });
    });

    it('should show selected tools as checked', async () => {
      render(<ToolSelector selectedTools={['tool1', 'tool3']} onToolsChange={jest.fn()} />);

      await waitFor(() => {
        const vectorSearchToggle = screen.getByRole('switch', { name: /vector search/i });
        expect(vectorSearchToggle).toBeChecked();

        const databaseQueryToggle = screen.getByRole('switch', { name: /database query/i });
        expect(databaseQueryToggle).toBeChecked();

        const webSearchToggle = screen.getByRole('switch', { name: /web search/i });
        expect(webSearchToggle).not.toBeChecked();
      });
    });
  });

  describe('Tool Search', () => {
    it('should filter tools by search query', async () => {
      render(<ToolSelector selectedTools={[]} onToolsChange={jest.fn()} />);

      await waitFor(() => {
        expect(screen.getByText('Vector Search')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/search tools/i);
      fireEvent.change(searchInput, { target: { value: 'vector' } });

      await waitFor(() => {
        expect(screen.getByText('Vector Search')).toBeInTheDocument();
        expect(screen.queryByText('Web Search')).not.toBeInTheDocument();
        expect(screen.queryByText('Database Query')).not.toBeInTheDocument();
      });
    });

    it('should show no results message when search has no matches', async () => {
      render(<ToolSelector selectedTools={[]} onToolsChange={jest.fn()} />);

      await waitFor(() => {
        expect(screen.getByText('Vector Search')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/search tools/i);
      fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

      await waitFor(() => {
        expect(screen.getByText(/no tools found/i)).toBeInTheDocument();
      });
    });

    it('should search in tool names and descriptions', async () => {
      render(<ToolSelector selectedTools={[]} onToolsChange={jest.fn()} />);

      await waitFor(() => {
        expect(screen.getByText('Vector Search')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/search tools/i);
      fireEvent.change(searchInput, { target: { value: 'semantic' } });

      await waitFor(() => {
        expect(screen.getByText('Vector Search')).toBeInTheDocument();
        expect(screen.queryByText('Web Search')).not.toBeInTheDocument();
      });
    });
  });

  describe('Category Filtering', () => {
    it('should filter tools by category', async () => {
      render(<ToolSelector selectedTools={[]} onToolsChange={jest.fn()} />);

      await waitFor(() => {
        expect(screen.getByText('Vector Search')).toBeInTheDocument();
      });

      const categoryFilter = screen.getByRole('combobox', { name: /category/i });
      fireEvent.change(categoryFilter, { target: { value: 'database' } });

      await waitFor(() => {
        expect(screen.getByText('Database Query')).toBeInTheDocument();
        expect(screen.queryByText('Vector Search')).not.toBeInTheDocument();
        expect(screen.queryByText('Web Search')).not.toBeInTheDocument();
      });
    });

    it('should show all tools when "All" category is selected', async () => {
      render(<ToolSelector selectedTools={[]} onToolsChange={jest.fn()} />);

      await waitFor(() => {
        expect(screen.getByText('Vector Search')).toBeInTheDocument();
      });

      const categoryFilter = screen.getByRole('combobox', { name: /category/i });
      fireEvent.change(categoryFilter, { target: { value: 'all' } });

      await waitFor(() => {
        expect(screen.getByText('Vector Search')).toBeInTheDocument();
        expect(screen.getByText('Web Search')).toBeInTheDocument();
        expect(screen.getByText('Database Query')).toBeInTheDocument();
        expect(screen.getByText('HTTP API Call')).toBeInTheDocument();
      });
    });

    it('should combine search and category filters', async () => {
      render(<ToolSelector selectedTools={[]} onToolsChange={jest.fn()} />);

      await waitFor(() => {
        expect(screen.getByText('Vector Search')).toBeInTheDocument();
      });

      const categoryFilter = screen.getByRole('combobox', { name: /category/i });
      fireEvent.change(categoryFilter, { target: { value: 'search' } });

      const searchInput = screen.getByPlaceholderText(/search tools/i);
      fireEvent.change(searchInput, { target: { value: 'web' } });

      await waitFor(() => {
        expect(screen.getByText('Web Search')).toBeInTheDocument();
        expect(screen.queryByText('Vector Search')).not.toBeInTheDocument();
        expect(screen.queryByText('Database Query')).not.toBeInTheDocument();
      });
    });
  });

  describe('Tool Details', () => {
    it('should display tool descriptions', async () => {
      render(<ToolSelector selectedTools={[]} onToolsChange={jest.fn()} />);

      await waitFor(() => {
        expect(screen.getByText('Search documents using semantic similarity')).toBeInTheDocument();
        expect(screen.getByText('Search the web using DuckDuckGo')).toBeInTheDocument();
      });
    });

    it('should display tool categories as badges', async () => {
      render(<ToolSelector selectedTools={[]} onToolsChange={jest.fn()} />);

      await waitFor(() => {
        const searchBadges = screen.getAllByText('search');
        expect(searchBadges.length).toBeGreaterThan(0);

        expect(screen.getByText('database')).toBeInTheDocument();
        expect(screen.getByText('api')).toBeInTheDocument();
      });
    });
  });

  describe('Tool Configuration', () => {
    it('should open configuration dialog when clicking configure button', async () => {
      render(<ToolSelector selectedTools={['tool1']} onToolsChange={jest.fn()} />);

      await waitFor(() => {
        const configureButton = screen.getByRole('button', { name: /configure vector search/i });
        fireEvent.click(configureButton);
      });

      expect(screen.getByText(/tool configuration/i)).toBeInTheDocument();
    });

    it('should only show configure button for selected tools', async () => {
      render(<ToolSelector selectedTools={['tool1']} onToolsChange={jest.fn()} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /configure vector search/i })).toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /configure web search/i })).not.toBeInTheDocument();
      });
    });
  });
});
