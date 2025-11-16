'use client';

import React, { useMemo } from 'react';
import { Play, Pause, Square, RotateCcw, Activity, Clock, CheckCircle2, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { NodeExecutionStatus } from '@/hooks/useWorkflowExecutionStream';
import { ExecutionStatusBadge } from './ExecutionStatusBadge';

interface ExecutionControlPanelProps {
  nodeStatuses: Record<string, NodeExecutionStatus>;
  isConnected: boolean;
  isComplete: boolean;
  executionStatus: string | null;
  retryCount?: number;
  maxRetries?: number;
  onStart?: () => void;
  onPause?: () => void;
  onStop?: () => void;
  onReset?: () => void;
}

export function ExecutionControlPanel({
  nodeStatuses,
  isConnected,
  isComplete,
  executionStatus,
  retryCount = 0,
  maxRetries = 3,
  onStart,
  onPause,
  onStop,
  onReset,
}: ExecutionControlPanelProps) {
  const stats = useMemo(() => {
    const statuses = Object.values(nodeStatuses);
    return {
      total: statuses.length,
      pending: statuses.filter(s => s.status === 'pending').length,
      running: statuses.filter(s => s.status === 'running').length,
      success: statuses.filter(s => s.status === 'success').length,
      failed: statuses.filter(s => s.status === 'failed').length,
      skipped: statuses.filter(s => s.status === 'skipped').length,
    };
  }, [nodeStatuses]);

  const elapsedTime = useMemo(() => {
    const statuses = Object.values(nodeStatuses);
    if (statuses.length === 0) return 0;
    
    const startTimes = statuses
      .filter(s => s.startTime)
      .map(s => s.startTime!);
    
    if (startTimes.length === 0) return 0;
    
    const earliestStart = Math.min(...startTimes);
    const now = Date.now();
    
    return Math.floor((now - earliestStart) / 1000);
  }, [nodeStatuses]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getOverallStatus = () => {
    if (!isConnected && !isComplete) return 'idle';
    if (isComplete) {
      if (executionStatus === 'completed' || stats.success === stats.total) return 'success';
      if (stats.failed > 0) return 'error';
      return 'idle';
    }
    if (stats.running > 0) return 'running';
    if (stats.pending > 0) return 'pending';
    return 'idle';
  };

  const overallStatus = getOverallStatus();

  return (
    <div className="execution-control-panel">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-600" />
          <h3 className="font-semibold text-gray-900 dark:text-white">
            Execution Status
          </h3>
        </div>
        <ExecutionStatusBadge status={overallStatus as any} size="sm" />
      </div>

      {/* Stats Grid */}
      <div className="execution-stats">
        <div className="stat-item">
          <div className="stat-value text-blue-600">{stats.running}</div>
          <div className="stat-label">Running</div>
        </div>
        <div className="stat-item">
          <div className="stat-value text-green-600">{stats.success}</div>
          <div className="stat-label">Success</div>
        </div>
        <div className="stat-item">
          <div className="stat-value text-red-600">{stats.failed}</div>
          <div className="stat-label">Failed</div>
        </div>
      </div>

      {/* Progress */}
      {stats.total > 0 && (
        <div className="mt-4">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-gray-600 dark:text-gray-400">Progress</span>
            <span className="font-medium text-gray-900 dark:text-white">
              {stats.success + stats.failed + stats.skipped} / {stats.total}
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{
                width: `${((stats.success + stats.failed + stats.skipped) / stats.total) * 100}%`,
              }}
            />
          </div>
        </div>
      )}

      {/* Timer */}
      {isConnected && (
        <div className="mt-4 flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <Clock className="w-4 h-4" />
          <span>Elapsed: {formatTime(elapsedTime)}</span>
        </div>
      )}

      {/* Retry Status */}
      {retryCount > 0 && !isConnected && !isComplete && (
        <div className="mt-4 p-3 rounded-lg bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800">
          <div className="flex items-center gap-2">
            <RotateCcw className="w-4 h-4 text-yellow-600 dark:text-yellow-400 animate-spin" />
            <span className="text-sm text-yellow-700 dark:text-yellow-400 font-medium">
              Reconnecting... (Attempt {retryCount}/{maxRetries})
            </span>
          </div>
        </div>
      )}

      {/* Control Buttons */}
      <div className="mt-4 flex gap-2">
        {!isConnected && !isComplete && (
          <Button
            onClick={onStart}
            size="sm"
            className="flex-1"
          >
            <Play className="w-4 h-4 mr-2" />
            Start
          </Button>
        )}
        
        {isConnected && !isComplete && (
          <>
            <Button
              onClick={onPause}
              size="sm"
              variant="outline"
              className="flex-1"
            >
              <Pause className="w-4 h-4 mr-2" />
              Pause
            </Button>
            <Button
              onClick={onStop}
              size="sm"
              variant="destructive"
              className="flex-1"
            >
              <Square className="w-4 h-4 mr-2" />
              Stop
            </Button>
          </>
        )}
        
        {isComplete && (
          <Button
            onClick={onReset}
            size="sm"
            variant="outline"
            className="flex-1"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Reset
          </Button>
        )}
      </div>

      {/* Status Message */}
      {isComplete && (
        <div className="mt-4 p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
          <div className="flex items-center gap-2">
            {overallStatus === 'success' ? (
              <>
                <CheckCircle2 className="w-4 h-4 text-green-600" />
                <span className="text-sm text-green-700 dark:text-green-400 font-medium">
                  Execution completed successfully
                </span>
              </>
            ) : (
              <>
                <XCircle className="w-4 h-4 text-red-600" />
                <span className="text-sm text-red-700 dark:text-red-400 font-medium">
                  Execution failed with errors
                </span>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
