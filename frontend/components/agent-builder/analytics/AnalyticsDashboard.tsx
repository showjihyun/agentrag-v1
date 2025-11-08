'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { TrendingUp, Users, Zap, Target, BarChart3, PieChart as PieChartIcon } from 'lucide-react';
import { PerformanceAnalytics } from './PerformanceAnalytics';
import { UsageAnalytics } from './UsageAnalytics';
import { QualityAnalytics } from './QualityAnalytics';
import { InsightsPanel } from './InsightsPanel';

interface AnalyticsDashboardProps {
  agentId?: string;
  timeRange?: '24h' | '7d' | '30d' | '90d' | 'all';
}

interface AnalyticsOverview {
  total_executions: number;
  success_rate: number;
  avg_response_time: number;
  total_users: number;
  top_performing_agents: Array<{
    id: string;
    name: string;
    success_rate: number;
    execution_count: number;
  }>;
  insights: Array<{
    type: 'success' | 'warning' | 'info';
    title: string;
    description: string;
    action?: string;
  }>;
}

export function AnalyticsDashboard({ agentId, timeRange = '30d' }: AnalyticsDashboardProps) {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOverview();
  }, [agentId, timeRange]);

  const loadOverview = async () => {
    try {
      setLoading(true);
      const data = await agentBuilderAPI.getAnalyticsOverview(agentId, timeRange);
      setOverview(data);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Total Executions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {overview?.total_executions.toLocaleString() || 0}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Last {timeRange}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-2">
              <Target className="h-4 w-4" />
              Success Rate
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {overview?.success_rate.toFixed(1) || 0}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Overall performance
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Avg Response Time
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {overview?.avg_response_time.toFixed(2) || 0}s
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Per execution
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Active Users
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {overview?.total_users || 0}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Unique users
            </p>
          </CardContent>
        </Card>
      </div>

      {/* AI Insights */}
      {overview?.insights && overview.insights.length > 0 && (
        <InsightsPanel insights={overview.insights} />
      )}

      {/* Detailed Analytics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Detailed Analytics
          </CardTitle>
          <CardDescription>
            Deep dive into performance, usage, and quality metrics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="performance" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="performance">Performance</TabsTrigger>
              <TabsTrigger value="usage">Usage</TabsTrigger>
              <TabsTrigger value="quality">Quality</TabsTrigger>
            </TabsList>

            <TabsContent value="performance">
              <PerformanceAnalytics agentId={agentId} timeRange={timeRange} />
            </TabsContent>

            <TabsContent value="usage">
              <UsageAnalytics agentId={agentId} timeRange={timeRange} />
            </TabsContent>

            <TabsContent value="quality">
              <QualityAnalytics agentId={agentId} timeRange={timeRange} />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Top Performing Agents */}
      {overview?.top_performing_agents && overview.top_performing_agents.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Top Performing Agents</CardTitle>
            <CardDescription>Best agents by success rate</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {overview.top_performing_agents.map((agent, index) => (
                <div
                  key={agent.id}
                  className="flex items-center justify-between p-3 border rounded-md"
                >
                  <div className="flex items-center gap-3">
                    <Badge variant="outline">#{index + 1}</Badge>
                    <div>
                      <p className="font-medium">{agent.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {agent.execution_count} executions
                      </p>
                    </div>
                  </div>
                  <Badge variant="default">{agent.success_rate.toFixed(1)}%</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
