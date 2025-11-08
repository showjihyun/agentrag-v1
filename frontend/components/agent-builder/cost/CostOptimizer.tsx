'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { Sparkles, TrendingDown, Check, Loader2 } from 'lucide-react';

interface CostOptimizerProps {
  agentId?: string;
  currentStats: any;
  onOptimize?: () => void;
}

interface Recommendation {
  id: string;
  type: 'model_switch' | 'caching' | 'batching' | 'prompt_optimization';
  title: string;
  description: string;
  estimated_savings: number;
  estimated_savings_percentage: number;
  impact: 'low' | 'medium' | 'high';
  effort: 'low' | 'medium' | 'high';
  applicable_to?: string[];
}

export function CostOptimizer({ agentId, currentStats, onOptimize }: CostOptimizerProps) {
  const { toast } = useToast();
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState<string | null>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const data = await agentBuilderAPI.analyzeCostOptimization(agentId);
      setRecommendations(data.recommendations || []);
      
      toast({
        title: 'Analysis Complete',
        description: `Found ${data.recommendations?.length || 0} optimization opportunities`,
      });
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to analyze costs',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async (recommendationId: string) => {
    setApplying(recommendationId);
    try {
      await agentBuilderAPI.applyCostOptimization(agentId, recommendationId);
      
      toast({
        title: 'Optimization Applied',
        description: 'Cost optimization has been applied successfully',
      });

      if (onOptimize) onOptimize();
      
      // Remove applied recommendation
      setRecommendations(recs => recs.filter(r => r.id !== recommendationId));
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to apply optimization',
        variant: 'destructive',
      });
    } finally {
      setApplying(null);
    }
  };

  const getImpactBadge = (impact: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive'> = {
      low: 'secondary',
      medium: 'default',
      high: 'destructive',
    };
    return <Badge variant={variants[impact]}>{impact} impact</Badge>;
  };

  const getEffortBadge = (effort: string) => {
    const colors: Record<string, string> = {
      low: 'text-green-500',
      medium: 'text-yellow-500',
      high: 'text-red-500',
    };
    return <span className={`text-xs ${colors[effort]}`}>{effort} effort</span>;
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const totalSavings = recommendations.reduce((sum, rec) => sum + rec.estimated_savings, 0);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Cost Optimization Analysis</CardTitle>
              <CardDescription>
                AI-powered recommendations to reduce costs
              </CardDescription>
            </div>
            <Button onClick={handleAnalyze} disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Analyze Costs
                </>
              )}
            </Button>
          </div>
        </CardHeader>
        {recommendations.length > 0 && (
          <CardContent>
            <div className="flex items-center gap-2 p-4 bg-green-50 dark:bg-green-950/50 border border-green-200 dark:border-green-900 rounded-md">
              <TrendingDown className="h-5 w-5 text-green-600 dark:text-green-400" />
              <div>
                <p className="font-semibold text-green-800 dark:text-green-200">
                  Potential Savings: {formatCurrency(totalSavings)}/month
                </p>
                <p className="text-sm text-green-700 dark:text-green-300">
                  {recommendations.length} optimization{recommendations.length !== 1 ? 's' : ''} available
                </p>
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {recommendations.length === 0 && !loading ? (
        <Card>
          <CardContent className="p-12 text-center text-muted-foreground">
            <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Click "Analyze Costs" to get optimization recommendations</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {recommendations.map((rec) => (
            <Card key={rec.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <CardTitle className="text-lg">{rec.title}</CardTitle>
                      {getImpactBadge(rec.impact)}
                    </div>
                    <CardDescription>{rec.description}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Estimated Savings</p>
                    <p className="text-lg font-bold text-green-600 dark:text-green-400">
                      {formatCurrency(rec.estimated_savings)}/mo
                    </p>
                    <p className="text-xs text-muted-foreground">
                      ({rec.estimated_savings_percentage.toFixed(1)}% reduction)
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Implementation Effort</p>
                    <p className="text-lg font-semibold">{getEffortBadge(rec.effort)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Type</p>
                    <Badge variant="outline">{rec.type.replace('_', ' ')}</Badge>
                  </div>
                </div>

                {rec.applicable_to && rec.applicable_to.length > 0 && (
                  <div>
                    <p className="text-xs text-muted-foreground mb-2">Applicable to:</p>
                    <div className="flex flex-wrap gap-2">
                      {rec.applicable_to.map((item, idx) => (
                        <Badge key={idx} variant="secondary" className="text-xs">
                          {item}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                <Button
                  onClick={() => handleApply(rec.id)}
                  disabled={applying === rec.id}
                  className="w-full"
                >
                  {applying === rec.id ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Applying...
                    </>
                  ) : (
                    <>
                      <Check className="mr-2 h-4 w-4" />
                      Apply Optimization
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
