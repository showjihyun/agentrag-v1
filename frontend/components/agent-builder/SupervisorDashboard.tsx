'use client';

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Activity,
  Users,
  Clock,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  Zap,
  Brain,
  Target,
  BarChart3,
  Settings,
  RotateCcw,
  Play,
  Pause,
  AlertCircle,
} from 'lucide-react';
import { agentBuilderAPI } from '@/lib/api/agent-builder';

interface SupervisorMetrics {
  active_agents: number;
  current_tasks: number;
  success_rate: number;
  average_response_time: number;
  total_executions: number;
  failed_executions: number;
  resource_utilization: {
    cpu: number;
    memory: number;
    network: number;
  };
}

interface AgentPerformance {
  agent_id: string;
  agent_name: string;
  success_rate: number;
  avg_response_time: number;
  execution_count: number;
  status: 'active' | 'idle' | 'error';
  last_execution: string;
}

interface SupervisorDashboardProps {
  agentflowId: string;
  supervisorEnabled: boolean;
  onToggleSupervisor?: (enabled: boolean) => void;
}

export function SupervisorDashboard({
  agentflowId,
  supervisorEnabled,
  onToggleSupervisor,
}: SupervisorDashboardProps) {
  const [refreshInterval, setRefreshInterval] = useState(5000); // 5초
  const [autoRefresh, setAutoRefresh] = useState(true);

  // 실시간 메트릭 조회
  const { data: metrics, isLoading: metricsLoading, refetch: refetchMetrics } = useQuery({
    queryKey: ['supervisor-metrics', agentflowId],
    queryFn: () => agentBuilderAPI.getSupervisorMetrics(agentflowId),
    enabled: supervisorEnabled,
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  // 에이전트 성능 데이터 조회
  const { data: agentPerformance, isLoading: performanceLoading } = useQuery({
    queryKey: ['agent-performance', agentflowId],
    queryFn: () => agentBuilderAPI.getAgentPerformance(agentflowId),
    enabled: supervisorEnabled,
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  // 예측 인사이트 조회
  const { data: insights } = useQuery({
    queryKey: ['supervisor-insights', agentflowId],
    queryFn: () => agentBuilderAPI.getSupervisorInsights(agentflowId),
    enabled: supervisorEnabled,
    refetchInterval: 30000, // 30초마다 업데이트
  });

  const mockMetrics: SupervisorMetrics = {
    active_agents: 3,
    current_tasks: 7,
    success_rate: 94.2,
    average_response_time: 2.3,
    total_executions: 1247,
    failed_executions: 72,
    resource_utilization: {
      cpu: 45,
      memory: 62,
      network: 28,
    },
  };

  const mockAgentPerformance: AgentPerformance[] = [
    {
      agent_id: '1',
      agent_name: '데이터 분석가',
      success_rate: 96.5,
      avg_response_time: 1.8,
      execution_count: 423,
      status: 'active',
      last_execution: '2분 전',
    },
    {
      agent_id: '2',
      agent_name: '보고서 작성자',
      success_rate: 91.2,
      avg_response_time: 3.1,
      execution_count: 387,
      status: 'idle',
      last_execution: '15분 전',
    },
    {
      agent_id: '3',
      agent_name: '품질 검토자',
      success_rate: 98.7,
      avg_response_time: 2.0,
      execution_count: 437,
      status: 'active',
      last_execution: '1분 전',
    },
  ];

  const currentMetrics = metrics || mockMetrics;
  const currentPerformance = agentPerformance?.agents || mockAgentPerformance;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500';
      case 'idle':
        return 'bg-yellow-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <Play className="h-3 w-3" />;
      case 'idle':
        return <Pause className="h-3 w-3" />;
      case 'error':
        return <AlertCircle className="h-3 w-3" />;
      default:
        return <Activity className="h-3 w-3" />;
    }
  };

  if (!supervisorEnabled) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Brain className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">슈퍼바이저 비활성화</h3>
          <p className="text-muted-foreground text-center mb-4">
            슈퍼바이저를 활성화하면 실시간 모니터링과 지능형 관리 기능을 사용할 수 있습니다
          </p>
          <Button onClick={() => onToggleSupervisor?.(true)} className="gap-2">
            <Settings className="h-4 w-4" />
            슈퍼바이저 활성화
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
            <Brain className="h-6 w-6 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">슈퍼바이저 대시보드</h2>
            <p className="text-muted-foreground">실시간 에이전트 모니터링 및 성능 분석</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={autoRefresh ? 'bg-green-50 border-green-200' : ''}
          >
            <Activity className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-pulse' : ''}`} />
            {autoRefresh ? '실시간 ON' : '실시간 OFF'}
          </Button>
          <Button variant="outline" size="sm" onClick={() => refetchMetrics()}>
            <RotateCcw className="h-4 w-4 mr-2" />
            새로고침
          </Button>
        </div>
      </div>

      {/* 주요 메트릭 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Users className="h-4 w-4" />
              활성 에이전트
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{currentMetrics.active_agents}</div>
            <div className="flex items-center gap-1 text-xs text-green-600">
              <TrendingUp className="h-3 w-3" />
              +12% 이번 주
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Activity className="h-4 w-4" />
              현재 작업
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{currentMetrics.current_tasks}</div>
            <div className="flex items-center gap-1 text-xs text-blue-600">
              <Zap className="h-3 w-3" />
              실시간 처리 중
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              성공률
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {currentMetrics.success_rate.toFixed(1)}%
            </div>
            <Progress value={currentMetrics.success_rate} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Clock className="h-4 w-4" />
              평균 응답시간
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{currentMetrics.average_response_time}초</div>
            <div className="flex items-center gap-1 text-xs text-green-600">
              <Target className="h-3 w-3" />
              목표: 3초 이하
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 탭 컨텐츠 */}
      <Tabs defaultValue="performance" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="performance">성능 분석</TabsTrigger>
          <TabsTrigger value="agents">에이전트 상태</TabsTrigger>
          <TabsTrigger value="resources">리소스 사용량</TabsTrigger>
          <TabsTrigger value="insights">AI 인사이트</TabsTrigger>
        </TabsList>

        {/* 성능 분석 탭 */}
        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  실행 통계
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">총 실행 횟수</span>
                  <span className="font-semibold">{currentMetrics.total_executions.toLocaleString()}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">실패 횟수</span>
                  <span className="font-semibold text-red-600">{currentMetrics.failed_executions}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">성공률</span>
                  <span className="font-semibold text-green-600">
                    {((currentMetrics.total_executions - currentMetrics.failed_executions) / currentMetrics.total_executions * 100).toFixed(1)}%
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  성능 트렌드
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">응답 시간 개선</span>
                    <Badge variant="outline" className="text-green-600 border-green-200">
                      -15% 이번 주
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">성공률 향상</span>
                    <Badge variant="outline" className="text-green-600 border-green-200">
                      +3.2% 이번 달
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">처리량 증가</span>
                    <Badge variant="outline" className="text-blue-600 border-blue-200">
                      +28% 이번 달
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 에이전트 상태 탭 */}
        <TabsContent value="agents" className="space-y-4">
          <div className="grid gap-4">
            {currentPerformance.map((agent) => (
              <Card key={agent.agent_id}>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${getStatusColor(agent.status)}`} />
                      <div>
                        <h4 className="font-semibold">{agent.agent_name}</h4>
                        <p className="text-sm text-muted-foreground">
                          마지막 실행: {agent.last_execution}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-sm font-medium">성공률</div>
                        <div className="text-lg font-bold text-green-600">
                          {agent.success_rate.toFixed(1)}%
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium">응답시간</div>
                        <div className="text-lg font-bold">
                          {agent.avg_response_time.toFixed(1)}초
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium">실행 횟수</div>
                        <div className="text-lg font-bold">
                          {agent.execution_count.toLocaleString()}
                        </div>
                      </div>
                      <Badge variant="outline" className="gap-1">
                        {getStatusIcon(agent.status)}
                        {agent.status === 'active' ? '활성' : agent.status === 'idle' ? '대기' : '오류'}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* 리소스 사용량 탭 */}
        <TabsContent value="resources" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">CPU 사용률</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold mb-2">
                  {currentMetrics.resource_utilization.cpu}%
                </div>
                <Progress value={currentMetrics.resource_utilization.cpu} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm">메모리 사용률</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold mb-2">
                  {currentMetrics.resource_utilization.memory}%
                </div>
                <Progress value={currentMetrics.resource_utilization.memory} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm">네트워크 사용률</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold mb-2">
                  {currentMetrics.resource_utilization.network}%
                </div>
                <Progress value={currentMetrics.resource_utilization.network} />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* AI 인사이트 탭 */}
        <TabsContent value="insights" className="space-y-4">
          <div className="grid gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5" />
                  AI 추천사항
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-start gap-3 p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
                  <AlertTriangle className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-blue-800 dark:text-blue-200">
                      성능 최적화 기회 발견
                    </h4>
                    <p className="text-sm text-blue-700 dark:text-blue-300">
                      '데이터 분석가' 에이전트의 병렬 처리를 활성화하면 처리 속도를 30% 향상시킬 수 있습니다.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3 bg-green-50 dark:bg-green-950/20 rounded-lg">
                  <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-green-800 dark:text-green-200">
                      리소스 효율성 우수
                    </h4>
                    <p className="text-sm text-green-700 dark:text-green-300">
                      현재 리소스 사용량이 최적 범위 내에 있습니다. 추가 에이전트를 배치할 여유가 있습니다.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3 bg-yellow-50 dark:bg-yellow-950/20 rounded-lg">
                  <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-yellow-800 dark:text-yellow-200">
                      에이전트 밸런싱 필요
                    </h4>
                    <p className="text-sm text-yellow-700 dark:text-yellow-300">
                      '보고서 작성자' 에이전트의 작업 부하가 다른 에이전트보다 높습니다. 역할 재분배를 고려해보세요.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}