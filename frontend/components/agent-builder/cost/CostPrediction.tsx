'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import { useTheme } from '@/contexts/ThemeContext';
import { TrendingUp, Calendar } from 'lucide-react';

interface CostPredictionProps {
  historicalData: Array<{
    date: string;
    cost: number;
    tokens: number;
  }>;
  currentCost: number;
}

export function CostPrediction({ historicalData, currentCost }: CostPredictionProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  // Simple linear regression for prediction
  const predictFutureCosts = () => {
    if (historicalData.length < 2) return [];

    const n = historicalData.length;
    const sumX = historicalData.reduce((sum, _, i) => sum + i, 0);
    const sumY = historicalData.reduce((sum, d) => sum + d.cost, 0);
    const sumXY = historicalData.reduce((sum, d, i) => sum + i * d.cost, 0);
    const sumX2 = historicalData.reduce((sum, _, i) => sum + i * i, 0);

    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    // Predict next 30 days
    const predictions = [];
    for (let i = 0; i < 30; i++) {
      const x = n + i;
      const predictedCost = slope * x + intercept;
      const date = new Date();
      date.setDate(date.getDate() + i + 1);
      
      predictions.push({
        date: date.toISOString().split('T')[0],
        predicted: Math.max(0, predictedCost),
        lower: Math.max(0, predictedCost * 0.8),
        upper: predictedCost * 1.2,
      });
    }

    return predictions;
  };

  const predictions = predictFutureCosts();
  const combinedData = [
    ...historicalData.map(d => ({
      date: d.date,
      actual: d.cost,
      predicted: null,
      lower: null,
      upper: null,
    })),
    ...predictions.map(p => ({
      date: p.date,
      actual: null,
      predicted: p.predicted,
      lower: p.lower,
      upper: p.upper,
    })),
  ];

  const predictedMonthly = predictions.reduce((sum, p) => sum + p.predicted, 0);
  const growthRate = historicalData.length >= 2
    ? ((historicalData[historicalData.length - 1].cost - historicalData[0].cost) / historicalData[0].cost) * 100
    : 0;

  const formatCurrency = (value: number) => {
    return `$${value.toFixed(2)}`;
  };

  return (
    <div className="space-y-6">
      {/* Prediction Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Predicted Next 30 Days</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(predictedMonthly)}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Based on current trends
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Growth Rate</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div className="text-2xl font-bold">
                {growthRate > 0 ? '+' : ''}{growthRate.toFixed(1)}%
              </div>
              {growthRate > 0 ? (
                <TrendingUp className="h-5 w-5 text-red-500" />
              ) : (
                <TrendingUp className="h-5 w-5 text-green-500 rotate-180" />
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Month over month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Confidence Level</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {historicalData.length >= 7 ? 'High' : historicalData.length >= 3 ? 'Medium' : 'Low'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {historicalData.length} days of data
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Prediction Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Cost Forecast</CardTitle>
          <CardDescription>
            Historical data and 30-day prediction with confidence interval
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <AreaChart data={combinedData}>
              <defs>
                <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
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
              <Area
                type="monotone"
                dataKey="upper"
                stroke="none"
                fill="#3b82f6"
                fillOpacity={0.1}
                name="Upper Bound"
              />
              <Area
                type="monotone"
                dataKey="lower"
                stroke="none"
                fill="#3b82f6"
                fillOpacity={0.1}
                name="Lower Bound"
              />
              <Line
                type="monotone"
                dataKey="actual"
                stroke="#10b981"
                strokeWidth={2}
                name="Actual Cost"
                dot={{ r: 3 }}
              />
              <Line
                type="monotone"
                dataKey="predicted"
                stroke="#3b82f6"
                strokeWidth={2}
                strokeDasharray="5 5"
                name="Predicted Cost"
                dot={{ r: 3 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Insights */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Insights & Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {growthRate > 20 && (
              <div className="flex items-start gap-2 p-3 bg-yellow-50 dark:bg-yellow-950/50 border border-yellow-200 dark:border-yellow-900 rounded-md">
                <Badge variant="outline" className="mt-0.5">
                  Warning
                </Badge>
                <p className="text-sm">
                  Your costs are growing rapidly ({growthRate.toFixed(1)}% per month). Consider
                  implementing cost optimization strategies.
                </p>
              </div>
            )}
            {predictedMonthly > currentCost * 1.5 && (
              <div className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-950/50 border border-blue-200 dark:border-blue-900 rounded-md">
                <Badge variant="outline" className="mt-0.5">
                  Tip
                </Badge>
                <p className="text-sm">
                  Based on trends, your costs may increase by{' '}
                  {(((predictedMonthly - currentCost) / currentCost) * 100).toFixed(0)}% next month.
                  Review your budget settings.
                </p>
              </div>
            )}
            {historicalData.length < 7 && (
              <div className="flex items-start gap-2 p-3 bg-gray-50 dark:bg-gray-950/50 border border-gray-200 dark:border-gray-900 rounded-md">
                <Badge variant="outline" className="mt-0.5">
                  Info
                </Badge>
                <p className="text-sm">
                  Predictions will become more accurate with more historical data. We recommend at
                  least 7 days of data for reliable forecasts.
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
