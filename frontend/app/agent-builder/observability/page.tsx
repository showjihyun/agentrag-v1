'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart3,
  Activity,
  Clock,
  DollarSign,
  Zap,
  AlertTriangle,
  CheckCircle,
  XCircle,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Download,
  Filter,
  Calendar,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { agentBuilderAPI } from '@/lib/api/agent-builder';

interface MetricCard {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
}

interface ExecutionTrace {
  id: string;
  flow_name: string;
  flow_type: 'agentflow' | 'chatflow' | 'workflow';
  status: 'running' | 'completed' | 'failed';
  started_at: string;
  duration_ms?: number;
  nodes_executed: number;
  total_nodes: number;
  llm_calls: number;
  tokens_used: number;
  cost: number;
  error?: string;
}

export default function ObservabilityPage() {
  const [timeRange, setTimeRange] = useState('24h');
  const [selectedTab, setSelectedTab] = useState('overview');

  // Fetch dashboard stats
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ['observability-stats', timeRange],
    queryFn: () => agentBuilderAPI.getDashboardStats(),
    refetchInterval: 30000,
  });

  // Fetch execution trend
  const { data: trendData, isLoading: trendLoading } = useQuery({
    queryKey: ['execution-trend', timeRange],
    queryFn: () => agentBuilderAPI.getExecutionTrend(timeRange === '24h' ? 1 : timeRange === '7d' ? 7 : 30),
  });

  // Fetch recent executions
  const { data: recentExecutions, isLoading: executionsLoading } = useQuery({
    queryKey: ['recent-executions'],
    queryFn: () => agentBuilderAPI.getExecutions({ page_size: 20 }),
    refetchInterval: 10000,
  });

  const metrics: MetricCard[] = [
    {
      title: '총 실행 횟수',
      value: stats?.total_executions || 0,
      change: 12.5,
      changeLabel: '지난 주 대비',
      icon: <Activity className="h-4 w-4" />,
      trend: 'up',
    },
    {
      title: '성공률',
      value: `${stats?.success_rate || 0}%`,
      change: 2.3,
      changeLabel: '지난 주 대비',
      icon: <CheckCircle className="h-4 w-4" />,
      trend: 'up',
    },
    {
      title: '평균 응답 시간',
      value: `${((stats?.executions?.avg_duration_seconds || 0) * 1000).toFixed(0)}ms`,
      change: -8.1,
      changeLabel: '지난 주 대비',
      icon: <Clock className="h-4 w-4" />,
      trend: 'down',
    },
    {
      title: '예상 비용',
      value: `$${(stats?.estimated_cost || 0).toFixed(2)}`,
      change: 5.2,
      changeLabel: '지난 주 대비',
      icon: <DollarSign className="h-4 w-4" />,
      trend: 'up',
    },
  ];

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);

    if (diffMins < 1) return '방금 전';
    if (diffMins < 60) return `${diffMins}분 전`;
    if (diffHours < 24) return `${diffHours}시간 전`;
    return `${Math.floor(diffHours / 24)}일 전`;
  };

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <BarChart3 className="h-8 w-8 text-green-500" />
            Observability
          </h1>
          <p className="text-muted-foreground mt-1">
            실행 추적, 성능 모니터링, 비용 분석을 한눈에 확인하세요
          </p>
        </div>
        <div className="flex gap-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-[140px]">
              <Calendar className="h-4 w-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">최근 24시간</SelectItem>
              <SelectItem value="7d">최근 7일</SelectItem>
              <SelectItem value="30d">최근 30일</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={() => refetchStats()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            새로고침
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            내보내기
          </Button>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {statsLoading
          ? [1, 2, 3, 4].map((i) => (
              <Card key={i}>
                <CardHeader className="pb-2">
                  <Skeleton className="h-4 w-24" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-8 w-20" />
                  <Skeleton className="h-3 w-32 mt-2" />
                </CardContent>
              </Card>
            ))
          : metrics.map((metric, index) => (
              <Card key={index}>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    {metric.title}
                  </CardTitle>
                  <div className="text-muted-foreground">{metric.icon}</div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{metric.value}</div>
                  {metric.change !== undefined && (
                    <div className="flex items-center gap-1 mt-1">
                      {metric.trend === 'up' ? (
                        <TrendingUp className="h-3 w-3 text-green-500" />
                      ) : metric.trend === 'down' ? (
                        <TrendingDown className="h-3 w-3 text-red-500" />
                      ) : null}
                      <span
                        className={`text-xs ${
                          metric.trend === 'up'
                            ? 'text-green-500'
                            : metric.trend === 'down'
                            ? 'text-red-500'
                            : 'text-muted-foreground'
                        }`}
                      >
                        {metric.change > 0 ? '+' : ''}
                        {metric.change}% {metric.changeLabel}
                      </span>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
      </div>

      {/* Tabs */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">개요</TabsTrigger>
          <TabsTrigger value="traces">실행 추적</TabsTrigger>
          <TabsTrigger value="performance">성능</TabsTrigger>
          <TabsTrigger value="costs">비용</TabsTrigger>
          <TabsTrigger value="errors">오류</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Execution Trend Chart */}
            <Card>
              <CardHeader>
                <CardTitle>실행 추이</CardTitle>
                <CardDescription>시간별 실행 현황</CardDescription>
              </CardHeader>
              <CardContent>
                {trendLoading ? (
                  <Skeleton className="h-[200px] w-full" />
                ) : (
                  <div className="h-[200px] flex items-end gap-1">
                    {(trendData?.trend || []).map((item: any, index: number) => (
                      <div key={index} className="flex-1 flex flex-col items-center gap-1">
                        <div
                          className="w-full bg-primary/20 rounded-t relative"
                          style={{ height: `${Math.max((item.total / 100) * 150, 10)}px` }}
                        >
                          <div
                            className="absolute bottom-0 w-full bg-green-500 rounded-t"
                            style={{
                              height: `${(item.success / Math.max(item.total, 1)) * 100}%`,
                            }}
                          />
                        </div>
                        <span className="text-[10px] text-muted-foreground">
                          {new Date(item.date).toLocaleDateString('ko-KR', { weekday: 'short' })}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Status Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>상태 분포</CardTitle>
                <CardDescription>실행 결과별 분포</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>성공</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Progress value={stats?.success_rate || 0} className="w-32 h-2" />
                      <span className="text-sm font-medium">{stats?.success_rate || 0}%</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <XCircle className="h-4 w-4 text-red-500" />
                      <span>실패</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Progress value={100 - (stats?.success_rate || 0)} className="w-32 h-2" />
                      <span className="text-sm font-medium">{100 - (stats?.success_rate || 0)}%</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Activity className="h-4 w-4 text-blue-500 animate-pulse" />
                      <span>실행 중</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{stats?.executions?.running || 0}개</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recent Executions */}
          <Card>
            <CardHeader>
              <CardTitle>최근 실행</CardTitle>
              <CardDescription>실시간 실행 현황</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[300px]">
                {executionsLoading ? (
                  <div className="space-y-2">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <Skeleton key={i} className="h-16 w-full" />
                    ))}
                  </div>
                ) : (
                  <div className="space-y-2">
                    {(recentExecutions?.executions || []).map((execution: any) => (
                      <div
                        key={execution.id}
                        className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent cursor-pointer"
                      >
                        <div className="flex items-center gap-3">
                          {execution.status === 'completed' ? (
                            <CheckCircle className="h-5 w-5 text-green-500" />
                          ) : execution.status === 'failed' ? (
                            <XCircle className="h-5 w-5 text-red-500" />
                          ) : (
                            <Activity className="h-5 w-5 text-blue-500 animate-pulse" />
                          )}
                          <div>
                            <p className="font-medium">{execution.agent_name || 'Unknown'}</p>
                            <p className="text-xs text-muted-foreground">
                              {formatTimeAgo(execution.started_at)}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          {execution.duration_ms && (
                            <Badge variant="outline">{formatDuration(execution.duration_ms)}</Badge>
                          )}
                          <Badge
                            variant={
                              execution.status === 'completed'
                                ? 'default'
                                : execution.status === 'failed'
                                ? 'destructive'
                                : 'secondary'
                            }
                          >
                            {execution.status}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Traces Tab */}
        <TabsContent value="traces" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>실행 추적</CardTitle>
                  <CardDescription>상세 실행 로그 및 노드별 추적</CardDescription>
                </div>
                <Button variant="outline" size="sm">
                  <Filter className="h-4 w-4 mr-2" />
                  필터
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px]">
                <div className="space-y-4">
                  {(recentExecutions?.executions || []).map((execution: any) => (
                    <Card key={execution.id} className="border-l-4 border-l-primary">
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Badge
                              variant={
                                execution.status === 'completed'
                                  ? 'default'
                                  : execution.status === 'failed'
                                  ? 'destructive'
                                  : 'secondary'
                              }
                            >
                              {execution.status}
                            </Badge>
                            <span className="font-medium">{execution.agent_name}</span>
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {new Date(execution.started_at).toLocaleString()}
                          </span>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-4 gap-4 text-sm">
                          <div>
                            <p className="text-muted-foreground">실행 시간</p>
                            <p className="font-medium">
                              {execution.duration_ms ? formatDuration(execution.duration_ms) : '-'}
                            </p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">LLM 호출</p>
                            <p className="font-medium">{execution.llm_calls || 0}회</p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">토큰 사용</p>
                            <p className="font-medium">{execution.tokens_used || 0}</p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">비용</p>
                            <p className="font-medium">${(execution.cost || 0).toFixed(4)}</p>
                          </div>
                        </div>
                        {execution.error_message && (
                          <div className="mt-3 p-2 bg-red-50 dark:bg-red-950 rounded text-sm text-red-600 dark:text-red-400">
                            <AlertTriangle className="h-4 w-4 inline mr-1" />
                            {execution.error_message}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>응답 시간 분포</CardTitle>
                <CardDescription>P50, P90, P99 레이턴시</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span>P50 (중앙값)</span>
                    <Badge variant="outline">245ms</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>P90</span>
                    <Badge variant="outline">890ms</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>P99</span>
                    <Badge variant="outline">2.3s</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>최대</span>
                    <Badge variant="destructive">5.2s</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>처리량</CardTitle>
                <CardDescription>시간당 요청 처리량</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span>현재 RPS</span>
                    <Badge variant="default">12.5</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>평균 RPS</span>
                    <Badge variant="outline">8.3</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>최대 RPS</span>
                    <Badge variant="outline">45.2</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Costs Tab */}
        <TabsContent value="costs" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>총 비용</CardTitle>
                <CardDescription>{timeRange === '24h' ? '오늘' : timeRange === '7d' ? '이번 주' : '이번 달'}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">${(stats?.estimated_cost || 0).toFixed(2)}</div>
                <p className="text-sm text-muted-foreground mt-1">
                  예상 월간 비용: ${((stats?.estimated_cost || 0) * 30).toFixed(2)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>LLM 비용</CardTitle>
                <CardDescription>토큰 사용량 기반</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">${((stats?.estimated_cost || 0) * 0.8).toFixed(2)}</div>
                <p className="text-sm text-muted-foreground mt-1">
                  총 토큰: {stats?.total_tokens || 0}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>인프라 비용</CardTitle>
                <CardDescription>컴퓨팅 리소스</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">${((stats?.estimated_cost || 0) * 0.2).toFixed(2)}</div>
                <p className="text-sm text-muted-foreground mt-1">
                  벡터 DB, 캐시 등
                </p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>비용 최적화 제안</CardTitle>
              <CardDescription>비용 절감을 위한 권장 사항</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-3 bg-yellow-50 dark:bg-yellow-950 rounded-lg">
                  <Zap className="h-5 w-5 text-yellow-600 mt-0.5" />
                  <div>
                    <p className="font-medium">캐시 적중률 개선</p>
                    <p className="text-sm text-muted-foreground">
                      현재 캐시 적중률 45%. 60% 이상으로 개선 시 약 15% 비용 절감 가능
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-blue-50 dark:bg-blue-950 rounded-lg">
                  <Zap className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div>
                    <p className="font-medium">모델 다운그레이드 검토</p>
                    <p className="text-sm text-muted-foreground">
                      단순 쿼리에 GPT-4 대신 GPT-3.5 사용 시 약 20% 비용 절감 가능
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Errors Tab */}
        <TabsContent value="errors" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>오류 현황</CardTitle>
              <CardDescription>최근 발생한 오류 목록</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                <div className="space-y-3">
                  {(recentExecutions?.executions || [])
                    .filter((e: any) => e.status === 'failed')
                    .map((execution: any) => (
                      <div
                        key={execution.id}
                        className="p-4 border border-red-200 dark:border-red-800 rounded-lg bg-red-50 dark:bg-red-950"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <XCircle className="h-5 w-5 text-red-500" />
                            <span className="font-medium">{execution.agent_name}</span>
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {formatTimeAgo(execution.started_at)}
                          </span>
                        </div>
                        <p className="text-sm text-red-600 dark:text-red-400">
                          {execution.error_message || 'Unknown error'}
                        </p>
                      </div>
                    ))}
                  {(recentExecutions?.executions || []).filter((e: any) => e.status === 'failed')
                    .length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                      <CheckCircle className="h-12 w-12 mx-auto mb-2 text-green-500" />
                      <p>최근 오류가 없습니다</p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
