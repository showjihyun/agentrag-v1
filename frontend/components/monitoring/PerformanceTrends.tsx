'use client';

/**
 * Performance Trends Component
 * Displays time-series charts for latency and mode distribution
 */

import React, { useState, useEffect } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface PerformanceTrendsProps {
  autoRefresh: boolean;
  refreshInterval: number;
}

interface TimeSeriesData {
  timestamp: string;
  values: Record<string, number>;
}

export default function PerformanceTrends({ autoRefresh, refreshInterval }: PerformanceTrendsProps) {
  const [latencyData, setLatencyData] = useState<TimeSeriesData[]>([]);
  const [modeData, setModeData] = useState<TimeSeriesData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<number>(24); // hours

  const fetchTimeSeriesData = async () => {
    try {
      setError(null);
      
      // Fetch latency time series
      const latencyResponse = await fetch(
        `${API_BASE_URL}/api/metrics/adaptive/timeseries?metric=latency&hours=${timeRange}`
      );
      if (!latencyResponse.ok) throw new Error('Failed to fetch latency data');
      const latencyJson = await latencyResponse.json();
      setLatencyData(latencyJson.data || []);
      
      // Fetch mode distribution time series
      const modeResponse = await fetch(
        `${API_BASE_URL}/api/metrics/adaptive/timeseries?metric=mode_distribution&hours=${timeRange}`
      );
      if (!modeResponse.ok) throw new Error('Failed to fetch mode distribution data');
      const modeJson = await modeResponse.json();
      setModeData(modeJson.data || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTimeSeriesData();
  }, [timeRange]);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchTimeSeriesData, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, timeRange]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading trends...</p>
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
            <h3 className="text-red-800 font-medium">Error loading trends</h3>
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        </div>
        <button
          onClick={fetchTimeSeriesData}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="space-y-6">
      {/* Header with time range selector */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-900">Performance Trends</h2>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(Number(e.target.value))}
          className="border border-gray-300 rounded px-3 py-2 text-sm"
        >
          <option value={1}>Last Hour</option>
          <option value={6}>Last 6 Hours</option>
          <option value={24}>Last 24 Hours</option>
          <option value={168}>Last Week</option>
        </select>
      </div>

      {/* Latency Trends */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Latency Over Time</h3>
        {latencyData.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p>No latency data available yet.</p>
            <p className="text-sm mt-2">Data will appear as queries are processed.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Simple line chart representation */}
            <div className="h-64 flex items-end gap-1">
              {latencyData.slice(-50).map((point, index) => {
                const maxLatency = Math.max(
                  ...latencyData.map(p => Math.max(...Object.values(p.values)))
                );
                const avgLatency = Object.values(point.values).reduce((a, b) => a + b, 0) / 
                  Object.values(point.values).length;
                const height = (avgLatency / maxLatency) * 100;
                
                return (
                  <div
                    key={index}
                    className="flex-1 bg-blue-500 rounded-t hover:bg-blue-600 transition-colors cursor-pointer"
                    style={{ height: `${height}%` }}
                    title={`${formatTimestamp(point.timestamp)}: ${avgLatency.toFixed(2)}s`}
                  />
                );
              })}
            </div>
            
            {/* Legend */}
            <div className="flex justify-between text-sm text-gray-600">
              <span>{latencyData.length > 0 ? formatTimestamp(latencyData[0].timestamp) : ''}</span>
              <span>Average Latency</span>
              <span>{latencyData.length > 0 ? formatTimestamp(latencyData[latencyData.length - 1].timestamp) : ''}</span>
            </div>
            
            {/* Mode-specific latency table */}
            {latencyData.length > 0 && (
              <div className="mt-6 overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Mode</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Current</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Min</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Max</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Avg</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {['fast', 'balanced', 'deep'].map(mode => {
                      const values = latencyData
                        .map(p => p.values[mode])
                        .filter(v => v !== undefined);
                      
                      if (values.length === 0) return null;
                      
                      const current = values[values.length - 1];
                      const min = Math.min(...values);
                      const max = Math.max(...values);
                      const avg = values.reduce((a, b) => a + b, 0) / values.length;
                      
                      return (
                        <tr key={mode}>
                          <td className="px-4 py-2 text-sm font-medium text-gray-900 capitalize">{mode}</td>
                          <td className="px-4 py-2 text-sm text-gray-900">{current.toFixed(2)}s</td>
                          <td className="px-4 py-2 text-sm text-gray-600">{min.toFixed(2)}s</td>
                          <td className="px-4 py-2 text-sm text-gray-600">{max.toFixed(2)}s</td>
                          <td className="px-4 py-2 text-sm text-gray-600">{avg.toFixed(2)}s</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Mode Distribution Trends */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Mode Distribution Over Time</h3>
        {modeData.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p>No mode distribution data available yet.</p>
            <p className="text-sm mt-2">Data will appear as queries are processed.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Stacked area chart representation */}
            <div className="h-64 flex items-end gap-1">
              {modeData.slice(-50).map((point, index) => {
                const total = Object.values(point.values).reduce((a, b) => a + b, 0);
                const fastPct = ((point.values.fast || 0) / total) * 100;
                const balancedPct = ((point.values.balanced || 0) / total) * 100;
                const deepPct = ((point.values.deep || 0) / total) * 100;
                
                return (
                  <div key={index} className="flex-1 flex flex-col justify-end h-full">
                    <div
                      className="bg-purple-500 hover:bg-purple-600 transition-colors"
                      style={{ height: `${deepPct}%` }}
                      title={`Deep: ${deepPct.toFixed(1)}%`}
                    />
                    <div
                      className="bg-blue-500 hover:bg-blue-600 transition-colors"
                      style={{ height: `${balancedPct}%` }}
                      title={`Balanced: ${balancedPct.toFixed(1)}%`}
                    />
                    <div
                      className="bg-green-500 hover:bg-green-600 transition-colors"
                      style={{ height: `${fastPct}%` }}
                      title={`Fast: ${fastPct.toFixed(1)}%`}
                    />
                  </div>
                );
              })}
            </div>
            
            {/* Legend */}
            <div className="flex justify-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-green-500 rounded"></div>
                <span className="text-gray-700">Fast Mode</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-blue-500 rounded"></div>
                <span className="text-gray-700">Balanced Mode</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-purple-500 rounded"></div>
                <span className="text-gray-700">Deep Mode</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
