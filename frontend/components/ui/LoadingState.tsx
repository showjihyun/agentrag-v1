'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface LoadingStateProps {
  variant?: 'spinner' | 'dots' | 'pulse';
  size?: 'sm' | 'md' | 'lg';
  message?: string;
  className?: string;
}

export function LoadingState({
  variant = 'spinner',
  size = 'md',
  message,
  className
}: LoadingStateProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  };

  return (
    <div className={cn('flex flex-col items-center justify-center gap-3', className)}>
      {variant === 'spinner' && (
        <div
          className={cn(
            'animate-spin rounded-full border-2 border-gray-300 dark:border-gray-600 border-t-blue-600 dark:border-t-blue-400',
            sizeClasses[size]
          )}
          role="status"
          aria-label="Loading"
        />
      )}

      {variant === 'dots' && (
        <div className="flex gap-2" role="status" aria-label="Loading">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className={cn(
                'rounded-full bg-blue-600 dark:bg-blue-400 animate-bounce',
                size === 'sm' && 'w-2 h-2',
                size === 'md' && 'w-3 h-3',
                size === 'lg' && 'w-4 h-4'
              )}
              style={{
                animationDelay: `${i * 0.15}s`,
                animationDuration: '0.6s'
              }}
            />
          ))}
        </div>
      )}

      {variant === 'pulse' && (
        <div
          className={cn(
            'rounded-full bg-blue-600 dark:bg-blue-400 animate-pulse',
            sizeClasses[size]
          )}
          role="status"
          aria-label="Loading"
        />
      )}

      {message && (
        <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
          {message}
        </p>
      )}
    </div>
  );
}

interface SkeletonProps {
  className?: string;
  count?: number;
}

export function Skeleton({ className, count = 1 }: SkeletonProps) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={cn(
            'animate-pulse bg-gray-200 dark:bg-gray-700 rounded',
            className
          )}
          role="status"
          aria-label="Loading content"
        />
      ))}
    </>
  );
}
