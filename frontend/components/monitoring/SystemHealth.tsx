/**
 * System Health Monitor Component
 * Displays real-time system health status from /health/detailed endpoint
 */

'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

interface HealthStatus {
  status: 'healthy' | 'warning' | 'unhealthy';
  timestamp: string;
  components: {
    database: {
      status: string;
      latency_ms: number;
      message: string;
    };
    system: {
      status: string;
      cpu_percent: number;
      memory_percent: number;
      disk_usage_percent: number;
      issues: string[];
    };
  };
}

export default function SystemHealth() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchHealth = async () => {
    try {
      const response = await fetch('/api/health/detailed');
      if (!response.ok) throw new Error('Failed to fetch health status');
      const data = await response.json();
      setHealth(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="animate-pulse bg-gray-100 rounded-lg p-4">
        <div className="h-4 bg-gray-300 rounded w-1/4 mb-2"></div>
        <div className="h-3 bg-gray-300 rounded w-1/2"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800 text-sm">⚠️ Unable to fetch health status</p>
        <p className="text-red-600 text-xs mt-1">{error}</p>
      </div>
    );
  }

  if (!health) return null;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'warning':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'unhealthy':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return '✓';
      case 'warning':
        return '⚠';
      case 'unhealthy':
        return '✗';
      default:
        return '?';
    }
  };

  return (
    <div className="space-y-4">
      {/* Overall Status */}
      <div className={`border rounded-lg p-4 ${getStatusColor(health.status)}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-2xl">{getStatusIcon(health.status)}</span>
            <div>
              <h3 className="font-semibold">System Status</h3>
              <p className="text-sm capitalize">{health.status}</p>
            </div>
          </div>
          <button
            onClick={fetchHealth}
            className="text-sm px-3 py-1 rounded hover:bg-white/50 transition-colors"
            title="Refresh"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Database Status */}
      <div className="bg-white border rounded-lg p-4">
        <h4 className="font-semibold mb-2 flex items-center">
          <span className="mr-2">💾</span>
          Database
        </h4>
        <div className="space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Status:</span>
            <span className={`font-medium ${
              health.components.database.status === 'healthy' 
                ? 'text-green-600' 
                : 'text-red-600'
            }`}>
              {health.components.database.status}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Latency:</span>
            <span className="font-medium">
              {health.components.database.latency_ms.toFixed(2)}ms
            </span>
          </div>
          <p className="text-gray-500 text-xs mt-2">
            {health.components.database.message}
          </p>
        </div>
      </div>

      {/* System Resources */}
      <div className="bg-white border rounded-lg p-4">
        <h4 className="font-semibold mb-3 flex items-center">
          <span className="mr-2">🖥️</span>
          System Resources
        </h4>
        <div className="space-y-3">
          {/* CPU */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">CPU</span>
              <span className="font-medium">
                {health.components.system.cpu_percent.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${
                  health.components.system.cpu_percent > 80
                    ? 'bg-red-500'
                    : health.components.system.cpu_percent > 60
                    ? 'bg-yellow-500'
                    : 'bg-green-500'
                }`}
                style={{ width: `${health.components.system.cpu_percent}%` }}
              />
            </div>
          </div>

          {/* Memory */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">Memory</span>
              <span className="font-medium">
                {health.components.system.memory_percent.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${
                  health.components.system.memory_percent > 85
                    ? 'bg-red-500'
                    : health.components.system.memory_percent > 70
                    ? 'bg-yellow-500'
                    : 'bg-green-500'
                }`}
                style={{ width: `${health.components.system.memory_percent}%` }}
              />
            </div>
          </div>

          {/* Disk */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">Disk</span>
              <span className="font-medium">
                {health.components.system.disk_usage_percent.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${
                  health.components.system.disk_usage_percent > 90
                    ? 'bg-red-500'
                    : health.components.system.disk_usage_percent > 75
                    ? 'bg-yellow-500'
                    : 'bg-green-500'
                }`}
                style={{ width: `${health.components.system.disk_usage_percent}%` }}
              />
            </div>
          </div>
        </div>

        {/* Issues */}
        {health.components.system.issues.length > 0 && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
            <p className="text-sm font-semibold text-yellow-800 mb-1">
              ⚠️ Issues Detected
            </p>
            <ul className="text-xs text-yellow-700 space-y-1">
              {health.components.system.issues.map((issue, idx) => (
                <li key={idx}>• {issue}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Last Updated */}
      <p className="text-xs text-gray-500 text-center">
        Last updated: {new Date(health.timestamp).toLocaleTimeString()}
      </p>
    </div>
  );
}
