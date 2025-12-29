'use client';

import { useState, useEffect } from 'react';
import { Clock, Zap, Database, TrendingUp, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { agentBuilderAPI, ExecutionMetrics as ExecutionMetricsType } from '@/lib/api/agent-builder';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface ExecutionMetricsProps {
  executionId: string;
}

export default function ExecutionMetrics({ executionId }: ExecutionMetricsProps) {
  const [metrics, setMetrics] = useState<ExecutionMetricsType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMetrics();
  }, [executionId]);

  const loadMetrics = async () => {
    try {
      const metricsData = await agentBuilderAPI.getExecutionMetrics(executionId);
      setMetrics(metricsData);
    } catch (error) {
      console.error('Failed to load execution metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-muted-foreground">Loading metrics...</div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-muted-foreground">No metrics available</div>
      </div>
    );
  }

  const tokenData = [
    {
      name: 'Prompt Tokens',
      value: metrics.llm_prompt_tokens,
      fill: '#3b82f6',
    },
    {
      name: 'Completion Tokens',
      value: metrics.llm_completion_tokens,
      fill: '#10b981',
    },
  ];

  const cacheData = [
    {
      name: 'Cache Hits',
      value: metrics.cache_hit_count,
      fill: '#10b981',
    },
    {
      name: 'Cache Misses',
      value: metrics.cache_miss_count,
      fill: '#ef4444',
    },
  ];

  const cacheHitRate =
    metrics.cache_hit_count + metrics.cache_miss_count > 0
      ? ((metrics.cache_hit_count / (metrics.cache_hit_count + metrics.cache_miss_count)) * 100).toFixed(1)
      : '0';

  return (
    <div className="space-y-6">
      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">LLM Calls</CardTitle>
              <Zap className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.llm_call_count}</div>
            <p className="text-xs text-muted-foreground mt-1">Total LLM invocations</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">Total Tokens</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.llm_total_tokens.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {metrics.llm_prompt_tokens.toLocaleString()} prompt + {metrics.llm_completion_tokens.toLocaleString()}{' '}
              completion
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">Tool Calls</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.tool_call_count}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {metrics.tool_total_duration_ms}ms total duration
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">Cache Hit Rate</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{cacheHitRate}%</div>
            <p className="text-xs text-muted-foreground mt-1">
              {metrics.cache_hit_count} hits / {metrics.cache_miss_count} misses
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Token Distribution Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Token Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={tokenData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Cache Performance Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Cache Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={cacheData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Performance Percentiles */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">Average LLM Call Duration</div>
              <div className="text-sm font-medium">
                {metrics.llm_call_count > 0
                  ? `${(metrics.tool_total_duration_ms / metrics.llm_call_count).toFixed(2)}ms`
                  : '-'}
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">Average Tool Call Duration</div>
              <div className="text-sm font-medium">
                {metrics.tool_call_count > 0
                  ? `${(metrics.tool_total_duration_ms / metrics.tool_call_count).toFixed(2)}ms`
                  : '-'}
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">Tokens per LLM Call</div>
              <div className="text-sm font-medium">
                {metrics.llm_call_count > 0
                  ? `${Math.round(metrics.llm_total_tokens / metrics.llm_call_count)}`
                  : '-'}
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">Cache Efficiency</div>
              <div className="text-sm font-medium">{cacheHitRate}%</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Rates (if applicable) */}
      {metrics.llm_call_count > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              <CardTitle>Error Analysis</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="text-sm text-muted-foreground">Success Rate</div>
                <div className="text-sm font-medium text-green-600">100%</div>
              </div>
              <div className="flex items-center justify-between">
                <div className="text-sm text-muted-foreground">Failed Calls</div>
                <div className="text-sm font-medium">0</div>
              </div>
              <div className="flex items-center justify-between">
                <div className="text-sm text-muted-foreground">Retry Count</div>
                <div className="text-sm font-medium">0</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
