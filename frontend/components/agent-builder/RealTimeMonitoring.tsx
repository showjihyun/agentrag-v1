'use client';

import React, { useState, useEffect, useRef, useCallback, useMemo, Profiler } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  Activity,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RotateCcw,
  Zap,
  Users,
  BarChart3,
  TrendingUp,
  RefreshCw,
} from 'lucide-react';

import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { onRenderCallback } from '@/lib/utils/performance';

interface ExecutionLog {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
  agent_id?: string;
  agent_name?: string;
  duration_ms?: number;
  metadata?: Record<string, any>;
}

interface AgentStatus {
  id: string;
  name: string;
  status: 'idle' | 'running' | 'completed' | 'failed' | 'waiting';
  progress: number;
  current_task?: string;
  start_time?: string;
  duration_ms?: number;
  error_message?: string;
  output?: any;
  confidence_score?: number;
  resource_usage?: {
    cpu_percent: number;
    memory_mb: number;
    tokens_used: number;
  };
}

interface WorkflowMetrics {
  total_executions: number;
  success_rate: number;
  average_duration_ms: number;
  active_agents: number;
  completed_agents: number;
  failed_agents: number;
  tokens_used: number;
  cost_estimate: number;
  // Enhanced metrics
  prediction_accuracy: number;
  resource_efficiency: number;
  speedup_factor: number;
  optimization_score: number;
}

interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  active_connections: number;
  timestamp: string;
}

interface ExecutionPrediction {
  estimated_duration: number;
  actual_duration?: number;
  accuracy?: number;
  confidence: number;
  recommended_concurrency: number;
}

interface OptimizationInsight {
  type: 'performance' | 'cost' | 'reliability' | 'resource';
  title: string;
  description: string;
  impact: 'low' | 'medium' | 'high';
  priority: 'low' | 'medium' | 'high';
  action?: string;
}

interface RealTimeMonitoringProps {
  agentflowId: string;
  executionId?: string;
  autoRefresh?: boolean;
}

