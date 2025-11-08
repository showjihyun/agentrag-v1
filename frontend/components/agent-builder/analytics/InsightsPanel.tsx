'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { CheckCircle, AlertTriangle, Info, ArrowRight, Brain } from 'lucide-react';
import { EnhancedInsightsPanel } from '../insights/EnhancedInsightsPanel';

interface Insight {
  type: 'success' | 'warning' | 'info';
  title: string;
  description: string;
  action?: string;
}

interface InsightsPanelProps {
  insights: Insight[];
  executionData?: any[];
  metricsData?: any;
  agentId?: string;
}

export function InsightsPanel({ insights, executionData, metricsData, agentId }: InsightsPanelProps) {
  // 고급 인사이트가 활성화된 경우
  if (executionData || metricsData) {
    return (
      <EnhancedInsightsPanel
        agentId={agentId}
        executionData={executionData}
        metricsData={metricsData}
        autoRefresh={true}
        refreshInterval={30}
      />
    );
  }

  // 기본 인사이트 표시 (하위 호환성)
  const getIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'info':
        return <Info className="h-5 w-5 text-blue-500" />;
      default:
        return <Info className="h-5 w-5" />;
    }
  };

  const getBackgroundColor = (type: string) => {
    switch (type) {
      case 'success':
        return 'bg-green-50 dark:bg-green-950/50 border-green-200 dark:border-green-900';
      case 'warning':
        return 'bg-yellow-50 dark:bg-yellow-950/50 border-yellow-200 dark:border-yellow-900';
      case 'info':
        return 'bg-blue-50 dark:bg-blue-950/50 border-blue-200 dark:border-blue-900';
      default:
        return 'bg-muted';
    }
  };

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center gap-2 mb-4">
          <Brain className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold">AI-Powered Insights</h3>
          <Badge variant="secondary">Enhanced</Badge>
        </div>
        <div className="space-y-3">
          {insights.map((insight, index) => (
            <div
              key={index}
              className={`flex items-start gap-3 p-4 border rounded-md ${getBackgroundColor(
                insight.type
              )}`}
            >
              <div className="mt-0.5">{getIcon(insight.type)}</div>
              <div className="flex-1">
                <h4 className="font-semibold mb-1">{insight.title}</h4>
                <p className="text-sm text-muted-foreground">{insight.description}</p>
                {insight.action && (
                  <Button variant="link" size="sm" className="mt-2 p-0 h-auto">
                    {insight.action}
                    <ArrowRight className="ml-1 h-3 w-3" />
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
