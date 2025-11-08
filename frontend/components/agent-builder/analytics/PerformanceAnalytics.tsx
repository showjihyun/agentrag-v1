'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useTheme } from 'next-themes';

interface PerformanceAnalyticsProps {
  agentId?: string;
  timeRange?: string;
}

export function PerformanceAnalytics({ agentId, timeRange }: PerformanceAnalyticsProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    loadData();
  }, [agentId, timeRange]);

  const loadData = async () => {
    try {
      const result = await agentBuilderAPI.getPerformanceAnalytics(agentId, timeRange);
      setData(result);
    } catch (error) {
      console.error('Failed to load performance analytics:', error);
    }
  };

  if (!data) return <div>Loading...</div>;

  return (
    <div className="space-y-6 mt-4">
      {/* Response Time Trend */}
      <Card>
        <CardContent className="pt-6">
          <h3 className="text-lg font-semibold mb-4">Response Time Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={data.response_time_trend}>
              <defs>
                <linearGradient id="colorResponseTime" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
              <XAxis dataKey="date" stroke={isDark ? '#9ca3af' : '#6b7280'} fontSize={12} />
              <YAxis stroke={isDark ? '#9ca3af' : '#6b7280'} fontSize={12} />
              <Tooltip
                contentStyle={{
                  backgroundColor: isDark ? '#1f2937' : '#ffffff',
                  border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                }}
              />
              <Area
                type="monotone"
                dataKey="avg_time"
                stroke="#3b82f6"
                fillOpacity={1}
                fill="url(#colorResponseTime)"
                name="Avg Response Time (s)"
              />
              <Area
                type="monotone"
                dataKey="p95_time"
                stroke="#8b5cf6"
                fillOpacity={0.3}
                fill="#8b5cf6"
                name="P95 Response Time (s)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Throughput */}
      <Card>
        <CardContent className="pt-6">
          <h3 className="text-lg font-semibold mb-4">Throughput (Executions per Hour)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={data.throughput}>
              <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
              <XAxis dataKey="hour" stroke={isDark ? '#9ca3af' : '#6b7280'} fontSize={12} />
              <YAxis stroke={isDark ? '#9ca3af' : '#6b7280'} fontSize={12} />
              <Tooltip
                contentStyle={{
                  backgroundColor: isDark ? '#1f2937' : '#ffffff',
                  border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                }}
              />
              <Bar dataKey="count" fill="#10b981" name="Executions" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Error Rate */}
      <Card>
        <CardContent className="pt-6">
          <h3 className="text-lg font-semibold mb-4">Error Rate Over Time</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={data.error_rate}>
              <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
              <XAxis dataKey="date" stroke={isDark ? '#9ca3af' : '#6b7280'} fontSize={12} />
              <YAxis stroke={isDark ? '#9ca3af' : '#6b7280'} fontSize={12} />
              <Tooltip
                contentStyle={{
                  backgroundColor: isDark ? '#1f2937' : '#ffffff',
                  border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="error_rate"
                stroke="#ef4444"
                strokeWidth={2}
                name="Error Rate (%)"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
