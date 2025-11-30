/**
 * Tests for AlertsPanel component
 * @jest-environment jsdom
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import AlertsPanel from '@/components/monitoring/AlertsPanel';

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

const mockAlerts = {
  alerts: [
    {
      level: 'critical',
      metric: 'latency_p95',
      message: 'High latency detected',
      current_value: 5.5,
      threshold_value: 3.0,
      timestamp: '2024-01-01T10:00:00Z',
      recommendations: ['Scale up resources', 'Check database connections'],
    },
    {
      level: 'warning',
      metric: 'cache_hit_rate',
      message: 'Low cache hit rate',
      current_value: 45,
      threshold_value: 60,
      timestamp: '2024-01-01T09:00:00Z',
      recommendations: ['Increase cache TTL'],
    },
    {
      level: 'info',
      metric: 'query_count',
      message: 'Query volume increasing',
      current_value: 1000,
      threshold_value: 800,
      timestamp: '2024-01-01T08:00:00Z',
      recommendations: [],
    },
  ],
};

describe('AlertsPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render loading state initially', () => {
    mockFetch.mockImplementation(() => new Promise(() => {}));
    
    render(<AlertsPanel autoRefresh={false} refreshInterval={30} />);
    
    expect(screen.getByText('Loading alerts...')).toBeInTheDocument();
  });

  it('should render alerts after successful fetch', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockAlerts),
    });

    render(<AlertsPanel autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Performance Alerts')).toBeInTheDocument();
    });

    expect(screen.getByText('High latency detected')).toBeInTheDocument();
    expect(screen.getByText('Low cache hit rate')).toBeInTheDocument();
  });

  it('should render error state on fetch failure', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'));

    render(<AlertsPanel autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Error loading alerts')).toBeInTheDocument();
    });
  });

  it('should filter alerts by level', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockAlerts),
    });

    render(<AlertsPanel autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Performance Alerts')).toBeInTheDocument();
    });

    // Click critical filter
    fireEvent.click(screen.getByText(/Critical \(1\)/));

    // Should only show critical alert
    expect(screen.getByText('High latency detected')).toBeInTheDocument();
    expect(screen.queryByText('Low cache hit rate')).not.toBeInTheDocument();
  });

  it('should show all clear message when no alerts', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ alerts: [] }),
    });

    render(<AlertsPanel autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('All Clear!')).toBeInTheDocument();
    });
  });

  it('should display alert counts correctly', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockAlerts),
    });

    render(<AlertsPanel autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Critical Alerts')).toBeInTheDocument();
    });

    // Check summary cards exist
    expect(screen.getByText('Warnings')).toBeInTheDocument();
    expect(screen.getByText('Info')).toBeInTheDocument();
  });

  it('should display recommendations', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockAlerts),
    });

    render(<AlertsPanel autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Scale up resources')).toBeInTheDocument();
    });
  });

  it('should auto-refresh when enabled', async () => {
    jest.useFakeTimers();
    
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockAlerts),
    });

    render(<AlertsPanel autoRefresh={true} refreshInterval={5} />);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    jest.advanceTimersByTime(5000);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });

    jest.useRealTimers();
  });
});
