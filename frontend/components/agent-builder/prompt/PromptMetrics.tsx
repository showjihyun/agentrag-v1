'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts';
import { useTheme } from 'next-themes';
import { TrendingUp, TrendingDown, Minus, Target, Clock, DollarSign } from 'lucide-react';

interface PromptMetricsProps {
  agentId: string;
  currentPrompt: string;
}

interface Metrics {
  clarity_score: number;
  specificity_score: number;
  token_efficiency: number;
  avg_response_time: number;
  success_rate: number;
  avg_cost_per_execution: number;
  total_executions: number;
  history: Array<{
    date: string;
    success_rate: number;
    avg_response_time: number;
  }>;
}

export function PromptMetrics({ agentId, currentPrompt }: PromptMetricsProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMetrics();
  }, [agentId]);

  const loadMetrics = async () => {
    try {
      setLoading(true);
      const data = await agentBuilderAPI.getPromptMetrics(agentId);
      setMetrics(data);
    } catch (error) {
      console.error('Failed to load metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-500';
    if (score >= 60) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getScoreBadgeVariant = (score: number): 'default' | 'secondary' | 'destructive' => {
    if (score >= 80) return 'default';
    if (score >= 60) return 'secondary';
    return 'destructive';
  };

  const getTrendIcon = (current: number, previous: number) => {
    if (current > previous) return <TrendingUp className="h-4 w-4 text-green-500" />;
    if (current < previous) return <TrendingDown className="h-4 w-4 text-red-500" />;
    return <Minus className="h-4 w-4 text-gray-500" />;
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!metrics) {
    return (
      <Card>
        <CardContent className="p-12 text-center text-muted-foreground">
          No metrics available yet. Execute the agent to collect performance data.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Quality Scores */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Clarity Score</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className={`text-3xl font-bold ${getScoreColor(metrics.clarity_score)}`}>
                  {metrics.clarity_score}
                </span>
                <Badge variant={getScoreBadgeVariant(metrics.clarity_score)}>
                  {metrics.clarity_score >= 80 ? 'Excellent' : metrics.clarity_score >= 60 ? 'Good' : 'Needs Work'}
                </Badge>
              </div>
              <Progress value={metrics.clarity_score} className="h-2" />
              <p className="text-xs text-muted-foreground">
                How clear and unambiguous your prompt is
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Specificity Score</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className={`text-3xl font-bold ${getScoreColor(metrics.specificity_score)}`}>
                  {metrics.specificity_score}
                </span>
                <Badge variant={getScoreBadgeVariant(metrics.specificity_score)}>
                  {metrics.specificity_score >= 80 ? 'Excellent' : metrics.specificity_score >= 60 ? 'Good' : 'Needs Work'}
                </Badge>
              </div>
              <Progress value={metrics.specificity_score} className="h-2" />
              <p className="text-xs text-muted-foreground">
                How specific and detailed your instructions are
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Token Efficiency</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className={`text-3xl font-bold ${getScoreColor(metrics.token_efficiency)}`}>
                  {metrics.token_efficiency}%
                </span>
                <Badge variant={getScoreBadgeVariant(metrics.token_efficiency)}>
                  {metrics.token_efficiency >= 80 ? 'Efficient' : metrics.token_efficiency >= 60 ? 'Moderate' : 'Verbose'}
                </Badge>
              </div>
              <Progress value={metrics.token_efficiency} className="h-2" />
              <p className="text-xs text-muted-foreground">
                How efficiently your prompt uses tokens
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-2">
              <Target className="h-4 w-4" />
              Success Rate
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.success_rate}%</div>
            <p className="text-xs text-muted-foreground mt-1">
              {metrics.total_executions} executions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Avg Response Time
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.avg_response_time.toFixed(2)}s</div>
            <p className="text-xs text-muted-foreground mt-1">
              Per execution
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              Avg Cost
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${metrics.avg_cost_per_execution.toFixed(4)}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Per execution
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Total Executions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.total_executions}</div>
            <p className="text-xs text-muted-foreground mt-1">
              All time
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Performance History */}
      {metrics.history && metrics.history.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Performance Trend</CardTitle>
            <CardDescription>Success rate and response time over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={metrics.history}>
                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
                <XAxis
                  dataKey="date"
                  stroke={isDark ? '#9ca3af' : '#6b7280'}
                  fontSize={12}
                />
                <YAxis stroke={isDark ? '#9ca3af' : '#6b7280'} fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: isDark ? '#1f2937' : '#ffffff',
                    border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="success_rate"
                  stroke="#10b981"
                  name="Success Rate (%)"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="avg_response_time"
                  stroke="#3b82f6"
                  name="Response Time (s)"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
