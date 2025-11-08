'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

interface QualityAnalyticsProps {
  agentId?: string;
  timeRange?: string;
}

export function QualityAnalytics({ agentId, timeRange }: QualityAnalyticsProps) {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    loadData();
  }, [agentId, timeRange]);

  const loadData = async () => {
    try {
      const result = await agentBuilderAPI.getQualityAnalytics(agentId, timeRange);
      setData(result);
    } catch (error) {
      console.error('Failed to load quality analytics:', error);
    }
  };

  if (!data) return <div>Loading...</div>;

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-500';
    if (score >= 60) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div className="space-y-6 mt-4">
      {/* Quality Scores */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold">Accuracy Score</h3>
              <CheckCircle className={`h-5 w-5 ${getScoreColor(data.accuracy_score)}`} />
            </div>
            <div className={`text-3xl font-bold ${getScoreColor(data.accuracy_score)}`}>
              {data.accuracy_score}
            </div>
            <Progress value={data.accuracy_score} className="mt-2 h-2" />
            <p className="text-xs text-muted-foreground mt-2">
              Based on {data.total_evaluations} evaluations
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold">Relevance Score</h3>
              <CheckCircle className={`h-5 w-5 ${getScoreColor(data.relevance_score)}`} />
            </div>
            <div className={`text-3xl font-bold ${getScoreColor(data.relevance_score)}`}>
              {data.relevance_score}
            </div>
            <Progress value={data.relevance_score} className="mt-2 h-2" />
            <p className="text-xs text-muted-foreground mt-2">
              Response relevance to queries
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold">Consistency Score</h3>
              <CheckCircle className={`h-5 w-5 ${getScoreColor(data.consistency_score)}`} />
            </div>
            <div className={`text-3xl font-bold ${getScoreColor(data.consistency_score)}`}>
              {data.consistency_score}
            </div>
            <Progress value={data.consistency_score} className="mt-2 h-2" />
            <p className="text-xs text-muted-foreground mt-2">
              Output consistency
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Common Issues */}
      <Card>
        <CardContent className="pt-6">
          <h3 className="text-lg font-semibold mb-4">Common Issues</h3>
          <div className="space-y-3">
            {data.common_issues.map((issue: any, index: number) => (
              <div
                key={index}
                className="flex items-start gap-3 p-3 border rounded-md bg-yellow-50 dark:bg-yellow-950/50"
              >
                <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="font-semibold">{issue.title}</h4>
                    <Badge variant="outline">{issue.count} occurrences</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">{issue.description}</p>
                  {issue.suggestion && (
                    <p className="text-sm text-blue-600 dark:text-blue-400 mt-2">
                      💡 {issue.suggestion}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* User Feedback */}
      <Card>
        <CardContent className="pt-6">
          <h3 className="text-lg font-semibold mb-4">User Feedback Summary</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 border rounded-md">
              <CheckCircle className="h-8 w-8 text-green-500 mx-auto mb-2" />
              <div className="text-2xl font-bold">{data.positive_feedback}</div>
              <p className="text-sm text-muted-foreground">Positive</p>
            </div>
            <div className="text-center p-4 border rounded-md">
              <AlertTriangle className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
              <div className="text-2xl font-bold">{data.neutral_feedback}</div>
              <p className="text-sm text-muted-foreground">Neutral</p>
            </div>
            <div className="text-center p-4 border rounded-md">
              <XCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
              <div className="text-2xl font-bold">{data.negative_feedback}</div>
              <p className="text-sm text-muted-foreground">Negative</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
