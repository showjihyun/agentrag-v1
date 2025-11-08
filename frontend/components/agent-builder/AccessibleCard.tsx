'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface AccessibleCardProps {
  title: string;
  description?: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  className?: string;
  ariaLabel?: string;
}

export function AccessibleCard({
  title,
  description,
  value,
  subtitle,
  icon,
  trend,
  trendValue,
  className,
  ariaLabel,
}: AccessibleCardProps) {
  const trendColors = {
    up: 'text-green-600 dark:text-green-400',
    down: 'text-red-600 dark:text-red-400',
    neutral: 'text-muted-foreground',
  };

  return (
    <Card 
      className={cn(
        'transition-all hover:shadow-lg focus-within:ring-2 focus-within:ring-primary focus-within:ring-offset-2',
        className
      )}
      role="article"
      aria-label={ariaLabel || `${title}: ${value}`}
    >
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium" id={`card-title-${title.replace(/\s+/g, '-')}`}>
          {title}
        </CardTitle>
        {icon && (
          <div 
            className="text-muted-foreground" 
            aria-hidden="true"
          >
            {icon}
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div 
          className="text-2xl font-bold"
          aria-describedby={description ? `card-desc-${title.replace(/\s+/g, '-')}` : undefined}
        >
          {value}
        </div>
        {subtitle && (
          <p 
            className="text-xs text-muted-foreground mt-1"
            id={`card-desc-${title.replace(/\s+/g, '-')}`}
          >
            {subtitle}
          </p>
        )}
        {trend && trendValue && (
          <p 
            className={cn('text-xs mt-1', trendColors[trend])}
            aria-label={`Trend: ${trend} ${trendValue}`}
          >
            {trendValue}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
