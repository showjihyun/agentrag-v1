import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SessionItem from '../SessionItem';
import { SessionResponse } from '@/lib/types';

// Mock window.confirm
const mockConfirm = jest.fn();
global.confirm = mockConfirm;

describe('SessionItem', () => {
  const mockSession: SessionResponse = {
    id: 'session-1',
    user_id: 'user-1',
    title: 'Test Session',
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
    updated_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    message_count: 5,
  };

  const mockOnSelect = jest.fn();
  const mockOnDelete = jest.fn();
  const mockOnRename = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockConfirm.mockReturnValue(true);
  });

  it('renders session title and relative time', () => {
    render(
      <SessionItem
        session={mockSession}
        isActive={false}
        onSelect={mockOnSelect}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    expect(screen.getByText('Test Session')).toBeInTheDocument();
    expect(screen.getByText(/2 hours ago/i)).toBeInTheDocument();
  });

  it('displays message count', () => {
    render(
      <SessionItem
        session={mockSession}
        isActive={false}
        onSelect={mockOnSelect}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    expect(screen.getByText('5 messages')).toBeInTheDocument();
  });

  it('highlights active session', () => {
    const { container } = render(
      <SessionItem
        session={mockSession}
        isActive={true}
        onSelect={mockOnSelect}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    const sessionDiv = container.firstChild as HTMLElement;
    expect(sessionDiv).toHaveClass('bg-blue-100');
  });

  it('calls onSelect when clicked', () => {
    render(
      <SessionItem
        session={mockSession}
        isActive={false}
        onSelect={mockOnSelect}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    const sessionDiv = screen.getByText('Test Session').closest('div')?.parentElement;
    fireEvent.click(sessionDiv!);

    expect(mockOnSelect).toHaveBeenCalledWith('session-1');
  });

  it('enters edit mode on double-click', () => {
    render(
      <SessionItem
        session={mockSession}
        isActive={false}
        onSelect={mockOnSelect}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    const sessionDiv = screen.getByText('Test Session').closest('div')?.parentElement;
    fireEvent.doubleClick(sessionDiv!);

    const input = screen.getByDisplayValue('Test Session');
    expect(input).toBeInTheDocument();
    expect(input).toHaveFocus();
  });

  it('saves edited title on Enter key', async () => {
    render(
      <SessionItem
        session={mockSession}
        isActive={false}
        onSelect={mockOnSelect}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    const sessionDiv = screen.getByText('Test Session').closest('div')?.parentElement;
    fireEvent.doubleClick(sessionDiv!);

    const input = screen.getByDisplayValue('Test Session') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'Updated Title' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      expect(mockOnRename).toHaveBeenCalledWith('session-1', 'Updated Title');
    });
  });

  it('cancels edit on Escape key', async () => {
    render(
      <SessionItem
        session={mockSession}
        isActive={false}
        onSelect={mockOnSelect}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    const sessionDiv = screen.getByText('Test Session').closest('div')?.parentElement;
    fireEvent.doubleClick(sessionDiv!);

    const input = screen.getByDisplayValue('Test Session') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'Updated Title' } });
    fireEvent.keyDown(input, { key: 'Escape' });

    await waitFor(() => {
      expect(mockOnRename).not.toHaveBeenCalled();
      expect(screen.getByText('Test Session')).toBeInTheDocument();
    });
  });

  it('shows confirmation dialog before delete', () => {
    render(
      <SessionItem
        session={mockSession}
        isActive={false}
        onSelect={mockOnSelect}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    const deleteButton = screen.getByLabelText('Delete conversation');
    fireEvent.click(deleteButton);

    expect(mockConfirm).toHaveBeenCalledWith(
      expect.stringContaining('Are you sure you want to delete "Test Session"?')
    );
  });

  it('calls onDelete when confirmed', () => {
    mockConfirm.mockReturnValue(true);

    render(
      <SessionItem
        session={mockSession}
        isActive={false}
        onSelect={mockOnSelect}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    const deleteButton = screen.getByLabelText('Delete conversation');
    fireEvent.click(deleteButton);

    expect(mockOnDelete).toHaveBeenCalledWith('session-1');
  });

  it('does not call onDelete when cancelled', () => {
    mockConfirm.mockReturnValue(false);

    render(
      <SessionItem
        session={mockSession}
        isActive={false}
        onSelect={mockOnSelect}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    const deleteButton = screen.getByLabelText('Delete conversation');
    fireEvent.click(deleteButton);

    expect(mockOnDelete).not.toHaveBeenCalled();
  });

  it('formats relative time correctly for recent messages', () => {
    const recentSession = {
      ...mockSession,
      updated_at: new Date(Date.now() - 30 * 1000).toISOString(), // 30 seconds ago
    };

    render(
      <SessionItem
        session={recentSession}
        isActive={false}
        onSelect={mockOnSelect}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    expect(screen.getByText('Just now')).toBeInTheDocument();
  });

  it('formats relative time correctly for yesterday', () => {
    const yesterdaySession = {
      ...mockSession,
      updated_at: new Date(Date.now() - 25 * 60 * 60 * 1000).toISOString(), // 25 hours ago
    };

    render(
      <SessionItem
        session={yesterdaySession}
        isActive={false}
        onSelect={mockOnSelect}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    expect(screen.getByText('Yesterday')).toBeInTheDocument();
  });

  it('does not rename if title is empty', async () => {
    render(
      <SessionItem
        session={mockSession}
        isActive={false}
        onSelect={mockOnSelect}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    const sessionDiv = screen.getByText('Test Session').closest('div')?.parentElement;
    fireEvent.doubleClick(sessionDiv!);

    const input = screen.getByDisplayValue('Test Session') as HTMLInputElement;
    fireEvent.change(input, { target: { value: '   ' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      expect(mockOnRename).not.toHaveBeenCalled();
    });
  });

  it('does not rename if title is unchanged', async () => {
    render(
      <SessionItem
        session={mockSession}
        isActive={false}
        onSelect={mockOnSelect}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    const sessionDiv = screen.getByText('Test Session').closest('div')?.parentElement;
    fireEvent.doubleClick(sessionDiv!);

    const input = screen.getByDisplayValue('Test Session') as HTMLInputElement;
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      expect(mockOnRename).not.toHaveBeenCalled();
    });
  });
});
