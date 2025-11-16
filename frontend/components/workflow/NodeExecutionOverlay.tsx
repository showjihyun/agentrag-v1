'use client';

import React, { useState, useEffect } from 'react';
import { Clock, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { NodeStatus } from './ExecutionStatusBadge';

type ExecutionStatus = NodeStatus | 'failed';

interface NodeExecutionOverlayProps {
  status?: ExecutionStatus;
  startTime?: number;
  endTime?: number;
  error?: string;
  progress?: number;
  showDetails?: boolean;
}

export function NodeExecutionOverlay({
  status,
  startTime,
  endTime,
  error,
  progress,
  showDetails = true,
}: NodeExecutionOverlayProps) {
  const [elapsedTime, setElapsedTime] = useState(0);

  // Update elapsed time for running nodes
  useEffect(() => {
    if (status !== 'running' || !startTime) return;

    const interval = setInterval(() => {
      const now = Date.now();
      const elapsed = Math.floor((now - startTime) / 1000);
      setElapsedTime(elapsed);
    }, 1000);

    return () => clearInterval(interval);
  }, [status, startTime]);

  // Calculate duration for completed nodes
  const duration = startTime && endTime 
    ? Math.floor((endTime - startTime) / 1000)
    : elapsedTime;

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  if (!status || status === 'idle') return null;

  return (
    <div className="absolute inset-0 pointer-events-none">
      {/* Status Badge (Top Right) */}
      <div className="absolute -top-2 -right-2 pointer-events-auto">
        <div className={`
          w-6 h-6 rounded-full flex items-center justify-center shadow-md
          ${status === 'pending' ? 'bg-yellow-400' : ''}
          ${status === 'running' ? 'bg-blue-500' : ''}
          ${status === 'success' ? 'bg-green-500' : ''}
          ${status === 'failed' || status === 'error' ? 'bg-red-500' : ''}
          ${status === 'skipped' ? 'bg-gray-400' : ''}
        `}>
          {status === 'pending' && <Clock className="w-3 h-3 text-yellow-900" />}
          {status === 'running' && <Loader2 className="w-3 h-3 text-white animate-spin" />}
          {status === 'success' && <CheckCircle2 className="w-3 h-3 text-white" />}
          {(status === 'failed' || status === 'error') && <AlertCircle className="w-3 h-3 text-white" />}
        </div>
      </div>

      {/* Timer (Top Left) */}
      {showDetails && (status === 'running' || status === 'success') && duration > 0 && (
        <div className="absolute -top-2 -left-2 pointer-events-auto">
          <div className="bg-gray-900 text-white text-xs px-2 py-1 rounded shadow-md font-mono">
            {formatTime(duration)}
          </div>
        </div>
      )}

      {/* Progress Bar (Bottom) */}
      {status === 'running' && progress !== undefined && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200 overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {/* Animated Progress Bar (when progress unknown) */}
      {status === 'running' && progress === undefined && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200 overflow-hidden">
          <div className="h-full bg-blue-500 node-progress-fill" />
        </div>
      )}

      {/* Error Message (Tooltip) */}
      {(status === 'failed' || status === 'error') && error && showDetails && (
        <div className="absolute top-full left-0 mt-2 z-50 pointer-events-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-2 shadow-lg max-w-xs">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="text-xs text-red-800">
                {error}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
