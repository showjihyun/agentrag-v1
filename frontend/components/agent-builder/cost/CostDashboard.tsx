'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { DollarSign, TrendingDown, TrendingUp, AlertTriangle, Zap } from 'lucide-react';
import { CostBreakdown } from './CostBreakdown';
import { BudgetManager } from './BudgetManager';
import { CostOptimizer } from './CostOptimizer';
import { CostPrediction } from './CostPrediction';

interface CostDashboardProps {
  agentId?: string;
  timeRange?: '24h' | '7d' | '30d' | '90d';
}

interface CostStats {
  total_cost: number;
  total_cost_previous_period: number;
  cost_by_model: Record<string, number>;
  cost_by_agent: Record<string, number>;
  total_tokens: number;
  avg_cost_per_execution: number;
  budget_limit?: number;
  budget_used_percentage: number;
  cost_trend: Array<{
    date: string;
    cost: number;
    tokens: number;
  }>;
  top_expensive_executions: Array<{
    id: string;
    agent_name: string;
    cost: number;
    tokens: number;
    timestamp: string;
  }>;
}

export function CostDashboard({ agentId, timeRange = '30d' }: CostDashboardProps) {
  const [stats, setStats] = useState<CostStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, [agentId, timeRange]);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await agentBuilderAPI.getCostStats(agentId, timeRange);
      setStats(data);
    } catch (error) {
      console.error('Failed to load cost stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 4,
    }).format(amount);
  };

  const getCostTrend = () => {
    if (!stats) return null;
    const change = stats.total_cost - stats.total_cost_previous_period;
    const percentChange = (change / stats.total_cost_previous_period) * 100;
    return { change, percentChange };
  };

  const trend = getCostTrend();

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!stats) {
    return (
      <Card>
        <CardContent className="p-12 text-center text-muted-foreground">
          No cost data available
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              Total Cost
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(stats.total_cost)}</div>
            {trend && (
              <div className="flex items-center gap-1 mt-1">
                {trend.change > 0 ? (
                  <TrendingUp className="h-4 w-4 text-red-500" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-green-500" />
                )}
                <span
                  className={`text-xs ${
                    trend.change > 0 ? 'text-red-500' : 'text-green-500'
                  }`}
                >
                  {Math.abs(trend.percentChange).toFixed(1)}% vs last period
                </span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Total Tokens
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.total_tokens.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {formatCurrency(stats.avg_cost_per_execution)} per execution
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Budget Status</CardDescription>
          </CardHeader>
          <CardContent>
            {stats.budget_limit ? (
              <>
                <div className="text-2xl font-bold">
                  {stats.budget_used_percentage.toFixed(0)}%
                </div>
                <Progress value={stats.budget_used_percentage} className="mt-2 h-2" />
                <p className="text-xs text-muted-foreground mt-1">
                  {formatCurrency(stats.total_cost)} of {formatCurrency(stats.budget_limit)}
                </p>
                {stats.budget_used_percentage > 80 && (
                  <Badge variant="destructive" className="mt-2">
                    <AlertTriangle className="mr-1 h-3 w-3" />
                    Near Limit
                  </Badge>
                )}
              </>
            ) : (
              <div className="text-sm text-muted-foreground">No budget set</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Avg Cost/Execution</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(stats.avg_cost_per_execution)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Across all executions
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Views */}
      <Card>
        <CardHeader>
          <CardTitle>Cost Management</CardTitle>
          <CardDescription>
            Analyze and optimize your AI costs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="breakdown" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="breakdown">Breakdown</TabsTrigger>
              <TabsTrigger value="budget">Budget</TabsTrigger>
              <TabsTrigger value="optimizer">Optimizer</TabsTrigger>
              <TabsTrigger value="prediction">Prediction</TabsTrigger>
            </TabsList>

            <TabsContent value="breakdown">
              <CostBreakdown
                costByModel={stats.cost_by_model}
                costByAgent={stats.cost_by_agent}
                costTrend={stats.cost_trend}
                topExpensiveExecutions={stats.top_expensive_executions}
              />
            </TabsContent>

            <TabsContent value="budget">
              <BudgetManager
                agentId={agentId || undefined}
                currentCost={stats.total_cost}
                budgetLimit={stats.budget_limit}
                onUpdate={loadStats}
              />
            </TabsContent>

            <TabsContent value="optimizer">
              <CostOptimizer
                agentId={agentId || undefined}
                currentStats={stats}
                onOptimize={loadStats}
              />
            </TabsContent>

            <TabsContent value="prediction">
              <CostPrediction
                historicalData={stats.cost_trend}
                currentCost={stats.total_cost}
              />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
