import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import DocumentUpload from '@/components/agent-builder/DocumentUpload';
import KnowledgebaseSearch from '@/components/agent-builder/KnowledgebaseSearch';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { it } from 'zod/v4/locales';
import { it } from 'zod/v4/locales';
import { it } from 'zod/v4/locales';
import { beforeEach } from 'node:test';
import { describe } from 'node:test';
import { it } from 'zod/v4/locales';
import { it } from 'zod/v4/locales';
import { it } from 'zod/v4/locales';
import { beforeEach } from 'node:test';
import { describe } from 'node:test';
import { describe } from 'node:test';

// Mock the API
jest.mock('@/lib/api/agent-builder');
const mockAPI = agentBuilderAPI as jest.Mocked<typeof agentBuilderAPI>;

// Mock toast
jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}));

describe('Knowledgebase Components', () => {
  describe('DocumentUpload', () => {
    beforeEach(() => {
      jest.clearAllMocks();
    });

    it('renders upload interface', () => {
      render(<DocumentUpload knowledgebaseId="kb-1" />);
      
      expect(screen.getByText('Upload Documents')).toBeInTheDocument();
      expect(screen.getByText(/Drag and drop files/i)).toBeInTheDocument();
    });

    it('handles file selection', () => {
      render(<DocumentUpload knowledgebaseId="kb-1" />);
      
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      const input = document.querySelector('input[type="file"]') as HTMLInputElement;
      
      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false,
      });

      fireEvent.change(input);

      // Check that the file list section appears
      expect(screen.getByText(/Files \(/i)).toBeInTheDocument();
      expect(screen.getByText('Upload All')).toBeInTheDocument();
    });

    it('uploads documents successfully', async () => {
      const mockProgress = [
        {
          document_id: 'doc-1',
          filename: 'test.pdf',
          status: 'completed' as const,
          progress: 100,
        },
      ];

      mockAPI.uploadDocuments.mockResolvedValue(mockProgress);

      const onComplete = jest.fn();
      render(<DocumentUpload knowledgebaseId="kb-1" onUploadComplete={onComplete} />);

      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      const input = document.querySelector('input[type="file"]') as HTMLInputElement;
      
      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false,
      });

      fireEvent.change(input);

      const uploadButton = screen.getByText('Upload All');
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(mockAPI.uploadDocuments).toHaveBeenCalledWith('kb-1', expect.any(Array));
        expect(onComplete).toHaveBeenCalled();
      });
    });
  });

  describe('KnowledgebaseSearch', () => {
    beforeEach(() => {
      jest.clearAllMocks();
    });

    it('renders search interface', () => {
      render(<KnowledgebaseSearch knowledgebaseId="kb-1" />);
      
      expect(screen.getByText('Search Knowledgebase')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Enter your search query/i)).toBeInTheDocument();
    });

    it('performs search and displays results', async () => {
      const mockResults = [
        {
          document_id: 'doc-1',
          content: 'Test content from document',
          score: 0.95,
          metadata: { filename: 'test.pdf' },
        },
        {
          document_id: 'doc-2',
          content: 'Another relevant result',
          score: 0.85,
          metadata: { filename: 'doc2.pdf' },
        },
      ];

      mockAPI.searchKnowledgebase.mockResolvedValue(mockResults);

      render(<KnowledgebaseSearch knowledgebaseId="kb-1" />);

      const searchInput = screen.getByPlaceholderText(/Enter your search query/i);
      fireEvent.change(searchInput, { target: { value: 'test query' } });

      const searchButton = screen.getByRole('button', { name: /Search/i });
      fireEvent.click(searchButton);

      await waitFor(() => {
        expect(mockAPI.searchKnowledgebase).toHaveBeenCalledWith('kb-1', 'test query', 10);
        expect(screen.getByText('Test content from document')).toBeInTheDocument();
        expect(screen.getByText('Another relevant result')).toBeInTheDocument();
      });
    });

    it('handles empty search results', async () => {
      mockAPI.searchKnowledgebase.mockResolvedValue([]);

      render(<KnowledgebaseSearch knowledgebaseId="kb-1" />);

      const searchInput = screen.getByPlaceholderText(/Enter your search query/i);
      fireEvent.change(searchInput, { target: { value: 'nonexistent query' } });

      const searchButton = screen.getByRole('button', { name: /Search/i });
      fireEvent.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText('No Results Found')).toBeInTheDocument();
      });
    });
  });
});
