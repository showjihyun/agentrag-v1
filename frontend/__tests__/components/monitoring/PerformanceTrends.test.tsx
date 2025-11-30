/**
 * Tests for PerformanceTrends component
 * @jest-environment jsdom
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import PerformanceTrends from '@/components/monitoring/PerformanceTrends';

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

const mockLatencyData = {
  data: [
    { timestamp: '2024-01-01T10:00:00Z', values: { fast: 0.5, balanced: 1.5, deep: 5.0 } },
    { timestamp: '2024-01-01T11:00:00Z', values: { fast: 0.6, balanced: 1.8, deep: 6.0 } },
  ],
};

const mockModeData = {
  data: [
    { timestamp: '2024-01-01T10:00:00Z', values: { fast: 50, balanced: 30, deep: 20 } },
    { timestamp: '2024-01-01T11:00:00Z', values: { fast: 45, balanced: 35, deep: 20 } },
  ],
};

describe('PerformanceTrends', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render loading state initially', () => {
    mockFetch.mockImplementation(() => new Promise(() => {}));
    
    render(<PerformanceTrends autoRefresh={false} refreshInterval={30} />);
    
    expect(screen.getByText('Loading trends...')).toBeInTheDocument();
  });

  it('should render data after successful fetch', async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockLatencyData) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockModeData) });

    render(<PerformanceTrends autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Performance Trends')).toBeInTheDocument();
    });

    expect(screen.getByText('Latency Over Time')).toBeInTheDocument();
    expect(screen.getByText('Mode Distribution Over Time')).toBeInTheDocument();
  });

  it('should render error state on fetch failure', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'));

    render(<PerformanceTrends autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Error loading trends')).toBeInTheDocument();
    });

    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('should change time range when selector changes', async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockLatencyData) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockModeData) });

    render(<PerformanceTrends autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Performance Trends')).toBeInTheDocument();
    });

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: '6' } });

    // Should trigger new fetch with updated time range
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('hours=6')
      );
    });
  });

  it('should show empty state when no data', async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ data: [] }) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ data: [] }) });

    render(<PerformanceTrends autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('No latency data available yet.')).toBeInTheDocument();
    });
  });

  it('should auto-refresh when enabled', async () => {
    jest.useFakeTimers();
    
    mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(mockLatencyData) });

    render(<PerformanceTrends autoRefresh={true} refreshInterval={5} />);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(2); // Initial fetch for both endpoints
    });

    // Advance timer
    jest.advanceTimersByTime(5000);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(4); // Refresh fetch
    });

    jest.useRealTimers();
  });

  it('should use API_BASE_URL from environment', async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockLatencyData) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockModeData) });

    render(<PerformanceTrends autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/metrics/adaptive/timeseries')
      );
    });
  });
});
