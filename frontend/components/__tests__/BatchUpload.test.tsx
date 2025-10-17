/**
 * Tests for BatchUpload component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import BatchUpload from '../BatchUpload';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api-client';

// Mock dependencies
jest.mock('@/contexts/AuthContext');
jest.mock('@/lib/api-client');

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('BatchUpload', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should not render when user is not authenticated', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      user: null,
      isLoading: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      refreshUser: jest.fn(),
    });

    const { container } = render(<BatchUpload />);
    expect(container.firstChild).toBeNull();
  });

  it('should render when user is authenticated', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: {
        id: '1',
        email: 'test@example.com',
        username: 'testuser',
        role: 'user',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
        query_count: 0,
        storage_used_bytes: 0,
      },
      isLoading: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      refreshUser: jest.fn(),
    });

    render(<BatchUpload />);
    expect(screen.getByText('Batch Upload')).toBeInTheDocument();
    expect(screen.getByText(/Drag and drop files here/i)).toBeInTheDocument();
  });

  it('should show file input when browse button is clicked', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: {
        id: '1',
        email: 'test@example.com',
        username: 'testuser',
        role: 'user',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
        query_count: 0,
        storage_used_bytes: 0,
      },
      isLoading: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      refreshUser: jest.fn(),
    });

    render(<BatchUpload />);
    
    const browseButton = screen.getByText('browse');
    expect(browseButton).toBeInTheDocument();
  });

  it('should display file information when files are added', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: {
        id: '1',
        email: 'test@example.com',
        username: 'testuser',
        role: 'user',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
        query_count: 0,
        storage_used_bytes: 0,
      },
      isLoading: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      refreshUser: jest.fn(),
    });

    render(<BatchUpload />);
    
    // Create a mock file
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    // Simulate file selection
    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
    });
    
    fireEvent.change(input);
    
    // Check if file is displayed
    expect(screen.getByText('test.pdf')).toBeInTheDocument();
  });

  it('should validate file types', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: {
        id: '1',
        email: 'test@example.com',
        username: 'testuser',
        role: 'user',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
        query_count: 0,
        storage_used_bytes: 0,
      },
      isLoading: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      refreshUser: jest.fn(),
    });

    render(<BatchUpload />);
    
    // Create an invalid file
    const file = new File(['test content'], 'test.exe', { type: 'application/x-msdownload' });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
    });
    
    fireEvent.change(input);
    
    // Check if error is displayed
    expect(screen.getByText(/Invalid file type/i)).toBeInTheDocument();
  });

  it('should disable upload button when no valid files', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: {
        id: '1',
        email: 'test@example.com',
        username: 'testuser',
        role: 'user',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
        query_count: 0,
        storage_used_bytes: 0,
      },
      isLoading: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      refreshUser: jest.fn(),
    });

    render(<BatchUpload />);
    
    // Initially no files, so no upload button should be visible
    expect(screen.queryByText(/Upload/i)).not.toBeInTheDocument();
  });

  it('should allow removing files from the list', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: {
        id: '1',
        email: 'test@example.com',
        username: 'testuser',
        role: 'user',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
        query_count: 0,
        storage_used_bytes: 0,
      },
      isLoading: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      refreshUser: jest.fn(),
    });

    render(<BatchUpload />);
    
    // Add a file
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
    });
    
    fireEvent.change(input);
    
    // File should be displayed
    expect(screen.getByText('test.pdf')).toBeInTheDocument();
    
    // Click clear all button
    const clearButton = screen.getByText('Clear All');
    fireEvent.click(clearButton);
    
    // File should be removed
    expect(screen.queryByText('test.pdf')).not.toBeInTheDocument();
  });
});
