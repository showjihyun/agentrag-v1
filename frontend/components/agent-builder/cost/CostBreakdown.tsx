'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useTheme } from 'next-themes';

interface CostBreakdownProps {
  costByModel: Record<string, number>;
  costByAgent: Record<string, number>;
  costTrend: Array<{
    date: string;
    cost: number;
    tokens: number;
  }>;
  topExpensiveExecutions: Array<{
    id: string;
    agent_name: string;
    cost: number;
    tokens: number;
    timestamp: string;
  }>;
}

export function CostBreakdown({
  costByModel,
  costByAgent,
  costTrend,
  topExpensiveExecutions,
}: CostBreakdownProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const modelData = Object.entries(costByModel).map(([name, cost]) => ({
    name,
    cost,
  }));

  const agentData = Object.entries(costByAgent).map(([name, cost]) => ({
    name,
    cost,
  }));

  const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981'];

  const formatCurrency = (value: number) => {
    return `$${value.toFixed(4)}`;
  };

  return (
    <div className="space-y-6">
      {/* Cost by Model */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Cost by Model</CardTitle>
            <CardDescription>Distribution across LLM models</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={modelData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) =>
                    `${name}: ${(percent * 100).toFixed(0)}%`
                  }
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="cost"
                >
                  {modelData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Cost by Agent</CardTitle>
            <CardDescription>Top spending agents</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={agentData.slice(0, 5)}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke={isDark ? '#374151' : '#e5e7eb'}
                />
                <XAxis
                  dataKey="name"
                  stroke={isDark ? '#9ca3af' : '#6b7280'}
                  fontSize={12}
                />
                <YAxis stroke={isDark ? '#9ca3af' : '#6b7280'} fontSize={12} />
                <Tooltip
                  formatter={(value: number) => formatCurrency(value)}
                  contentStyle={{
                    backgroundColor: isDark ? '#1f2937' : '#ffffff',
                    border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                  }}
                />
                <Bar dataKey="cost" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Cost Trend */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Cost Trend</CardTitle>
          <CardDescription>Daily cost over time</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={costTrend}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke={isDark ? '#374151' : '#e5e7eb'}
              />
              <XAxis
                dataKey="date"
                stroke={isDark ? '#9ca3af' : '#6b7280'}
                fontSize={12}
              />
              <YAxis stroke={isDark ? '#9ca3af' : '#6b7280'} fontSize={12} />
              <Tooltip
                formatter={(value: number) => formatCurrency(value)}
                contentStyle={{
                  backgroundColor: isDark ? '#1f2937' : '#ffffff',
                  border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="cost"
                stroke="#3b82f6"
                strokeWidth={2}
                name="Cost ($)"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Top Expensive Executions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Most Expensive Executions</CardTitle>
          <CardDescription>Top 10 costly executions</CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[300px]">
            <div className="space-y-2">
              {topExpensiveExecutions.map((execution, index) => (
                <Card key={execution.id}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Badge variant="outline">#{index + 1}</Badge>
                        <div>
                          <p className="font-medium">{execution.agent_name}</p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(execution.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-lg">
                          {formatCurrency(execution.cost)}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {execution.tokens.toLocaleString()} tokens
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
