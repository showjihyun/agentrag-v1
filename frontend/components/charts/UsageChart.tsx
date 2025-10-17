'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface DataPoint {
  label: string;
  value: number;
}

interface UsageChartProps {
  data: DataPoint[];
  title?: string;
  color?: string;
  className?: string;
}

export default function UsageChart({
  data,
  title,
  color = 'blue',
  className,
}: UsageChartProps) {
  const maxValue = Math.max(...data.map(d => d.value), 1);
  
  const colorClasses = {
    blue: 'bg-blue-500 hover:bg-blue-600',
    green: 'bg-green-500 hover:bg-green-600',
    purple: 'bg-purple-500 hover:bg-purple-600',
    orange: 'bg-orange-500 hover:bg-orange-600',
  };

  return (
    <div className={cn('bg-white dark:bg-gray-800 rounded-lg p-6', className)}>
      {title && (
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          {title}
        </h3>
      )}
      
      <div className="space-y-3">
        {data.map((point, index) => (
          <div key={index} className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-700 dark:text-gray-300">{point.label}</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">{point.value}</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
              <div
                className={cn(
                  'h-full rounded-full transition-all duration-500',
                  colorClasses[color as keyof typeof colorClasses] || colorClasses.blue
                )}
                style={{ width: `${(point.value / maxValue) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
      
      {data.length === 0 && (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          No data available
        </div>
      )}
    </div>
  );
}
