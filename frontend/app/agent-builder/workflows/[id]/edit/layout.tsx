'use client';

import { Suspense } from 'react';
import { WorkflowErrorBoundary } from '@/components/workflow/WorkflowErrorBoundary';
import { WorkflowEditorSkeleton } from '@/components/workflow/WorkflowSkeleton';

export default function WorkflowEditLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <WorkflowErrorBoundary>
      <Suspense fallback={<WorkflowEditorSkeleton />}>
        {children}
      </Suspense>
    </WorkflowErrorBoundary>
  );
}