export function RealTimeMonitoring({
  agentflowId,
  executionId,
  autoRefresh = true,
}: RealTimeMonitoringProps) {
  const [isConnected, setIsConnected] = useState(false);
  const [logs, setLogs] = useState<ExecutionLog[]>([]);
  const [agentStatuses, setAgentStatuses] = useState<AgentStatus[]>([]);
  const [metrics, setMetrics] = useState<WorkflowMetrics | null>(null);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [prediction, setPrediction] = useState<ExecutionPrediction | null>(null);
  const [optimizationInsights, setOptimizationInsights] = useState<OptimizationInsight[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [filterLevel, setFilterLevel] = useState<string>('all');
  const [showPredictions, setShowPredictions] = useState(true);
  const [showOptimizations, setShowOptimizations] = useState(true);
  const eventSourceRef = useRef<EventSource | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Fetch initial data (for potential future use)
  useQuery({
    queryKey: ['agentflow', agentflowId],
    queryFn: () => agentBuilderAPI.getAgentflow(agentflowId),
    enabled: !!agentflowId,
  });

  // Auto-scroll logs to bottom
  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [logs]);

  // Setup Server-Sent Events for real-time updates
  useEffect(() => {
    if (!agentflowId || !autoRefresh) return;

    const setupSSE = () => {
      const url = executionId
        ? `/api/agent-builder/agentflows/${agentflowId}/executions/${executionId}/stream`
        : `/api/agent-builder/agentflows/${agentflowId}/monitor`;

      eventSourceRef.current = new EventSource(`http://127.0.0.1:8000${url}`);

      eventSourceRef.current.onopen = () => {
        setIsConnected(true);
        console.log('SSE connection established');
      };

      eventSourceRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as {
            type: string;
            payload: any;
          };
          
          switch (data.type) {
            case 'log':
              setLogs(prev => [...prev, data.payload as ExecutionLog]);
              break;
            case 'agent_status':
              setAgentStatuses(prev => {
                const existing = prev.find(a => a.id === data.payload.id);
                if (existing) {
                  return prev.map(a => a.id === data.payload.id ? { ...a, ...data.payload } : a);
                }
                return [...prev, data.payload as AgentStatus];
              });
              break;
            case 'metrics':
              setMetrics(data.payload as WorkflowMetrics);
              break;
            case 'system_metrics':
              setSystemMetrics(data.payload as SystemMetrics);
              break;
            case 'prediction':
              setPrediction(data.payload as ExecutionPrediction);
              break;
            case 'optimization_insights':
              setOptimizationInsights(data.payload as OptimizationInsight[]);
              break;
            case 'execution_complete':
              addLog({
                id: `complete-${Date.now()}`,
                timestamp: new Date().toISOString(),
                level: 'success',
                message: `워크플로우 실행 완료 - 총 소요시간: ${data.payload.duration_ms}ms`,
                metadata: data.payload,
              });
              // Update final metrics
              if (data.payload.final_metrics) {
                setMetrics(data.payload.final_metrics as WorkflowMetrics);
              }
              break;
            case 'execution_failed':
              addLog({
                id: `failed-${Date.now()}`,
                timestamp: new Date().toISOString(),
                level: 'error',
                message: `워크플로우 실행 실패: ${data.payload.error}`,
                metadata: data.payload,
              });
              break;
            default:
              console.warn('Unknown SSE event type:', data.type);
          }
        } catch (error) {
          console.error('Failed to parse SSE data:', error);
        }
      };

      eventSourceRef.current.onerror = (error) => {
        console.error('SSE connection error:', error);
        setIsConnected(false);
        
        // Attempt to reconnect after 5 seconds
        setTimeout(() => {
          if (eventSourceRef.current?.readyState === EventSource.CLOSED) {
            setupSSE();
          }
        }, 5000);
      };
    };

    setupSSE();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        setIsConnected(false);
      }
    };
  }, [agentflowId, executionId, autoRefresh]);

  // Helper function to add logs
  const addLog = (log: ExecutionLog) => {
    setLogs(prev => [...prev, log]);
  };

  // Clear logs with useCallback for performance
  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  // Get status color with useMemo for performance
  const getStatusColor = useCallback((status: string) => {
    switch (status) {
      case 'running':
        return 'bg-blue-500';
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      case 'waiting':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  }, []);

  // Get log level icon and color with useMemo for performance
  const getLogLevelIcon = useCallback((level: string) => {
    switch (level) {
      case 'success':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'warning':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      default:
        return <Activity className="w-4 h-4 text-blue-500" />;
    }
  }, []);

  // Format duration with useCallback for performance
  const formatDuration = useCallback((ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  }, []);

  // Memoize filtered logs for performance
  const filteredLogs = useMemo(() => {
    return logs.filter(log => filterLevel === 'all' || log.level === filterLevel);
  }, [logs, filterLevel]);

  // Memoize agent status calculations
  const agentStatusSummary = useMemo(() => {
    const running = agentStatuses.filter(a => a.status === 'running').length;
    const completed = agentStatuses.filter(a => a.status === 'completed').length;
    const failed = agentStatuses.filter(a => a.status === 'failed').length;
    const waiting = agentStatuses.filter(a => a.status === 'waiting').length;
    const completionRate = agentStatuses.length > 0 
      ? (completed / agentStatuses.length) * 100 
      : 0;

    return { running, completed, failed, waiting, completionRate };
  }, [agentStatuses]);

  return (
    <Profiler id="RealTimeMonitoring" onRender={onRenderCallback}>
      <div className="space-y-4">
      {/* Connection Status & Controls */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              <Activity className="w-5 h-5" />
              실시간 모니터링
            </CardTitle>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm text-muted-foreground">
                  {isConnected ? '연결됨' : '연결 끊김'}
                </span>
              </div>
              
              {/* Toggle Controls */}
              <div className="flex items-center gap-4 text-sm">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={showPredictions}
                    onChange={(e) => setShowPredictions(e.target.checked)}
                    className="rounded"
                  />
                  예측 표시
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={showOptimizations}
                    onChange={(e) => setShowOptimizations(e.target.checked)}
                    className="rounded"
                  />
                  최적화 제안
                </label>
              </div>
              
              <Button
                size="sm"
                variant="outline"
                onClick={() => window.location.reload()}
              >
                <RefreshCw className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">개요</TabsTrigger>
          <TabsTrigger value="agents">에이전트</TabsTrigger>
          <TabsTrigger value="logs">로그</TabsTrigger>
          <TabsTrigger value="metrics">메트릭</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          {/* Enhanced Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">활성 에이전트</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {agentStatuses.filter(a => a.status === 'running').length}
                </div>
                <p className="text-xs text-muted-foreground">
                  총 {agentStatuses.length}개 중
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">완료율</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {agentStatuses.length > 0
                    ? Math.round((agentStatuses.filter(a => a.status === 'completed').length / agentStatuses.length) * 100)
                    : 0}%
                </div>
                <Progress
                  value={agentStatuses.length > 0
                    ? (agentStatuses.filter(a => a.status === 'completed').length / agentStatuses.length) * 100
                    : 0}
                  className="mt-2"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">평균 실행 시간</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {metrics?.average_duration_ms
                    ? formatDuration(metrics.average_duration_ms)
                    : '0ms'}
                </div>
                <p className="text-xs text-muted-foreground">
                  최근 실행 기준
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">최적화 점수</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">
                  {metrics?.optimization_score ? `${(metrics.optimization_score * 100).toFixed(0)}` : 'N/A'}
                </div>
                <p className="text-xs text-muted-foreground">
                  성능 최적화 지수
                </p>
              </CardContent>
            </Card>
          </div>

          {/* System Status & Predictions */}
          {(showPredictions && prediction) || systemMetrics ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {showPredictions && prediction && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm flex items-center gap-2">
                      <TrendingUp className="w-4 h-4" />
                      실행 예측
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>예상 소요시간:</span>
                      <span className="font-medium">{formatDuration(prediction.estimated_duration * 1000)}</span>
                    </div>
                    {prediction.actual_duration && (
                      <div className="flex justify-between text-sm">
                        <span>실제 소요시간:</span>
                        <span className="font-medium">{formatDuration(prediction.actual_duration * 1000)}</span>
                      </div>
                    )}
                    <div className="flex justify-between text-sm">
                      <span>예측 정확도:</span>
                      <span className={`font-medium ${
                        (prediction.accuracy || 0) > 0.8 ? 'text-green-600' : 
                        (prediction.accuracy || 0) > 0.6 ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        {prediction.accuracy ? `${(prediction.accuracy * 100).toFixed(1)}%` : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>권장 동시성:</span>
                      <span className="font-medium">{prediction.recommended_concurrency}</span>
                    </div>
                  </CardContent>
                </Card>
              )}
              
              {systemMetrics && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm flex items-center gap-2">
                      <BarChart3 className="w-4 h-4" />
                      시스템 상태
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>CPU 사용률:</span>
                      <span className={`font-medium ${
                        systemMetrics.cpu_usage > 80 ? 'text-red-600' : 
                        systemMetrics.cpu_usage > 60 ? 'text-yellow-600' : 'text-green-600'
                      }`}>
                        {systemMetrics.cpu_usage.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>메모리 사용률:</span>
                      <span className={`font-medium ${
                        systemMetrics.memory_usage > 90 ? 'text-red-600' : 
                        systemMetrics.memory_usage > 75 ? 'text-yellow-600' : 'text-green-600'
                      }`}>
                        {systemMetrics.memory_usage.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>활성 연결:</span>
                      <span className="font-medium">{systemMetrics.active_connections}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>업데이트:</span>
                      <span className="text-gray-500">{new Date(systemMetrics.timestamp).toLocaleTimeString()}</span>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          ) : null}

          {/* Optimization Insights */}
          {showOptimizations && optimizationInsights.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Zap className="w-4 h-4" />
                  최적화 제안
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {optimizationInsights.map((insight, index) => (
                    <div key={index} className="flex items-start gap-3 p-3 border rounded-lg">
                      <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                        {insight.type === 'performance' && <Zap className="w-4 h-4 text-blue-600" />}
                        {insight.type === 'cost' && <TrendingUp className="w-4 h-4 text-green-600" />}
                        {insight.type === 'reliability' && <CheckCircle2 className="w-4 h-4 text-purple-600" />}
                        {insight.type === 'resource' && <BarChart3 className="w-4 h-4 text-orange-600" />}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-sm">{insight.title}</span>
                          <Badge 
                            variant={insight.impact === 'high' ? 'destructive' : 
                                    insight.impact === 'medium' ? 'default' : 'secondary'}
                            className="text-xs"
                          >
                            {insight.impact} 임팩트
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {insight.priority} 우선순위
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600">{insight.description}</p>
                        {insight.action && (
                          <Button variant="link" size="sm" className="p-0 h-auto mt-1">
                            {insight.action}
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">최근 활동</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-48">
                <div className="space-y-2">
                  {logs.slice(-10).map((log) => (
                    <div key={log.id} className="flex items-start gap-3 p-2 rounded-lg bg-muted/50">
                      {getLogLevelIcon(log.level)}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm">{log.message}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-muted-foreground">
                            {new Date(log.timestamp).toLocaleTimeString()}
                          </span>
                          {log.agent_name && (
                            <Badge variant="outline" className="text-xs">
                              {log.agent_name}
                            </Badge>
                          )}
                          {log.duration_ms && (
                            <Badge variant="secondary" className="text-xs">
                              {formatDuration(log.duration_ms)}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Agents Tab */}
        <TabsContent value="agents" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {agentStatuses.map((agent) => (
              <Card
                key={agent.id}
                className={`cursor-pointer transition-all ${
                  selectedAgent === agent.id ? 'ring-2 ring-blue-500' : ''
                }`}
                onClick={() => setSelectedAgent(agent.id)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                      <Users className="w-4 h-4" />
                      {agent.name}
                    </CardTitle>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="outline"
                        className={`${getStatusColor(agent.status)} text-white border-0`}
                      >
                        {agent.status}
                      </Badge>
                      {agent.confidence_score && (
                        <Badge variant="outline" className="text-xs">
                          신뢰도: {(agent.confidence_score * 100).toFixed(0)}%
                        </Badge>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>진행률</span>
                        <span>{agent.progress}%</span>
                      </div>
                      <Progress value={agent.progress} className="h-2" />
                    </div>
                    
                    {agent.current_task && (
                      <p className="text-xs text-muted-foreground">
                        현재 작업: {agent.current_task}
                      </p>
                    )}
                    
                    <div className="grid grid-cols-2 gap-4 text-xs text-muted-foreground">
                      {agent.start_time && (
                        <span>시작: {new Date(agent.start_time).toLocaleTimeString()}</span>
                      )}
                      {agent.duration_ms && (
                        <span>소요: {formatDuration(agent.duration_ms)}</span>
                      )}
                    </div>
                    
                    {/* Resource Usage */}
                    {agent.resource_usage && (
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div className="text-center p-2 bg-gray-50 rounded">
                          <div className="font-medium">{agent.resource_usage.cpu_percent.toFixed(1)}%</div>
                          <div className="text-gray-500">CPU</div>
                        </div>
                        <div className="text-center p-2 bg-gray-50 rounded">
                          <div className="font-medium">{agent.resource_usage.memory_mb.toFixed(0)}MB</div>
                          <div className="text-gray-500">메모리</div>
                        </div>
                        <div className="text-center p-2 bg-gray-50 rounded">
                          <div className="font-medium">{agent.resource_usage.tokens_used.toLocaleString()}</div>
                          <div className="text-gray-500">토큰</div>
                        </div>
                      </div>
                    )}
                    
                    {agent.error_message && (
                      <div className="p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                        {agent.error_message}
                      </div>
                    )}
                    
                    {selectedAgent === agent.id && agent.output && (
                      <div className="mt-3 p-3 bg-gray-50 rounded">
                        <div className="text-sm font-medium mb-2">출력 결과:</div>
                        <pre className="text-xs overflow-auto max-h-40">
                          {JSON.stringify(agent.output, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Logs Tab */}
        <TabsContent value="logs" className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h3 className="text-lg font-semibold">실행 로그</h3>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">로그 레벨:</span>
                <select
                  value={filterLevel}
                  onChange={(e) => setFilterLevel(e.target.value)}
                  className="text-sm border rounded px-2 py-1"
                >
                  <option value="all">전체</option>
                  <option value="info">정보</option>
                  <option value="warning">경고</option>
                  <option value="error">오류</option>
                  <option value="success">성공</option>
                </select>
              </div>
              <div className="text-sm text-gray-500">
                {logs.filter(log => filterLevel === 'all' || log.level === filterLevel).length}개 로그 (전체 {logs.length}개)
              </div>
            </div>
            <Button size="sm" variant="outline" onClick={clearLogs}>
              <RotateCcw className="w-4 h-4 mr-2" />
              로그 지우기
            </Button>
          </div>
          
          <Card>
            <CardContent className="p-0">
              <ScrollArea className="h-96">
                <div className="p-4 space-y-2">
                  {logs
                    .filter(log => filterLevel === 'all' || log.level === filterLevel)
                    .map((log) => (
                    <div
                      key={log.id}
                      className="flex items-start gap-3 p-3 rounded-lg border bg-card hover:bg-muted/50 transition-colors"
                    >
                      {getLogLevelIcon(log.level)}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs text-muted-foreground font-mono">
                            {new Date(log.timestamp).toLocaleString()}
                          </span>
                          {log.agent_name && (
                            <Badge variant="outline" className="text-xs">
                              {log.agent_name}
                            </Badge>
                          )}
                          {log.duration_ms && (
                            <Badge variant="secondary" className="text-xs">
                              {formatDuration(log.duration_ms)}
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm">{log.message}</p>
                        {log.metadata && Object.keys(log.metadata).length > 0 && (
                          <details className="mt-2">
                            <summary className="text-xs text-muted-foreground cursor-pointer">
                              메타데이터 보기
                            </summary>
                            <pre className="text-xs bg-muted p-2 rounded mt-1 overflow-x-auto">
                              {JSON.stringify(log.metadata, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    </div>
                  ))}
                  <div ref={logsEndRef} />
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Enhanced Metrics Tab */}
        <TabsContent value="metrics" className="space-y-4">
          {metrics && (
            <>
              {/* Basic Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                      <BarChart3 className="w-4 h-4" />
                      총 실행 횟수
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{metrics.total_executions}</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                      <TrendingUp className="w-4 h-4" />
                      성공률
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{(metrics.success_rate * 100).toFixed(1)}%</div>
                    <Progress value={metrics.success_rate * 100} className="mt-2" />
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                      <Zap className="w-4 h-4" />
                      토큰 사용량
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{metrics.tokens_used.toLocaleString()}</div>
                    <p className="text-xs text-muted-foreground">
                      예상 비용: ${metrics.cost_estimate.toFixed(4)}
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      평균 실행 시간
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {formatDuration(metrics.average_duration_ms)}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Advanced Performance Metrics */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">고급 성능 지표</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-blue-600">
                        {metrics.prediction_accuracy ? `${(metrics.prediction_accuracy * 100).toFixed(1)}%` : 'N/A'}
                      </div>
                      <div className="text-sm text-gray-500 mt-1">예측 정확도</div>
                      <div className="text-xs text-gray-400 mt-1">
                        실행 시간 예측의 정확성
                      </div>
                      <Progress 
                        value={metrics.prediction_accuracy ? metrics.prediction_accuracy * 100 : 0} 
                        className="mt-2 h-2" 
                      />
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-green-600">
                        {metrics.resource_efficiency ? `${(metrics.resource_efficiency * 100).toFixed(1)}%` : 'N/A'}
                      </div>
                      <div className="text-sm text-gray-500 mt-1">리소스 효율성</div>
                      <div className="text-xs text-gray-400 mt-1">
                        CPU/메모리 사용 최적화
                      </div>
                      <Progress 
                        value={metrics.resource_efficiency ? metrics.resource_efficiency * 100 : 0} 
                        className="mt-2 h-2" 
                      />
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-purple-600">
                        {metrics.speedup_factor ? `${metrics.speedup_factor.toFixed(1)}x` : 'N/A'}
                      </div>
                      <div className="text-sm text-gray-500 mt-1">속도 향상</div>
                      <div className="text-xs text-gray-400 mt-1">
                        순차 실행 대비 개선
                      </div>
                      <div className="mt-2 text-xs text-purple-600">
                        {metrics.speedup_factor && metrics.speedup_factor > 2 ? '우수' : 
                         metrics.speedup_factor && metrics.speedup_factor > 1.5 ? '양호' : '개선 필요'}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-orange-600">
                        {metrics.optimization_score ? `${(metrics.optimization_score * 100).toFixed(0)}` : 'N/A'}
                      </div>
                      <div className="text-sm text-gray-500 mt-1">최적화 점수</div>
                      <div className="text-xs text-gray-400 mt-1">
                        전체 성능 최적화 지수
                      </div>
                      <Progress 
                        value={metrics.optimization_score ? metrics.optimization_score * 100 : 0} 
                        className="mt-2 h-2" 
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Agent Status Breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">에이전트 현황</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex justify-between">
                      <span>활성 에이전트:</span>
                      <span className="font-medium text-blue-600">{metrics.active_agents || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>완료된 에이전트:</span>
                      <span className="font-medium text-green-600">{metrics.completed_agents || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>실패한 에이전트:</span>
                      <span className="font-medium text-red-600">{metrics.failed_agents || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>대기 중인 에이전트:</span>
                      <span className="font-medium text-yellow-600">
                        {agentStatuses.filter(a => a.status === 'waiting').length}
                      </span>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">성능 요약</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex justify-between">
                      <span>평균 응답 시간:</span>
                      <span className="font-medium">{formatDuration(metrics.average_duration_ms)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>처리량 (req/min):</span>
                      <span className="font-medium">
                        {metrics.average_duration_ms > 0 ? (60000 / metrics.average_duration_ms).toFixed(1) : '0'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>에러율:</span>
                      <span className="font-medium text-red-600">
                        {((1 - metrics.success_rate) * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>비용 효율성:</span>
                      <span className="font-medium">
                        {metrics.tokens_used > 0 ? (metrics.tokens_used / metrics.cost_estimate).toFixed(0) : '0'} tokens/$
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
    </Profiler>
  );
}