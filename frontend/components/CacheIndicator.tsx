'use client';

import React from 'react';
import { Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CacheIndicatorProps {
  isCached: boolean;
  similarity?: number;
  cacheType?: 'exact' | 'semantic';
  className?: string;
}

export default function CacheIndicator({
  isCached,
  similarity,
  cacheType,
  className
}: CacheIndicatorProps) {
  if (!isCached) return null;

  const isExact = cacheType === 'exact';
  const similarityPercent = similarity ? Math.round(similarity * 100) : 100;

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium',
        isExact
          ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800'
          : 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800',
        className
      )}
      title={
        isExact
          ? 'Response retrieved from cache (exact match)'
          : `Response retrieved from cache (${similarityPercent}% similar)`
      }
    >
      <Zap className="w-3 h-3" />
      <span>
        {isExact ? 'Cached' : `Similar (${similarityPercent}%)`}
      </span>
      {!isExact && similarity && (
        <div className="ml-1 flex items-center gap-0.5">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className={cn(
                'w-1 h-2 rounded-sm',
                i < Math.floor(similarity * 5)
                  ? 'bg-blue-600 dark:bg-blue-400'
                  : 'bg-blue-200 dark:bg-blue-800'
              )}
            />
          ))}
        </div>
      )}
    </div>
  );
}
