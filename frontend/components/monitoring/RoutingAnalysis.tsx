'use client';

/**
 * Routing Analysis Component
 * Displays complexity distribution, routing accuracy, and escalation patterns
 */

import React, { useState, useEffect } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface RoutingAnalysisProps {
  autoRefresh: boolean;
  refreshInterval: number;
}

interface DashboardData {
  complexity_distribution: Record<string, number>;
  mode_distribution: {
    counts: Record<string, number>;
    percentages: Record<string, number>;
  };
  escalations: {
    total: number;
    rate_percent: number;
    by_transition: Record<string, number>;
  };
  overview: {
    total_queries: number;
    avg_routing_confidence: number;
  };
}

export default function RoutingAnalysis({ autoRefresh, refreshInterval }: RoutingAnalysisProps) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setError(null);
      const response = await fetch(`${API_BASE_URL}/api/metrics/adaptive`);
      if (!response.ok) throw new Error('Failed to fetch metrics');
      const metricsData = await response.json();
      setData(metricsData);
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
          <p className="text-gray-600">Loading routing analysis...</p>
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
            <h3 className="text-red-800 font-medium">Error loading routing analysis</h3>
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

  const complexityLabels: Record<string, string> = {
    simple: 'Simple',
    medium: 'Medium',
    complex: 'Complex',
  };

  const complexityColors: Record<string, string> = {
    simple: 'bg-green-500',
    medium: 'bg-yellow-500',
    complex: 'bg-red-500',
  };

  // Calculate routing accuracy (simplified - assumes mode matches complexity)
  const calculateRoutingAccuracy = () => {
    const total = data.overview.total_queries;
    if (total === 0) return 0;
    
    // Simplified accuracy based on routing confidence
    return data.overview.avg_routing_confidence * 100;
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Routing Analysis</h2>

      {/* Routing Accuracy Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Routing Accuracy</h3>
        <div className="flex items-center justify-center">
          <div className="relative inline-flex items-center justify-center w-48 h-48">
            <svg className="w-48 h-48 transform -rotate-90">
              <circle
                cx="96"
                cy="96"
                r="80"
                stroke="currentColor"
                strokeWidth="16"
                fill="none"
                className="text-gray-200"
              />
              <circle
                cx="96"
                cy="96"
                r="80"
                stroke="currentColor"
                strokeWidth="16"
                fill="none"
                strokeDasharray={`${2 * Math.PI * 80}`}
                strokeDashoffset={`${2 * Math.PI * 80 * (1 - calculateRoutingAccuracy() / 100)}`}
                className={calculateRoutingAccuracy() > 85 ? 'text-green-500' : 
                          calculateRoutingAccuracy() > 70 ? 'text-yellow-500' : 'text-red-500'}
              />
            </svg>
            <div className="absolute text-center">
              <span className="text-4xl font-bold text-gray-900">
                {calculateRoutingAccuracy().toFixed(1)}%
              </span>
              <p className="text-sm text-gray-600 mt-1">Confidence</p>
            </div>
          </div>
        </div>
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Based on {data.overview.total_queries} total queries
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Target: &gt;85% routing confidence
          </p>
        </div>
      </div>

      {/* Complexity Distribution */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Query Complexity Distribution</h3>
        {Object.keys(data.complexity_distribution).length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No complexity data available yet.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {Object.entries(data.complexity_distribution).map(([complexity, count]) => {
              const total = Object.values(data.complexity_distribution).reduce((a, b) => a + b, 0);
              const percentage = total > 0 ? (count / total) * 100 : 0;
              
              return (
                <div key={complexity}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium text-gray-700">
                      {complexityLabels[complexity] || complexity}
                    </span>
                    <span className="text-gray-600">
                      {percentage.toFixed(1)}% ({count} queries)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full ${complexityColors[complexity] || 'bg-gray-500'}`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Complexity vs Mode Matrix */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Complexity vs Mode Routing</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Complexity
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  Fast Mode
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  Balanced Mode
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  Deep Mode
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {['simple', 'medium', 'complex'].map(complexity => (
                <tr key={complexity}>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900 capitalize">
                    {complexity}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`inline-block w-3 h-3 rounded-full ${
                      complexity === 'simple' ? 'bg-green-500' : 'bg-gray-300'
                    }`} />
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`inline-block w-3 h-3 rounded-full ${
                      complexity === 'medium' ? 'bg-blue-500' : 'bg-gray-300'
                    }`} />
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`inline-block w-3 h-3 rounded-full ${
                      complexity === 'complex' ? 'bg-purple-500' : 'bg-gray-300'
                    }`} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-gray-500 mt-4">
          Colored circles indicate expected routing patterns
        </p>
      </div>

      {/* Escalation Patterns */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Escalation Patterns</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Escalation Summary */}
          <div>
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Total Escalations</span>
                <span className="text-2xl font-bold text-gray-900">{data.escalations.total}</span>
              </div>
              <div className="flex justify-between items-center mt-2">
                <span className="text-sm text-gray-600">Escalation Rate</span>
                <span className={`text-lg font-semibold ${
                  data.escalations.rate_percent > 15 ? 'text-red-600' : 'text-green-600'
                }`}>
                  {data.escalations.rate_percent.toFixed(1)}%
                </span>
              </div>
            </div>
            <p className="text-xs text-gray-500">
              Target escalation rate: &lt;15%
            </p>
          </div>

          {/* Escalation Transitions */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Escalation Transitions</h4>
            {Object.keys(data.escalations.by_transition).length === 0 ? (
              <p className="text-sm text-gray-500">No escalations recorded yet.</p>
            ) : (
              <div className="space-y-2">
                {Object.entries(data.escalations.by_transition).map(([transition, count]) => {
                  const [from, to] = transition.split('_to_');
                  return (
                    <div key={transition} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <div className="flex items-center gap-2 text-sm">
                        <span className="capitalize text-gray-700">{from}</span>
                        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                        </svg>
                        <span className="capitalize text-gray-700">{to}</span>
                      </div>
                      <span className="text-sm font-medium text-gray-900">{count}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
