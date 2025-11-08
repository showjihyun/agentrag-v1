'use client';

import React from 'react';
import { useTheme } from 'next-themes';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface DarkModeOptimizedChartProps {
  data: any[];
}

export function DarkModeOptimizedChart({ data }: DarkModeOptimizedChartProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  // Dark mode optimized colors
  const colors = {
    grid: isDark ? '#374151' : '#e5e7eb',
    text: isDark ? '#9ca3af' : '#6b7280',
    total: isDark ? '#60a5fa' : '#3b82f6',
    successful: isDark ? '#34d399' : '#10b981',
    failed: isDark ? '#f87171' : '#ef4444',
    background: isDark ? '#1f2937' : '#ffffff',
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid 
          strokeDasharray="3 3" 
          stroke={colors.grid}
          opacity={isDark ? 0.3 : 0.5}
        />
        <XAxis
          dataKey="date"
          tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          stroke={colors.text}
          style={{ fontSize: '12px' }}
        />
        <YAxis 
          stroke={colors.text}
          style={{ fontSize: '12px' }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: colors.background,
            border: `1px solid ${colors.grid}`,
            borderRadius: '8px',
            boxShadow: isDark ? '0 4px 6px rgba(0, 0, 0, 0.3)' : '0 4px 6px rgba(0, 0, 0, 0.1)',
          }}
          labelStyle={{ color: colors.text }}
          labelFormatter={(value) => new Date(value).toLocaleDateString()}
        />
        <Legend 
          wrapperStyle={{ 
            fontSize: '12px',
            color: colors.text,
          }}
        />
        <Line 
          type="monotone" 
          dataKey="total" 
          stroke={colors.total}
          strokeWidth={2}
          dot={{ fill: colors.total, r: 4 }}
          activeDot={{ r: 6 }}
          name="Total" 
        />
        <Line 
          type="monotone" 
          dataKey="successful" 
          stroke={colors.successful}
          strokeWidth={2}
          dot={{ fill: colors.successful, r: 4 }}
          activeDot={{ r: 6 }}
          name="Successful" 
        />
        <Line 
          type="monotone" 
          dataKey="failed" 
          stroke={colors.failed}
          strokeWidth={2}
          dot={{ fill: colors.failed, r: 4 }}
          activeDot={{ r: 6 }}
          name="Failed" 
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
