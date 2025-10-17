'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface PieChartData {
  label: string;
  value: number;
  color: string;
}

interface PieChartProps {
  data: PieChartData[];
  title?: string;
  className?: string;
}

export default function PieChart({ data, title, className }: PieChartProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  
  // Calculate percentages and cumulative angles
  let cumulativeAngle = 0;
  const segments = data.map(item => {
    const percentage = (item.value / total) * 100;
    const angle = (item.value / total) * 360;
    const startAngle = cumulativeAngle;
    cumulativeAngle += angle;
    
    return {
      ...item,
      percentage,
      startAngle,
      endAngle: cumulativeAngle,
    };
  });

  // SVG path for pie slice
  const getSlicePath = (startAngle: number, endAngle: number) => {
    const start = polarToCartesian(50, 50, 40, endAngle);
    const end = polarToCartesian(50, 50, 40, startAngle);
    const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1';
    
    return [
      `M 50 50`,
      `L ${start.x} ${start.y}`,
      `A 40 40 0 ${largeArcFlag} 0 ${end.x} ${end.y}`,
      'Z',
    ].join(' ');
  };

  const polarToCartesian = (centerX: number, centerY: number, radius: number, angleInDegrees: number) => {
    const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180.0;
    return {
      x: centerX + radius * Math.cos(angleInRadians),
      y: centerY + radius * Math.sin(angleInRadians),
    };
  };

  return (
    <div className={cn('bg-white dark:bg-gray-800 rounded-lg p-6', className)}>
      {title && (
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          {title}
        </h3>
      )}
      
      <div className="flex flex-col md:flex-row items-center gap-6">
        {/* Pie Chart */}
        <div className="relative w-48 h-48">
          <svg viewBox="0 0 100 100" className="transform -rotate-90">
            {segments.map((segment, index) => (
              <path
                key={index}
                d={getSlicePath(segment.startAngle, segment.endAngle)}
                fill={segment.color}
                className="hover:opacity-80 transition-opacity cursor-pointer"
                title={`${segment.label}: ${segment.percentage.toFixed(1)}%`}
              />
            ))}
          </svg>
          
          {/* Center hole for donut effect */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-20 h-20 bg-white dark:bg-gray-800 rounded-full flex items-center justify-center">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {total}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Total
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Legend */}
        <div className="flex-1 space-y-2">
          {segments.map((segment, index) => (
            <div key={index} className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <div
                  className="w-4 h-4 rounded"
                  style={{ backgroundColor: segment.color }}
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  {segment.label}
                </span>
              </div>
              <div className="text-right">
                <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {segment.value}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {segment.percentage.toFixed(1)}%
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {data.length === 0 && (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          No data available
        </div>
      )}
    </div>
  );
}
