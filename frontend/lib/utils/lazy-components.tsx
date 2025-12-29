/**
 * Lazy-loaded components for code splitting
 * Reduces initial bundle size by loading components on demand
 */

import dynamic from 'next/dynamic';
import { ComponentType } from 'react';

// Loading fallback component
const LoadingFallback = () => (
  <div className="flex items-center justify-center p-8">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
  </div>
);

// Heavy components - loaded on demand
export const LazyMonitoringDashboard = dynamic(
  () => import('@/components/monitoring/AdaptiveMonitoringDashboard'),
  {
    loading: () => <LoadingFallback />,
    ssr: false,
  }
);

export const LazyBatchUpload = dynamic(
  () => import('@/components/BatchUpload'),
  {
    loading: () => <LoadingFallback />,
  }
);

export const LazyUserDashboard = dynamic(
  () => import('@/components/UserDashboard'),
  {
    loading: () => <LoadingFallback />,
  }
);

export const LazyConversationHistory = dynamic(
  () => import('@/components/ConversationHistory'),
  {
    loading: () => <LoadingFallback />,
  }
);

export const LazyAnswerFeedback = dynamic(
  () => import('@/components/AnswerFeedback'),
  {
    loading: () => <LoadingFallback />,
  }
);

// Chart components - loaded on demand
export const LazyUsageChart = dynamic(
  () => import('@/components/charts/UsageChart'),
  {
    loading: () => <LoadingFallback />,
    ssr: false,
  }
);

export const LazyPieChart = dynamic(
  () => import('@/components/charts/PieChart'),
  {
    loading: () => <LoadingFallback />,
    ssr: false,
  }
);

// Utility function for creating lazy components with custom loading
export function createLazyComponent<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  options?: {
    loading?: ComponentType;
    ssr?: boolean;
  }
) {
  const LoadingComponent = options?.loading || LoadingFallback;
  return dynamic(importFn, {
    loading: () => <LoadingComponent />,
    ssr: options?.ssr ?? true,
  });
}
