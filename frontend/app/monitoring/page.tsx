'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface MetricStats {
  metric_name: string;
  time_window_minutes: number;
  count: number;
  avg: number;
  p50: number;
  p95: number;
  p99: number;
  min: number;
  max: number;
}

interface CacheMetrics {
  cache_type: string;
  hit_rate: number;
  time_window_minutes: number;
}

interface AgentMetrics {
  agent_name: string;
  success_rate: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  time_window_minutes: number;
}

interface SystemMetrics {
  timestamp: string;
  query_metrics: MetricStats | null;
  cache_metrics: CacheMetrics[];
  agent_metrics: AgentMetrics[];
  llm_metrics: {
    avg_latency_ms: number;
    p95_latency_ms: number;
    total_requests: number;
  } | null;
}

export default function MonitoringPage() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [timeWindow, setTimeWindow] = useState(60);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [timeWindow]);

  const fetchMetrics = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/monitoring/metrics/system?time_window=${timeWindow}`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch metrics');
      }
      
      const data = await response.json();
      setMetrics(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading metrics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">System Monitoring</h1>
        <select
          value={timeWindow}
          onChange={(e) => setTimeWindow(Number(e.target.value))}
          className="px-4 py-2 border rounded-lg"
        >
          <option value={15}>Last 15 minutes</option>
          <option value={60}>Last hour</option>
          <option value={360}>Last 6 hours</option>
          <option value={1440}>Last 24 hours</option>
        </select>
      </div>

      {/* Query Performance */}
      {metrics?.query_metrics && (
        <Card>
          <CardHeader>
            <CardTitle>Query Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard
                label="Total Queries"
                value={metrics.query_metrics.count}
              />
              <MetricCard
                label="Avg Latency"
                value={`${metrics.query_metrics.avg.toFixed(0)}ms`}
              />
              <MetricCard
                label="P95 Latency"
                value={`${metrics.query_metrics.p95.toFixed(0)}ms`}
                warning={metrics.query_metrics.p95 > 3000}
              />
              <MetricCard
                label="P99 Latency"
                value={`${metrics.query_metrics.p99.toFixed(0)}ms`}
                warning={metrics.query_metrics.p99 > 5000}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Cache Performance */}
      {metrics?.cache_metrics && metrics.cache_metrics.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Cache Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {metrics.cache_metrics.map((cache) => (
                <MetricCard
                  key={cache.cache_type}
                  label={`${cache.cache_type} Cache`}
                  value={`${(cache.hit_rate * 100).toFixed(1)}%`}
                  warning={cache.hit_rate < 0.3}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Agent Performance */}
      {metrics?.agent_metrics && metrics.agent_metrics.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Agent Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {metrics.agent_metrics.map((agent) => (
                <div key={agent.agent_name} className="border-b pb-4 last:border-b-0">
                  <h3 className="font-semibold mb-2 capitalize">
                    {agent.agent_name.replace('_', ' ')}
                  </h3>
                  <div className="grid grid-cols-3 gap-4">
                    <MetricCard
                      label="Success Rate"
                      value={`${(agent.success_rate * 100).toFixed(1)}%`}
                      warning={agent.success_rate < 0.9}
                    />
                    <MetricCard
                      label="Avg Latency"
                      value={`${agent.avg_latency_ms.toFixed(0)}ms`}
                    />
                    <MetricCard
                      label="P95 Latency"
                      value={`${agent.p95_latency_ms.toFixed(0)}ms`}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* LLM Performance */}
      {metrics?.llm_metrics && (
        <Card>
          <CardHeader>
            <CardTitle>LLM Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              <MetricCard
                label="Total Requests"
                value={metrics.llm_metrics.total_requests}
              />
              <MetricCard
                label="Avg Latency"
                value={`${metrics.llm_metrics.avg_latency_ms.toFixed(0)}ms`}
              />
              <MetricCard
                label="P95 Latency"
                value={`${metrics.llm_metrics.p95_latency_ms.toFixed(0)}ms`}
                warning={metrics.llm_metrics.p95_latency_ms > 10000}
              />
            </div>
          </CardContent>
        </Card>
      )}

      <div className="text-sm text-gray-500 text-center">
        Last updated: {metrics?.timestamp ? new Date(metrics.timestamp).toLocaleString() : 'N/A'}
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  warning = false,
}: {
  label: string;
  value: string | number;
  warning?: boolean;
}) {
  return (
    <div className={`p-4 rounded-lg ${warning ? 'bg-yellow-50 border-yellow-200' : 'bg-gray-50'} border`}>
      <div className="text-sm text-gray-600 mb-1">{label}</div>
      <div className={`text-2xl font-bold ${warning ? 'text-yellow-700' : 'text-gray-900'}`}>
        {value}
      </div>
    </div>
  );
}
