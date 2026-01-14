'use client';

import React from 'react';

/**
 * Message Loading Skeleton Component
 * 
 * Skeleton displayed while messages are loading,
 * prevents layout shift and improves perceived performance.
 */
export const MessageSkeleton: React.FC = () => {
  return (
    <div className="flex justify-start animate-fadeIn">
      <div className="w-full max-w-3xl bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-md">
        <div className="animate-pulse">
          <div className="flex items-start gap-3">
            {/* Avatar skeleton */}
            <div className="flex-shrink-0 w-8 h-8 bg-gray-300 dark:bg-gray-700 rounded-full" />
            
            <div className="flex-1 space-y-3">
              {/* Name skeleton */}
              <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-20" />
              
              {/* Text line skeleton */}
              <div className="space-y-2">
                <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-full" />
                <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-5/6" />
                <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-4/6" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * Component that displays multiple message skeletons
 */
export const MessageSkeletonList: React.FC<{ count?: number }> = ({ count = 1 }) => {
  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <MessageSkeleton key={index} />
      ))}
    </>
  );
};

export default MessageSkeleton;
