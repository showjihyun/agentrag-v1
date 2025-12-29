'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  Play,
  Square,
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Loader2,
  Download,
  RefreshCw,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { flowsAPI } from '@/lib/api/flows';

interface ExecutionStep {
  id: string;
  agent_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  input?: any;
  output?: any;
  error?: string;
}

interface LocalExecutionStep {
  id: string;
  agent_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  input?: any;
  output?: string;
  error?: string;
}

interface ExecutionState {
  id?: string;
  status: 'idle' | 'running' | 'completed' | 'failed';
  started_at?: string;
  completed_at?: string;
  steps: LocalExecutionStep[];
  result?: any;
  error?: string;
}

export default function AgentflowExecutePage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const { toast } = useToast();
  
  // Unwrap params using React.use()
  const { id } = React.use(params);
  
  const [input, setInput] = useState('');
  const [execution, setExecution] = useState<ExecutionState>({
    status: 'idle',
    steps: [],
  });

  const { data: flowData, isLoading } = useQuery({
    queryKey: ['agentflow', id],
    queryFn: () => flowsAPI.getFlow(id),
  });

  const flow = flowData as any;

  const handleExecute = async () => {
    if (!input.trim()) {
      toast({
        title: '입력 필요',
        description: '실행할 입력을 제공해주세요',
        variant: 'destructive',
      });
      return;
    }

    try {
      setExecution({
        status: 'running',
        started_at: new Date().toISOString(),
        steps: [],
      });

      // 시뮬레이션된 실행 과정
      const agents = flow?.agents || [
        { name: '데이터 수집 에이전트', role: 'collector' },
        { name: '분석 에이전트', role: 'analyzer' },
        { name: '결과 생성 에이전트', role: 'generator' },
      ];

      for (let i = 0; i < agents.length; i++) {
        const agent = agents[i];
        const stepId = `step-${i + 1}`;
        
        // 단계 시작
        setExecution(prev => ({
          ...prev,
          steps: [
            ...prev.steps,
            {
              id: stepId,
              agent_name: agent.name,
              status: 'running',
              started_at: new Date().toISOString(),
            }
          ]
        }));

        // 시뮬레이션 지연
        await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 3000));

        // 단계 완료 (90% 성공률)
        const success = Math.random() > 0.1;
        
        setExecution(prev => ({
          ...prev,
          steps: prev.steps.map(step => 
            step.id === stepId 
              ? {
                  ...step,
                  status: (success ? 'completed' : 'failed') as LocalExecutionStep['status'],
                  completed_at: new Date().toISOString(),
                  duration_ms: 2000 + Math.random() * 3000,
                  ...(success 
                    ? { output: `${agent.name} 처리 완료` }
                    : { error: `${agent.name} 처리 중 오류 발생` }
                  ),
                }
              : step
          )
        }));

        if (!success) {
          setExecution(prev => ({
            ...prev,
            status: 'failed',
            completed_at: new Date().toISOString(),
            error: `${agent.name}에서 실행이 실패했습니다`,
          }));
          return;
        }
      }

      // 전체 실행 완료
      setExecution(prev => ({
        ...prev,
        status: 'completed',
        completed_at: new Date().toISOString(),
        result: {
          message: 'Agentflow 실행이 성공적으로 완료되었습니다',
          processed_input: input,
          agents_executed: agents.length,
          total_duration: prev.steps.reduce((sum, step) => sum + (step.duration_ms || 0), 0),
        }
      }));

      toast({
        title: '실행 완료',
        description: 'Agentflow가 성공적으로 실행되었습니다',
      });

    } catch (error: any) {
      setExecution(prev => ({
        ...prev,
        status: 'failed',
        completed_at: new Date().toISOString(),
        error: error.message || '실행 중 오류가 발생했습니다',
      }));

      toast({
        title: '실행 실패',
        description: error.message || '실행 중 오류가 발생했습니다',
        variant: 'destructive',
      });
    }
  };

  const handleStop = () => {
    setExecution(prev => ({
      ...prev,
      status: 'failed',
      completed_at: new Date().toISOString(),
      error: '사용자에 의해 중단되었습니다',
    }));
  };

  const handleReset = () => {
    setExecution({
      status: 'idle',
      steps: [],
    });
    setInput('');
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-gray-400" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'border-blue-500 bg-blue-50 dark:bg-blue-950/20';
      case 'completed':
        return 'border-green-500 bg-green-50 dark:bg-green-950/20';
      case 'failed':
        return 'border-red-500 bg-red-50 dark:bg-red-950/20';
      default:
        return 'border-gray-200 bg-gray-50 dark:bg-gray-900/20';
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto p-6 max-w-6xl">
        <Skeleton className="h-12 w-full mb-6" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!flow) {
    return (
      <div className="container mx-auto p-6 max-w-6xl">
        <Card className="border-red-500">
          <CardContent className="pt-6">
            <p className="text-red-500">Agentflow를 불러오는데 실패했습니다</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
              <Activity className="h-7 w-7 text-purple-600 dark:text-purple-400" />
            </div>
            {flow.name} 실행
          </h1>
          <p className="text-muted-foreground mt-1">{flow.description || '설명 없음'}</p>
        </div>
        <div className="flex gap-2">
          {execution.status === 'running' ? (
            <Button variant="destructive" onClick={handleStop}>
              <Square className="h-4 w-4 mr-2" />
              중단
            </Button>
          ) : (
            <>
              {execution.status !== 'idle' && (
                <Button variant="outline" onClick={handleReset}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  초기화
                </Button>
              )}
              <Button 
                onClick={handleExecute}
                disabled={execution.status !== 'idle'}
                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
              >
                <Play className="h-4 w-4 mr-2" />
                실행
              </Button>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Section */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>입력</CardTitle>
              <CardDescription>Agentflow에 전달할 입력을 작성하세요</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="input">실행 입력</Label>
                <Textarea
                  id="input"
                  placeholder="예: 최신 AI 트렌드에 대한 보고서를 작성해주세요"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  rows={6}
                  disabled={execution.status === 'running'}
                />
              </div>
              
              {/* Flow Info */}
              <Separator />
              <div className="space-y-2">
                <h4 className="font-medium">Flow 정보</h4>
                <div className="text-sm text-muted-foreground space-y-1">
                  <p>오케스트레이션: {flow.orchestration_type}</p>
                  <p>에이전트 수: {flow.agents?.length || 0}개</p>
                  <p>상태: {flow.is_active ? '활성' : '비활성'}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Execution Section */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    실행 상태
                    {execution.status === 'running' && (
                      <Badge variant="secondary" className="animate-pulse">
                        <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                        실행 중
                      </Badge>
                    )}
                    {execution.status === 'completed' && (
                      <Badge className="bg-green-500">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        완료
                      </Badge>
                    )}
                    {execution.status === 'failed' && (
                      <Badge variant="destructive">
                        <XCircle className="h-3 w-3 mr-1" />
                        실패
                      </Badge>
                    )}
                  </CardTitle>
                  <CardDescription>
                    {execution.started_at && (
                      <>시작: {new Date(execution.started_at).toLocaleString()}</>
                    )}
                    {execution.completed_at && (
                      <> | 완료: {new Date(execution.completed_at).toLocaleString()}</>
                    )}
                  </CardDescription>
                </div>
                {execution.status === 'completed' && (
                  <Button variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-2" />
                    결과 다운로드
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {execution.status === 'idle' ? (
                <div className="text-center py-12 text-muted-foreground">
                  <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>실행 버튼을 클릭하여 Agentflow를 시작하세요</p>
                </div>
              ) : (
                <ScrollArea className="h-[400px]">
                  <div className="space-y-4">
                    {/* Execution Steps */}
                    {execution.steps.map((step, index) => (
                      <Card key={step.id} className={`border-2 ${getStatusColor(step.status)}`}>
                        <CardContent className="pt-4">
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 mt-1">
                              {getStatusIcon(step.status)}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between">
                                <h4 className="font-medium">{step.agent_name}</h4>
                                <Badge variant="outline" className="text-xs">
                                  Step {index + 1}
                                </Badge>
                              </div>
                              {step.started_at && (
                                <p className="text-xs text-muted-foreground mt-1">
                                  시작: {new Date(step.started_at).toLocaleTimeString()}
                                  {step.duration_ms && (
                                    <> | 소요시간: {(step.duration_ms / 1000).toFixed(1)}초</>
                                  )}
                                </p>
                              )}
                              {step.output && (
                                <div className="mt-2 p-2 bg-green-50 dark:bg-green-950/20 rounded text-sm">
                                  {step.output}
                                </div>
                              )}
                              {step.error && (
                                <div className="mt-2 p-2 bg-red-50 dark:bg-red-950/20 rounded text-sm text-red-700 dark:text-red-300">
                                  {step.error}
                                </div>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}

                    {/* Final Result */}
                    {execution.result && (
                      <Card className="border-2 border-green-500 bg-green-50 dark:bg-green-950/20">
                        <CardHeader>
                          <CardTitle className="text-green-700 dark:text-green-300 flex items-center gap-2">
                            <CheckCircle className="h-5 w-5" />
                            실행 결과
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <p className="font-medium">{execution.result.message}</p>
                            <div className="text-sm text-muted-foreground">
                              <p>처리된 입력: {execution.result.processed_input}</p>
                              <p>실행된 에이전트: {execution.result.agents_executed}개</p>
                              <p>총 소요시간: {(execution.result.total_duration / 1000).toFixed(1)}초</p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    {/* Error */}
                    {execution.error && (
                      <Card className="border-2 border-red-500 bg-red-50 dark:bg-red-950/20">
                        <CardContent className="pt-4">
                          <div className="flex items-start gap-3">
                            <AlertTriangle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                            <div>
                              <h4 className="font-medium text-red-700 dark:text-red-300">실행 오류</h4>
                              <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                                {execution.error}
                              </p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )}
                  </div>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}