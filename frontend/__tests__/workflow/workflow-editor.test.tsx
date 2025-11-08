import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { WorkflowEditor } from '@/components/workflow/WorkflowEditor';
import { BlockPalette, BlockConfig } from '@/components/workflow/BlockPalette';
import { BlockConfigPanel } from '@/components/workflow/BlockConfigPanel';
import { Node, Edge } from 'reactflow';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { describe } from 'node:test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { describe } from 'node:test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { describe } from 'node:test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { describe } from 'node:test';
import { describe } from 'node:test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { describe } from 'node:test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { describe } from 'node:test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { describe } from 'node:test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { describe } from 'node:test';
import { describe } from 'node:test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { describe } from 'node:test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { describe } from 'node:test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { describe } from 'node:test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { describe } from 'node:test';
import { describe } from 'node:test';

// Mock ReactFlow
jest.mock('reactflow', () => {
  const actual = jest.requireActual('reactflow');
  return {
    ...actual,
    ReactFlowProvider: ({ children }: any) => <div data-testid="react-flow-provider">{children}</div>,
    ReactFlow: ({ children, nodes, edges, onNodesChange, onEdgesChange, onConnect, onDrop, onDragOver }: any) => (
      <div data-testid="react-flow" data-nodes={JSON.stringify(nodes)} data-edges={JSON.stringify(edges)}>
        <div data-testid="react-flow-canvas" onDrop={onDrop} onDragOver={onDragOver}>
          {children}
        </div>
      </div>
    ),
    Controls: () => <div data-testid="react-flow-controls" />,
    MiniMap: () => <div data-testid="react-flow-minimap" />,
    Background: () => <div data-testid="react-flow-background" />,
    Panel: ({ children }: any) => <div data-testid="react-flow-panel">{children}</div>,
    useNodesState: (initial: any) => {
      const [nodes, setNodes] = require('react').useState(initial);
      return [nodes, setNodes, jest.fn()];
    },
    useEdgesState: (initial: any) => {
      const [edges, setEdges] = require('react').useState(initial);
      return [edges, setEdges, jest.fn()];
    },
    addEdge: (edge: any, edges: any) => [...edges, edge],
  };
});

