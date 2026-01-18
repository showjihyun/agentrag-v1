'use client';

import React, { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Clock, 
  Users, 
  MessageSquare,
  CheckCircle,
  XCircle,
  AlertTriangle,
  BarChart3,
  PieChart,
  Calendar
} from 'lucide-react';

interface FlowAnalyticsProps {
  flows: any[];
  type: 'agentflow' | 'chatflow' | 'all';
  timeRange?: 'week' | 'month' | 'quarter' | 'year';
}

interface AnalyticsData {
  totalFlows: number;
  activeFlows: number;
  totalExecutions: number;
  successRate: number;
  avgExecutionTime: number;
  topPerformers: any[];
  recentTrends: {
    executions: { period: string; count: number; change: number }[];
    success: { period: string; rate: number; change: number }[];
  };
  categoryBreakdown: { category: string; count: number; percentage: number }[];
  performanceInsights: string[];
}

export function FlowAnalytics({ flows, type, timeRange = 'month' }: FlowAnalyticsProps) {
  const analytics = useMemo((): AnalyticsData => {
    const filteredFlows = type === 'all' ? flows : flows.filter(f => 
      (type === 'agentflow' && f.agents) || (type === 'chatflow' && !f.agents)
    );

    const totalFlows = filteredFlows.length;
    const activeFlows = filteredFlows.filter(f => f.is_active).length;
    const totalExecutions = filteredFlows.reduce((sum, f) => sum + (f.execution_count || 0), 0);
    
    // 실제 성공 횟수 계산 (success_count가 있으면 사용, 없으면 0)
    const successfulExecutions = filteredFlows.reduce((sum, f) => 
      sum + (f.success_count || 0), 0
    );
    const successRate = totalExecutions > 0 ? (successfulExecutions / totalExecutions) * 100 : 0;

    // 실제 평균 실행 시간 계산 (avg_execution_time이 있으면 사용)
    const flowsWithExecutionTime = filteredFlows.filter(f => f.avg_execution_time);
    const avgExecutionTime = flowsWithExecutionTime.length > 0
      ? flowsWithExecutionTime.reduce((sum, f) => sum + (f.avg_execution_time || 0), 0) / flowsWithExecutionTime.length
      : 0;

    // 상위 성과자 (실제 데이터 기반)
    const topPerformers = filteredFlows
      .filter(f => (f.execution_count || 0) > 0)
      .sort((a, b) => (b.execution_count || 0) - (a.execution_count || 0))
      .slice(0, 5)
      .map(f => ({
        ...f,
        successRate: (f.execution_count || 0) > 0 
          ? ((f.success_count || 0) / (f.execution_count || 0)) * 100
          : 0
      }));

    // 실제 트렌드 데이터 계산 (최근 7일)
    const now = new Date();
    const recentTrends = {
      executions: Array.from({ length: 7 }, (_, i) => {
        const date = new Date(now);
        date.setDate(date.getDate() - (6 - i));
        const dateStr = date.toISOString().split('T')[0];
        
        // 해당 날짜에 생성되거나 업데이트된 플로우의 실행 횟수 추정
        const dayFlows = filteredFlows.filter(f => {
          const flowDate = new Date(f.updated_at || f.created_at);
          return flowDate.toISOString().split('T')[0] === dateStr;
        });
        
        const count = dayFlows.reduce((sum, f) => sum + (f.execution_count || 0), 0);
        
        return {
          period: i === 0 ? 'Today' : i === 1 ? 'Yesterday' : `${7-i}d ago`,
          count: count,
          change: 0 // 실제 변화율은 이전 기간 데이터가 필요
        };
      }),
      success: Array.from({ length: 7 }, (_, i) => {
        const date = new Date(now);
        date.setDate(date.getDate() - (6 - i));
        const dateStr = date.toISOString().split('T')[0];
        
        const dayFlows = filteredFlows.filter(f => {
          const flowDate = new Date(f.updated_at || f.created_at);
          return flowDate.toISOString().split('T')[0] === dateStr;
        });
        
        const dayExecutions = dayFlows.reduce((sum, f) => sum + (f.execution_count || 0), 0);
        const daySuccess = dayFlows.reduce((sum, f) => sum + (f.success_count || 0), 0);
        const rate = dayExecutions > 0 ? (daySuccess / dayExecutions) * 100 : 0;
        
        return {
          period: i === 0 ? 'Today' : i === 1 ? 'Yesterday' : `${7-i}d ago`,
          rate: rate,
          change: 0
        };
      })
    };

    // 실제 카테고리 분석 (tags 또는 category 기반)
    const categoryMap = new Map<string, number>();
    filteredFlows.forEach(flow => {
      // category 필드가 있으면 사용
      if (flow.category) {
        categoryMap.set(flow.category, (categoryMap.get(flow.category) || 0) + 1);
      } 
      // tags가 있으면 첫 번째 태그를 카테고리로 사용
      else if (flow.tags && flow.tags.length > 0) {
        const category = flow.tags[0];
        categoryMap.set(category, (categoryMap.get(category) || 0) + 1);
      }
      // 둘 다 없으면 'uncategorized'
      else {
        categoryMap.set('uncategorized', (categoryMap.get('uncategorized') || 0) + 1);
      }
    });
    
    const categoryBreakdown = Array.from(categoryMap.entries())
      .map(([category, count]) => ({
        category,
        count,
        percentage: totalFlows > 0 ? (count / totalFlows) * 100 : 0
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5); // 상위 5개 카테고리만

    // 실제 데이터 기반 성능 인사이트
    const performanceInsights: string[] = [];
    
    if (totalFlows === 0) {
      performanceInsights.push('No flows created yet. Create your first flow to get started.');
    } else {
      if (totalExecutions === 0) {
        performanceInsights.push('No executions recorded. Test your flows to see performance metrics.');
      } else {
        if (successRate < 70) {
          performanceInsights.push(`Success rate is ${successRate.toFixed(1)}%. Review flow configurations to improve reliability.`);
        }
        if (successRate >= 95) {
          performanceInsights.push(`Excellent success rate of ${successRate.toFixed(1)}%! Your flows are performing well.`);
        }
      }
      
      if (avgExecutionTime > 10000) {
        performanceInsights.push(`Average execution time is ${(avgExecutionTime / 1000).toFixed(1)}s. Consider optimizing for better performance.`);
      }
      
      const inactiveRatio = totalFlows > 0 ? (totalFlows - activeFlows) / totalFlows : 0;
      if (inactiveRatio > 0.5) {
        performanceInsights.push(`${Math.round(inactiveRatio * 100)}% of flows are inactive. Consider archiving unused flows.`);
      }
      
      if (topPerformers.length > 0) {
        const topFlow = topPerformers[0];
        performanceInsights.push(`"${topFlow.name}" is your most executed flow with ${topFlow.execution_count} runs.`);
      }
      
      if (categoryBreakdown.length > 0) {
        const topCategory = categoryBreakdown[0];
        performanceInsights.push(`Most flows are in "${topCategory.category}" category (${topCategory.count} flows).`);
      }
    }

    return {
      totalFlows,
      activeFlows,
      totalExecutions,
      successRate,
      avgExecutionTime,
      topPerformers,
      recentTrends,
      categoryBreakdown,
      performanceInsights
    };
  }, [flows, type, timeRange]);

  const formatExecutionTime = (ms: number) => {
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const getSuccessRateColor = (rate: number) => {
    if (rate >= 90) return 'text-green-600';
    if (rate >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getTrendIcon = (change: number) => {
    if (change > 0) return <TrendingUp className="h-3 w-3 text-green-500" />;
    if (change < 0) return <TrendingDown className="h-3 w-3 text-red-500" />;
    return <Activity className="h-3 w-3 text-gray-500" />;
  };

  return (
    <div className="space-y-6">
      {/* Overview Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              {type === 'agentflow' ? <Users className="h-4 w-4" /> : <MessageSquare className="h-4 w-4" />}
              Total Flows
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.totalFlows}</div>
            <div className="text-xs text-muted-foreground">
              Active: {analytics.activeFlows} ({analytics.totalFlows > 0 ? Math.round((analytics.activeFlows / analytics.totalFlows) * 100) : 0}%)
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Total Executions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.totalExecutions.toLocaleString()}</div>
            <div className="text-xs text-muted-foreground">
              {analytics.totalExecutions === 0 ? 'No executions yet' : 'All time'}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <CheckCircle className="h-4 w-4" />
              Success Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getSuccessRateColor(analytics.successRate)}`}>
              {analytics.totalExecutions > 0 ? `${analytics.successRate.toFixed(1)}%` : 'N/A'}
            </div>
            {analytics.totalExecutions > 0 && (
              <Progress value={analytics.successRate} className="mt-2" />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Avg Execution Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {analytics.avgExecutionTime > 0 ? formatExecutionTime(analytics.avgExecutionTime) : 'N/A'}
            </div>
            <div className="text-xs text-muted-foreground">
              {analytics.avgExecutionTime === 0 ? 'No data available' : 'Average'}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Performers */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Top Performing Flows
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {analytics.topPerformers.length > 0 ? (
                analytics.topPerformers.map((flow, index) => (
                  <div key={flow.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-900">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900 text-xs font-semibold">
                        {index + 1}
                      </div>
                      <div>
                        <div className="font-medium truncate max-w-[200px]">{flow.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {flow.execution_count} executions
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-sm font-semibold ${getSuccessRateColor(flow.successRate)}`}>
                        {flow.successRate.toFixed(1)}%
                      </div>
                      <div className="text-xs text-muted-foreground">success</div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Activity className="mx-auto h-8 w-8 mb-2 opacity-50" />
                  <p className="text-sm">No executed flows yet</p>
                  <p className="text-xs mt-1">Execute flows to see performance data</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Category Analysis */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="h-5 w-5" />
              Category Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            {analytics.categoryBreakdown.length > 0 ? (
              <div className="space-y-3">
                {analytics.categoryBreakdown.map((category) => (
                  <div key={category.category} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="capitalize">{category.category}</span>
                      <span>{category.count} ({category.percentage.toFixed(1)}%)</span>
                    </div>
                    <Progress value={category.percentage} className="h-2" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <PieChart className="mx-auto h-8 w-8 mb-2 opacity-50" />
                <p className="text-sm">No categories found</p>
                <p className="text-xs mt-1">Add tags or categories to your flows</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Performance Insights */}
      {analytics.performanceInsights.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              Performance Insights
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {analytics.performanceInsights.map((insight, index) => (
                <div key={index} className="flex items-start gap-2 p-3 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800">
                  <AlertTriangle className="h-4 w-4 text-blue-600 mt-0.5 shrink-0" />
                  <p className="text-sm text-blue-800 dark:text-blue-200">{insight}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Execution Trends */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Recent 7-Day Execution Trend
          </CardTitle>
        </CardHeader>
        <CardContent>
          {analytics.totalExecutions > 0 ? (
            <div className="grid grid-cols-7 gap-2">
              {analytics.recentTrends.executions.map((trend, index) => {
                const maxCount = Math.max(...analytics.recentTrends.executions.map(t => t.count), 1);
                return (
                  <div key={index} className="text-center">
                    <div className="text-xs text-muted-foreground mb-1 truncate">{trend.period}</div>
                    <div className="h-20 bg-gray-100 dark:bg-gray-800 rounded flex items-end justify-center p-1">
                      <div 
                        className="bg-blue-500 rounded-sm w-full transition-all"
                        style={{ height: `${Math.max((trend.count / maxCount) * 100, 5)}%` }}
                      />
                    </div>
                    <div className="text-xs font-medium mt-1">{trend.count}</div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Calendar className="mx-auto h-8 w-8 mb-2 opacity-50" />
              <p className="text-sm">No execution data available</p>
              <p className="text-xs mt-1">Execute flows to see trend analysis</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}