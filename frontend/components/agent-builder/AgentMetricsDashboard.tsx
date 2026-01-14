'use client';

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
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
  Area,
  AreaChart,
} from 'recharts';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle,
  XCircle,
  Zap,
  Users,
  Target,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';

interface AgentMetrics {
  agent_id: string;
  agent_name: string;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  success_rate: number;
  avg_execution_time: number;
  total_tokens_used: number;
  avg_tokens_per_execution: number;
  last_execution_at: string | null;
  executions_today: number;
  executions_this_week: number;
  executions_this_month: number;
  performance_trend: 'up' | 'down' | 'stable';
  error_rate_trend: 'up' | 'down' | 'stable';
}

interface AgentMetricsDashboardProps {
  agentId?: string;
  timeRange?: '24h' | '7d' | '30d' | '90d';
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00'];

export function AgentMetricsDashboard({ 
  agentId, 
  timeRange = '7d' 
}: AgentMetricsDashboardProps) {
  const [selectedTimeRange, setSelectedTimeRange] = useState(timeRange);
  const [selectedMetric, setSelectedMetric] = useState<'executions' | 'success_rate' | 'avg_time' | 'tokens'>('executions');

  // Fetch agent metrics
  const { data: metricsData, isLoading, refetch } = useQuery({
    queryKey: ['agent-metrics', agentId, selectedTimeRange],
    queryFn: async () => {
      if (agentId) {
        // Single agent metrics
        const stats = await agentBuilderAPI.getAgentStats(agentId);
        return { agents: [stats], summary: stats };
      } else {
        // All agents metrics (mock data for now)
        return {
          agents: [],
          summary: {
            total_agents: 0,
            total_executions: 0,
            avg_success_rate: 0,
            avg_execution_time: 0,
            total_tokens_used: 0,
          }
        };
      }
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Mock historical data for charts
  const generateMockHistoricalData = () => {
    const days = selectedTimeRange === '24h' ? 24 : 
                 selectedTimeRange === '7d' ? 7 : 
                 selectedTimeRange === '30d' ? 30 : 90;
    
    return Array.from({ length: days }, (_, i) => ({
      date: new Date(Date.now() - (days - i - 1) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      executions: Math.floor(Math.random() * 50) + 10,
      success_rate: Math.floor(Math.random() * 20) + 80,
      avg_time: Math.floor(Math.random() * 1000) + 500,
      tokens: Math.floor(Math.random() * 5000) + 1000,
    }));
  };

  const historicalData = generateMockHistoricalData();

  const getMetricIcon = (metric: string) => {
    switch (metric) {
      case 'executions': return Activity;
      case 'success_rate': return CheckCircle;
      case 'avg_time': return Clock;
      case 'tokens': return Zap;
      default: return Activity;
    }
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up': return TrendingUp;
      case 'down': return TrendingDown;
      default: return Activity;
    }
  };

  const getTrendColor = (trend: 'up' | 'down' | 'stable', isGoodTrend: boolean = true) => {
    if (trend === 'stable') return 'text-gray-500';
    const isPositive = (trend === 'up' && isGoodTrend) || (trend === 'down' && !isGoodTrend);
    return isPositive ? 'text-green-500' : 'text-red-500';
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16 mb-2" />
                <Skeleton className="h-3 w-20" />
              </CardContent>
            </Card>
          ))}
        </div>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  const metrics = metricsData?.agents?.[0] || metricsData?.summary;

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h3 className="text-lg font-semibold">Performance Metrics</h3>
          <Select value={selectedTimeRange} onValueChange={(value) => setSelectedTimeRange(value as typeof selectedTimeRange)}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">24 Hours</SelectItem>
              <SelectItem value="7d">7 Days</SelectItem>
              <SelectItem value="30d">30 Days</SelectItem>
              <SelectItem value="90d">90 Days</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Executions</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics && 'total_runs' in metrics ? metrics.total_runs : (metrics && 'total_executions' in metrics ? metrics.total_executions : 0)}
            </div>
            <div className="flex items-center text-xs text-muted-foreground">
              <TrendingUp className="h-3 w-3 mr-1 text-green-500" />
              +12% vs last week
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics && 'success_rate' in metrics ? metrics.success_rate : (metrics && 'avg_success_rate' in metrics ? metrics.avg_success_rate : 0)}%
            </div>
            <Progress value={metrics && 'success_rate' in metrics ? metrics.success_rate : (metrics && 'avg_success_rate' in metrics ? metrics.avg_success_rate : 0)} className="mt-2" />
            <div className="flex items-center text-xs text-muted-foreground mt-1">
              <TrendingUp className="h-3 w-3 mr-1 text-green-500" />
              +2.1% vs last week
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Execution Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(metrics && 'avg_duration_ms' in metrics ? metrics.avg_duration_ms : (metrics && 'avg_execution_time' in metrics ? metrics.avg_execution_time : 0)) 
                ? `${((metrics && 'avg_duration_ms' in metrics ? (metrics.avg_duration_ms || 0) : (metrics && 'avg_execution_time' in metrics ? (metrics.avg_execution_time || 0) : 0)) / 1000).toFixed(1)}s` 
                : '0s'}
            </div>
            <div className="flex items-center text-xs text-muted-foreground">
              <TrendingDown className="h-3 w-3 mr-1 text-green-500" />
              -5.2% vs last week
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Token Usage</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(metrics && 'total_tokens' in metrics ? metrics.total_tokens : (metrics && 'total_tokens_used' in metrics ? metrics.total_tokens_used : 0))
                ? `${(Number(metrics && 'total_tokens' in metrics ? metrics.total_tokens : (metrics && 'total_tokens_used' in metrics ? metrics.total_tokens_used : 0)) / 1000).toFixed(1)}K`
                : '0'}
            </div>
            <div className="flex items-center text-xs text-muted-foreground">
              <TrendingUp className="h-3 w-3 mr-1 text-orange-500" />
              +8.3% vs last week
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <Tabs defaultValue="performance" className="space-y-4">
        <TabsList>
          <TabsTrigger value="performance">Performance Trend</TabsTrigger>
          <TabsTrigger value="usage">Usage Analysis</TabsTrigger>
          <TabsTrigger value="errors">Error Analysis</TabsTrigger>
          <TabsTrigger value="comparison">Comparison</TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Performance Trend</CardTitle>
                  <CardDescription>Execution performance changes over time</CardDescription>
                </div>
                <Select value={selectedMetric} onValueChange={(value: any) => setSelectedMetric(value)}>
                  <SelectTrigger className="w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="executions">Executions</SelectItem>
                    <SelectItem value="success_rate">Success Rate</SelectItem>
                    <SelectItem value="avg_time">Avg Time</SelectItem>
                    <SelectItem value="tokens">Token Usage</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={historicalData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Area 
                    type="monotone" 
                    dataKey={selectedMetric} 
                    stroke="#8884d8" 
                    fill="#8884d8" 
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="usage" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Usage by Time</CardTitle>
                <CardDescription>Usage pattern over 24 hours</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={historicalData.slice(0, 24)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="executions" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Execution Results</CardTitle>
                <CardDescription>Success/Failure ratio</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Success', value: (metrics && 'successful_runs' in metrics ? metrics.successful_runs : 0), fill: '#82ca9d' },
                        { name: 'Failed', value: (metrics && 'failed_runs' in metrics ? metrics.failed_runs : 0), fill: '#ff7300' },
                      ]}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="value"
                      label
                    >
                      {[
                        { name: 'Success', value: (metrics && 'successful_runs' in metrics ? metrics.successful_runs : 0) },
                        { name: 'Failed', value: (metrics && 'failed_runs' in metrics ? metrics.failed_runs : 0) },
                      ].map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="errors" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Error Analysis</CardTitle>
              <CardDescription>Error patterns and types</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="flex items-center gap-3 p-3 border rounded-lg">
                    <AlertTriangle className="h-8 w-8 text-red-500" />
                    <div>
                      <p className="font-medium">Timeout Errors</p>
                      <p className="text-sm text-muted-foreground">3 cases</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 border rounded-lg">
                    <XCircle className="h-8 w-8 text-orange-500" />
                    <div>
                      <p className="font-medium">API Errors</p>
                      <p className="text-sm text-muted-foreground">1 case</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 border rounded-lg">
                    <AlertTriangle className="h-8 w-8 text-yellow-500" />
                    <div>
                      <p className="font-medium">Validation Errors</p>
                      <p className="text-sm text-muted-foreground">2 cases</p>
                    </div>
                  </div>
                </div>

                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={historicalData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line 
                      type="monotone" 
                      dataKey="success_rate" 
                      stroke="#82ca9d" 
                      name="Success Rate"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="comparison" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Agent Comparison</CardTitle>
              <CardDescription>Performance comparison with other agents</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Compare the current agent&apos;s performance with other agents.
                </p>
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <Badge variant="outline">Current</Badge>
                      <span className="font-medium">{String(metrics && 'agent_name' in metrics ? metrics.agent_name : 'Current Agent')}</span>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span>Success Rate: {(metrics && 'success_rate' in metrics ? metrics.success_rate : (metrics && 'avg_success_rate' in metrics ? metrics.avg_success_rate : 0))}%</span>
                      <span>Avg Time: {(metrics && 'avg_duration_ms' in metrics ? metrics.avg_duration_ms : (metrics && 'avg_execution_time' in metrics ? metrics.avg_execution_time : 0)) ? `${((metrics && 'avg_duration_ms' in metrics ? (metrics.avg_duration_ms || 0) : (metrics && 'avg_execution_time' in metrics ? (metrics.avg_execution_time || 0) : 0)) / 1000).toFixed(1)}s` : '0s'}</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 border rounded-lg bg-muted/50">
                    <div className="flex items-center gap-3">
                      <Badge variant="secondary">Average</Badge>
                      <span className="font-medium">All Agents Average</span>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span>Success Rate: 87.3%</span>
                      <span>Avg Time: 2.1s</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}