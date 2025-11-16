'use client';

import React, { useEffect, useState } from 'react';
import { Loader2, CheckCircle, XCircle, Clock, Play } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

export interface NodeExecutionStatus {
  nodeId: string;
  nodeName: string;
  status: 'pending' | 'running' | 'success' | 'failed' | 'skipped';
  startTime?: number;
  endTime?: number;
  error?: string;
  output?: any;
}

interface ExecutionProgressProps {
  workflowId: string;
  executionId?: string;
  isExecuting: boolean;
  nodeStatuses: Record<string, NodeExecutionStatus>;
  onNodeClick?: (nodeId: string) => void;
  className?: string;
}

export function ExecutionProgress({
  workflowId,
  executionId,
  isExecuting,
  nodeStatuses,
  onNodeClick,
  className,
}: ExecutionProgressProps) {
  const [elapsedTime, setElapsedTime] = useState(0);
  const [startTime] = useState(Date.now());

  // Update elapsed time
  useEffect(() => {
    if (!isExecuting) return;

    const interval = setInterval(() => {
      setElapsedTime(Date.now() - startTime);
    }, 100);

    return () => clearInterval(interval);
  }, [isExecuting, startTime]);

  const statuses = Object.values(nodeStatuses);
  const totalNodes = statuses.length;
  const completedNodes = statuses.filter(s => 
    s.status === 'success' || s.status === 'failed' || s.status === 'skipped'
  ).length;
  const failedNodes = statuses.filter(s => s.status === 'failed').length;
  const progress = totalNodes > 0 ? (completedNodes / totalNodes) * 100 : 0;

  const formatTime = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    }
    return `${seconds}s`;
  };

  const getStatusIcon = (status: NodeExecutionStatus['status']) => {
    switch (status) {
      case 'running':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'skipped':
        return <div className="h-4 w-4 rounded-full border-2 border-gray-300" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: NodeExecutionStatus['status']) => {
    switch (status) {
      case 'running':
        return <Badge variant="outline" className="border-blue-500 text-blue-600">Running</Badge>;
      case 'success':
        return <Badge variant="outline" className="border-green-500 text-green-600">Success</Badge>;
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>;
      case 'skipped':
        return <Badge variant="outline">Skipped</Badge>;
      default:
        return <Badge variant="outline" className="text-gray-500">Pending</Badge>;
    }
  };

  if (!isExecuting && totalNodes === 0) {
    return null;
  }

  return (
    <Card className={cn('border-l-4 border-l-blue-500', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isExecuting ? (
              <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
            ) : failedNodes > 0 ? (
              <XCircle className="h-5 w-5 text-red-500" />
            ) : (
              <CheckCircle className="h-5 w-5 text-green-500" />
            )}
            <CardTitle className="text-base">
              {isExecuting ? 'Executing Workflow' : failedNodes > 0 ? 'Execution Failed' : 'Execution Complete'}
            </CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">
              {completedNodes} / {totalNodes} nodes
            </Badge>
            <Badge variant="outline">
              <Clock className="h-3 w-3 mr-1" />
              {formatTime(elapsedTime)}
            </Badge>
          </div>
        </div>
        {isExecuting && (
          <div className="mt-2">
            <Progress value={progress} className="h-2" />
          </div>
        )}
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[300px]">
          <div className="space-y-2">
            {statuses.map((nodeStatus) => {
              const duration = nodeStatus.startTime && nodeStatus.endTime
                ? nodeStatus.endTime - nodeStatus.startTime
                : nodeStatus.startTime
                ? Date.now() - nodeStatus.startTime
                : 0;

              return (
                <div
                  key={nodeStatus.nodeId}
                  className={cn(
                    'flex items-start gap-3 p-3 rounded-md border transition-colors',
                    {
                      'bg-blue-50 border-blue-200': nodeStatus.status === 'running',
                      'bg-green-50 border-green-200': nodeStatus.status === 'success',
                      'bg-red-50 border-red-200': nodeStatus.status === 'failed',
                      'bg-gray-50 border-gray-200': nodeStatus.status === 'pending' || nodeStatus.status === 'skipped',
                      'cursor-pointer hover:shadow-sm': onNodeClick,
                    }
                  )}
                  onClick={() => onNodeClick?.(nodeStatus.nodeId)}
                >
                  <div className="mt-0.5">
                    {getStatusIcon(nodeStatus.status)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <div className="font-medium text-sm truncate">
                        {nodeStatus.nodeName}
                      </div>
                      {getStatusBadge(nodeStatus.status)}
                    </div>
                    {duration > 0 && (
                      <div className="text-xs text-muted-foreground">
                        {formatTime(duration)}
                      </div>
                    )}
                    {nodeStatus.error && (
                      <div className="text-xs text-red-600 mt-1 p-2 bg-red-100 rounded">
                        {nodeStatus.error}
                      </div>
                    )}
                    {nodeStatus.output && nodeStatus.status === 'success' && (
                      <div className="text-xs text-gray-600 mt-1 p-2 bg-gray-100 rounded font-mono">
                        {typeof nodeStatus.output === 'string'
                          ? nodeStatus.output.substring(0, 100) + (nodeStatus.output.length > 100 ? '...' : '')
                          : JSON.stringify(nodeStatus.output).substring(0, 100) + '...'}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

/**
 * Compact execution status for toolbar
 */
export function ExecutionStatusBadge({
  isExecuting,
  nodeStatuses,
}: {
  isExecuting: boolean;
  nodeStatuses: Record<string, NodeExecutionStatus>;
}) {
  const statuses = Object.values(nodeStatuses);
  const completedNodes = statuses.filter(s => 
    s.status === 'success' || s.status === 'failed' || s.status === 'skipped'
  ).length;
  const failedNodes = statuses.filter(s => s.status === 'failed').length;

  if (!isExecuting && statuses.length === 0) {
    return null;
  }

  if (isExecuting) {
    return (
      <Badge variant="outline" className="border-blue-500 text-blue-600">
        <Loader2 className="h-3 w-3 mr-1 animate-spin" />
        Executing {completedNodes}/{statuses.length}
      </Badge>
    );
  }

  if (failedNodes > 0) {
    return (
      <Badge variant="destructive">
        <XCircle className="h-3 w-3 mr-1" />
        Failed
      </Badge>
    );
  }

  return (
    <Badge variant="outline" className="border-green-500 text-green-600">
      <CheckCircle className="h-3 w-3 mr-1" />
      Complete
    </Badge>
  );
}
