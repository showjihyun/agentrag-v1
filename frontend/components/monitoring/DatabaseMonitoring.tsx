'use client';

/**
 * Database Monitoring Component
 * Displays PostgreSQL and Milvus database metrics
 * Reuses existing StatCard and chart components
 */

import React, { useState, useEffect } from 'react';
import StatCard from '@/components/charts/StatCard';
import { cn } from '@/lib/utils';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface DatabaseMonitoringProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface PostgreSQLMetrics {
  pool_size: number;
  checked_in: number;
  checked_out: number;
  overflow: number;
  utilization_percent: number;
  health_status: string;
  total_checkouts?: number;
  avg_connection_duration_ms?: number;
  long_connections_count?: number;
  potential_leaks_count?: number;
}

interface MilvusMetrics {
  total_connections: number;
  in_use: number;
  available: number;
  utilization_percent?: number;
  collection_size?: number;
  index_type?: string;
}

interface DatabaseHealth {
  postgresql: {
    status: string;
    message: string;
    utilization: number;
  };
  milvus: {
    status: string;
    message: string;
  };
  overall_status: string;
}

export default function DatabaseMonitoring({ 
  autoRefresh = true, 
  refreshInterval = 30 
}: DatabaseMonitoringProps) {
  const [pgMetrics, setPgMetrics] = useState<PostgreSQLMetrics | null>(null);
  const [milvusMetrics, setMilvusMetrics] = useState<MilvusMetrics | null>(null);
  const [health, setHealth] = useState<DatabaseHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchMetrics = async () => {
    try {
      setError(null);
      
      // Fetch PostgreSQL metrics
      const pgResponse = await fetch(`${API_BASE_URL}/api/metrics/database/postgresql/pool`);
      if (pgResponse.ok) {
        const pgData = await pgResponse.json();
        setPgMetrics(pgData.detailed || pgData.basic);
      }
      
      // Fetch Milvus metrics
      const milvusResponse = await fetch(`${API_BASE_URL}/api/metrics/database/milvus/pool`);
      if (milvusResponse.ok) {
        const milvusData = await milvusResponse.json();
        setMilvusMetrics(milvusData.stats);
      }
      
      // Fetch overall health
      const healthResponse = await fetch(`${API_BASE_URL}/api/metrics/database/summary`);
      if (healthResponse.ok) {
        const healthData = await healthResponse.json();
        setHealth(healthData);
      }
      
      setLastUpdate(new Date());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchMetrics, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading database metrics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
        <div className="flex items-center gap-3">
          <svg className="w-6 h-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <h3 className="text-red-800 dark:text-red-300 font-medium">Error loading metrics</h3>
            <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
          </div>
        </div>
        <button
          onClick={fetchMetrics}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 dark:text-green-400';
      case 'warning':
      case 'degraded': return 'text-yellow-600 dark:text-yellow-400';
      case 'critical': return 'text-red-600 dark:text-red-400';
      default: return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getHealthBadge = (status: string) => {
    const colors = {
      healthy: 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300',
      warning: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300',
      degraded: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300',
      critical: 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300',
    };
    
    return colors[status as keyof typeof colors] || 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Database Monitoring</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Real-time PostgreSQL and Milvus metrics
          </p>
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-500 dark:text-gray-400">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </div>
          {health && (
            <span className={cn(
              'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium mt-2',
              getHealthBadge(health.overall_status)
            )}>
              <span className={cn(
                'w-2 h-2 rounded-full mr-2',
                health.overall_status === 'healthy' ? 'bg-green-500 animate-pulse' :
                health.overall_status === 'critical' ? 'bg-red-500' :
                'bg-yellow-500'
              )} />
              {health.overall_status.toUpperCase()}
            </span>
          )}
        </div>
      </div>

      {/* PostgreSQL Section */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
          </svg>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">PostgreSQL</h3>
          {health && (
            <span className={cn('text-sm font-medium', getHealthColor(health.postgresql.status))}>
              {health.postgresql.message}
            </span>
          )}
        </div>

        {pgMetrics && (
          <>
            {/* PostgreSQL Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                title="Pool Size"
                value={pgMetrics.pool_size}
                color="blue"
                icon={
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                }
              />
              
              <StatCard
                title="Active Connections"
                value={pgMetrics.checked_out}
                color="green"
                icon={
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                }
              />
              
              <StatCard
                title="Pool Utilization"
                value={`${pgMetrics.utilization_percent.toFixed(1)}%`}
                color={pgMetrics.utilization_percent > 75 ? 'orange' : 'green'}
                icon={
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                }
              />
              
              <StatCard
                title="Avg Connection Time"
                value={pgMetrics.avg_connection_duration_ms ? `${pgMetrics.avg_connection_duration_ms.toFixed(1)}ms` : 'N/A'}
                color="purple"
                icon={
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                }
              />
            </div>

            {/* PostgreSQL Pool Details */}
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
              <h4 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Connection Pool Details</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Checked In</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{pgMetrics.checked_in}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Checked Out</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{pgMetrics.checked_out}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Overflow</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{pgMetrics.overflow}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Checkouts</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {pgMetrics.total_checkouts?.toLocaleString() || 'N/A'}
                  </p>
                </div>
              </div>

              {/* Utilization Bar */}
              <div className="mt-6">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-gray-600 dark:text-gray-400">Pool Utilization</span>
                  <span className="font-medium text-gray-900 dark:text-gray-100">
                    {pgMetrics.checked_out} / {pgMetrics.pool_size + pgMetrics.overflow}
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                  <div
                    className={cn(
                      'h-3 rounded-full transition-all duration-300',
                      pgMetrics.utilization_percent > 90 ? 'bg-red-500' :
                      pgMetrics.utilization_percent > 75 ? 'bg-yellow-500' :
                      'bg-green-500'
                    )}
                    style={{ width: `${Math.min(pgMetrics.utilization_percent, 100)}%` }}
                  />
                </div>
              </div>

              {/* Warnings */}
              {((pgMetrics.long_connections_count && pgMetrics.long_connections_count > 0) || 
                (pgMetrics.potential_leaks_count && pgMetrics.potential_leaks_count > 0)) && (
                <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded">
                  <div className="flex items-start gap-2">
                    <svg className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div className="text-sm">
                      {pgMetrics.long_connections_count && pgMetrics.long_connections_count > 0 && (
                        <p className="text-yellow-800 dark:text-yellow-300">
                          {pgMetrics.long_connections_count} long-lived connection(s) detected
                        </p>
                      )}
                      {pgMetrics.potential_leaks_count && pgMetrics.potential_leaks_count > 0 && (
                        <p className="text-red-800 dark:text-red-300 font-medium">
                          ⚠️ {pgMetrics.potential_leaks_count} potential connection leak(s)!
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Milvus Section */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <svg className="w-6 h-6 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Milvus</h3>
          {health && (
            <span className={cn('text-sm font-medium', getHealthColor(health.milvus.status))}>
              {health.milvus.message}
            </span>
          )}
        </div>

        {milvusMetrics && (
          <>
            {/* Milvus Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                title="Total Connections"
                value={milvusMetrics.total_connections}
                color="purple"
                icon={
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                }
              />
              
              <StatCard
                title="In Use"
                value={milvusMetrics.in_use}
                color="green"
                icon={
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                }
              />
              
              <StatCard
                title="Available"
                value={milvusMetrics.available}
                color="blue"
                icon={
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                }
              />
              
              <StatCard
                title="Collection Size"
                value={milvusMetrics.collection_size?.toLocaleString() || 'N/A'}
                color="orange"
                icon={
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                }
              />
            </div>

            {/* Milvus Pool Details */}
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
              <h4 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Connection Pool Status</h4>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{milvusMetrics.total_connections}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">In Use</p>
                  <p className="text-2xl font-bold text-green-600 dark:text-green-400">{milvusMetrics.in_use}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Available</p>
                  <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{milvusMetrics.available}</p>
                </div>
              </div>

              {milvusMetrics.index_type && (
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Index Type</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-gray-100 mt-1">
                    {milvusMetrics.index_type}
                  </p>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
