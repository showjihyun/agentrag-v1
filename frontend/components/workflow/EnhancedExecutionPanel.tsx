'use client';

/**
 * Enhanced Execution Panel
 * 
 * Improved execution monitoring with:
 * - Estimated completion time
 * - Node execution timeline
 * - Performance metrics
 * - Real-time progress visualization
 */

import React, { useMemo, useState, useEffect } from 'react';
import {
  Play,
  Pause,
  Square,
  RotateCcw,
  Activity,
  Clock,
  CheckCircle2,
  XCircle,
  Timer,
  TrendingUp,
  Zap,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

interface NodeExecutionStatus {
  status: 'pending' | 'running' | 'success' | 'failed' | 'skipped' | 'waiting';
  startTime?: number;
  endTime?: number;
  error?: string;
  output?: any;
}

interface EnhancedExecutionPanelProps {
  nodeStatuses: Record<string, NodeExecutionStatus>;
  nodeNames?: Record<string, string>;
  isConnected: boolean;
  isComplete: boolean;
  executionStatus: string | null;
  retryCount?: number;
  maxRetries?: number;
  onStart?: () => void;
  onPause?: () => void;
  onStop?: () => void;
  onReset?: () => void;
  onNodeClick?: (nodeId: string) => void;
}

// Status colors and icons
const statusConfig = {
  pending: { color: 'text-gray-500', bg: 'bg-gray-100', icon: Clock },
  running: { color: 'text-blue-500', bg: 'bg-blue-100', icon: Activity },
  success: { color: 'text-green-500', bg: 'bg-green-100', icon: CheckCircle2 },
  failed: { color: 'text-red-500', bg: 'bg-red-100', icon: XCircle },
  skipped: { color: 'text-gray-400', bg: 'bg-gray-50', icon: Clock },
  waiting: { color: 'text-amber-500', bg: 'bg-amber-100', icon: Timer },
};


export function EnhancedExecutionPanel({
  nodeStatuses,
  nodeNames = {},
  isConnected,
  isComplete,
  executionStatus,
  retryCount = 0,
  maxRetries = 3,
  onStart,
  onPause,
  onStop,
  onReset,
  onNodeClick,
}: EnhancedExecutionPanelProps) {
  const [showTimeline, setShowTimeline] = useState(true);
  const [elapsedTime, setElapsedTime] = useState(0);

  // Calculate stats
  const stats = useMemo(() => {
    const statuses = Object.values(nodeStatuses);
    const completed = statuses.filter(s => ['success', 'failed', 'skipped'].includes(s.status));
    
    // Calculate average execution time from completed nodes
    const executionTimes = statuses
      .filter(s => s.startTime && s.endTime)
      .map(s => s.endTime! - s.startTime!);
    
    const avgTime = executionTimes.length > 0
      ? executionTimes.reduce((a, b) => a + b, 0) / executionTimes.length
      : 0;

    const pendingCount = statuses.filter(s => s.status === 'pending').length;
    const estimatedRemaining = pendingCount * avgTime;

    return {
      total: statuses.length,
      pending: pendingCount,
      running: statuses.filter(s => s.status === 'running').length,
      success: statuses.filter(s => s.status === 'success').length,
      failed: statuses.filter(s => s.status === 'failed').length,
      skipped: statuses.filter(s => s.status === 'skipped').length,
      completed: completed.length,
      avgExecutionTime: avgTime,
      estimatedRemaining,
      progress: statuses.length > 0 ? (completed.length / statuses.length) * 100 : 0,
    };
  }, [nodeStatuses]);

  // Update elapsed time
  useEffect(() => {
    if (!isConnected || isComplete) return;

    const startTimes = Object.values(nodeStatuses)
      .filter(s => s.startTime)
      .map(s => s.startTime!);

    if (startTimes.length === 0) return;

    const earliestStart = Math.min(...startTimes);
    
    const interval = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - earliestStart) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [nodeStatuses, isConnected, isComplete]);

  // Format time
  const formatTime = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    const seconds = Math.floor(ms / 1000);
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const formatElapsed = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Get overall status
  const getOverallStatus = () => {
    if (!isConnected && !isComplete) return 'idle';
    if (isComplete) {
      if (executionStatus === 'completed' || stats.failed === 0) return 'success';
      return 'failed';
    }
    if (stats.running > 0) return 'running';
    return 'pending';
  };

  const overallStatus = getOverallStatus();

  // Sort nodes by execution order
  const sortedNodes = useMemo(() => {
    return Object.entries(nodeStatuses)
      .sort(([, a], [, b]) => {
        if (!a.startTime && !b.startTime) return 0;
        if (!a.startTime) return 1;
        if (!b.startTime) return -1;
        return a.startTime - b.startTime;
      });
  }, [nodeStatuses]);

  return (
    <TooltipProvider>
      <Card className="w-full">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Execution Monitor
            </CardTitle>
            <Badge
              variant={overallStatus === 'success' ? 'default' : overallStatus === 'failed' ? 'destructive' : 'secondary'}
              className="capitalize"
            >
              {overallStatus}
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Progress</span>
              <span className="font-medium">{stats.completed} / {stats.total} nodes</span>
            </div>
            <Progress value={stats.progress} className="h-2" />
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-4 gap-2">
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="text-center p-2 rounded-lg bg-blue-50 dark:bg-blue-950/30">
                  <div className="text-lg font-bold text-blue-600">{stats.running}</div>
                  <div className="text-xs text-muted-foreground">Running</div>
                </div>
              </TooltipTrigger>
              <TooltipContent>Currently executing nodes</TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <div className="text-center p-2 rounded-lg bg-green-50 dark:bg-green-950/30">
                  <div className="text-lg font-bold text-green-600">{stats.success}</div>
                  <div className="text-xs text-muted-foreground">Success</div>
                </div>
              </TooltipTrigger>
              <TooltipContent>Successfully completed nodes</TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <div className="text-center p-2 rounded-lg bg-red-50 dark:bg-red-950/30">
                  <div className="text-lg font-bold text-red-600">{stats.failed}</div>
                  <div className="text-xs text-muted-foreground">Failed</div>
                </div>
              </TooltipTrigger>
              <TooltipContent>Failed nodes</TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <div className="text-center p-2 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                  <div className="text-lg font-bold text-gray-600">{stats.pending}</div>
                  <div className="text-xs text-muted-foreground">Pending</div>
                </div>
              </TooltipTrigger>
              <TooltipContent>Waiting to execute</TooltipContent>
            </Tooltip>
          </div>

          {/* Time Metrics */}
          <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <div>
                  <div className="text-xs text-muted-foreground">Elapsed</div>
                  <div className="font-mono font-medium">{formatElapsed(elapsedTime)}</div>
                </div>
              </div>

              {stats.estimatedRemaining > 0 && stats.running > 0 && (
                <div className="flex items-center gap-2 pl-4 border-l">
                  <Timer className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <div className="text-xs text-muted-foreground">Est. Remaining</div>
                    <div className="font-mono font-medium">~{formatTime(stats.estimatedRemaining)}</div>
                  </div>
                </div>
              )}
            </div>

            {stats.avgExecutionTime > 0 && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <TrendingUp className="h-3 w-3" />
                    <span>Avg: {formatTime(stats.avgExecutionTime)}</span>
                  </div>
                </TooltipTrigger>
                <TooltipContent>Average node execution time</TooltipContent>
              </Tooltip>
            )}
          </div>

          {/* Node Timeline */}
          <div>
            <button
              className="flex items-center justify-between w-full text-sm font-medium py-2"
              onClick={() => setShowTimeline(!showTimeline)}
            >
              <span className="flex items-center gap-2">
                <Zap className="h-4 w-4" />
                Execution Timeline
              </span>
              {showTimeline ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>

            {showTimeline && (
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {sortedNodes.map(([nodeId, status]) => {
                  const config = statusConfig[status.status];
                  const StatusIcon = config.icon;
                  const duration = status.startTime && status.endTime
                    ? status.endTime - status.startTime
                    : null;

                  return (
                    <button
                      key={nodeId}
                      className={cn(
                        'w-full flex items-center gap-2 p-2 rounded-lg text-left transition-colors',
                        'hover:bg-muted/50',
                        status.status === 'running' && 'bg-blue-50 dark:bg-blue-950/20'
                      )}
                      onClick={() => onNodeClick?.(nodeId)}
                    >
                      <div className={cn('p-1 rounded', config.bg)}>
                        <StatusIcon className={cn('h-3 w-3', config.color, status.status === 'running' && 'animate-pulse')} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-xs font-medium truncate">
                          {nodeNames[nodeId] || nodeId}
                        </div>
                        {status.error && (
                          <div className="text-xs text-red-500 truncate">{status.error}</div>
                        )}
                      </div>
                      {duration !== null && (
                        <span className="text-xs text-muted-foreground font-mono">
                          {formatTime(duration)}
                        </span>
                      )}
                    </button>
                  );
                })}

                {sortedNodes.length === 0 && (
                  <div className="text-center py-4 text-sm text-muted-foreground">
                    No execution data yet
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Retry Status */}
          {retryCount > 0 && !isConnected && !isComplete && (
            <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800">
              <div className="flex items-center gap-2">
                <RotateCcw className="h-4 w-4 text-amber-600 animate-spin" />
                <span className="text-sm text-amber-700 dark:text-amber-400">
                  Reconnecting... ({retryCount}/{maxRetries})
                </span>
              </div>
            </div>
          )}

          {/* Control Buttons */}
          <div className="flex gap-2 pt-2 border-t">
            {!isConnected && !isComplete && (
              <Button size="sm" className="flex-1 gap-2" onClick={onStart}>
                <Play className="h-4 w-4" />
                Start
              </Button>
            )}
            {isConnected && !isComplete && (
              <>
                <Button size="sm" variant="outline" className="flex-1 gap-2" onClick={onPause}>
                  <Pause className="h-4 w-4" />
                  Pause
                </Button>
                <Button size="sm" variant="destructive" className="flex-1 gap-2" onClick={onStop}>
                  <Square className="h-4 w-4" />
                  Stop
                </Button>
              </>
            )}
            {isComplete && (
              <Button size="sm" variant="outline" className="flex-1 gap-2" onClick={onReset}>
                <RotateCcw className="h-4 w-4" />
                Reset
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </TooltipProvider>
  );
}
