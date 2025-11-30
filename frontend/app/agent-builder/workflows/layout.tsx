'use client';

import { Suspense } from 'react';
import { ErrorBoundary } from '@/components/error-boundary';
import { WorkflowListSkeleton } from '@/components/workflow/WorkflowSkeleton';

export default function WorkflowsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ErrorBoundary>
      <Suspense fallback={<WorkflowListSkeleton />}>
        {children}
      </Suspense>
    </ErrorBoundary>
  );
}
