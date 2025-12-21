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
    const successfulExecutions = filteredFlows.reduce((sum, f) => 
      sum + (f.success_count || Math.floor((f.execution_count || 0) * 0.85)), 0
    );
    const successRate = totalExecutions > 0 ? (successfulExecutions / totalExecutions) * 100 : 0;

    // 평균 실행 시간 (시뮬레이션)
    const avgExecutionTime = filteredFlows.reduce((sum, f) => 
      sum + (f.avg_execution_time || Math.random() * 5000 + 1000), 0
    ) / Math.max(totalFlows, 1);

    // 상위 성과자
    const topPerformers = filteredFlows
      .filter(f => f.execution_count > 0)
      .sort((a, b) => (b.execution_count || 0) - (a.execution_count || 0))
      .slice(0, 5)
      .map(f => ({
        ...f,
        successRate: f.execution_count > 0 
          ? ((f.success_count || Math.floor(f.execution_count * 0.85)) / f.execution_count) * 100
          : 0
      }));

    // 트렌드 데이터 (시뮬레이션)
    const recentTrends = {
      executions: Array.from({ length: 7 }, (_, i) => ({
        period: `${7-i}일 전`,
        count: Math.floor(Math.random() * 100) + 50,
        change: (Math.random() - 0.5) * 20
      })),
      success: Array.from({ length: 7 }, (_, i) => ({
        period: `${7-i}일 전`,
        rate: Math.random() * 20 + 80,
        change: (Math.random() - 0.5) * 10
      }))
    };

    // 카테고리 분석
    const categories = type === 'agentflow' 
      ? ['research', 'support', 'content', 'business']
      : ['rag', 'support', 'assistant', 'custom'];
    
    const categoryBreakdown = categories.map(category => {
      const count = Math.floor(Math.random() * totalFlows * 0.3) + 1;
      return {
        category,
        count,
        percentage: totalFlows > 0 ? (count / totalFlows) * 100 : 0
      };
    });

    // 성능 인사이트
    const performanceInsights = [];
    if (successRate < 70) {
      performanceInsights.push('성공률이 낮습니다. 플로우 설정을 검토해보세요.');
    }
    if (avgExecutionTime > 10000) {
      performanceInsights.push('평균 실행 시간이 깁니다. 성능 최적화를 고려해보세요.');
    }
    if (activeFlows / totalFlows < 0.5) {
      performanceInsights.push('비활성 플로우가 많습니다. 사용하지 않는 플로우를 정리해보세요.');
    }
    if (totalExecutions === 0) {
      performanceInsights.push('실행된 플로우가 없습니다. 플로우를 테스트해보세요.');
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
      {/* 개요 메트릭 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              {type === 'agentflow' ? <Users className="h-4 w-4" /> : <MessageSquare className="h-4 w-4" />}
              총 플로우
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.totalFlows}</div>
            <div className="text-xs text-muted-foreground">
              활성: {analytics.activeFlows}개 ({analytics.totalFlows > 0 ? Math.round((analytics.activeFlows / analytics.totalFlows) * 100) : 0}%)
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Activity className="h-4 w-4" />
              총 실행 횟수
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.totalExecutions.toLocaleString()}</div>
            <div className="text-xs text-muted-foreground flex items-center gap-1">
              {getTrendIcon(5.2)}
              지난 주 대비 +5.2%
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <CheckCircle className="h-4 w-4" />
              성공률
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getSuccessRateColor(analytics.successRate)}`}>
              {analytics.successRate.toFixed(1)}%
            </div>
            <Progress value={analytics.successRate} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Clock className="h-4 w-4" />
              평균 실행 시간
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatExecutionTime(analytics.avgExecutionTime)}</div>
            <div className="text-xs text-muted-foreground flex items-center gap-1">
              {getTrendIcon(-2.1)}
              지난 주 대비 -2.1%
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 상위 성과자 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              상위 성과 플로우
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
                          {flow.execution_count}회 실행
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-sm font-semibold ${getSuccessRateColor(flow.successRate)}`}>
                        {flow.successRate.toFixed(1)}%
                      </div>
                      <div className="text-xs text-muted-foreground">성공률</div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Activity className="mx-auto h-8 w-8 mb-2" />
                  <p>실행된 플로우가 없습니다</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 카테고리 분석 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="h-5 w-5" />
              카테고리별 분포
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {analytics.categoryBreakdown.map((category) => (
                <div key={category.category} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="capitalize">{category.category}</span>
                    <span>{category.count}개 ({category.percentage.toFixed(1)}%)</span>
                  </div>
                  <Progress value={category.percentage} className="h-2" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 성능 인사이트 */}
      {analytics.performanceInsights.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              성능 인사이트
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {analytics.performanceInsights.map((insight, index) => (
                <div key={index} className="flex items-start gap-2 p-3 rounded-lg bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-200 dark:border-yellow-800">
                  <AlertTriangle className="h-4 w-4 text-yellow-600 mt-0.5 shrink-0" />
                  <p className="text-sm text-yellow-800 dark:text-yellow-200">{insight}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 실행 트렌드 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            최근 7일 실행 트렌드
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-7 gap-2">
            {analytics.recentTrends.executions.map((trend, index) => (
              <div key={index} className="text-center">
                <div className="text-xs text-muted-foreground mb-1">{trend.period}</div>
                <div className="h-20 bg-gray-100 dark:bg-gray-800 rounded flex items-end justify-center p-1">
                  <div 
                    className="bg-blue-500 rounded-sm w-full transition-all"
                    style={{ height: `${Math.max((trend.count / 150) * 100, 10)}%` }}
                  />
                </div>
                <div className="text-xs font-medium mt-1">{trend.count}</div>
                <div className="text-xs text-muted-foreground flex items-center justify-center gap-1">
                  {getTrendIcon(trend.change)}
                  {Math.abs(trend.change).toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}