'use client';

/**
 * ReAct Statistics Dashboard Page
 * 
 * Displays real-time statistics for ReAct improvements:
 * - Episodic Memory (pattern reuse)
 * - Observation Processing (relevance filtering)
 * - System health
 */

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

interface EpisodicMemoryStats {
  total_episodes: number;
  avg_confidence: number;
  avg_iterations: number;
  avg_elapsed_time: number;
  total_reuses: number;
  most_reused_query: string | null;
  most_reused_count: number;
  reuse_rate: number;
}

interface ObservationStats {
  total_observations: number;
  filtered_observations: number;
  filter_rate: number;
  avg_relevance: number;
  processing_count: number;
  avg_observations_per_query: number;
}

interface SystemMetrics {
  total_queries_processed: number;
  pattern_reuse_rate: number;
  avg_observations_filtered: number;
}

interface ReactStats {
  status: string;
  episodic_memory: EpisodicMemoryStats;
  observation_processing: ObservationStats;
  system_metrics: SystemMetrics;
}

export default function ReactStatsPage() {
  const [stats, setStats] = useState<ReactStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/react/statistics');
      if (!response.ok) throw new Error('Failed to fetch statistics');
      const data = await response.json();
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    
    if (autoRefresh) {
      const interval = setInterval(fetchStats, 10000); // Refresh every 10 seconds
      return () => clearInterval(interval);
    }
    
    return () => {}; // Return empty cleanup function for other code paths
  }, [autoRefresh]);

  const handleReset = async () => {
    if (!confirm('Are you sure you want to reset statistics? This cannot be undone.')) {
      return;
    }
    
    try {
      const response = await fetch('/api/react/statistics/reset', {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to reset statistics');
      await fetchStats(); // Refresh after reset
      alert('Statistics reset successfully');
    } catch (err) {
      alert('Failed to reset statistics: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading statistics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 dark:text-red-400">Error: {error}</p>
          <button
            onClick={fetchStats}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                ReAct Statistics Dashboard
              </h1>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                Real-time performance metrics for ReAct improvements
              </p>
            </div>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="rounded"
                />
                Auto-refresh (10s)
              </label>
              <button
                onClick={fetchStats}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
              >
                Refresh Now
              </button>
              <button
                onClick={handleReset}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition"
              >
                Reset Stats
              </button>
            </div>
          </div>
        </div>

        {/* System Metrics Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <MetricCard
            title="Total Queries"
            value={stats.system_metrics.total_queries_processed}
            icon="📊"
            color="blue"
          />
          <MetricCard
            title="Pattern Reuse Rate"
            value={`${(stats.system_metrics.pattern_reuse_rate * 100).toFixed(1)}%`}
            icon="🎯"
            color="green"
            subtitle={`${stats.episodic_memory.total_reuses} reuses`}
          />
          <MetricCard
            title="Avg Filter Rate"
            value={`${(stats.system_metrics.avg_observations_filtered * 100).toFixed(1)}%`}
            icon="🔍"
            color="purple"
          />
        </div>

        {/* Episodic Memory Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
            <span>🧠</span>
            Episodic Memory (Pattern Reuse)
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatItem
              label="Total Episodes"
              value={stats.episodic_memory.total_episodes}
              description="Stored successful patterns"
            />
            <StatItem
              label="Avg Confidence"
              value={stats.episodic_memory.avg_confidence.toFixed(2)}
              description="Pattern quality score"
            />
            <StatItem
              label="Avg Iterations"
              value={stats.episodic_memory.avg_iterations.toFixed(1)}
              description="Steps per query"
            />
            <StatItem
              label="Avg Time"
              value={`${stats.episodic_memory.avg_elapsed_time.toFixed(1)}s`}
              description="Processing time"
            />
          </div>

          {stats.episodic_memory.most_reused_query && (
            <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Most Reused Pattern:
              </p>
              <p className="mt-1 text-lg font-semibold text-blue-600 dark:text-blue-400">
                "{stats.episodic_memory.most_reused_query}"
              </p>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                Reused {stats.episodic_memory.most_reused_count} times
              </p>
            </div>
          )}
        </div>

        {/* Observation Processing Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
            <span>🔍</span>
            Observation Processing (Relevance Filtering)
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <StatItem
              label="Total Observations"
              value={stats.observation_processing.total_observations}
              description="All processed observations"
            />
            <StatItem
              label="Filtered Observations"
              value={stats.observation_processing.filtered_observations}
              description="Passed relevance threshold"
            />
            <StatItem
              label="Filter Rate"
              value={`${(stats.observation_processing.filter_rate * 100).toFixed(1)}%`}
              description="Percentage filtered out"
            />
            <StatItem
              label="Avg Relevance"
              value={stats.observation_processing.avg_relevance.toFixed(2)}
              description="Quality score (0-1)"
            />
            <StatItem
              label="Processing Count"
              value={stats.observation_processing.processing_count}
              description="Total filter operations"
            />
            <StatItem
              label="Avg per Query"
              value={stats.observation_processing.avg_observations_per_query.toFixed(1)}
              description="Observations per query"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
          Last updated: {new Date().toLocaleString()}
        </div>
      </div>
    </div>
  );
}

// Helper Components

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: string;
  color: 'blue' | 'green' | 'purple';
  subtitle?: string;
}

function MetricCard({ title, value, icon, color, subtitle }: MetricCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
    green: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800',
    purple: 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800'
  };

  return (
    <div className={`${colorClasses[color]} border-2 rounded-lg p-6`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-3xl">{icon}</span>
      </div>
      <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
        {title}
      </h3>
      <p className="text-3xl font-bold text-gray-900 dark:text-white">
        {value}
      </p>
      {subtitle && (
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {subtitle}
        </p>
      )}
    </div>
  );
}

interface StatItemProps {
  label: string;
  value: string | number;
  description: string;
}

function StatItem({ label, value, description }: StatItemProps) {
  return (
    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
      <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
        {label}
      </p>
      <p className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
        {value}
      </p>
      <p className="text-xs text-gray-500 dark:text-gray-400">
        {description}
      </p>
    </div>
  );
}
