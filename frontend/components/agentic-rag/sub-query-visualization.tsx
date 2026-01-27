'use client';

import React from 'react';
import { GitBranch, CheckCircle2, FileText } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface SubQuery {
  id: string;
  query: string;
  num_results: number;
}

interface SubQueryVisualizationProps {
  subQueries: SubQuery[];
}

export function SubQueryVisualization({ subQueries }: SubQueryVisualizationProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <GitBranch className="h-5 w-5 text-purple-500" />
          Query Decomposition
        </CardTitle>
        <CardDescription>
          Complex query broken down into {subQueries.length} sub-queries
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {subQueries.map((subQuery, index) => (
            <div
              key={subQuery.id}
              className="relative pl-8 pb-4 last:pb-0"
            >
              {/* Connection Line */}
              {index < subQueries.length - 1 && (
                <div className="absolute left-3 top-8 bottom-0 w-0.5 bg-purple-200 dark:bg-purple-800" />
              )}

              {/* Node */}
              <div className="absolute left-0 top-1 flex items-center justify-center w-6 h-6 rounded-full bg-purple-100 dark:bg-purple-900 border-2 border-purple-500">
                <span className="text-xs font-bold text-purple-700 dark:text-purple-300">
                  {index + 1}
                </span>
              </div>

              {/* Content */}
              <div className="bg-muted/50 rounded-lg p-4 space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">Sub-query {index + 1}</span>
                    </div>
                    <p className="text-sm">{subQuery.query}</p>
                  </div>
                  <Badge variant="outline" className="flex items-center gap-1">
                    <CheckCircle2 className="h-3 w-3 text-green-500" />
                    {subQuery.num_results} results
                  </Badge>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Summary */}
        <div className="mt-4 p-3 bg-purple-50 dark:bg-purple-950 rounded-lg">
          <div className="text-sm text-purple-700 dark:text-purple-300">
            <span className="font-medium">Strategy:</span> Each sub-query was executed independently,
            then results were synthesized into a comprehensive answer.
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
