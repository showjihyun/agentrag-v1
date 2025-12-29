'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useTheme } from 'next-themes';

interface UsageAnalyticsProps {
  agentId?: string;
  timeRange?: string;
}

export function UsageAnalytics({ agentId, timeRange }: UsageAnalyticsProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    loadData();
  }, [agentId, timeRange]);

  const loadData = async () => {
    if (!agentId) return;
    
    try {
      const result = await agentBuilderAPI.getUsageAnalytics(agentId, timeRange);
      setData(result);
    } catch (error) {
      console.error('Failed to load usage analytics:', error);
    }
  };

  if (!data) return <div>Loading...</div>;

  const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981'];

  return (
    <div className="space-y-6 mt-4">
      {/* Usage by Agent */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardContent className="pt-6">
            <h3 className="text-lg font-semibold mb-4">Usage by Agent</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={data.usage_by_agent}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {data.usage_by_agent.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <h3 className="text-lg font-semibold mb-4">Usage by User</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={data.usage_by_user.slice(0, 5)}>
                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
                <XAxis dataKey="user" stroke={isDark ? '#9ca3af' : '#6b7280'} fontSize={12} />
                <YAxis stroke={isDark ? '#9ca3af' : '#6b7280'} fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: isDark ? '#1f2937' : '#ffffff',
                    border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                  }}
                />
                <Bar dataKey="count" fill="#3b82f6" name="Executions" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Peak Usage Times */}
      <Card>
        <CardContent className="pt-6">
          <h3 className="text-lg font-semibold mb-4">Peak Usage Times</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={data.peak_usage_times}>
              <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
              <XAxis dataKey="hour" stroke={isDark ? '#9ca3af' : '#6b7280'} fontSize={12} />
              <YAxis stroke={isDark ? '#9ca3af' : '#6b7280'} fontSize={12} />
              <Tooltip
                contentStyle={{
                  backgroundColor: isDark ? '#1f2937' : '#ffffff',
                  border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                }}
              />
              <Bar dataKey="count" fill="#8b5cf6" name="Executions" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Most Used Features */}
      <Card>
        <CardContent className="pt-6">
          <h3 className="text-lg font-semibold mb-4">Most Used Features</h3>
          <div className="space-y-3">
            {data.most_used_features.map((feature: any, index: number) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded-md">
                <div className="flex items-center gap-3">
                  <Badge variant="outline">#{index + 1}</Badge>
                  <span className="font-medium">{feature.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">
                    {feature.count.toLocaleString()} uses
                  </span>
                  <Badge variant="secondary">{feature.percentage.toFixed(1)}%</Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
