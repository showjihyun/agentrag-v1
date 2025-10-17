import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import BatchProgress from '../BatchProgress';
import { apiClient } from '@/lib/api-client';

// Mock the API client
jest.mock('@/lib/api-client', () => ({
  apiClient: {
    streamBatchProgress: jest.fn(),
  },
}));

describe('BatchProgress', () => {
  const mockBatchId = 'batch-123';
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders loading state initially', () => {
    // Mock EventSource
    const mockEventSource = {
      onmessage: null,
      onerror: null,
      close: jest.fn(),
    };
    (apiClient.streamBatchProgress as jest.Mock).mockReturnValue(mockEventSource);

    render(<BatchProgress batchId={mockBatchId} onClose={mockOnClose} />);

    expect(screen.getByText('Loading progress...')).toBeInTheDocument();
  });

  it('displays progress updates from SSE', async () => {
    // Mock EventSource
    const mockEventSource = {
      onmessage: null as ((event: MessageEvent) => void) | null,
      onerror: null,
      close: jest.fn(),
    };
    (apiClient.streamBatchProgress as jest.Mock).mockReturnValue(mockEventSource);

    render(<BatchProgress batchId={mockBatchId} onClose={mockOnClose} />);

    // Simulate SSE message
    const progressData = {
      id: mockBatchId,
      user_id: 'user-123',
      total_files: 5,
      completed_files: 2,
      failed_files: 0,
      status: 'processing',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:01:00Z',
      files: [
        { filename: 'file1.pdf', status: 'completed' },
        { filename: 'file2.pdf', status: 'completed' },
        { filename: 'file3.pdf', status: 'processing' },
        { filename: 'file4.pdf', status: 'pending' },
        { filename: 'file5.pdf', status: 'pending' },
      ],
    };

    act(() => {
      if (mockEventSource.onmessage) {
        mockEventSource.onmessage(
          new MessageEvent('message', {
            data: JSON.stringify(progressData),
          })
        );
      }
    });

    await waitFor(() => {
      expect(screen.getByText(/Uploading\.\.\. 2 of 5 files completed/)).toBeInTheDocument();
      expect(screen.getByText('40%')).toBeInTheDocument();
    });
  });

  it('displays file-by-file status with icons', async () => {
    const mockEventSource = {
      onmessage: null as ((event: MessageEvent) => void) | null,
      onerror: null,
      close: jest.fn(),
    };
    (apiClient.streamBatchProgress as jest.Mock).mockReturnValue(mockEventSource);

    render(<BatchProgress batchId={mockBatchId} onClose={mockOnClose} />);

    const progressData = {
      id: mockBatchId,
      user_id: 'user-123',
      total_files: 3,
      completed_files: 1,
      failed_files: 1,
      status: 'processing',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:01:00Z',
      files: [
        { filename: 'success.pdf', status: 'completed' },
        { filename: 'failed.pdf', status: 'failed', error_message: 'Invalid file format' },
        { filename: 'pending.pdf', status: 'pending' },
      ],
    };

    act(() => {
      if (mockEventSource.onmessage) {
        mockEventSource.onmessage(
          new MessageEvent('message', {
            data: JSON.stringify(progressData),
          })
        );
      }
    });

    await waitFor(() => {
      expect(screen.getByText('success.pdf')).toBeInTheDocument();
      expect(screen.getByText('failed.pdf')).toBeInTheDocument();
      expect(screen.getByText('pending.pdf')).toBeInTheDocument();
      expect(screen.getByText('Invalid file format')).toBeInTheDocument();
    });
  });

  it('shows success summary when batch completes', async () => {
    const mockEventSource = {
      onmessage: null as ((event: MessageEvent) => void) | null,
      onerror: null,
      close: jest.fn(),
    };
    (apiClient.streamBatchProgress as jest.Mock).mockReturnValue(mockEventSource);

    render(<BatchProgress batchId={mockBatchId} onClose={mockOnClose} />);

    const progressData = {
      id: mockBatchId,
      user_id: 'user-123',
      total_files: 3,
      completed_files: 3,
      failed_files: 0,
      status: 'completed',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:02:00Z',
      files: [
        { filename: 'file1.pdf', status: 'completed' },
        { filename: 'file2.pdf', status: 'completed' },
        { filename: 'file3.pdf', status: 'completed' },
      ],
    };

    act(() => {
      if (mockEventSource.onmessage) {
        mockEventSource.onmessage(
          new MessageEvent('message', {
            data: JSON.stringify(progressData),
          })
        );
      }
    });

    await waitFor(() => {
      expect(screen.getByText(/All 3 files uploaded successfully!/)).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument(); // Total files
      expect(screen.getByText('Successful')).toBeInTheDocument();
    });
  });

  it('shows failure summary when batch has failed files', async () => {
    const mockEventSource = {
      onmessage: null as ((event: MessageEvent) => void) | null,
      onerror: null,
      close: jest.fn(),
    };
    (apiClient.streamBatchProgress as jest.Mock).mockReturnValue(mockEventSource);

    render(<BatchProgress batchId={mockBatchId} onClose={mockOnClose} />);

    const progressData = {
      id: mockBatchId,
      user_id: 'user-123',
      total_files: 5,
      completed_files: 3,
      failed_files: 2,
      status: 'completed',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:02:00Z',
      files: [
        { filename: 'file1.pdf', status: 'completed' },
        { filename: 'file2.pdf', status: 'completed' },
        { filename: 'file3.pdf', status: 'completed' },
        { filename: 'file4.pdf', status: 'failed', error_message: 'Too large' },
        { filename: 'file5.pdf', status: 'failed', error_message: 'Invalid type' },
      ],
    };

    act(() => {
      if (mockEventSource.onmessage) {
        mockEventSource.onmessage(
          new MessageEvent('message', {
            data: JSON.stringify(progressData),
          })
        );
      }
    });

    await waitFor(() => {
      expect(screen.getByText(/3 of 5 files uploaded successfully\. 2 failed\./)).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument(); // Failed count
    });
  });

  it('calls onClose when close button is clicked', async () => {
    const user = userEvent.setup();
    const mockEventSource = {
      onmessage: null as ((event: MessageEvent) => void) | null,
      onerror: null,
      close: jest.fn(),
    };
    (apiClient.streamBatchProgress as jest.Mock).mockReturnValue(mockEventSource);

    render(<BatchProgress batchId={mockBatchId} onClose={mockOnClose} />);

    // Complete the batch
    const progressData = {
      id: mockBatchId,
      user_id: 'user-123',
      total_files: 1,
      completed_files: 1,
      failed_files: 0,
      status: 'completed',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:01:00Z',
      files: [{ filename: 'file1.pdf', status: 'completed' }],
    };

    act(() => {
      if (mockEventSource.onmessage) {
        mockEventSource.onmessage(
          new MessageEvent('message', {
            data: JSON.stringify(progressData),
          })
        );
      }
    });

    await waitFor(() => {
      expect(screen.getByText('Close')).toBeInTheDocument();
    });

    const closeButton = screen.getByText('Close');
    await user.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('auto-closes on success when enabled', async () => {
    jest.useFakeTimers();

    const mockEventSource = {
      onmessage: null as ((event: MessageEvent) => void) | null,
      onerror: null,
      close: jest.fn(),
    };
    (apiClient.streamBatchProgress as jest.Mock).mockReturnValue(mockEventSource);

    render(
      <BatchProgress
        batchId={mockBatchId}
        onClose={mockOnClose}
        autoCloseOnSuccess={true}
        autoCloseDelay={3000}
      />
    );

    // Complete the batch successfully
    const progressData = {
      id: mockBatchId,
      user_id: 'user-123',
      total_files: 1,
      completed_files: 1,
      failed_files: 0,
      status: 'completed',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:01:00Z',
      files: [{ filename: 'file1.pdf', status: 'completed' }],
    };

    act(() => {
      if (mockEventSource.onmessage) {
        mockEventSource.onmessage(
          new MessageEvent('message', {
            data: JSON.stringify(progressData),
          })
        );
      }
    });

    // Fast-forward time
    act(() => {
      jest.advanceTimersByTime(3000);
    });

    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    jest.useRealTimers();
  });

  it('does not auto-close on failure', async () => {
    jest.useFakeTimers();

    const mockEventSource = {
      onmessage: null as ((event: MessageEvent) => void) | null,
      onerror: null,
      close: jest.fn(),
    };
    (apiClient.streamBatchProgress as jest.Mock).mockReturnValue(mockEventSource);

    render(
      <BatchProgress
        batchId={mockBatchId}
        onClose={mockOnClose}
        autoCloseOnSuccess={true}
        autoCloseDelay={3000}
      />
    );

    // Complete the batch with failures
    const progressData = {
      id: mockBatchId,
      user_id: 'user-123',
      total_files: 2,
      completed_files: 1,
      failed_files: 1,
      status: 'completed',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:01:00Z',
      files: [
        { filename: 'file1.pdf', status: 'completed' },
        { filename: 'file2.pdf', status: 'failed', error_message: 'Error' },
      ],
    };

    act(() => {
      if (mockEventSource.onmessage) {
        mockEventSource.onmessage(
          new MessageEvent('message', {
            data: JSON.stringify(progressData),
          })
        );
      }
    });

    // Fast-forward time
    act(() => {
      jest.advanceTimersByTime(3000);
    });

    // Should not auto-close because there were failures
    expect(mockOnClose).not.toHaveBeenCalled();

    jest.useRealTimers();
  });

  it('closes EventSource on unmount', () => {
    const mockEventSource = {
      onmessage: null,
      onerror: null,
      close: jest.fn(),
    };
    (apiClient.streamBatchProgress as jest.Mock).mockReturnValue(mockEventSource);

    const { unmount } = render(<BatchProgress batchId={mockBatchId} onClose={mockOnClose} />);

    unmount();

    expect(mockEventSource.close).toHaveBeenCalledTimes(1);
  });

  it('displays error message when SSE connection fails', async () => {
    const mockEventSource = {
      onmessage: null,
      onerror: null as ((event: Event) => void) | null,
      close: jest.fn(),
    };
    (apiClient.streamBatchProgress as jest.Mock).mockReturnValue(mockEventSource);

    render(<BatchProgress batchId={mockBatchId} onClose={mockOnClose} />);

    // Simulate SSE error
    act(() => {
      if (mockEventSource.onerror) {
        mockEventSource.onerror(new Event('error'));
      }
    });

    await waitFor(() => {
      expect(screen.getByText('Failed to connect to progress stream')).toBeInTheDocument();
    });
  });
});
