'use client';

import { Suspense } from 'react';
import { WorkflowErrorBoundary } from '@/components/workflow/WorkflowErrorBoundary';
import { ExecutionDetailSkeleton } from '@/components/workflow/WorkflowSkeleton';

export default function WorkflowDetailLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <WorkflowErrorBoundary>
      <Suspense fallback={<ExecutionDetailSkeleton />}>
        {children}
      </Suspense>
    </WorkflowErrorBoundary>
  );
}
