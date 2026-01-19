'use client';

import React from 'react';
import { Brain, Zap, Sparkles } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface QueryComplexityIndicatorProps {
  complexity: string;
  className?: string;
}

export function QueryComplexityIndicator({ complexity, className }: QueryComplexityIndicatorProps) {
  const getComplexityConfig = (level: string) => {
    switch (level.toLowerCase()) {
      case 'simple':
        return {
          icon: Zap,
          label: 'Simple',
          color: 'text-green-600',
          bgColor: 'bg-green-50 dark:bg-green-950',
          borderColor: 'border-green-200 dark:border-green-800',
          description: 'Single-hop factual query',
        };
      case 'moderate':
        return {
          icon: Brain,
          label: 'Moderate',
          color: 'text-blue-600',
          bgColor: 'bg-blue-50 dark:bg-blue-950',
          borderColor: 'border-blue-200 dark:border-blue-800',
          description: 'Multi-hop reasoning required',
        };
      case 'complex':
        return {
          icon: Sparkles,
          label: 'Complex',
          color: 'text-purple-600',
          bgColor: 'bg-purple-50 dark:bg-purple-950',
          borderColor: 'border-purple-200 dark:border-purple-800',
          description: 'Multi-step decomposition needed',
        };
      default:
        return {
          icon: Brain,
          label: 'Unknown',
          color: 'text-gray-600',
          bgColor: 'bg-gray-50 dark:bg-gray-950',
          borderColor: 'border-gray-200 dark:border-gray-800',
          description: 'Analyzing...',
        };
    }
  };

  const config = getComplexityConfig(complexity);
  const Icon = config.icon;

  return (
    <div className={cn('text-center', className)}>
      <div className={cn('inline-flex items-center justify-center w-12 h-12 rounded-full mb-2', config.bgColor)}>
        <Icon className={cn('h-6 w-6', config.color)} />
      </div>
      <div className={cn('text-sm font-medium', config.color)}>
        {config.label}
      </div>
      <div className="text-xs text-muted-foreground mt-1">
        {config.description}
      </div>
    </div>
  );
}
