/**
 * Tests for ThresholdTuning component
 * @jest-environment jsdom
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ThresholdTuning from '@/components/monitoring/ThresholdTuning';

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

const mockConfigData = {
  adaptive_routing: {
    enabled: true,
    complexity_threshold_simple: 0.35,
    complexity_threshold_complex: 0.70,
  },
};

const mockMetricsData = {
  mode_distribution: {
    percentages: { fast: 45, balanced: 35, deep: 20 },
  },
  thresholds: {
    current: {
      simple_threshold: 0.35,
      complex_threshold: 0.70,
      timestamp: '2024-01-01T10:00:00Z',
      reason: 'Initial configuration',
    },
    history: [
      {
        simple_threshold: 0.30,
        complex_threshold: 0.65,
        timestamp: '2024-01-01T08:00:00Z',
        reason: 'Previous configuration',
      },
    ],
  },
};

describe('ThresholdTuning', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render loading state initially', () => {
    mockFetch.mockImplementation(() => new Promise(() => {}));
    
    render(<ThresholdTuning isAdmin={false} autoRefresh={false} refreshInterval={30} />);
    
    expect(screen.getByText('Loading threshold configuration...')).toBeInTheDocument();
  });

  it('should render configuration after successful fetch', async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockConfigData) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockMetricsData) });

    render(<ThresholdTuning isAdmin={false} autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Threshold Tuning')).toBeInTheDocument();
    });

    expect(screen.getByText('Current Thresholds')).toBeInTheDocument();
    expect(screen.getByText('Current vs Target Distribution')).toBeInTheDocument();
  });

  it('should show view-only message for non-admin users', async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockConfigData) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockMetricsData) });

    render(<ThresholdTuning isAdmin={false} autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText(/View Only/)).toBeInTheDocument();
    });
  });

  it('should show simulation buttons for admin users', async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockConfigData) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockMetricsData) });

    render(<ThresholdTuning isAdmin={true} autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Simulate Impact')).toBeInTheDocument();
    });

    expect(screen.getByText('Reset')).toBeInTheDocument();
  });

  it('should render error state on fetch failure', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'));

    render(<ThresholdTuning isAdmin={false} autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Error loading configuration')).toBeInTheDocument();
    });
  });

  it('should display threshold history', async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockConfigData) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockMetricsData) });

    render(<ThresholdTuning isAdmin={false} autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Threshold Change History')).toBeInTheDocument();
    });

    expect(screen.getByText('Previous configuration')).toBeInTheDocument();
  });

  it('should run simulation when button clicked', async () => {
    jest.useFakeTimers();
    
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockConfigData) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockMetricsData) });

    render(<ThresholdTuning isAdmin={true} autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Simulate Impact')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Simulate Impact'));
    
    expect(screen.getByText('Simulating...')).toBeInTheDocument();

    jest.advanceTimersByTime(1000);

    await waitFor(() => {
      expect(screen.getByText('Simulation Results')).toBeInTheDocument();
    });

    jest.useRealTimers();
  });

  it('should disable sliders for non-admin users', async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockConfigData) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockMetricsData) });

    render(<ThresholdTuning isAdmin={false} autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Threshold Tuning')).toBeInTheDocument();
    });

    const sliders = screen.getAllByRole('slider');
    sliders.forEach(slider => {
      expect(slider).toBeDisabled();
    });
  });
});
