'use client';

/**
 * Suspense Provider
 * 
 * Provides Suspense boundaries for async components
 */

import React, { Suspense, ReactNode } from 'react';
import { ErrorBoundary } from 'react-error-boundary';

interface SuspenseProviderProps {
  children: ReactNode;
  fallback?: ReactNode;
  errorFallback?: ReactNode;
}

// Default loading fallback
const DefaultLoadingFallback = () => (
  <div className="flex items-center justify-center min-h-[200px]">
    <div className="flex flex-col items-center gap-3">
      <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
      <p className="text-sm text-gray-600 dark:text-gray-400">Loading...</p>
    </div>
  </div>
);

// Default error fallback
const DefaultErrorFallback = ({ error, resetErrorBoundary }: any) => (
  <div className="flex items-center justify-center min-h-[200px] p-4">
    <div className="max-w-md w-full bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
      <div className="flex items-start gap-3">
        <svg className="w-6 h-6 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-red-900 dark:text-red-100 mb-1">
            Something went wrong
          </h3>
          <p className="text-sm text-red-700 dark:text-red-300 mb-3">
            {error?.message || 'An unexpected error occurred'}
          </p>
          <button
            onClick={resetErrorBoundary}
            className="text-sm font-medium text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 underline"
          >
            Try again
          </button>
        </div>
      </div>
    </div>
  </div>
);

export const SuspenseProvider: React.FC<SuspenseProviderProps> = ({
  children,
  fallback = <DefaultLoadingFallback />,
  errorFallback,
}) => {
  const ErrorFallbackComponent = errorFallback 
    ? ({ error, resetErrorBoundary }: any) => <>{errorFallback}</>
    : DefaultErrorFallback;

  return (
    <ErrorBoundary
      FallbackComponent={ErrorFallbackComponent}
      onReset={() => window.location.reload()}
    >
      <Suspense fallback={fallback}>
        {children}
      </Suspense>
    </ErrorBoundary>
  );
};

// Reusable Suspense wrapper component
export const WithSuspense = ({ 
  children, 
  fallback,
  errorFallback 
}: SuspenseProviderProps) => (
  <SuspenseProvider fallback={fallback} errorFallback={errorFallback}>
    {children}
  </SuspenseProvider>
);
