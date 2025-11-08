import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import BlockEditor from '@/components/agent-builder/BlockEditor';
import BlockTestPanel from '@/components/agent-builder/BlockTestPanel';
import { agentBuilderAPI } from '@/lib/api/agent-builder';

// Mock the API
jest.mock('@/lib/api/agent-builder');
const mockAPI = agentBuilderAPI as jest.Mocked<typeof agentBuilderAPI>;

// Mock Monaco Editor
jest.mock('@monaco-editor/react', () => ({
  __esModule: true,
  default: ({ value, onChange }: any) => (
    <textarea
      data-testid="monaco-editor"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  ),
}));

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    back: jest.fn(),
  }),
  useParams: () => ({ id: 'test-block-id' }),
}));

// Mock toast
jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}));

describe('Block Library Components', () => {
  describe('BlockEditor', () => {
    beforeEach(() => {
      jest.clearAllMocks();
    });

    it('loads existing block for editing', async () => {
      const mockBlock = {
        id: 'block-1',
        name: 'Existing Block',
        description: 'Test description',
        block_type: 'tool' as const,
        user_id: 'user-1',
        is_public: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      mockAPI.getBlock.mockResolvedValue(mockBlock);

      render(<BlockEditor blockId="block-1" />);

      await waitFor(() => {
        expect(mockAPI.getBlock).toHaveBeenCalledWith('block-1');
      });
    });
  });

  describe('BlockTestPanel', () => {
    beforeEach(() => {
      jest.clearAllMocks();
    });

    it('renders test panel with block info', async () => {
      const mockBlock = {
        id: 'block-1',
        name: 'Test Block',
        block_type: 'llm' as const,
        user_id: 'user-1',
        is_public: false,
        input_schema: {
          properties: {
            input: { type: 'string' },
          },
        },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      mockAPI.getBlock.mockResolvedValue(mockBlock);

      render(<BlockTestPanel blockId="block-1" />);

      await waitFor(() => {
        expect(screen.getByText('Test Block')).toBeInTheDocument();
      });
    });

    it('executes block test successfully', async () => {
      const mockBlock = {
        id: 'block-1',
        name: 'Test Block',
        block_type: 'llm' as const,
        user_id: 'user-1',
        is_public: false,
        input_schema: {
          properties: {
            input: { type: 'string' },
          },
        },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      const mockTestResult = {
        output: { result: 'success' },
        duration_ms: 150,
        success: true,
      };

      mockAPI.getBlock.mockResolvedValue(mockBlock);
      mockAPI.testBlock.mockResolvedValue(mockTestResult);

      render(<BlockTestPanel blockId="block-1" />);

      await waitFor(() => {
        expect(screen.getByText('Test Block')).toBeInTheDocument();
      });

      const runButton = screen.getByText('Run Test');
      fireEvent.click(runButton);

      await waitFor(() => {
        expect(mockAPI.testBlock).toHaveBeenCalled();
        expect(screen.getByText('Test Passed')).toBeInTheDocument();
      });
    });
  });
});
