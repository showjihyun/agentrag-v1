'use client';

import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader } from '@/components/ui/card';

// Enhanced Skeleton with shimmer animation
export function SkeletonShimmer({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-md bg-gray-200 dark:bg-gray-700',
        'before:absolute before:inset-0',
        'before:bg-gradient-to-r before:from-transparent before:via-white/20 before:to-transparent',
        'before:animate-[shimmer_1.5s_infinite]',
        className
      )}
    />
  );
}

// Card skeleton for list views
export function CardSkeleton({ showFooter = true }: { showFooter?: boolean }) {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="space-y-2">
        <div className="flex items-center justify-between">
          <SkeletonShimmer className="h-6 w-3/4" />
          <SkeletonShimmer className="h-8 w-8 rounded-full" />
        </div>
        <SkeletonShimmer className="h-4 w-full" />
        <SkeletonShimmer className="h-4 w-2/3" />
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-2">
          <SkeletonShimmer className="h-6 w-20 rounded-full" />
          <SkeletonShimmer className="h-6 w-24 rounded-full" />
          <SkeletonShimmer className="h-6 w-16 rounded-full" />
        </div>
      </CardContent>
      {showFooter && (
        <div className="px-6 py-3 border-t flex justify-between">
          <SkeletonShimmer className="h-4 w-20" />
          <SkeletonShimmer className="h-4 w-32" />
        </div>
      )}
    </Card>
  );
}

// Grid of card skeletons
export function CardGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}

// Stats card skeleton
export function StatsSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <Card key={i}>
          <CardHeader className="pb-2">
            <SkeletonShimmer className="h-4 w-24" />
          </CardHeader>
          <CardContent>
            <SkeletonShimmer className="h-8 w-16 mb-2" />
            <SkeletonShimmer className="h-3 w-32" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// Table skeleton
export function TableSkeleton({ rows = 5, columns = 4 }: { rows?: number; columns?: number }) {
  return (
    <div className="border rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-muted/50 p-4 flex gap-4">
        {Array.from({ length: columns }).map((_, i) => (
          <SkeletonShimmer key={i} className="h-4 flex-1" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="p-4 flex gap-4 border-t">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <SkeletonShimmer
              key={colIndex}
              className={cn('h-4 flex-1', colIndex === 0 && 'w-1/4 flex-none')}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

// Chat message skeleton
export function ChatMessageSkeleton({ isUser = false }: { isUser?: boolean }) {
  return (
    <div className={cn('flex gap-3', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser && <SkeletonShimmer className="h-8 w-8 rounded-full flex-shrink-0" />}
      <div className={cn('space-y-2', isUser ? 'items-end' : 'items-start')}>
        <SkeletonShimmer className={cn('h-16 rounded-2xl', isUser ? 'w-48' : 'w-64')} />
      </div>
      {isUser && <SkeletonShimmer className="h-8 w-8 rounded-full flex-shrink-0" />}
    </div>
  );
}

// Chat skeleton
export function ChatSkeleton() {
  return (
    <div className="space-y-4 p-4">
      <ChatMessageSkeleton />
      <ChatMessageSkeleton isUser />
      <ChatMessageSkeleton />
      <ChatMessageSkeleton isUser />
      <ChatMessageSkeleton />
    </div>
  );
}

// Form skeleton
export function FormSkeleton({ fields = 4 }: { fields?: number }) {
  return (
    <div className="space-y-6">
      {Array.from({ length: fields }).map((_, i) => (
        <div key={i} className="space-y-2">
          <SkeletonShimmer className="h-4 w-24" />
          <SkeletonShimmer className="h-10 w-full rounded-md" />
        </div>
      ))}
      <div className="flex gap-2 pt-4">
        <SkeletonShimmer className="h-10 w-24 rounded-md" />
        <SkeletonShimmer className="h-10 w-20 rounded-md" />
      </div>
    </div>
  );
}

// Execution trace skeleton
export function ExecutionTraceSkeleton({ nodes = 4 }: { nodes?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: nodes }).map((_, i) => (
        <div key={i} className="border rounded-lg p-3">
          <div className="flex items-center gap-3">
            <SkeletonShimmer className="h-5 w-5 rounded-full" />
            <SkeletonShimmer className="h-4 flex-1" />
            <SkeletonShimmer className="h-6 w-16 rounded-full" />
          </div>
        </div>
      ))}
    </div>
  );
}

// Page loading overlay
export function PageLoadingOverlay({ message = '로딩 중...' }: { message?: string }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="flex flex-col items-center gap-4">
        <div className="relative">
          <div className="h-12 w-12 rounded-full border-4 border-primary/20" />
          <div className="absolute inset-0 h-12 w-12 rounded-full border-4 border-primary border-t-transparent animate-spin" />
        </div>
        <p className="text-sm text-muted-foreground">{message}</p>
      </div>
    </div>
  );
}

// Inline loading spinner
export function InlineSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = {
    sm: 'h-4 w-4 border-2',
    md: 'h-6 w-6 border-2',
    lg: 'h-8 w-8 border-3',
  };

  return (
    <div
      className={cn(
        'rounded-full border-primary/20 border-t-primary animate-spin',
        sizeClasses[size]
      )}
    />
  );
}

// Pulse dot indicator
export function PulseDot({ color = 'primary' }: { color?: 'primary' | 'success' | 'warning' | 'error' }) {
  const colorClasses = {
    primary: 'bg-primary',
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    error: 'bg-red-500',
  };

  return (
    <span className="relative flex h-3 w-3">
      <span
        className={cn(
          'animate-ping absolute inline-flex h-full w-full rounded-full opacity-75',
          colorClasses[color]
        )}
      />
      <span className={cn('relative inline-flex rounded-full h-3 w-3', colorClasses[color])} />
    </span>
  );
}
