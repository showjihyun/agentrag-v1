'use client';

import React from 'react';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent, CardHeader } from '@/components/ui/card';

interface ProgressiveLoaderProps {
  type: 'card' | 'list' | 'table' | 'chart' | 'stats';
  count?: number;
  showShimmer?: boolean;
}

export function ProgressiveLoader({ 
  type, 
  count = 3,
  showShimmer = true 
}: ProgressiveLoaderProps) {
  const shimmerClass = showShimmer
    ? 'animate-pulse bg-gradient-to-r from-transparent via-white/10 to-transparent'
    : '';

  if (type === 'stats') {
    return (
      <>
        {Array.from({ length: count }).map((_, i) => (
          <Card key={i} className="relative overflow-hidden">
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-20 mb-2" />
              <Skeleton className="h-3 w-32" />
            </CardContent>
            {showShimmer && (
              <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-white/10 to-transparent" />
            )}
          </Card>
        ))}
      </>
    );
  }

  if (type === 'list') {
    return (
      <div className="space-y-3">
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            className="flex items-start gap-3 p-3 rounded-lg border relative overflow-hidden"
          >
            <Skeleton className="h-10 w-10 rounded-full flex-shrink-0" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
              <Skeleton className="h-3 w-1/4" />
            </div>
            {showShimmer && (
              <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-white/10 to-transparent" />
            )}
          </div>
        ))}
      </div>
    );
  }

  if (type === 'chart') {
    return (
      <Card className="relative overflow-hidden">
        <CardHeader>
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-end gap-2 h-32">
                {Array.from({ length: 7 }).map((_, j) => (
                  <Skeleton
                    key={j}
                    className="flex-1"
                    style={{
                      height: `${Math.random() * 80 + 20}%`,
                    }}
                  />
                ))}
              </div>
            ))}
          </div>
        </CardContent>
        {showShimmer && (
          <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-white/10 to-transparent" />
        )}
      </Card>
    );
  }

  if (type === 'table') {
    return (
      <div className="space-y-2">
        <div className="flex gap-4 pb-2 border-b">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-4 flex-1" />
          ))}
        </div>
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="flex gap-4 py-3 relative overflow-hidden">
            {Array.from({ length: 4 }).map((_, j) => (
              <Skeleton key={j} className="h-4 flex-1" />
            ))}
            {showShimmer && (
              <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-white/10 to-transparent" />
            )}
          </div>
        ))}
      </div>
    );
  }

  // Default: card
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <Card key={i} className="relative overflow-hidden">
          <CardHeader>
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </CardHeader>
          <CardContent className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
            <Skeleton className="h-4 w-4/6" />
          </CardContent>
          {showShimmer && (
            <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-white/10 to-transparent" />
          )}
        </Card>
      ))}
    </>
  );
}

// Add shimmer animation to global CSS
// @keyframes shimmer {
//   100% {
//     transform: translateX(100%);
//   }
// }
