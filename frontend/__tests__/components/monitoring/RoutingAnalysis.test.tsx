/**
 * Tests for RoutingAnalysis component
 * @jest-environment jsdom
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import RoutingAnalysis from '@/components/monitoring/RoutingAnalysis';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { expect } from '@playwright/test';
import { it } from 'zod/v4/locales';
import { beforeEach } from 'node:test';
import { describe } from 'node:test';

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

const mockDashboardData = {
  complexity_distribution: {
    simple: 500,
    medium: 350,
    complex: 150,
  },
  mode_distribution: {
    counts: { fast: 500, balanced: 350, deep: 150 },
    percentages: { fast: 50, balanced: 35, deep: 15 },
  },
  escalations: {
    total: 45,
    rate_percent: 4.5,
    by_transition: {
      fast_to_balanced: 30,
      balanced_to_deep: 15,
    },
  },
  overview: {
    total_queries: 1000,
    avg_routing_confidence: 0.88,
  },
};

describe('RoutingAnalysis', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render loading state initially', () => {
    mockFetch.mockImplementation(() => new Promise(() => {}));
    
    render(<RoutingAnalysis autoRefresh={false} refreshInterval={30} />);
    
    expect(screen.getByText('Loading routing analysis...')).toBeInTheDocument();
  });

  it('should render analysis after successful fetch', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDashboardData),
    });

    render(<RoutingAnalysis autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Routing Analysis')).toBeInTheDocument();
    });

    expect(screen.getByText('Routing Accuracy')).toBeInTheDocument();
    expect(screen.getByText('Query Complexity Distribution')).toBeInTheDocument();
    expect(screen.getByText('Escalation Patterns')).toBeInTheDocument();
  });

  it('should render error state on fetch failure', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'));

    render(<RoutingAnalysis autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Error loading routing analysis')).toBeInTheDocument();
    });
  });

  it('should display routing confidence', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDashboardData),
    });

    render(<RoutingAnalysis autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('88.0%')).toBeInTheDocument();
    });

    expect(screen.getByText('Confidence')).toBeInTheDocument();
  });

  it('should display complexity distribution', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDashboardData),
    });

    render(<RoutingAnalysis autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Simple')).toBeInTheDocument();
    });

    expect(screen.getByText('Medium')).toBeInTheDocument();
    expect(screen.getByText('Complex')).toBeInTheDocument();
  });

  it('should display escalation statistics', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDashboardData),
    });

    render(<RoutingAnalysis autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Total Escalations')).toBeInTheDocument();
    });

    expect(screen.getByText('45')).toBeInTheDocument();
    expect(screen.getByText('4.5%')).toBeInTheDocument();
  });

  it('should display escalation transitions', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDashboardData),
    });

    render(<RoutingAnalysis autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('Escalation Transitions')).toBeInTheDocument();
    });

    // Check that transitions section exists with data
    expect(screen.getByText('30')).toBeInTheDocument(); // fast_to_balanced count
    expect(screen.getByText('15')).toBeInTheDocument(); // balanced_to_deep count
  });

  it('should show empty state when no complexity data', async () => {
    const emptyData = {
      ...mockDashboardData,
      complexity_distribution: {},
    };

    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(emptyData),
    });

    render(<RoutingAnalysis autoRefresh={false} refreshInterval={30} />);

    await waitFor(() => {
      expect(screen.getByText('No complexity data available yet.')).toBeInTheDocument();
    });
  });

  it('should auto-refresh when enabled', async () => {
    jest.useFakeTimers();
    
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDashboardData),
    });

    render(<RoutingAnalysis autoRefresh={true} refreshInterval={5} />);

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
