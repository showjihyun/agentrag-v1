'use client';

import React, { useMemo } from 'react';
import { Clock, CheckCircle, XCircle, Loader2, Play, Pause } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { NodeExecutionStatus } from '@/hooks/useWorkflowExecutionStream';

interface ExecutionTimelineProps {
  nodeStatuses: Record<string, NodeExecutionStatus>;
  isExecuting: boolean;
  className?: string;
  onNodeClick?: (nodeId: string) => void;
}

interface TimelineEvent {
  nodeId: string;
  nodeName: string;
  status: NodeExecutionStatus['status'];
  timestamp: number;
  duration?: number;
  error?: string;
  type: 'start' | 'end';
}

export function ExecutionTimeline({
  nodeStatuses,
  isExecuting,
  className,
  onNodeClick,
}: ExecutionTimelineProps) {
  // Convert node statuses to timeline events
  const timelineEvents = useMemo(() => {
    const events: TimelineEvent[] = [];

    Object.values(nodeStatuses).forEach((status) => {
      // Start event
      if (status.startTime) {
        events.push({
          nodeId: status.nodeId,
          nodeName: status.nodeName,
          status: 'running',
          timestamp: status.startTime,
          type: 'start',
        });
      }

      // End event
      if (status.endTime) {
        events.push({
          nodeId: status.nodeId,
          nodeName: status.nodeName,
          status: status.status,
          timestamp: status.endTime,
          duration: status.endTime - (status.startTime || status.endTime),
          error: status.error,
          type: 'end',
        });
      }
    });

    // Sort by timestamp
    return events.sort((a, b) => a.timestamp - b.timestamp);
  }, [nodeStatuses]);

  const startTime = timelineEvents.length > 0 ? timelineEvents[0].timestamp : Date.now();
  const totalDuration = timelineEvents.length > 0
    ? (timelineEvents[timelineEvents.length - 1].timestamp - startTime) / 1000
    : 0;

  const formatTime = (timestamp: number) => {
    const elapsed = (timestamp - startTime) / 1000;
    return `+${elapsed.toFixed(2)}s`;
  };

  const formatDuration = (ms: number) => {
    const seconds = ms / 1000;
    if (seconds < 1) {
      return `${ms.toFixed(0)}ms`;
    }
    return `${seconds.toFixed(2)}s`;
  };

  const getEventIcon = (event: TimelineEvent) => {
    if (event.type === 'start') {
      return <Play className="h-4 w-4 text-blue-500" />;
    }

    switch (event.status) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'running':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      default:
        return <Pause className="h-4 w-4 text-gray-400" />;
    }
  };

  const getEventColor = (event: TimelineEvent) => {
    if (event.type === 'start') return 'border-blue-500';
    
    switch (event.status) {
      case 'success':
        return 'border-green-500';
      case 'failed':
        return 'border-red-500';
      case 'running':
        return 'border-blue-500';
      default:
        return 'border-gray-300';
    }
  };

  if (timelineEvents.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Execution Timeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No execution events yet</p>
            <p className="text-sm mt-2">Timeline will appear when workflow starts executing</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Execution Timeline
          </CardTitle>
          <div className="flex items-center gap-2">
            {isExecuting && (
              <Badge variant="outline" className="border-blue-500 text-blue-600">
                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                Running
              </Badge>
            )}
            <Badge variant="outline">
              {totalDuration.toFixed(2)}s total
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px] pr-4">
          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700" />

            {/* Events */}
            <div className="space-y-4">
              {timelineEvents.map((event, index) => (
                <div
                  key={`${event.nodeId}-${event.type}-${index}`}
                  className={cn(
                    'relative pl-14 cursor-pointer transition-colors hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg p-2 -ml-2',
                    onNodeClick && 'cursor-pointer'
                  )}
                  onClick={() => onNodeClick?.(event.nodeId)}
                >
                  {/* Icon */}
                  <div
                    className={cn(
                      'absolute left-4 top-2 w-5 h-5 rounded-full bg-white dark:bg-gray-900 border-2 flex items-center justify-center',
                      getEventColor(event)
                    )}
                  >
                    {getEventIcon(event)}
                  </div>

                  {/* Content */}
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-sm truncate">
                          {event.nodeName}
                        </span>
                        {event.type === 'start' ? (
                          <Badge variant="outline" className="text-xs">
                            Started
                          </Badge>
                        ) : (
                          <Badge
                            variant={
                              event.status === 'success'
                                ? 'default'
                                : event.status === 'failed'
                                ? 'destructive'
                                : 'secondary'
                            }
                            className="text-xs"
                          >
                            {event.status === 'success' ? 'Completed' : event.status}
                          </Badge>
                        )}
                      </div>

                      <div className="flex items-center gap-3 text-xs text-muted-foreground">
                        <span>{formatTime(event.timestamp)}</span>
                        {event.duration !== undefined && (
                          <>
                            <span>•</span>
                            <span>Duration: {formatDuration(event.duration)}</span>
                          </>
                        )}
                      </div>

                      {event.error && (
                        <div className="mt-2 text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded">
                          {event.error}
                        </div>
                      )}
                    </div>

                    <div className="text-xs text-muted-foreground whitespace-nowrap">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

/**
 * Compact timeline for toolbar
 */
export function CompactTimeline({
  nodeStatuses,
  isExecuting,
}: {
  nodeStatuses: Record<string, NodeExecutionStatus>;
  isExecuting: boolean;
}) {
  const stats = useMemo(() => {
    const statuses = Object.values(nodeStatuses);
    const completed = statuses.filter(s => s.status === 'success' || s.status === 'failed');
    
    let totalDuration = 0;
    completed.forEach(s => {
      if (s.startTime && s.endTime) {
        totalDuration += s.endTime - s.startTime;
      }
    });

    return {
      total: statuses.length,
      completed: completed.length,
      duration: totalDuration / 1000,
    };
  }, [nodeStatuses]);

  if (stats.total === 0) return null;

  return (
    <div className="flex items-center gap-2 text-sm">
      <Clock className="h-4 w-4 text-muted-foreground" />
      <span className="text-muted-foreground">
        {stats.completed}/{stats.total} nodes
      </span>
      <span className="text-muted-foreground">•</span>
      <span className="text-muted-foreground">
        {stats.duration.toFixed(2)}s
      </span>
      {isExecuting && (
        <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
      )}
    </div>
  );
}
