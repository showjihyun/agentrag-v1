/**
 * Loading Spinner Component with Performance Tracking
 */

'use client';

import { useEffect, useState } from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  message?: string;
  timeout?: number; // milliseconds
  onTimeout?: () => void;
  showElapsedTime?: boolean;
}

export default function LoadingSpinner({
  size = 'md',
  message = 'Loading...',
  timeout,
  onTimeout,
  showElapsedTime = false,
}: LoadingSpinnerProps) {
  const [elapsedTime, setElapsedTime] = useState(0);
  const [timedOut, setTimedOut] = useState(false);

  useEffect(() => {
    const startTime = Date.now();
    
    // Update elapsed time every 100ms
    const elapsedInterval = setInterval(() => {
      setElapsedTime(Date.now() - startTime);
    }, 100);

    // Handle timeout
    let timeoutId: NodeJS.Timeout | undefined;
    if (timeout) {
      timeoutId = setTimeout(() => {
        setTimedOut(true);
        if (onTimeout) onTimeout();
      }, timeout);
    }

    return () => {
      clearInterval(elapsedInterval);
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [timeout, onTimeout]);

  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-3',
    lg: 'w-12 h-12 border-4',
  };

  const formatTime = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  return (
    <div className="flex flex-col items-center justify-center space-y-3">
      {/* Spinner */}
      <div
        className={`${sizeClasses[size]} border-blue-200 border-t-blue-600 rounded-full animate-spin`}
        role="status"
        aria-label="Loading"
      />

      {/* Message */}
      {message && (
        <p className="text-gray-600 text-sm font-medium">{message}</p>
      )}

      {/* Elapsed Time */}
      {showElapsedTime && (
        <p className="text-gray-500 text-xs">
          {formatTime(elapsedTime)}
        </p>
      )}

      {/* Timeout Warning */}
      {timedOut && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 max-w-sm">
          <p className="text-yellow-800 text-sm">
            ⚠️ This is taking longer than expected...
          </p>
          <p className="text-yellow-600 text-xs mt-1">
            The request may be processing a large amount of data.
          </p>
        </div>
      )}
    </div>
  );
}
