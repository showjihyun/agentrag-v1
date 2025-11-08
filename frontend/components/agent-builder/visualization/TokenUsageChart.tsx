'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useTheme } from 'next-themes';
import { DollarSign, Zap } from 'lucide-react';

interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  estimatedCost: number;
}

interface TokenUsageChartProps {
  usage: TokenUsage;
  history?: Array<{
    timestamp: string;
    promptTokens: number;
    completionTokens: number;
  }>;
  limit?: number;
}

export function TokenUsageChart({ usage, history = [], limit }: TokenUsageChartProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const pieData = [
    { name: 'Prompt', value: usage.promptTokens },
    { name: 'Completion', value: usage.completionTokens },
  ];

  const COLORS = ['#3b82f6', '#8b5cf6'];

  const usagePercentage = limit ? (usage.totalTokens / limit) * 100 : 0;

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Tokens</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{usage.totalTokens.toLocaleString()}</div>
            {limit && (
              <div className="mt-2">
                <Progress value={usagePercentage} className="h-2" />
                <p className="text-xs text-muted-foreground mt-1">
                  {usagePercentage.toFixed(1)}% of {limit.toLocaleString()} limit
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Estimated Cost</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-green-500" />
              <div className="text-2xl font-bold">
                ${usage.estimatedCost.toFixed(4)}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Token Breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Prompt:</span>
                <Badge variant="outline">{usage.promptTokens.toLocaleString()}</Badge>
              </div>
              <div className="flex justify-between text-sm">
                <span>Completion:</span>
                <Badge variant="outline">{usage.completionTokens.toLocaleString()}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Pie Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Token Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) =>
                    `${name}: ${(percent * 100).toFixed(0)}%`
                  }
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* History Bar Chart */}
        {history.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Usage History</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={history}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke={isDark ? '#374151' : '#e5e7eb'}
                  />
                  <XAxis
                    dataKey="timestamp"
                    stroke={isDark ? '#9ca3af' : '#6b7280'}
                    fontSize={12}
                  />
                  <YAxis stroke={isDark ? '#9ca3af' : '#6b7280'} fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: isDark ? '#1f2937' : '#ffffff',
                      border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                    }}
                  />
                  <Legend />
                  <Bar dataKey="promptTokens" fill="#3b82f6" name="Prompt" />
                  <Bar dataKey="completionTokens" fill="#8b5cf6" name="Completion" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
