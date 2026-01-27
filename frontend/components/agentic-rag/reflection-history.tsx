'use client';

import React from 'react';
import { Sparkles, TrendingUp, CheckCircle2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

interface ReflectionIteration {
  iteration: number;
  output: string;
  critique: {
    quality_score: number;
    strengths: string[];
    weaknesses: string[];
    improvements: string[];
  };
  quality_score: number;
  timestamp: string;
}

interface ReflectionHistoryProps {
  history: ReflectionIteration[];
  finalScore: number;
  initialScore: number;
}

export function ReflectionHistory({ history, finalScore, initialScore }: ReflectionHistoryProps) {
  const improvement = ((finalScore - initialScore) / initialScore * 100).toFixed(1);
  const isImproved = finalScore > initialScore;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-purple-500" />
          Reflection History
        </CardTitle>
        <CardDescription>
          Self-evaluation and iterative improvement process
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Summary */}
        <div className="mb-6 p-4 bg-purple-50 dark:bg-purple-950 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Quality Improvement</span>
            <Badge variant={isImproved ? 'default' : 'secondary'} className="flex items-center gap-1">
              <TrendingUp className="h-3 w-3" />
              {isImproved ? '+' : ''}{improvement}%
            </Badge>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Initial:</span>
              <span className="ml-2 font-medium">{(initialScore * 100).toFixed(0)}%</span>
            </div>
            <div className="flex-1">
              <Progress value={finalScore * 100} className="h-2" />
            </div>
            <div>
              <span className="text-muted-foreground">Final:</span>
              <span className="ml-2 font-medium">{(finalScore * 100).toFixed(0)}%</span>
            </div>
          </div>
        </div>

        {/* Iterations */}
        <div className="space-y-4">
          {history.map((iteration, index) => (
            <div
              key={iteration.iteration}
              className="relative pl-8 pb-4 last:pb-0"
            >
              {/* Connection Line */}
              {index < history.length - 1 && (
                <div className="absolute left-3 top-8 bottom-0 w-0.5 bg-purple-200 dark:bg-purple-800" />
              )}

              {/* Node */}
              <div className="absolute left-0 top-1 flex items-center justify-center w-6 h-6 rounded-full bg-purple-100 dark:bg-purple-900 border-2 border-purple-500">
                {index === history.length - 1 ? (
                  <CheckCircle2 className="h-4 w-4 text-purple-700 dark:text-purple-300" />
                ) : (
                  <span className="text-xs font-bold text-purple-700 dark:text-purple-300">
                    {iteration.iteration}
                  </span>
                )}
              </div>

              {/* Content */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">
                    Iteration {iteration.iteration}
                  </span>
                  <Badge variant="outline">
                    Score: {(iteration.quality_score * 100).toFixed(0)}%
                  </Badge>
                </div>

                {/* Critique */}
                <div className="bg-muted/50 rounded-lg p-3 space-y-2">
                  {/* Strengths */}
                  {iteration.critique.strengths.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-green-600 dark:text-green-400 mb-1">
                        ✓ Strengths
                      </div>
                      <ul className="text-xs space-y-1 text-muted-foreground">
                        {iteration.critique.strengths.map((strength, i) => (
                          <li key={i}>• {strength}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Weaknesses */}
                  {iteration.critique.weaknesses.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-red-600 dark:text-red-400 mb-1">
                        ✗ Weaknesses
                      </div>
                      <ul className="text-xs space-y-1 text-muted-foreground">
                        {iteration.critique.weaknesses.map((weakness, i) => (
                          <li key={i}>• {weakness}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Improvements */}
                  {iteration.critique.improvements.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-blue-600 dark:text-blue-400 mb-1">
                        → Improvements
                      </div>
                      <ul className="text-xs space-y-1 text-muted-foreground">
                        {iteration.critique.improvements.map((improvement, i) => (
                          <li key={i}>• {improvement}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