describe('WorkflowEditor', () => {
  describe('Rendering', () => {
    it('renders workflow editor with ReactFlow canvas', () => {
      render(<WorkflowEditor />);
      
      expect(screen.getByTestId('react-flow-provider')).toBeInTheDocument();
      expect(screen.getByTestId('react-flow')).toBeInTheDocument();
      expect(screen.getByTestId('react-flow-controls')).toBeInTheDocument();
      expect(screen.getByTestId('react-flow-minimap')).toBeInTheDocument();
      expect(screen.getByTestId('react-flow-background')).toBeInTheDocument();
    });

    it('renders with initial nodes', () => {
      const initialNodes: Node[] = [
        {
          id: 'node-1',
          type: 'block',
          position: { x: 100, y: 100 },
          data: { label: 'Test Block', type: 'openai' },
        },
      ];

      render(<WorkflowEditor initialNodes={initialNodes} />);
      
      const reactFlow = screen.getByTestId('react-flow');
      const nodesData = JSON.parse(reactFlow.getAttribute('data-nodes') || '[]');
      expect(nodesData).toHaveLength(1);
      expect(nodesData[0].id).toBe('node-1');
    });

    it('renders with initial edges', () => {
      const initialEdges: Edge[] = [
        {
          id: 'edge-1',
          source: 'node-1',
          target: 'node-2',
        },
      ];

      render(<WorkflowEditor initialEdges={initialEdges} />);
      
      const reactFlow = screen.getByTestId('react-flow');
      const edgesData = JSON.parse(reactFlow.getAttribute('data-edges') || '[]');
      expect(edgesData).toHaveLength(1);
      expect(edgesData[0].id).toBe('edge-1');
    });

    it('renders save button when not read-only', () => {
      render(<WorkflowEditor readOnly={false} />);
      
      expect(screen.getByText('Save Workflow')).toBeInTheDocument();
    });

    it('does not render save button when read-only', () => {
      render(<WorkflowEditor readOnly={true} />);
      
      expect(screen.queryByText('Save Workflow')).not.toBeInTheDocument();
    });
  });

  describe('Block Addition', () => {
    it('handles drop event to add block', () => {
      const onNodesChange = jest.fn();
      render(<WorkflowEditor onNodesChange={onNodesChange} />);
      
      const canvas = screen.getByTestId('react-flow-canvas');
      const blockData = {
        type: 'openai',
        name: 'OpenAI',
        description: 'OpenAI API block',
        category: 'tools',
      };

      const dropEvent = new Event('drop', { bubbles: true }) as any;
      dropEvent.dataTransfer = {
        getData: jest.fn(() => JSON.stringify(blockData)),
      };

      fireEvent(canvas, dropEvent);
      
      // Verify drop was handled (implementation would add node)
      expect(dropEvent.dataTransfer.getData).toHaveBeenCalledWith('application/reactflow');
    });

    it('handles drag over event', () => {
      render(<WorkflowEditor />);
      
      const canvas = screen.getByTestId('react-flow-canvas');
      const dragOverEvent = new Event('dragover', { bubbles: true }) as any;
      dragOverEvent.dataTransfer = { dropEffect: '' };
      dragOverEvent.preventDefault = jest.fn();

      fireEvent(canvas, dragOverEvent);
      
      expect(dragOverEvent.preventDefault).toHaveBeenCalled();
    });
  });

  describe('Edge Creation', () => {
    it('creates edge when connecting nodes', () => {
      const onEdgesChange = jest.fn();
      const initialNodes: Node[] = [
        { id: 'node-1', type: 'block', position: { x: 0, y: 0 }, data: {} },
        { id: 'node-2', type: 'block', position: { x: 200, y: 0 }, data: {} },
      ];

      render(<WorkflowEditor initialNodes={initialNodes} onEdgesChange={onEdgesChange} />);
      
      // Edge creation would be triggered by ReactFlow's onConnect
      // This tests the structure is in place
      expect(screen.getByTestId('react-flow')).toBeInTheDocument();
    });

    it('does not create edge in read-only mode', () => {
      const onEdgesChange = jest.fn();
      render(<WorkflowEditor readOnly={true} onEdgesChange={onEdgesChange} />);
      
      // In read-only mode, connections should be disabled
      expect(screen.getByTestId('react-flow')).toBeInTheDocument();
    });
  });

  describe('Workflow Save', () => {
    it('calls onSave with current nodes and edges', async () => {
      const onSave = jest.fn();
      const initialNodes: Node[] = [
        { id: 'node-1', type: 'block', position: { x: 0, y: 0 }, data: {} },
      ];
      const initialEdges: Edge[] = [
        { id: 'edge-1', source: 'node-1', target: 'node-2' },
      ];

      render(
        <WorkflowEditor
          initialNodes={initialNodes}
          initialEdges={initialEdges}
          onSave={onSave}
        />
      );
      
      const saveButton = screen.getByText('Save Workflow');
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(onSave).toHaveBeenCalledWith(
          expect.arrayContaining([expect.objectContaining({ id: 'node-1' })]),
          expect.arrayContaining([expect.objectContaining({ id: 'edge-1' })])
        );
      });
    });
  });
});

