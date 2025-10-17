/**
 * Performance Metrics Component
 * Displays system performance metrics from /health/metrics endpoint
 */

'use client';

import { useState, useEffect } from 'react';

interface PerformanceMetrics {
  system: {
    cpu_percent: number;
    memory_percent: number;
    memory_used_mb: number;
    disk_usage_percent: number;
  };
  performance: {
    period_minutes: number;
    total_requests: number;
    average_duration_ms: number;
    error_count: number;
    error_rate_percent: number;
    requests_per_minute: number;
  };
  endpoints: Record<string, {
    total_requests: number;
    average_duration_ms: number;
    min_duration_ms: number;
    max_duration_ms: number;
    error_count: number;
    error_rate_percent: number;
  }>;
}

export default function PerformanceMetrics() {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await fetch('/api/health/metrics');
      if (!response.ok) throw new Error('Failed to fetch metrics');
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
      <div className="animate-pulse space-y-4">
        <div className="h-32 bg-gray-100 rounded-lg"></div>
        <div className="h-32 bg-gray-100 rounded-lg"></div>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800 text-sm">⚠️ Unable to fetch performance metrics</p>
        {error && <p className="text-red-600 text-xs mt-1">{error}</p>}
      </div>
    );
  }

  const topEndpoints = Object.entries(metrics.endpoints)
    .sort((a, b) => b[1].total_requests - a[1].total_requests)
    .slice(0, 5);

  return (
    <div className="space-y-4">
      {/* System Resources Card */}
      <div className="bg-white border rounded-lg p-4">
        <h3 className="font-semibold mb-3 flex items-center">
          <span className="mr-2">📊</span>
          System Resources
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-blue-50 rounded">
            <p className="text-2xl font-bold text-blue-600">
              {metrics.system.cpu_percent.toFixed(1)}%
            </p>
            <p className="text-xs text-gray-600">CPU Usage</p>
          </div>
          <div className="text-center p-3 bg-green-50 rounded">
            <p className="text-2xl font-bold text-green-600">
              {metrics.system.memory_percent.toFixed(1)}%
            </p>
            <p className="text-xs text-gray-600">Memory Usage</p>
          </div>
          <div className="text-center p-3 bg-purple-50 rounded">
            <p className="text-2xl font-bold text-purple-600">
              {metrics.system.memory_used_mb.toFixed(0)} MB
            </p>
            <p className="text-xs text-gray-600">Memory Used</p>
          </div>
          <div className="text-center p-3 bg-yellow-50 rounded">
            <p className="text-2xl font-bold text-yellow-600">
              {metrics.system.disk_usage_percent.toFixed(1)}%
            </p>
            <p className="text-xs text-gray-600">Disk Usage</p>
          </div>
        </div>
      </div>

      {/* Performance Stats Card */}
      <div className="bg-white border rounded-lg p-4">
        <h3 className="font-semibold mb-3 flex items-center">
          <span className="mr-2">⚡</span>
          Performance (Last {metrics.performance.period_minutes} minutes)
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <p className="text-2xl font-bold text-gray-800">
              {metrics.performance.total_requests}
            </p>
            <p className="text-xs text-gray-600">Total Requests</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-800">
              {metrics.performance.average_duration_ms.toFixed(0)}ms
            </p>
            <p className="text-xs text-gray-600">Avg Response Time</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-800">
              {metrics.performance.requests_per_minute.toFixed(1)}
            </p>
            <p className="text-xs text-gray-600">Requests/Min</p>
          </div>
          <div>
            <p className={`text-2xl font-bold ${
              metrics.performance.error_rate_percent > 5 
                ? 'text-red-600' 
                : 'text-green-600'
            }`}>
              {metrics.performance.error_rate_percent.toFixed(2)}%
            </p>
            <p className="text-xs text-gray-600">Error Rate</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-800">
              {metrics.performance.error_count}
            </p>
            <p className="text-xs text-gray-600">Errors</p>
          </div>
        </div>
      </div>

      {/* Top Endpoints Card */}
      <div className="bg-white border rounded-lg p-4">
        <h3 className="font-semibold mb-3 flex items-center">
          <span className="mr-2">🔝</span>
          Top Endpoints
        </h3>
        <div className="space-y-2">
          {topEndpoints.map(([endpoint, stats]) => (
            <div key={endpoint} className="border-b pb-2 last:border-b-0">
              <div className="flex justify-between items-start mb-1">
                <span className="text-sm font-medium text-gray-700 truncate flex-1">
                  {endpoint}
                </span>
                <span className="text-xs text-gray-500 ml-2">
                  {stats.total_requests} requests
                </span>
              </div>
              <div className="flex justify-between text-xs text-gray-600">
                <span>Avg: {stats.average_duration_ms.toFixed(0)}ms</span>
                <span>Min: {stats.min_duration_ms.toFixed(0)}ms</span>
                <span>Max: {stats.max_duration_ms.toFixed(0)}ms</span>
                <span className={stats.error_rate_percent > 0 ? 'text-red-600' : 'text-green-600'}>
                  Errors: {stats.error_rate_percent.toFixed(1)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Refresh Button */}
      <div className="text-center">
        <button
          onClick={fetchMetrics}
          className="text-sm px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          🔄 Refresh Metrics
        </button>
      </div>
    </div>
  );
}
