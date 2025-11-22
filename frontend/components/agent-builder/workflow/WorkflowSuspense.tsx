import { Suspense, ReactNode } from 'react';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

/**
 * Loading skeleton for workflow canvas
 */
export function WorkflowLoadingSkeleton() {
  return (
    <div className="h-full w-full p-4 space-y-4">
      {/* Toolbar skeleton */}
      <div className="flex items-center gap-2 p-4 border-b">
        <Skeleton className="h-9 w-20" />
        <Skeleton className="h-9 w-20" />
        <Skeleton className="h-9 w-20" />
        <div className="flex-1" />
        <Skeleton className="h-9 w-24" />
      </div>

      {/* Tabs skeleton */}
      <div className="flex gap-2 border-b pb-2">
        <Skeleton className="h-10 w-24" />
        <Skeleton className="h-10 w-24" />
        <Skeleton className="h-10 w-24" />
        <Skeleton className="h-10 w-24" />
      </div>

      {/* Canvas skeleton */}
      <div className="flex-1 grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <Skeleton className="h-6 w-32 mb-4" />
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-3/4" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <Skeleton className="h-6 w-32 mb-4" />
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-3/4" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <Skeleton className="h-6 w-32 mb-4" />
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-3/4" />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

/**
 * Error fallback for workflow canvas
 */
export function WorkflowErrorFallback({
  error,
  resetErrorBoundary,
}: {
  error?: Error;
  resetErrorBoundary?: () => void;
}) {
  return (
    <div className="h-full w-full flex items-center justify-center p-8">
      <Card className="max-w-md w-full">
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <AlertCircle className="h-8 w-8 text-destructive flex-shrink-0" />
            <div className="flex-1">
              <h3 className="text-lg font-semibold mb-2">
                Workflow Error
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                {error?.message || 'An unexpected error occurred while loading the workflow.'}
              </p>
              {error?.stack && (
                <details className="text-xs text-muted-foreground mb-4">
                  <summary className="cursor-pointer hover:text-foreground">
                    View error details
                  </summary>
                  <pre className="mt-2 p-2 bg-muted rounded overflow-auto max-h-40">
                    {error.stack}
                  </pre>
                </details>
              )}
              <div className="flex gap-2">
                <Button
                  onClick={resetErrorBoundary}
                  variant="default"
                  size="sm"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Try Again
                </Button>
                <Button
                  onClick={() => window.location.reload()}
                  variant="outline"
                  size="sm"
                >
                  Reload Page
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface WorkflowSuspenseProps {
  children: ReactNode;
  fallback?: ReactNode;
  errorFallback?: ReactNode;
}

/**
 * Wrapper component that provides Suspense and Error Boundary for workflow components
 */
export function WorkflowSuspense({
  children,
  fallback,
  errorFallback,
}: WorkflowSuspenseProps) {
  return (
    <ErrorBoundary
      fallback={errorFallback || <WorkflowErrorFallback />}
      onReset={() => {
        // Clear any cached data or state
        console.log('Resetting workflow error boundary');
      }}
    >
      <Suspense fallback={fallback || <WorkflowLoadingSkeleton />}>
        {children}
      </Suspense>
    </ErrorBoundary>
  );
}