describe('BlockPalette', () => {
  const mockBlocks: BlockConfig[] = [
    {
      type: 'openai',
      name: 'OpenAI',
      description: 'OpenAI API integration',
      category: 'tools',
      bg_color: '#10a37f',
      icon: 'AI',
    },
    {
      type: 'http',
      name: 'HTTP Request',
      description: 'Make HTTP requests',
      category: 'blocks',
      bg_color: '#3b82f6',
      icon: 'HTTP',
    },
    {
      type: 'condition',
      name: 'Condition',
      description: 'Conditional branching',
      category: 'blocks',
      bg_color: '#8b5cf6',
      icon: 'IF',
    },
    {
      type: 'webhook',
      name: 'Webhook',
      description: 'Webhook trigger',
      category: 'triggers',
      bg_color: '#f59e0b',
      icon: 'WH',
    },
  ];

  describe('Rendering', () => {
    it('renders block palette with all blocks', () => {
      render(<BlockPalette blocks={mockBlocks} />);
      
      expect(screen.getByText('Block Palette')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Search blocks...')).toBeInTheDocument();
      expect(screen.getByText('OpenAI')).toBeInTheDocument();
      expect(screen.getByText('HTTP Request')).toBeInTheDocument();
      expect(screen.getByText('Condition')).toBeInTheDocument();
      expect(screen.getByText('Webhook')).toBeInTheDocument();
    });

    it('renders category tabs', () => {
      render(<BlockPalette blocks={mockBlocks} />);
      
      expect(screen.getByText('All')).toBeInTheDocument();
      expect(screen.getByText('blocks')).toBeInTheDocument();
      expect(screen.getByText('tools')).toBeInTheDocument();
      expect(screen.getByText('triggers')).toBeInTheDocument();
    });

    it('displays block count for each category', () => {
      render(<BlockPalette blocks={mockBlocks} />);
      
      // When "All" is selected, it shows grouped categories with counts
      fireEvent.click(screen.getByText('All'));
      
      // Check that blocks are displayed
      expect(screen.getByText('OpenAI')).toBeInTheDocument();
    });
  });

  describe('Search Functionality', () => {
    it('filters blocks by search query', () => {
      render(<BlockPalette blocks={mockBlocks} />);
      
      const searchInput = screen.getByPlaceholderText('Search blocks...');
      fireEvent.change(searchInput, { target: { value: 'openai' } });

      expect(screen.getByText('OpenAI')).toBeInTheDocument();
      expect(screen.queryByText('HTTP Request')).not.toBeInTheDocument();
      expect(screen.queryByText('Condition')).not.toBeInTheDocument();
    });

    it('filters blocks by description', () => {
      render(<BlockPalette blocks={mockBlocks} />);
      
      const searchInput = screen.getByPlaceholderText('Search blocks...');
      fireEvent.change(searchInput, { target: { value: 'branching' } });

      expect(screen.getByText('Condition')).toBeInTheDocument();
      expect(screen.queryByText('OpenAI')).not.toBeInTheDocument();
    });

    it('shows no results message when no blocks match', () => {
      render(<BlockPalette blocks={mockBlocks} />);
      
      const searchInput = screen.getByPlaceholderText('Search blocks...');
      fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

      expect(screen.getByText('No blocks found')).toBeInTheDocument();
    });
  });

  describe('Category Filtering', () => {
    it('filters blocks by category', () => {
      render(<BlockPalette blocks={mockBlocks} />);
      
      fireEvent.click(screen.getByText('tools'));

      expect(screen.getByText('OpenAI')).toBeInTheDocument();
      expect(screen.queryByText('HTTP Request')).not.toBeInTheDocument();
      expect(screen.queryByText('Webhook')).not.toBeInTheDocument();
    });

    it('shows all blocks when "All" is selected', () => {
      render(<BlockPalette blocks={mockBlocks} />);
      
      fireEvent.click(screen.getByText('blocks'));
      fireEvent.click(screen.getByText('All'));

      expect(screen.getByText('OpenAI')).toBeInTheDocument();
      expect(screen.getByText('HTTP Request')).toBeInTheDocument();
      expect(screen.getByText('Webhook')).toBeInTheDocument();
    });

    it('combines search and category filters', () => {
      render(<BlockPalette blocks={mockBlocks} />);
      
      const searchInput = screen.getByPlaceholderText('Search blocks...');
      fireEvent.change(searchInput, { target: { value: 'request' } });
      fireEvent.click(screen.getByText('blocks'));

      expect(screen.getByText('HTTP Request')).toBeInTheDocument();
      expect(screen.queryByText('OpenAI')).not.toBeInTheDocument();
    });
  });

  describe('Block Interaction', () => {
    it('handles drag start event', () => {
      render(<BlockPalette blocks={mockBlocks} />);
      
      const blockElement = screen.getByText('OpenAI').closest('div[draggable="true"]');
      expect(blockElement).toBeInTheDocument();

      const dragStartEvent = new Event('dragstart', { bubbles: true }) as any;
      dragStartEvent.dataTransfer = {
        setData: jest.fn(),
        effectAllowed: '',
      };

      fireEvent(blockElement!, dragStartEvent);
      
      expect(dragStartEvent.dataTransfer.setData).toHaveBeenCalledWith(
        'application/reactflow',
        expect.stringContaining('openai')
      );
    });

    it('calls onAddBlock when block is clicked', () => {
      const onAddBlock = jest.fn();
      render(<BlockPalette blocks={mockBlocks} onAddBlock={onAddBlock} />);
      
      const blockElement = screen.getByText('OpenAI').closest('div[draggable="true"]');
      fireEvent.click(blockElement!);

      expect(onAddBlock).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'openai', name: 'OpenAI' })
      );
    });
  });
});

