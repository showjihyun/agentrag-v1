'use client';

/**
 * Real-Time Overview Component
 * Displays current system metrics and mode distribution
 */

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

interface RealTimeOverviewProps {
  autoRefresh: boolean;
  refreshInterval: number;
}

interface DashboardData {
  overview: {
    total_queries: number;
    time_range: { start: string; end: string };
    avg_routing_confidence: number;
    avg_routing_time_ms: number;
  };
  mode_distribution: {
    counts: Record<string, number>;
    percentages: Record<string, number>;
  };
  latency: {
    average_by_mode: Record<string, number>;
    p95_by_mode: Record<string, number>;
  };
  cache_performance: {
    hit_rates: Record<string, number>;
  };
  escalations: {
    total: number;
    rate_percent: number;
  };
}

export default function RealTimeOverview({ autoRefresh, refreshInterval }: RealTimeOverviewProps) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchData = async () => {
    try {
      setError(null);
      const response = await fetch('http://localhost:8000/api/metrics/adaptive');
      if (!response.ok) throw new Error('Failed to fetch metrics');
      const metricsData = await response.json();
      setData(metricsData);
      setLastUpdate(new Date());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchData, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading metrics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center gap-3">
          <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <h3 className="text-red-800 font-medium">Error loading metrics</h3>
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        </div>
        <button
          onClick={fetchData}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  const modeColors: Record<string, string> = {
    fast: 'bg-green-500',
    balanced: 'bg-blue-500',
    deep: 'bg-purple-500',
  };

  const modeLabels: Record<string, string> = {
    fast: 'Fast',
    balanced: 'Balanced',
    deep: 'Deep',
  };

  return (
    <div className="space-y-6">
      {/* Header with last update */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-900">Real-Time Overview</h2>
        <div className="text-sm text-gray-500">
          Last updated: {lastUpdate.toLocaleTimeString()}
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Queries */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Queries</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {data.overview.total_queries.toLocaleString()}
              </p>
            </div>
            <div className="bg-blue-100 rounded-full p-3">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
          </div>
        </div>

        {/* Routing Confidence */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Routing Confidence</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {(data.overview.avg_routing_confidence * 100).toFixed(1)}%
              </p>
            </div>
            <div className="bg-green-100 rounded-full p-3">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>

        {/* Routing Time */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Routing Time</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {data.overview.avg_routing_time_ms.toFixed(1)}ms
              </p>
            </div>
            <div className="bg-yellow-100 rounded-full p-3">
              <svg className="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>

        {/* Escalation Rate */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Escalation Rate</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {data.escalations.rate_percent.toFixed(1)}%
              </p>
            </div>
            <div className={`rounded-full p-3 ${
              data.escalations.rate_percent > 15 ? 'bg-red-100' : 'bg-purple-100'
            }`}>
              <svg className={`w-8 h-8 ${
                data.escalations.rate_percent > 15 ? 'text-red-600' : 'text-purple-600'
              }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Mode Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Mode Distribution Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Mode Distribution</h3>
          <div className="space-y-4">
            {Object.entries(data.mode_distribution.percentages).map(([mode, percentage]) => (
              <div key={mode}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium text-gray-700">{modeLabels[mode] || mode}</span>
                  <span className="text-gray-600">
                    {percentage.toFixed(1)}% ({data.mode_distribution.counts[mode]} queries)
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full ${modeColors[mode] || 'bg-gray-500'}`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
          
          {/* Target distribution indicator */}
          <div className="mt-6 pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-600 mb-2">Target Distribution:</p>
            <div className="flex gap-4 text-xs text-gray-500">
              <span>Fast: 40-50%</span>
              <span>Balanced: 30-40%</span>
              <span>Deep: 20-30%</span>
            </div>
          </div>
        </div>

        {/* Latency by Mode */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Latency by Mode</h3>
          <div className="space-y-4">
            {Object.entries(data.latency.average_by_mode).map(([mode, avgLatency]) => {
              const p95Latency = data.latency.p95_by_mode[mode] || 0;
              const targets: Record<string, number> = { fast: 1.0, balanced: 3.0, deep: 15.0 };
              const target = targets[mode] || 10;
              const isOverTarget = p95Latency > target;
              
              return (
                <div key={mode} className="border border-gray-200 rounded p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-medium text-gray-700">{modeLabels[mode] || mode}</span>
                    <span className={`text-sm ${isOverTarget ? 'text-red-600' : 'text-green-600'}`}>
                      Target: &lt;{target}s
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600">Average</p>
                      <p className="text-lg font-semibold text-gray-900">{avgLatency.toFixed(2)}s</p>
                    </div>
                    <div>
                      <p className="text-gray-600">P95</p>
                      <p className={`text-lg font-semibold ${isOverTarget ? 'text-red-600' : 'text-gray-900'}`}>
                        {p95Latency.toFixed(2)}s
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Cache Performance */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Cache Performance</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {Object.entries(data.cache_performance.hit_rates).map(([mode, hitRate]) => (
            <div key={mode} className="text-center">
              <p className="text-sm text-gray-600 mb-2">{modeLabels[mode] || mode} Mode</p>
              <div className="relative inline-flex items-center justify-center w-32 h-32">
                <svg className="w-32 h-32 transform -rotate-90">
                  <circle
                    cx="64"
                    cy="64"
                    r="56"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="none"
                    className="text-gray-200"
                  />
                  <circle
                    cx="64"
                    cy="64"
                    r="56"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="none"
                    strokeDasharray={`${2 * Math.PI * 56}`}
                    strokeDashoffset={`${2 * Math.PI * 56 * (1 - hitRate / 100)}`}
                    className={modeColors[mode]?.replace('bg-', 'text-') || 'text-gray-500'}
                  />
                </svg>
                <span className="absolute text-2xl font-bold text-gray-900">
                  {hitRate.toFixed(0)}%
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-2">Cache Hit Rate</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
