'use client';

import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Activity,
  Clock,
  Cpu,
  HardDrive,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Zap,
} from 'lucide-react';
import { Node } from 'reactflow';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

interface NodeMetrics {
  nodeId: string;
  nodeName: string;
  executions: number;
  avgDuration: number;
  totalDuration: number;
  successRate: number;
  errorRate: number;
  memory?: number;
  cpu?: number;
  isBottleneck?: boolean;
}

interface PerformanceProfilerProps {
  nodes: Node[];
  nodeMetrics: Record<string, NodeMetrics>;
  totalDuration: number;
  avgDuration: number;
  successRate: number;
  errorRate: number;
}

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'];

export function PerformanceProfiler({
  nodes,
  nodeMetrics,
  totalDuration,
  avgDuration,
  successRate,
  errorRate,
}: PerformanceProfilerProps) {
  // Identify bottlenecks (nodes taking >20% of total time)
  const bottlenecks = useMemo(() => {
    return Object.entries(nodeMetrics)
      .filter(([_, metrics]) => {
        const percentage = (metrics.totalDuration / totalDuration) * 100;
        return percentage > 20;
      })
      .map(([nodeId, metrics]) => ({
        ...metrics,
        percentage: (metrics.totalDuration / totalDuration) * 100,
      }))
      .sort((a, b) => b.percentage - a.percentage);
  }, [nodeMetrics, totalDuration]);

  // Prepare chart data
  const durationChartData = useMemo(() => {
    return Object.entries(nodeMetrics)
      .map(([nodeId, metrics]) => ({
        name: metrics.nodeName,
        duration: Math.round(metrics.avgDuration),
        executions: metrics.executions,
      }))
      .sort((a, b) => b.duration - a.duration)
      .slice(0, 10); // Top 10
  }, [nodeMetrics]);

  const successRateChartData = useMemo(() => {
    return Object.entries(nodeMetrics)
      .map(([nodeId, metrics]) => ({
        name: metrics.nodeName,
        successRate: Math.round(metrics.successRate),
        errorRate: Math.round(metrics.errorRate),
      }))
      .sort((a, b) => a.successRate - b.successRate)
      .slice(0, 10);
  }, [nodeMetrics]);

  const distributionData = useMemo(() => {
    return Object.entries(nodeMetrics)
      .map(([nodeId, metrics]) => ({
        name: metrics.nodeName,
        value: metrics.totalDuration,
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 5); // Top 5
  }, [nodeMetrics]);

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatMemory = (bytes: number) => {
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)}MB`;
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Clock className="h-4 w-4 text-blue-500" />
              Total Duration
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatDuration(totalDuration)}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Avg: {formatDuration(avgDuration)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Activity className="h-4 w-4 text-green-500" />
              Success Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {successRate.toFixed(1)}%
            </div>
            <Progress value={successRate} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              Error Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {errorRate.toFixed(1)}%
            </div>
            <Progress value={errorRate} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Zap className="h-4 w-4 text-yellow-500" />
              Bottlenecks
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{bottlenecks.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Nodes taking &gt;20% time
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Bottlenecks Alert */}
      {bottlenecks.length > 0 && (
        <Card className="border-yellow-500/50 bg-yellow-50 dark:bg-yellow-950/20">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
              Performance Bottlenecks Detected
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {bottlenecks.map((bottleneck) => (
                <div key={bottleneck.nodeId} className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium">{bottleneck.nodeName}</span>
                      <Badge variant="destructive" className="text-xs">
                        {bottleneck.percentage.toFixed(1)}% of total time
                      </Badge>
                    </div>
                    <Progress value={bottleneck.percentage} className="h-2" />
                  </div>
                  <div className="ml-4 text-right">
                    <div className="text-sm font-semibold">
                      {formatDuration(bottleneck.avgDuration)}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {bottleneck.executions} runs
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Duration Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Average Duration by Node</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={durationChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip
                  formatter={(value: number) => formatDuration(value)}
                  labelStyle={{ color: '#000' }}
                />
                <Bar dataKey="duration" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Success Rate Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Success vs Error Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={successRateChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip labelStyle={{ color: '#000' }} />
                <Bar dataKey="successRate" fill="#10b981" name="Success %" />
                <Bar dataKey="errorRate" fill="#ef4444" name="Error %" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Time Distribution Pie Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Time Distribution (Top 5 Nodes)</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={distributionData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {distributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number) => formatDuration(value)}
                  labelStyle={{ color: '#000' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Node Details Table */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Node Performance Details</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px]">
              <div className="space-y-2">
                {Object.entries(nodeMetrics)
                  .sort(([, a], [, b]) => b.avgDuration - a.avgDuration)
                  .map(([nodeId, metrics]) => (
                    <div
                      key={nodeId}
                      className="p-3 rounded-lg border bg-card hover:bg-muted transition-colors"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium">{metrics.nodeName}</span>
                        <Badge
                          variant={metrics.successRate > 90 ? 'default' : 'destructive'}
                        >
                          {metrics.successRate.toFixed(0)}%
                        </Badge>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-xs text-muted-foreground">
                        <div>
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            Avg
                          </div>
                          <div className="font-medium text-foreground">
                            {formatDuration(metrics.avgDuration)}
                          </div>
                        </div>
                        <div>
                          <div className="flex items-center gap-1">
                            <Activity className="h-3 w-3" />
                            Runs
                          </div>
                          <div className="font-medium text-foreground">
                            {metrics.executions}
                          </div>
                        </div>
                        <div>
                          <div className="flex items-center gap-1">
                            <TrendingUp className="h-3 w-3" />
                            Total
                          </div>
                          <div className="font-medium text-foreground">
                            {formatDuration(metrics.totalDuration)}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Optimization Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Zap className="h-4 w-4 text-yellow-500" />
            Optimization Recommendations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {bottlenecks.length > 0 && (
              <div className="flex items-start gap-3 p-3 rounded-lg bg-yellow-50 dark:bg-yellow-950/20">
                <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                <div>
                  <div className="font-medium text-sm">Optimize Bottleneck Nodes</div>
                  <p className="text-sm text-muted-foreground mt-1">
                    {bottlenecks.map(b => b.nodeName).join(', ')} are taking significant time.
                    Consider optimizing their logic or running them in parallel.
                  </p>
                </div>
              </div>
            )}

            {errorRate > 10 && (
              <div className="flex items-start gap-3 p-3 rounded-lg bg-red-50 dark:bg-red-950/20">
                <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
                <div>
                  <div className="font-medium text-sm">High Error Rate Detected</div>
                  <p className="text-sm text-muted-foreground mt-1">
                    Error rate is {errorRate.toFixed(1)}%. Review error-prone nodes and add
                    proper error handling.
                  </p>
                </div>
              </div>
            )}

            {Object.values(nodeMetrics).some(m => m.executions > 100) && (
              <div className="flex items-start gap-3 p-3 rounded-lg bg-blue-50 dark:bg-blue-950/20">
                <TrendingUp className="h-5 w-5 text-blue-600 mt-0.5" />
                <div>
                  <div className="font-medium text-sm">Consider Caching</div>
                  <p className="text-sm text-muted-foreground mt-1">
                    Some nodes are executed frequently. Implement caching for repeated
                    operations to improve performance.
                  </p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
