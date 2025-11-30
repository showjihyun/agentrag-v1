'use client';

/**
 * Workflow Analytics Dashboard
 * 
 * Performance monitoring with:
 * - Execution statistics
 * - Success/failure rates
 * - Average execution times
 * - Node performance breakdown
 */

import React, { useMemo } from 'react';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle2,
  XCircle,
  Zap,
  BarChart3,
  Timer,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';

interface ExecutionRecord {
  id: string;
  status: 'success' | 'failed' | 'running';
  startTime: number;
  endTime?: number;
  nodeExecutions: Array<{
    nodeId: string;
    nodeName: string;
    status: 'success' | 'failed' | 'skipped';
    duration: number;
  }>;
}

interface WorkflowAnalyticsProps {
  workflowId: string;
  workflowName: string;
  executions: ExecutionRecord[];
  className?: string;
}

export function WorkflowAnalytics({
  workflowId,
  workflowName,
  executions,
  className,
}: WorkflowAnalyticsProps) {
  // Calculate statistics
  const stats = useMemo(() => {
    const completed = executions.filter(e => e.status !== 'running');
    const successful = completed.filter(e => e.status === 'success');
    const failed = completed.filter(e => e.status === 'failed');

    // Execution times
    const executionTimes = completed
      .filter(e => e.endTime)
      .map(e => e.endTime! - e.startTime);

    const avgExecutionTime = executionTimes.length > 0
      ? executionTimes.reduce((a, b) => a + b, 0) / executionTimes.length
      : 0;

    const minExecutionTime = executionTimes.length > 0 ? Math.min(...executionTimes) : 0;
    const maxExecutionTime = executionTimes.length > 0 ? Math.max(...executionTimes) : 0;

    // Success rate
    const successRate = completed.length > 0
      ? (successful.length / completed.length) * 100
      : 0;

    // Node performance
    const nodeStats = new Map<string, { name: string; total: number; success: number; totalDuration: number }>();
    
    executions.forEach(exec => {
      exec.nodeExecutions.forEach(node => {
        const existing = nodeStats.get(node.nodeId) || {
          name: node.nodeName,
          total: 0,
          success: 0,
          totalDuration: 0,
        };
        existing.total++;
        if (node.status === 'success') existing.success++;
        existing.totalDuration += node.duration;
        nodeStats.set(node.nodeId, existing);
      });
    });

    const nodePerformance = Array.from(nodeStats.entries())
      .map(([id, data]) => ({
        id,
        name: data.name,
        successRate: (data.success / data.total) * 100,
        avgDuration: data.totalDuration / data.total,
        executions: data.total,
      }))
      .sort((a, b) => b.executions - a.executions);

    // Recent trend (last 10 vs previous 10)
    const recent = completed.slice(0, 10);
    const previous = completed.slice(10, 20);
    
    const recentSuccessRate = recent.length > 0
      ? (recent.filter(e => e.status === 'success').length / recent.length) * 100
      : 0;
    const previousSuccessRate = previous.length > 0
      ? (previous.filter(e => e.status === 'success').length / previous.length) * 100
      : 0;
    
    const trend = recentSuccessRate - previousSuccessRate;

    return {
      total: executions.length,
      completed: completed.length,
      successful: successful.length,
      failed: failed.length,
      running: executions.filter(e => e.status === 'running').length,
      successRate,
      avgExecutionTime,
      minExecutionTime,
      maxExecutionTime,
      nodePerformance,
      trend,
      recentSuccessRate,
    };
  }, [executions]);

  // Format duration
  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${Math.round(ms)}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  // Get trend icon and color
  const getTrendIndicator = (value: number) => {
    if (value > 0) {
      return { icon: ArrowUpRight, color: 'text-green-500', label: `+${value.toFixed(1)}%` };
    } else if (value < 0) {
      return { icon: ArrowDownRight, color: 'text-red-500', label: `${value.toFixed(1)}%` };
    }
    return { icon: null, color: 'text-muted-foreground', label: '0%' };
  };

  const trendIndicator = getTrendIndicator(stats.trend);
  const TrendIcon = trendIndicator.icon;

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Workflow Analytics
          </h2>
          <p className="text-sm text-muted-foreground">{workflowName}</p>
        </div>
        <Badge variant="outline" className="gap-1">
          <Activity className="h-3 w-3" />
          {stats.running} running
        </Badge>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Executions</p>
                <p className="text-2xl font-bold">{stats.total}</p>
              </div>
              <div className="p-3 rounded-full bg-primary/10">
                <Zap className="h-5 w-5 text-primary" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Success Rate</p>
                <div className="flex items-center gap-2">
                  <p className="text-2xl font-bold">{stats.successRate.toFixed(1)}%</p>
                  {TrendIcon && (
                    <span className={cn('flex items-center text-xs', trendIndicator.color)}>
                      <TrendIcon className="h-3 w-3" />
                      {trendIndicator.label}
                    </span>
                  )}
                </div>
              </div>
              <div className="p-3 rounded-full bg-green-500/10">
                <CheckCircle2 className="h-5 w-5 text-green-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Avg Duration</p>
                <p className="text-2xl font-bold">{formatDuration(stats.avgExecutionTime)}</p>
              </div>
              <div className="p-3 rounded-full bg-blue-500/10">
                <Timer className="h-5 w-5 text-blue-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Failed</p>
                <p className="text-2xl font-bold">{stats.failed}</p>
              </div>
              <div className="p-3 rounded-full bg-red-500/10">
                <XCircle className="h-5 w-5 text-red-500" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Stats */}
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="nodes">Node Performance</TabsTrigger>
          <TabsTrigger value="history">Recent History</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* Success/Failure breakdown */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Execution Breakdown</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                    Successful
                  </span>
                  <span className="font-medium">{stats.successful}</span>
                </div>
                <Progress value={(stats.successful / Math.max(stats.completed, 1)) * 100} className="h-2 bg-muted" />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2">
                    <XCircle className="h-4 w-4 text-red-500" />
                    Failed
                  </span>
                  <span className="font-medium">{stats.failed}</span>
                </div>
                <Progress value={(stats.failed / Math.max(stats.completed, 1)) * 100} className="h-2 bg-muted [&>div]:bg-red-500" />
              </div>
            </CardContent>
          </Card>

          {/* Execution time stats */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Execution Time</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-xs text-muted-foreground">Minimum</p>
                  <p className="text-lg font-semibold">{formatDuration(stats.minExecutionTime)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Average</p>
                  <p className="text-lg font-semibold">{formatDuration(stats.avgExecutionTime)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Maximum</p>
                  <p className="text-lg font-semibold">{formatDuration(stats.maxExecutionTime)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="nodes" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Node Performance</CardTitle>
              <CardDescription>Performance breakdown by node</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {stats.nodePerformance.slice(0, 10).map((node) => (
                  <div key={node.id} className="flex items-center gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium truncate">{node.name}</span>
                        <span className="text-xs text-muted-foreground">
                          {node.executions} runs
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Progress value={node.successRate} className="h-1.5 flex-1" />
                        <span className={cn(
                          'text-xs font-medium w-12 text-right',
                          node.successRate >= 90 ? 'text-green-500' :
                          node.successRate >= 70 ? 'text-amber-500' : 'text-red-500'
                        )}>
                          {node.successRate.toFixed(0)}%
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-xs text-muted-foreground">
                        avg {formatDuration(node.avgDuration)}
                      </span>
                    </div>
                  </div>
                ))}

                {stats.nodePerformance.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No node execution data available
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Recent Executions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {executions.slice(0, 10).map((exec) => (
                  <div
                    key={exec.id}
                    className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
                  >
                    <div className="flex items-center gap-3">
                      {exec.status === 'success' ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : exec.status === 'failed' ? (
                        <XCircle className="h-4 w-4 text-red-500" />
                      ) : (
                        <Activity className="h-4 w-4 text-blue-500 animate-pulse" />
                      )}
                      <div>
                        <p className="text-sm font-medium">
                          {exec.status === 'running' ? 'Running...' : 
                           exec.status === 'success' ? 'Completed' : 'Failed'}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(exec.startTime).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    {exec.endTime && (
                      <span className="text-xs text-muted-foreground">
                        {formatDuration(exec.endTime - exec.startTime)}
                      </span>
                    )}
                  </div>
                ))}

                {executions.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No executions yet
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
