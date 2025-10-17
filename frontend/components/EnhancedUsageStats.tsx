'use client';

/**
 * Enhanced Usage Statistics Component
 * Daily/Weekly/Monthly charts with usage patterns and cost estimation
 */

import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import UsageChart from './charts/UsageChart';
import StatCard from './charts/StatCard';

interface UsageData {
  date: string;
  queries: number;
  documents: number;
  tokens: number;
  cost: number;
}

interface UsageStatsProps {
  userId?: string;
  className?: string;
}

type TimeRange = 'day' | 'week' | 'month' | 'year';

export default function EnhancedUsageStats({ userId, className }: UsageStatsProps) {
  const [timeRange, setTimeRange] = useState<TimeRange>('week');
  const [usageData, setUsageData] = useState<UsageData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [totalStats, setTotalStats] = useState({
    totalQueries: 0,
    totalDocuments: 0,
    totalTokens: 0,
    estimatedCost: 0,
    avgQueriesPerDay: 0,
    peakUsageDay: '',
  });

  useEffect(() => {
    fetchUsageData();
  }, [timeRange, userId]);

  const fetchUsageData = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        timeRange,
        ...(userId && { userId }),
      });
      
      const response = await fetch(`/api/usage/stats?${params}`);
      if (!response.ok) throw new Error('Failed to fetch usage data');
      
      const data = await response.json();
      setUsageData(data.usage);
      setTotalStats(data.summary);
    } catch (error) {
      console.error('Failed to fetch usage data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const timeRangeOptions = [
    { value: 'day' as TimeRange, label: 'Today', icon: '📅' },
    { value: 'week' as TimeRange, label: 'Week', icon: '📊' },
    { value: 'month' as TimeRange, label: 'Month', icon: '📈' },
    { value: 'year' as TimeRange, label: 'Year', icon: '📉' },
  ];

  const formatCost = (cost: number): string => {
    return `$${cost.toFixed(2)}`;
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const getUsagePattern = (): string => {
    if (usageData.length === 0) return 'No data';
    
    const avgQueries = totalStats.avgQueriesPerDay;
    if (avgQueries > 100) return 'Heavy User';
    if (avgQueries > 50) return 'Active User';
    if (avgQueries > 10) return 'Regular User';
    return 'Light User';
  };

  const getPredictedCost = (): number => {
    const daysInMonth = 30;
    const dailyAvg = totalStats.estimatedCost / usageData.length;
    return dailyAvg * daysInMonth;
  };

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Usage Statistics
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Track your usage patterns and costs
          </p>
        </div>

        {/* Time Range Selector */}
        <div className="flex gap-2">
          {timeRangeOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => setTimeRange(option.value)}
              className={cn(
                'px-4 py-2 text-sm font-medium rounded-lg transition-all',
                timeRange === option.value
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
              )}
            >
              <span className="mr-1">{option.icon}</span>
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Loading usage data...</p>
          </div>
        </div>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Total Queries"
              value={formatNumber(totalStats.totalQueries)}
              period={`${totalStats.avgQueriesPerDay.toFixed(1)} per day`}
              color="blue"
              icon={
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              }
            />

            <StatCard
              title="Documents Processed"
              value={formatNumber(totalStats.totalDocuments)}
              period="Total uploads"
              color="green"
              icon={
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              }
            />

            <StatCard
              title="Tokens Used"
              value={formatNumber(totalStats.totalTokens)}
              period="API tokens"
              color="purple"
              icon={
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              }
            />

            <StatCard
              title="Estimated Cost"
              value={formatCost(totalStats.estimatedCost)}
              period={`~${formatCost(getPredictedCost())}/month`}
              color="orange"
              icon={
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              }
            />
          </div>

          {/* Usage Pattern Insights */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                  <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">Usage Pattern</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Your activity level</p>
                </div>
              </div>
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {getUsagePattern()}
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                  <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">Peak Usage</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Busiest day</p>
                </div>
              </div>
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {totalStats.peakUsageDay || 'N/A'}
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                  <svg className="w-5 h-5 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">Efficiency</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Tokens per query</p>
                </div>
              </div>
              <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                {totalStats.totalQueries > 0 
                  ? formatNumber(Math.round(totalStats.totalTokens / totalStats.totalQueries))
                  : '0'}
              </div>
            </div>
          </div>

          {/* Usage Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Query Activity
              </h3>
              <UsageChart
                data={usageData.map(d => ({ label: d.date, value: d.queries }))}
                color="blue"
              />
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Cost Trend
              </h3>
              <UsageChart
                data={usageData.map(d => ({ label: d.date, value: d.cost }))}
                color="orange"
              />
            </div>
          </div>

          {/* Detailed Table */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Detailed Usage
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-900/50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Queries
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Documents
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Tokens
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Cost
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {usageData.map((data, index) => (
                    <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                        {new Date(data.date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                        {data.queries}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                        {data.documents}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                        {formatNumber(data.tokens)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">
                        {formatCost(data.cost)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