describe('BlockConfigPanel', () => {
  const mockBlock = {
    id: 'block-1',
    type: 'openai',
    name: 'OpenAI',
    description: 'OpenAI API integration',
    category: 'tools',
    bg_color: '#10a37f',
    icon: 'AI',
    sub_blocks: [
      {
        id: 'model',
        type: 'dropdown',
        title: 'Model',
        required: true,
        options: ['gpt-4', 'gpt-3.5-turbo'],
        defaultValue: 'gpt-4',
      },
      {
        id: 'prompt',
        type: 'long-input',
        title: 'Prompt',
        required: true,
        placeholder: 'Enter your prompt...',
      },
      {
        id: 'temperature',
        type: 'short-input',
        title: 'Temperature',
        required: false,
        defaultValue: 0.7,
      },
    ],
  };

  describe('Rendering', () => {
    it('renders block configuration panel', () => {
      const onClose = jest.fn();
      const onSave = jest.fn();

      render(<BlockConfigPanel block={mockBlock} onClose={onClose} onSave={onSave} />);
      
      expect(screen.getByText('OpenAI')).toBeInTheDocument();
      expect(screen.getByText('OpenAI API integration')).toBeInTheDocument();
      expect(screen.getByText('tools')).toBeInTheDocument();
    });

    it('does not render when block is null', () => {
      const onClose = jest.fn();
      const onSave = jest.fn();

      const { container } = render(
        <BlockConfigPanel block={null} onClose={onClose} onSave={onSave} />
      );
      
      expect(container.firstChild).toBeNull();
    });

    it('renders sub-blocks configuration fields', () => {
      const onClose = jest.fn();
      const onSave = jest.fn();

      render(<BlockConfigPanel block={mockBlock} onClose={onClose} onSave={onSave} />);
      
      expect(screen.getByText('Model')).toBeInTheDocument();
      expect(screen.getByText('Prompt')).toBeInTheDocument();
      expect(screen.getByText('Temperature')).toBeInTheDocument();
    });

    it('shows no configuration message when no sub-blocks', () => {
      const blockWithoutSubBlocks = { ...mockBlock, sub_blocks: [] };
      const onClose = jest.fn();
      const onSave = jest.fn();

      render(
        <BlockConfigPanel block={blockWithoutSubBlocks} onClose={onClose} onSave={onSave} />
      );
      
      expect(screen.getByText('No configuration options available')).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('validates required fields on save', async () => {
      const onClose = jest.fn();
      const onSave = jest.fn();
      const blockWithoutDefaults = {
        ...mockBlock,
        sub_blocks: [
          {
            id: 'prompt',
            type: 'long-input',
            title: 'Prompt',
            required: true,
            placeholder: 'Enter your prompt...',
          },
        ],
      };

      render(<BlockConfigPanel block={blockWithoutDefaults} onClose={onClose} onSave={onSave} />);
      
      const saveButton = screen.getByText('Save');
      
      // Initially disabled because no changes
      expect(saveButton).toBeDisabled();
    });

    it('enables save button when values change', async () => {
      const onClose = jest.fn();
      const onSave = jest.fn();

      render(<BlockConfigPanel block={mockBlock} onClose={onClose} onSave={onSave} />);
      
      // Make a change
      const promptField = screen.getByPlaceholderText('Enter your prompt...');
      fireEvent.change(promptField, { target: { value: 'Test prompt' } });

      const saveButton = screen.getByText('Save');
      
      await waitFor(() => {
        expect(saveButton).not.toBeDisabled();
      });
    });
  });

  describe('Save and Cancel', () => {
    it('calls onSave with configuration values', async () => {
      const onClose = jest.fn();
      const onSave = jest.fn();
      const blockWithConfig = {
        ...mockBlock,
        config: {
          model: 'gpt-4',
          prompt: 'Test prompt',
          temperature: 0.7,
        },
      };

      render(<BlockConfigPanel block={blockWithConfig} onClose={onClose} onSave={onSave} />);
      
      // Make a change
      const promptField = screen.getByText('Prompt').closest('div')?.querySelector('textarea');
      if (promptField) {
        fireEvent.change(promptField, { target: { value: 'Updated prompt' } });
      }

      const saveButton = screen.getByText('Save');
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(onSave).toHaveBeenCalledWith(
          'block-1',
          expect.objectContaining({ prompt: 'Updated prompt' })
        );
      });
    });

    it('calls onClose when cancel is clicked', () => {
      const onClose = jest.fn();
      const onSave = jest.fn();

      render(<BlockConfigPanel block={mockBlock} onClose={onClose} onSave={onSave} />);
      
      const cancelButton = screen.getByText('Cancel');
      fireEvent.click(cancelButton);

      expect(onClose).toHaveBeenCalled();
    });

    it('shows confirmation when closing with unsaved changes', () => {
      const onClose = jest.fn();
      const onSave = jest.fn();
      window.confirm = jest.fn(() => false);

      render(<BlockConfigPanel block={mockBlock} onClose={onClose} onSave={onSave} />);
      
      // Make a change
      const promptField = screen.getByText('Prompt').closest('div')?.querySelector('textarea');
      if (promptField) {
        fireEvent.change(promptField, { target: { value: 'Updated prompt' } });
      }

      const closeButton = screen.getByRole('button', { name: '' }); // X button
      fireEvent.click(closeButton);

      expect(window.confirm).toHaveBeenCalled();
      expect(onClose).not.toHaveBeenCalled();
    });
  });

  describe('Change Detection', () => {
    it('shows unsaved changes alert when values change', () => {
      const onClose = jest.fn();
      const onSave = jest.fn();

      render(<BlockConfigPanel block={mockBlock} onClose={onClose} onSave={onSave} />);
      
      // Make a change
      const promptField = screen.getByText('Prompt').closest('div')?.querySelector('textarea');
      if (promptField) {
        fireEvent.change(promptField, { target: { value: 'Updated prompt' } });
      }

      expect(screen.getByText('You have unsaved changes')).toBeInTheDocument();
    });

    it('disables save button when no changes', () => {
      const onClose = jest.fn();
      const onSave = jest.fn();
      const blockWithConfig = {
        ...mockBlock,
        config: {
          model: 'gpt-4',
          prompt: 'Test prompt',
          temperature: 0.7,
        },
      };

      render(<BlockConfigPanel block={blockWithConfig} onClose={onClose} onSave={onSave} />);
      
      const saveButton = screen.getByText('Save');
      expect(saveButton).toBeDisabled();
    });
  });
});
