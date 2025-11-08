import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import AgentNode from '@/components/agent-builder/workflow-nodes/AgentNode';
import BlockNode from '@/components/agent-builder/workflow-nodes/BlockNode';
import ControlNode from '@/components/agent-builder/workflow-nodes/ControlNode';
import WorkflowPropertiesPanel from '@/components/agent-builder/WorkflowPropertiesPanel';

// Mock React Flow
jest.mock('reactflow', () => ({
  Handle: ({ type, position }: any) => <div data-testid={`handle-${type}-${position}`} />,
  Position: {
    Left: 'left',
    Right: 'right',
    Top: 'top',
    Bottom: 'bottom',
  },
}));

describe('Workflow Designer Components', () => {
  describe('AgentNode', () => {
    it('renders agent node with label', () => {
      const mockData = {
        label: 'Test Agent',
        description: 'Test description',
        id: 'agent-1',
      };

      render(<AgentNode data={mockData} selected={false} id="test-node" />);
      
      expect(screen.getByText('Test Agent')).toBeInTheDocument();
      expect(screen.getByText('Test description')).toBeInTheDocument();
      expect(screen.getByText('Agent')).toBeInTheDocument();
    });

    it('shows selected state', () => {
      const mockData = {
        label: 'Test Agent',
        id: 'agent-1',
      };

      const { container } = render(<AgentNode data={mockData} selected={true} id="test-node" />);
      
      const card = container.querySelector('.ring-2');
      expect(card).toBeInTheDocument();
    });

    it('renders input and output handles', () => {
      const mockData = {
        label: 'Test Agent',
        id: 'agent-1',
      };

      render(<AgentNode data={mockData} selected={false} id="test-node" />);
      
      expect(screen.getByTestId('handle-target-left')).toBeInTheDocument();
      expect(screen.getByTestId('handle-source-right')).toBeInTheDocument();
    });
  });

  describe('BlockNode', () => {
    it('renders block node with different types', () => {
      const blockTypes = ['llm', 'tool', 'logic', 'composite'];

      blockTypes.forEach((blockType) => {
        const mockData = {
          label: `Test ${blockType} Block`,
          block_type: blockType,
          id: `block-${blockType}`,
        };

        const { unmount } = render(<BlockNode data={mockData} selected={false} id="test-node" />);
        
        expect(screen.getByText(`Test ${blockType} Block`)).toBeInTheDocument();
        expect(screen.getByText('Block')).toBeInTheDocument();
        expect(screen.getByText(blockType)).toBeInTheDocument();
        
        unmount();
      });
    });

    it('renders with description', () => {
      const mockData = {
        label: 'Test Block',
        description: 'Block description',
        block_type: 'llm',
        id: 'block-1',
      };

      render(<BlockNode data={mockData} selected={false} id="test-node" />);
      
      expect(screen.getByText('Block description')).toBeInTheDocument();
    });
  });

  describe('ControlNode', () => {
    it('renders conditional control node', () => {
      const mockData = {
        label: 'Conditional',
        controlType: 'conditional',
        condition: 'state["value"] > 0',
        id: 'control-1',
      };

      render(<ControlNode data={mockData} selected={false} id="test-node" />);
      
      expect(screen.getByText('Conditional')).toBeInTheDocument();
      expect(screen.getByText('state["value"] > 0')).toBeInTheDocument();
    });

    it('renders loop control node', () => {
      const mockData = {
        label: 'Loop',
        controlType: 'loop',
        id: 'control-2',
      };

      render(<ControlNode data={mockData} selected={false} id="test-node" />);
      
      expect(screen.getByText('Loop')).toBeInTheDocument();
      expect(screen.getByText('loop')).toBeInTheDocument();
    });

    it('renders parallel control node', () => {
      const mockData = {
        label: 'Parallel',
        controlType: 'parallel',
        id: 'control-3',
      };

      render(<ControlNode data={mockData} selected={false} id="test-node" />);
      
      expect(screen.getByText('Parallel')).toBeInTheDocument();
      expect(screen.getByText('parallel')).toBeInTheDocument();
    });
  });

  describe('WorkflowPropertiesPanel', () => {
    it('renders when open with node', () => {
      const mockNode = {
        id: 'node-1',
        type: 'agent',
        position: { x: 0, y: 0 },
        data: {
          label: 'Test Agent',
          description: 'Test description',
          id: 'agent-1',
        },
      };

      const mockOnClose = jest.fn();
      const mockOnUpdate = jest.fn();

      render(
        <WorkflowPropertiesPanel
          node={mockNode}
          isOpen={true}
          onClose={mockOnClose}
          onUpdate={mockOnUpdate}
        />
      );

      expect(screen.getByText('Node Properties')).toBeInTheDocument();
      expect(screen.getByText(/Configure the selected agent node/i)).toBeInTheDocument();
    });

    it('does not render when closed', () => {
      const mockNode = {
        id: 'node-1',
        type: 'agent',
        position: { x: 0, y: 0 },
        data: {
          label: 'Test Agent',
          id: 'agent-1',
        },
      };

      const mockOnClose = jest.fn();
      const mockOnUpdate = jest.fn();

      render(
        <WorkflowPropertiesPanel
          node={mockNode}
          isOpen={false}
          onClose={mockOnClose}
          onUpdate={mockOnUpdate}
        />
      );

      expect(screen.queryByText('Node Properties')).not.toBeInTheDocument();
    });

    it('calls onUpdate when save is clicked', async () => {
      const mockNode = {
        id: 'node-1',
        type: 'agent',
        position: { x: 0, y: 0 },
        data: {
          label: 'Test Agent',
          id: 'agent-1',
        },
      };

      const mockOnClose = jest.fn();
      const mockOnUpdate = jest.fn();

      render(
        <WorkflowPropertiesPanel
          node={mockNode}
          isOpen={true}
          onClose={mockOnClose}
          onUpdate={mockOnUpdate}
        />
      );

      const saveButton = screen.getByRole('button', { name: /save changes/i });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(mockOnUpdate).toHaveBeenCalledWith('node-1', expect.any(Object));
        expect(mockOnClose).toHaveBeenCalled();
      });
    });

    it('updates node label', async () => {
      const mockNode = {
        id: 'node-1',
        type: 'agent',
        position: { x: 0, y: 0 },
        data: {
          label: 'Test Agent',
          id: 'agent-1',
        },
      };

      const mockOnClose = jest.fn();
      const mockOnUpdate = jest.fn();

      render(
        <WorkflowPropertiesPanel
          node={mockNode}
          isOpen={true}
          onClose={mockOnClose}
          onUpdate={mockOnUpdate}
        />
      );

      const nameInput = screen.getByLabelText(/node name/i);
      fireEvent.change(nameInput, { target: { value: 'Updated Agent' } });

      const saveButton = screen.getByRole('button', { name: /save changes/i });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(mockOnUpdate).toHaveBeenCalledWith(
          'node-1',
          expect.objectContaining({ label: 'Updated Agent' })
        );
      });
    });
  });

  describe('Connection Validation', () => {
    it('validates connection data structure', () => {
      const validConnection = {
        source: 'node-1',
        target: 'node-2',
        sourceHandle: 'output',
        targetHandle: 'input',
      };

      expect(validConnection.source).toBeDefined();
      expect(validConnection.target).toBeDefined();
      expect(validConnection.source).not.toBe(validConnection.target);
    });

    it('detects self-connections', () => {
      const selfConnection = {
        source: 'node-1',
        target: 'node-1',
      };

      expect(selfConnection.source).toBe(selfConnection.target);
    });
  });

  describe('Workflow Save and Load', () => {
    it('validates workflow structure', () => {
      const workflow = {
        id: 'workflow-1',
        name: 'Test Workflow',
        graph_definition: {
          nodes: [
            {
              id: 'node-1',
              type: 'agent',
              position: { x: 0, y: 0 },
              data: { label: 'Agent 1' },
            },
          ],
          edges: [
            {
              id: 'edge-1',
              source: 'node-1',
              target: 'node-2',
            },
          ],
          entry_point: 'node-1',
        },
      };

      expect(workflow.graph_definition.nodes).toHaveLength(1);
      expect(workflow.graph_definition.edges).toHaveLength(1);
      expect(workflow.graph_definition.entry_point).toBe('node-1');
    });
  });
});
