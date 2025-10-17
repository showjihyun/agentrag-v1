import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ConversationHistory from '../ConversationHistory';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api-client';
import { useRouter } from 'next/navigation';

// Mock dependencies
jest.mock('@/contexts/AuthContext');
jest.mock('@/lib/api-client');
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>;

describe('ConversationHistory', () => {
  const mockPush = jest.fn();
  const mockSessions = [
    {
      id: 'session-1',
      user_id: 'user-1',
      title: 'Test Conversation 1',
      created_at: '2024-01-01T10:00:00Z',
      updated_at: '2024-01-01T10:30:00Z',
      message_count: 5,
    },
    {
      id: 'session-2',
      user_id: 'user-1',
      title: 'Test Conversation 2',
      created_at: '2024-01-01T09:00:00Z',
      updated_at: '2024-01-01T09:30:00Z',
      message_count: 3,
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockUseRouter.mockReturnValue({
      push: mockPush,
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
    } as any);

    mockUseAuth.mockReturnValue({
      user: {
        id: 'user-1',
        email: 'test@example.com',
        username: 'testuser',
        role: 'user',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        query_count: 10,
        storage_used_bytes: 1024,
      },
      isAuthenticated: true,
      isLoading: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      refreshUser: jest.fn(),
    });

    (apiClient.getSessions as jest.Mock) = jest.fn().mockResolvedValue({
      sessions: mockSessions,
      total: 2,
      limit: 20,
      offset: 0,
    });
  });

  it('should not render when user is not authenticated', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      refreshUser: jest.fn(),
    });

    const { container } = render(<ConversationHistory />);
    expect(container.firstChild).toBeNull();
  });

  it('should fetch and display sessions on mount', async () => {
    render(<ConversationHistory />);

    await waitFor(() => {
      expect(apiClient.getSessions).toHaveBeenCalledWith(20, 0);
    });

    expect(screen.getByText('Test Conversation 1')).toBeInTheDocument();
    expect(screen.getByText('Test Conversation 2')).toBeInTheDocument();
  });

  it('should display loading skeleton while fetching', () => {
    render(<ConversationHistory />);

    // Should show loading state initially
    const skeletons = document.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('should display empty state when no sessions', async () => {
    (apiClient.getSessions as jest.Mock).mockResolvedValue({
      sessions: [],
      total: 0,
      limit: 20,
      offset: 0,
    });

    render(<ConversationHistory />);

    await waitFor(() => {
      expect(screen.getByText('Start a new conversation')).toBeInTheDocument();
    });
  });

  it('should create new conversation when button clicked', async () => {
    const newSession = {
      id: 'session-3',
      user_id: 'user-1',
      title: 'New Conversation',
      created_at: '2024-01-01T11:00:00Z',
      updated_at: '2024-01-01T11:00:00Z',
      message_count: 0,
    };

    (apiClient.createSession as jest.Mock) = jest.fn().mockResolvedValue(newSession);

    render(<ConversationHistory />);

    await waitFor(() => {
      expect(screen.getByText('Test Conversation 1')).toBeInTheDocument();
    });

    const newButton = screen.getByText('New Conversation');
    fireEvent.click(newButton);

    await waitFor(() => {
      expect(apiClient.createSession).toHaveBeenCalled();
      expect(mockPush).toHaveBeenCalledWith('/?session=session-3');
    });
  });

  it('should filter sessions by search query', async () => {
    render(<ConversationHistory />);

    await waitFor(() => {
      expect(screen.getByText('Test Conversation 1')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search conversations...');
    fireEvent.change(searchInput, { target: { value: 'Conversation 1' } });

    expect(screen.getByText('Test Conversation 1')).toBeInTheDocument();
    expect(screen.queryByText('Test Conversation 2')).not.toBeInTheDocument();
  });

  it('should handle session selection', async () => {
    const onSessionSelect = jest.fn();
    
    render(<ConversationHistory onSessionSelect={onSessionSelect} />);

    await waitFor(() => {
      expect(screen.getByText('Test Conversation 1')).toBeInTheDocument();
    });

    const sessionItem = screen.getByText('Test Conversation 1').closest('div');
    if (sessionItem) {
      fireEvent.click(sessionItem);
    }

    await waitFor(() => {
      expect(onSessionSelect).toHaveBeenCalledWith('session-1');
    });
  });

  it('should load more sessions when button clicked', async () => {
    (apiClient.getSessions as jest.Mock)
      .mockResolvedValueOnce({
        sessions: mockSessions,
        total: 25,
        limit: 20,
        offset: 0,
      })
      .mockResolvedValueOnce({
        sessions: [
          {
            id: 'session-3',
            user_id: 'user-1',
            title: 'Test Conversation 3',
            created_at: '2024-01-01T08:00:00Z',
            updated_at: '2024-01-01T08:30:00Z',
            message_count: 2,
          },
        ],
        total: 25,
        limit: 20,
        offset: 2,
      });

    render(<ConversationHistory />);

    await waitFor(() => {
      expect(screen.getByText('Test Conversation 1')).toBeInTheDocument();
    });

    const loadMoreButton = screen.getByText('Load more');
    fireEvent.click(loadMoreButton);

    await waitFor(() => {
      expect(apiClient.getSessions).toHaveBeenCalledWith(20, 2);
      expect(screen.getByText('Test Conversation 3')).toBeInTheDocument();
    });
  });

  it('should display error message on fetch failure', async () => {
    (apiClient.getSessions as jest.Mock).mockRejectedValue(
      new Error('Network error')
    );

    render(<ConversationHistory />);

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('should toggle mobile sidebar', async () => {
    render(<ConversationHistory />);

    await waitFor(() => {
      expect(screen.getByText('Test Conversation 1')).toBeInTheDocument();
    });

    // Find hamburger button
    const hamburgerButton = screen.getByLabelText('Toggle conversation history');
    
    // Sidebar should be hidden on mobile initially
    const sidebar = hamburgerButton.nextElementSibling?.nextElementSibling;
    expect(sidebar).toHaveClass('-translate-x-full');

    // Click to open
    fireEvent.click(hamburgerButton);
    expect(sidebar).toHaveClass('translate-x-0');
  });

  it('should highlight active session', async () => {
    render(<ConversationHistory activeSessionId="session-1" />);

    await waitFor(() => {
      expect(screen.getByText('Test Conversation 1')).toBeInTheDocument();
    });

    const activeSession = screen.getByText('Test Conversation 1').closest('div');
    expect(activeSession).toHaveClass('bg-blue-100');
  });
});
