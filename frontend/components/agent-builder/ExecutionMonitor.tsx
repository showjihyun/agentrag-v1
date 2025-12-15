'use client';

import { useState, useEffect, useRef } from 'react';
import {
  Play,
  Pause,
  Square,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Activity,
  Zap,
  Users,
  MessageSquare,
  BarChart3,
  RefreshCw,
  Eye,
  Download,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';

interface ExecutionStep {
  id: string;
  name: string;
  type: 'agent' | 'tool' | 'llm' | 'condition' | 'loop';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  startTime?: Date;
  endTime?: Date;
  duration?: number;
  input?: any;
  output?: any;
  error?: string;
  metadata?: {
    tokens_used?: number;
    cost_usd?: number;
    model?: string;
    provider?: string;
  };
}

interface ExecutionData {
  id: string;
  flowId: string;
  flowName: string;
  flowType: 'agentflow' | 'chatflow';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  startTime: Date;
  endTime?: Date;
  duration?: number;
  steps: ExecutionStep[];
  metrics: {
    totalSteps: number;
    completedSteps: number;
    failedSteps: number;
    skippedSteps: number;
    totalTokens: number;
    totalCost: number;
    averageStepDuration: number;
  };
  logs: Array<{
    timestamp: Date;
    level: 'info' | 'warn' | 'error' | 'debug';
    message: string;
    metadata?: any;
  }>;
}

interface ExecutionMonitorProps {
  executionId?: string;
  flowId?: string;
  autoRefresh?: boolean;
  onExecutionComplete?: (execution: ExecutionData) => void;
}

export function ExecutionMonitor({
  executionId,
  flowId,
  autoRefresh = true,
  onExecutionComplete,
}: ExecutionMonitorProps) {
  const { toast } = useToast();
  const [execution, setExecution] = useState<ExecutionData | null>(null);
  const [loading, setLoading] = useState(false);
  const [isLive, setIsLive] = useState(autoRefresh);
  const intervalRef = useRef<NodeJS.Timeout>();
  const eventSourceRef = useRef<EventSource>();

  useEffect(() => {
    if (executionId) {
      loadExecution();
      if (isLive) {
        startLiveUpdates();
      }
    }

    return () => {
      stopLiveUpdates();
    };
  }, [executionId, isLive]);

  const loadExecution = async () => {
    if (!executionId) return;

    try {
      setLoading(true);
      // Mock data for demonstration
      const mockExecution: ExecutionData = {
        id: executionId,
        flowId: flowId || 'flow-1',
        flowName: '고객 지원 자동화',
        flowType: 'agentflow',
        status: 'running',
        startTime: new Date(Date.now() - 30000),
        steps: [
          {
            id: 'step-1',
            name: '입력 분석 에이전트',
            type: 'agent',
            status: 'completed',
            startTime: new Date(Date.now() - 30000),
            endTime: new Date(Date.now() - 25000),
            duration: 5000,
            metadata: {
              tokens_used: 150,
              cost_usd: 0.003,
              model: 'llama3.1:8b',
              provider: 'ollama',
            },
          },
          {
            id: 'step-2',
            name: '의도 분류',
            type: 'llm',
            status: 'completed',
            startTime: new Date(Date.now() - 25000),
            endTime: new Date(Date.now() - 20000),
            duration: 5000,
            metadata: {
              tokens_used: 200,
              cost_usd: 0.004,
              model: 'llama3.1:8b',
              provider: 'ollama',
            },
          },
          {
            id: 'step-3',
            name: '지식베이스 검색',
            type: 'tool',
            status: 'running',
            startTime: new Date(Date.now() - 20000),
            metadata: {
              tokens_used: 0,
              cost_usd: 0,
            },
          },
          {
            id: 'step-4',
            name: '응답 생성 에이전트',
            type: 'agent',
            status: 'pending',
          },
          {
            id: 'step-5',
            name: '품질 검증',
            type: 'condition',
            status: 'pending',
          },
        ],
        metrics: {
          totalSteps: 5,
          completedSteps: 2,
          failedSteps: 0,
          skippedSteps: 0,
          totalTokens: 350,
          totalCost: 0.007,
          averageStepDuration: 5000,
        },
        logs: [
          {
            timestamp: new Date(Date.now() - 30000),
            level: 'info',
            message: '실행 시작됨',
          },
          {
            timestamp: new Date(Date.now() - 25000),
            level: 'info',
            message: '입력 분석 완료: 고객 문의 유형 - 기술 지원',
          },
          {
            timestamp: new Date(Date.now() - 20000),
            level: 'info',
            message: '의도 분류 완료: 카테고리 - 계정 문제',
          },
          {
            timestamp: new Date(Date.now() - 15000),
            level: 'info',
            message: '지식베이스 검색 중...',
          },
        ],
      };

      setExecution(mockExecution);
    } catch (error: any) {
      toast({
        title: '오류',
        description: '실행 정보를 불러오는데 실패했습니다',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const startLiveUpdates = () => {
    if (!executionId) return;

    // Server-Sent Events for real-time updates
    eventSourceRef.current = new EventSource(
      `/api/agent-builder/executions/${executionId}/stream`
    );

    eventSourceRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setExecution(prev => prev ? { ...prev, ...data } : data);
      } catch (error) {
        console.error('Failed to parse SSE data:', error);
      }
    };

    eventSourceRef.current.onerror = () => {
      // Fallback to polling if SSE fails
      intervalRef.current = setInterval(loadExecution, 2000);
    };
  };

  const stopLiveUpdates = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = undefined;
    }
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = undefined;
    }
  };

  const toggleLiveUpdates = () => {
    setIsLive(!isLive);
    if (!isLive) {
      startLiveUpdates();
    } else {
      stopLiveUpdates();
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'running':
        return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-gray-400" />;
      case 'skipped':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50 dark:bg-green-950';
      case 'failed':
        return 'text-red-600 bg-red-50 dark:bg-red-950';
      case 'running':
        return 'text-blue-600 bg-blue-50 dark:bg-blue-950';
      case 'pending':
        return 'text-gray-600 bg-gray-50 dark:bg-gray-950';
      case 'skipped':
        return 'text-yellow-600 bg-yellow-50 dark:bg-yellow-950';
      default:
        return 'text-gray-600 bg-gray-50 dark:bg-gray-950';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'agent':
        return <Users className="h-4 w-4" />;
      case 'llm':
        return <MessageSquare className="h-4 w-4" />;
      case 'tool':
        return <Zap className="h-4 w-4" />;
      case 'condition':
        return <AlertCircle className="h-4 w-4" />;
      case 'loop':
        return <RefreshCw className="h-4 w-4" />;
      default:
        return <Activity className="h-4 w-4" />;
    }
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const formatCost = (cost?: number) => {
    if (!cost) return '$0.000';
    return `$${cost.toFixed(3)}`;
  };

  if (!execution) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-center">
            <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">
              {loading ? '실행 정보를 불러오는 중...' : '실행 정보가 없습니다'}
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const progress = (execution.metrics.completedSteps / execution.metrics.totalSteps) * 100;

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                {execution.flowType === 'agentflow' ? (
                  <Users className="h-5 w-5 text-purple-500" />
                ) : (
                  <MessageSquare className="h-5 w-5 text-blue-500" />
                )}
                {execution.flowName}
              </CardTitle>
              <CardDescription>
                실행 ID: {execution.id} • 시작: {execution.startTime.toLocaleTimeString()}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge className={getStatusColor(execution.status)}>
                {getStatusIcon(execution.status)}
                <span className="ml-1">{execution.status}</span>
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={toggleLiveUpdates}
              >
                {isLive ? (
                  <>
                    <Pause className="h-4 w-4 mr-1" />
                    일시정지
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-1" />
                    실시간
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Progress */}
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>진행률</span>
                <span>{execution.metrics.completedSteps}/{execution.metrics.totalSteps} 단계</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 rounded-lg bg-muted">
                <div className="text-2xl font-bold text-blue-600">
                  {formatDuration(execution.duration || (Date.now() - execution.startTime.getTime()))}
                </div>
                <div className="text-xs text-muted-foreground">실행 시간</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-muted">
                <div className="text-2xl font-bold text-green-600">
                  {execution.metrics.totalTokens.toLocaleString()}
                </div>
                <div className="text-xs text-muted-foreground">토큰 사용</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-muted">
                <div className="text-2xl font-bold text-purple-600">
                  {formatCost(execution.metrics.totalCost)}
                </div>
                <div className="text-xs text-muted-foreground">예상 비용</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-muted">
                <div className="text-2xl font-bold text-orange-600">
                  {formatDuration(execution.metrics.averageStepDuration)}
                </div>
                <div className="text-xs text-muted-foreground">평균 단계 시간</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detailed View */}
      <Tabs defaultValue="steps" className="space-y-4">
        <TabsList>
          <TabsTrigger value="steps">실행 단계</TabsTrigger>
          <TabsTrigger value="logs">로그</TabsTrigger>
          <TabsTrigger value="metrics">메트릭</TabsTrigger>
        </TabsList>

        <TabsContent value="steps">
          <Card>
            <CardHeader>
              <CardTitle>실행 단계</CardTitle>
              <CardDescription>
                각 단계의 상세 실행 정보를 확인하세요
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {execution.steps.map((step, index) => (
                  <div
                    key={step.id}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      step.status === 'running' 
                        ? 'border-blue-400 bg-blue-50 dark:bg-blue-950/20' 
                        : 'border-border'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-muted text-sm font-medium">
                          {index + 1}
                        </div>
                        <div className="flex items-center gap-2">
                          {getTypeIcon(step.type)}
                          <span className="font-medium">{step.name}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className={getStatusColor(step.status)}>
                          {getStatusIcon(step.status)}
                          <span className="ml-1">{step.status}</span>
                        </Badge>
                        {step.duration && (
                          <Badge variant="outline">
                            <Clock className="h-3 w-3 mr-1" />
                            {formatDuration(step.duration)}
                          </Badge>
                        )}
                      </div>
                    </div>

                    {step.metadata && (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3 text-sm">
                        {step.metadata.tokens_used && (
                          <div>
                            <span className="text-muted-foreground">토큰:</span>
                            <span className="ml-1 font-medium">{step.metadata.tokens_used}</span>
                          </div>
                        )}
                        {step.metadata.cost_usd && (
                          <div>
                            <span className="text-muted-foreground">비용:</span>
                            <span className="ml-1 font-medium">{formatCost(step.metadata.cost_usd)}</span>
                          </div>
                        )}
                        {step.metadata.model && (
                          <div>
                            <span className="text-muted-foreground">모델:</span>
                            <span className="ml-1 font-medium">{step.metadata.model}</span>
                          </div>
                        )}
                        {step.metadata.provider && (
                          <div>
                            <span className="text-muted-foreground">제공자:</span>
                            <span className="ml-1 font-medium">{step.metadata.provider}</span>
                          </div>
                        )}
                      </div>
                    )}

                    {step.error && (
                      <div className="mt-3 p-3 rounded bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800">
                        <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
                          <XCircle className="h-4 w-4" />
                          <span className="font-medium">오류</span>
                        </div>
                        <p className="text-sm text-red-600 dark:text-red-300 mt-1">{step.error}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logs">
          <Card>
            <CardHeader>
              <CardTitle>실행 로그</CardTitle>
              <CardDescription>
                실시간 실행 로그를 확인하세요
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96">
                <div className="space-y-2">
                  {execution.logs.map((log, index) => (
                    <div
                      key={index}
                      className={`p-3 rounded text-sm ${
                        log.level === 'error' 
                          ? 'bg-red-50 dark:bg-red-950/20 text-red-700 dark:text-red-300'
                          : log.level === 'warn'
                          ? 'bg-yellow-50 dark:bg-yellow-950/20 text-yellow-700 dark:text-yellow-300'
                          : 'bg-muted'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs text-muted-foreground">
                          {log.timestamp.toLocaleTimeString()}
                        </span>
                        <Badge variant="outline" className="text-xs">
                          {log.level}
                        </Badge>
                      </div>
                      <p>{log.message}</p>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="metrics">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                성능 메트릭
              </CardTitle>
              <CardDescription>
                실행 성능과 리소스 사용량을 분석하세요
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="font-medium">단계별 성능</h4>
                  <div className="space-y-2">
                    {execution.steps.filter(s => s.duration).map((step) => (
                      <div key={step.id} className="flex items-center justify-between">
                        <span className="text-sm">{step.name}</span>
                        <span className="text-sm font-medium">{formatDuration(step.duration)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-4">
                  <h4 className="font-medium">리소스 사용량</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm">총 토큰 사용량</span>
                      <span className="font-medium">{execution.metrics.totalTokens.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">예상 비용</span>
                      <span className="font-medium">{formatCost(execution.metrics.totalCost)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">평균 응답 시간</span>
                      <span className="font-medium">{formatDuration(execution.metrics.averageStepDuration)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}