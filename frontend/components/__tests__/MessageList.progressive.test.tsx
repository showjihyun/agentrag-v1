import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import MessageList, { Message } from '../MessageList';

describe('MessageList - Progressive Display', () => {
  const mockMessages: Message[] = [
    {
      id: '1',
      role: 'user',
      content: 'What is machine learning?',
      timestamp: new Date('2024-01-01T10:00:00'),
    },
    {
      id: '2',
      role: 'assistant',
      content: 'Machine learning is a subset of AI...',
      timestamp: new Date('2024-01-01T10:00:05'),
      responseType: 'preliminary',
      pathSource: 'speculative',
      confidenceScore: 0.75,
      isRefining: false,
    },
  ];

  it('renders messages with preliminary badge', () => {
    render(<MessageList messages={mockMessages} />);

    expect(screen.getByText('What is machine learning?')).toBeInTheDocument();
    expect(screen.getByText('Machine learning is a subset of AI...')).toBeInTheDocument();
    expect(screen.getByText('Preliminary')).toBeInTheDocument();
  });

  it('displays confidence score for assistant messages', () => {
    render(<MessageList messages={mockMessages} />);

    expect(screen.getByText('Confidence: 75%')).toBeInTheDocument();
  });

  it('shows refining indicator when isRefining is true', () => {
    const refiningMessages: Message[] = [
      ...mockMessages,
      {
        id: '3',
        role: 'assistant',
        content: 'Machine learning is a subset of AI that enables...',
        timestamp: new Date('2024-01-01T10:00:10'),
        responseType: 'refinement',
        pathSource: 'agentic',
        confidenceScore: 0.85,
        isRefining: true,
      },
    ];

    render(<MessageList messages={refiningMessages} />);

    expect(screen.getByText('Refining...')).toBeInTheDocument();
    expect(screen.getByText('Processing deeper analysis...')).toBeInTheDocument();
  });

  it('displays comparison toggle for refined messages with previous content', () => {
    const refinedMessages: Message[] = [
      mockMessages[0],
      {
        ...mockMessages[1],
        content: 'Machine learning is a subset of AI that enables systems to learn...',
        responseType: 'final',
        previousContent: 'Machine learning is a subset of AI...',
        isRefining: false,
      },
    ];

    render(<MessageList messages={refinedMessages} />);

    expect(screen.getByText('Compare versions')).toBeInTheDocument();
  });

  it('preserves scroll position when user scrolls up', async () => {
    const { container } = render(<MessageList messages={mockMessages} />);

    const scrollContainer = container.querySelector('.overflow-y-auto');
    expect(scrollContainer).toBeInTheDocument();

    if (scrollContainer) {
      // Simulate scroll up
      Object.defineProperty(scrollContainer, 'scrollTop', { value: 100, writable: true });
      Object.defineProperty(scrollContainer, 'scrollHeight', { value: 1000, writable: true });
      Object.defineProperty(scrollContainer, 'clientHeight', { value: 500, writable: true });

      fireEvent.scroll(scrollContainer);

      await waitFor(() => {
        const scrollButton = screen.queryByLabelText('Scroll to bottom');
        expect(scrollButton).toBeInTheDocument();
      });
    }
  });

  it('shows scroll to bottom button when not at bottom', async () => {
    const { container } = render(<MessageList messages={mockMessages} />);

    const scrollContainer = container.querySelector('.overflow-y-auto');
    
    if (scrollContainer) {
      // Simulate being scrolled up
      Object.defineProperty(scrollContainer, 'scrollTop', { value: 0, writable: true });
      Object.defineProperty(scrollContainer, 'scrollHeight', { value: 1000, writable: true });
      Object.defineProperty(scrollContainer, 'clientHeight', { value: 500, writable: true });

      fireEvent.scroll(scrollContainer);

      await waitFor(() => {
        const scrollButton = screen.queryByLabelText('Scroll to bottom');
        expect(scrollButton).toBeInTheDocument();
      });
    }
  });

  it('scrolls to bottom when scroll button is clicked', async () => {
    const { container } = render(<MessageList messages={mockMessages} />);

    const scrollContainer = container.querySelector('.overflow-y-auto');
    
    if (scrollContainer) {
      // Simulate being scrolled up
      Object.defineProperty(scrollContainer, 'scrollTop', { value: 0, writable: true });
      Object.defineProperty(scrollContainer, 'scrollHeight', { value: 1000, writable: true });
      Object.defineProperty(scrollContainer, 'clientHeight', { value: 500, writable: true });

      fireEvent.scroll(scrollContainer);

      await waitFor(() => {
        const scrollButton = screen.getByLabelText('Scroll to bottom');
        fireEvent.click(scrollButton);
      });
    }
  });

  it('displays processing indicator when isProcessing is true', () => {
    render(<MessageList messages={mockMessages} isProcessing={true} />);

    expect(screen.getByText('Thinking...')).toBeInTheDocument();
  });

  it('renders empty state when no messages', () => {
    render(<MessageList messages={[]} />);

    expect(screen.getByText('No messages yet')).toBeInTheDocument();
    expect(screen.getByText('Start by asking a question about your documents')).toBeInTheDocument();
  });

  it('displays reasoning steps when provided', () => {
    const messagesWithSteps: Message[] = [
      mockMessages[0],
      {
        ...mockMessages[1],
        reasoningSteps: [
          {
            step_id: 'step1',
            type: 'thought',
            content: 'Analyzing the query...',
            timestamp: '2024-01-01T10:00:06',
            metadata: {},
          },
        ],
      },
    ];

    render(<MessageList messages={messagesWithSteps} />);

    expect(screen.getByText('Analyzing the query...')).toBeInTheDocument();
  });

  it('displays source citations when provided', () => {
    const messagesWithSources: Message[] = [
      mockMessages[0],
      {
        ...mockMessages[1],
        sources: [
          {
            chunk_id: 'chunk1',
            document_id: 'doc1',
            document_name: 'ML Guide',
            text: 'Machine learning definition...',
            score: 0.95,
            metadata: {},
          },
        ],
      },
    ];

    render(<MessageList messages={messagesWithSources} />);

    expect(screen.getByText('ML Guide')).toBeInTheDocument();
  });
});
