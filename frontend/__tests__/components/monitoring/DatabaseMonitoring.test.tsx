/**
 * Tests for DatabaseMonitoring component
 * @jest-environment jsdom
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import DatabaseMonitoring from '@/components/monitoring/DatabaseMonitoring';

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock StatCard component
jest.mock('@/components/charts/StatCard', () => {
  return function MockStatCard({ title, value }: { title: string; value: string | number }) {
    return (
      <div data-testid="stat-card">
        <span>{title}</span>
        <span>{value}</span>
      </div>
    );
  };
});

const mockPgMetrics = {
  detailed: {
    pool_size: 20,
    checked_in: 15,
    checked_out: 5,
    overflow: 0,
    utilization_percent: 25,
    health_status: 'healthy',
    total_checkouts: 1500,
    avg_connection_duration_ms: 45.5,
    long_connections_count: 0,
    potential_leaks_count: 0,
  },
};

const mockMilvusMetrics = {
  stats: {
    total_connections: 5,
    in_use: 2,
    available: 3,
    collection_size: 10000,
    index_type: 'IVF_FLAT',
  },
};

const mockHealthData = {
  postgresql: {
    status: 'healthy',
    message: 'All connections healthy',
    utilization: 25,
  },
  milvus: {
    status: 'healthy',
    message: 'Connected',
  },
  overall_status: 'healthy',
};

describe('DatabaseMonitoring', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render loading state initially', () => {
    mockFetch.mockImplementation(() => new Promise(() => {}));
    
    render(<DatabaseMonitoring autoRefresh={false} refreshInterval={30} />);
    
    expect(screen.getByText('Loading database metrics...')).toBeInTheDocument();
  });

  it('should render metrics after successful fetch', async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockPgMetrics) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockMilvusMetrics) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockHealthData) });

    render(<DatabaseMonitoring autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Database Monitoring')).toBeInTheDocument();
    });

    expect(screen.getByText('PostgreSQL')).toBeInTheDocument();
    expect(screen.getByText('Milvus')).toBeInTheDocument();
  });

  it('should render error state on fetch failure', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'));

    render(<DatabaseMonitoring autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Error loading metrics')).toBeInTheDocument();
    });
  });

  it('should display PostgreSQL pool details', async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockPgMetrics) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockMilvusMetrics) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockHealthData) });

    render(<DatabaseMonitoring autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Connection Pool Details')).toBeInTheDocument();
    });

    expect(screen.getByText('Checked In')).toBeInTheDocument();
    expect(screen.getByText('Checked Out')).toBeInTheDocument();
    expect(screen.getByText('Overflow')).toBeInTheDocument();
  });

  it('should display Milvus connection status', async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockPgMetrics) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockMilvusMetrics) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockHealthData) });

    render(<DatabaseMonitoring autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Connection Pool Status')).toBeInTheDocument();
    });

    expect(screen.getByText('IVF_FLAT')).toBeInTheDocument();
  });

  it('should display overall health status', async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockPgMetrics) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockMilvusMetrics) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockHealthData) });

    render(<DatabaseMonitoring autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('HEALTHY')).toBeInTheDocument();
    });
  });

  it('should show warnings for connection issues', async () => {
    const metricsWithWarnings = {
      detailed: {
        ...mockPgMetrics.detailed,
        long_connections_count: 3,
        potential_leaks_count: 1,
      },
    };

    mockFetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(metricsWithWarnings) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockMilvusMetrics) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockHealthData) });

    render(<DatabaseMonitoring autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText(/3 long-lived connection/)).toBeInTheDocument();
    });

    expect(screen.getByText(/1 potential connection leak/)).toBeInTheDocument();
  });

  it('should auto-refresh when enabled', async () => {
    jest.useFakeTimers();
    
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockPgMetrics) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockMilvusMetrics) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockHealthData) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockPgMetrics) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockMilvusMetrics) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockHealthData) });

    render(<DatabaseMonitoring autoRefresh={true} refreshInterval={5} />);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(3); // Initial fetch for 3 endpoints
    });

    jest.advanceTimersByTime(5000);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(6); // Refresh fetch
    });

    jest.useRealTimers();
  });

  it('should display last update time', async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockPgMetrics) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockMilvusMetrics) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockHealthData) });

    render(<DatabaseMonitoring autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
    });
  });
});
