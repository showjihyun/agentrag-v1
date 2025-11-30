/**
 * Tests for RealTimeOverview component
 * @jest-environment jsdom
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import RealTimeOverview from '@/components/monitoring/RealTimeOverview';

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

const mockDashboardData = {
  overview: {
    total_queries: 1500,
    time_range: { start: '2024-01-01T00:00:00Z', end: '2024-01-01T23:59:59Z' },
    avg_routing_confidence: 0.85,
    avg_routing_time_ms: 12.5,
  },
  mode_distribution: {
    counts: { fast: 750, balanced: 500, deep: 250 },
    percentages: { fast: 50, balanced: 33.3, deep: 16.7 },
  },
  latency: {
    average_by_mode: { fast: 0.5, balanced: 1.8, deep: 6.5 },
    p95_by_mode: { fast: 0.8, balanced: 2.5, deep: 10.0 },
  },
  cache_performance: {
    hit_rates: { fast: 75, balanced: 60, deep: 45 },
  },
  escalations: {
    total: 50,
    rate_percent: 3.3,
  },
};

describe('RealTimeOverview', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render loading state initially', () => {
    mockFetch.mockImplementation(() => new Promise(() => {}));
    
    render(<RealTimeOverview autoRefresh={false} refreshInterval={30} />);
    
    expect(screen.getByText('Loading metrics...')).toBeInTheDocument();
  });

  it('should render metrics after successful fetch', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDashboardData),
    });

    render(<RealTimeOverview autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Real-Time Overview')).toBeInTheDocument();
    });

    // Check key metrics
    expect(screen.getByText('1,500')).toBeInTheDocument(); // Total queries
    expect(screen.getByText('85.0%')).toBeInTheDocument(); // Routing confidence
    expect(screen.getByText('12.5ms')).toBeInTheDocument(); // Routing time
    expect(screen.getByText('3.3%')).toBeInTheDocument(); // Escalation rate
  });

  it('should render error state on fetch failure', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'));

    render(<RealTimeOverview autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Error loading metrics')).toBeInTheDocument();
    });

    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('should display mode distribution', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDashboardData),
    });

    render(<RealTimeOverview autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Mode Distribution')).toBeInTheDocument();
    });

    expect(screen.getByText(/50\.0%/)).toBeInTheDocument();
    expect(screen.getByText(/750 queries/)).toBeInTheDocument();
  });

  it('should display latency by mode', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDashboardData),
    });

    render(<RealTimeOverview autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Latency by Mode')).toBeInTheDocument();
    });

    expect(screen.getByText('0.50s')).toBeInTheDocument(); // Fast avg
    expect(screen.getByText('1.80s')).toBeInTheDocument(); // Balanced avg
  });

  it('should display cache performance', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDashboardData),
    });

    render(<RealTimeOverview autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Cache Performance')).toBeInTheDocument();
    });

    expect(screen.getByText('75%')).toBeInTheDocument();
    expect(screen.getByText('60%')).toBeInTheDocument();
    expect(screen.getByText('45%')).toBeInTheDocument();
  });

  it('should auto-refresh when enabled', async () => {
    jest.useFakeTimers();
    
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDashboardData),
    });

    render(<RealTimeOverview autoRefresh={true} refreshInterval={5} />);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    jest.advanceTimersByTime(5000);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });

    jest.useRealTimers();
  });

  it('should highlight high escalation rate', async () => {
    const highEscalationData = {
      ...mockDashboardData,
      escalations: { total: 300, rate_percent: 20 },
    };

    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(highEscalationData),
    });

    render(<RealTimeOverview autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('20.0%')).toBeInTheDocument();
    });
  });
});
