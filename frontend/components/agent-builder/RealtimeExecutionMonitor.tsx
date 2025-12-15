'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Play, 
  Pause, 
  Square, 
  RotateCcw,
  Zap,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  Eye,
  Mic,
  FileText,
  Globe,
  AlertCircle,
  Activity,
  TrendingUp,
  Users
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';

interface ExecutionEvent {
  type: string;
  timestamp: string;
  data: any;
}

interface BlockProgress {
  blockId: string;
  blockName: string;
  blockType: string;
  progress: number;
  status: 'idle' | 'running' | 'completed' | 'error';
  message?: string;
  result?: any;
  startTime?: string;
  endTime?: string;
  duration?: number;
}

interface RealtimeExecutionMonitorProps {
  executionId?: string;
  onExecutionComplete?: (results: any) => void;
  onExecutionError?: (error: string) => void;
  className?: string;
}

export default function RealtimeExecutionMonitor({
  executionId,
  onExecutionComplete,
  onExecutionError,
  className
}: RealtimeExecutionMonitorProps) {
  const { toast } = useToast();
  const [isConnected, setIsConnected] = useState(false);
  const [executionStatus, setExecutionStatus] = useState<'idle' | 'running' | 'completed' | 'error' | 'cancelled'>('idle');
  const [overallProgress, setOverallProgress] = useState(0);
  const [blocks, setBlocks] = useState<BlockProgress[]>([]);
  const [events, setEvents] = useState<ExecutionEvent[]>([]);
  const [executionStats, setExecutionStats] = useState({
    totalBlocks: 0,
    completedBlocks: 0,
    startTime: null as string | null,
    estimatedDuration: 0,
    elapsedTime: 0
  });
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // 실시간 스트림 연결
  const connectToStream = useCallback((execId: string) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const eventSource = new EventSource(`/api/agent-builder/gemini-realtime/stream/${execId}`);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
      setExecutionStatus('running');
      toast({
        title: '실시간 모니터링 시작',
        description: '워크플로우 실행을 실시간으로 추적합니다.',
      });
    };

    eventSource.onmessage = (event) => {
      try {
        const eventData: ExecutionEvent = JSON.parse(event.data);
        handleExecutionEvent(eventData);
      } catch (error) {
        console.error('Failed to parse event data:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('EventSource error:', error);
      setIsConnected(false);
      
      if (eventSource.readyState === EventSource.CLOSED) {
        toast({
          title: '연결 종료',
          description: '실시간 모니터링이 종료되었습니다.',
          variant: 'destructive'
        });
      }
    };

    return eventSource;
  }, [toast]);

  // 실행 이벤트 처리
  const handleExecutionEvent = useCallback((event: ExecutionEvent) => {
    setEvents(prev => [...prev, event].slice(-50)); // 최근 50개 이벤트만 유지

    switch (event.type) {
      case 'execution_start':
        setExecutionStats(prev => ({
          ...prev,
          totalBlocks: event.data.total_blocks,
          startTime: event.timestamp,
          estimatedDuration: event.data.estimated_duration || 0
        }));
        
        // 타이머 시작
        if (timerRef.current) clearInterval(timerRef.current);
        timerRef.current = setInterval(() => {
          setExecutionStats(prev => ({
            ...prev,
            elapsedTime: prev.startTime ? 
              (Date.now() - new Date(prev.startTime).getTime()) / 1000 : 0
          }));
        }, 1000);
        break;

      case 'block_start':
        setBlocks(prev => {
          const updated = [...prev];
          const existingIndex = updated.findIndex(b => b.blockId === event.data.block_id);
          
          const blockData: BlockProgress = {
            blockId: event.data.block_id,
            blockName: event.data.block_name,
            blockType: event.data.block_type,
            progress: 0,
            status: 'running',
            startTime: event.timestamp
          };

          if (existingIndex >= 0) {
            updated[existingIndex] = blockData;
          } else {
            updated.push(blockData);
          }
          
          return updated;
        });
        break;

      case 'block_progress':
        setBlocks(prev => prev.map(block => 
          block.blockId === event.data.block_id
            ? {
                ...block,
                progress: event.data.progress * 100,
                message: event.data.message,
                result: event.data.result
              }
            : block
        ));
        break;

      case 'block_complete':
        setBlocks(prev => prev.map(block => 
          block.blockId === event.data.block_id
            ? {
                ...block,
                progress: 100,
                status: 'completed',
                endTime: event.timestamp
              }
            : block
        ));
        
        setExecutionStats(prev => ({
          ...prev,
          completedBlocks: event.data.completed_blocks
        }));
        
        setOverallProgress(event.data.progress * 100);
        break;

      case 'execution_complete':
        setExecutionStatus('completed');
        setOverallProgress(100);
        
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
        
        toast({
          title: '실행 완료',
          description: `워크플로우가 성공적으로 완료되었습니다. (${event.data.duration?.toFixed(1)}초)`,
        });
        
        onExecutionComplete?.(event.data.results);
        break;

      case 'error':
        setExecutionStatus('error');
        
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
        
        toast({
          title: '실행 오류',
          description: event.data.error,
          variant: 'destructive'
        });
        
        onExecutionError?.(event.data.error);
        break;

      case 'stream_end':
        setIsConnected(false);
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }
        break;
    }
  }, [onExecutionComplete, onExecutionError, toast]);

  // 데모 실행 시작
  const startDemoExecution = useCallback(async () => {
    try {
      const response = await fetch('/api/agent-builder/gemini-realtime/demo/quick-start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to start demo execution');
      }

      const data = await response.json();
      connectToStream(data.execution_id);
      
    } catch (error) {
      console.error('Failed to start demo execution:', error);
      toast({
        title: '실행 시작 실패',
        description: '데모 실행을 시작할 수 없습니다.',
        variant: 'destructive'
      });
    }
  }, [connectToStream, toast]);

  // 실행 취소
  const cancelExecution = useCallback(async () => {
    if (!executionId) return;

    try {
      const response = await fetch(`/api/agent-builder/gemini-realtime/cancel/${executionId}`, {
        method: 'POST',
      });

      if (response.ok) {
        setExecutionStatus('cancelled');
        toast({
          title: '실행 취소됨',
          description: '워크플로우 실행이 취소되었습니다.',
        });
      }
    } catch (error) {
      console.error('Failed to cancel execution:', error);
    }
  }, [executionId, toast]);

  // 컴포넌트 언마운트 시 정리
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  // executionId가 변경되면 스트림 연결
  useEffect(() => {
    if (executionId) {
      connectToStream(executionId);
    }
  }, [executionId, connectToStream]);

  const getBlockIcon = (blockType: string) => {
    switch (blockType) {
      case 'gemini_vision': return Eye;
      case 'gemini_audio': return Mic;
      case 'gemini_document': return FileText;
      case 'http_request': return Globe;
      default: return Zap;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'text-blue-600';
      case 'completed': return 'text-green-600';
      case 'error': return 'text-red-600';
      case 'cancelled': return 'text-gray-600';
      default: return 'text-gray-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <Loader2 className="h-4 w-4 animate-spin" />;
      case 'completed': return <CheckCircle2 className="h-4 w-4" />;
      case 'error': return <XCircle className="h-4 w-4" />;
      case 'cancelled': return <Square className="h-4 w-4" />;
      default: return <Clock className="h-4 w-4" />;
    }
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* 헤더 및 컨트롤 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                실시간 워크플로우 모니터
                {isConnected && (
                  <Badge variant="secondary" className="bg-green-100 text-green-700">
                    <div className="h-2 w-2 bg-green-500 rounded-full mr-1 animate-pulse" />
                    Live
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>
                멀티모달 워크플로우 실행을 실시간으로 모니터링합니다
              </CardDescription>
            </div>
            
            <div className="flex items-center gap-2">
              {executionStatus === 'idle' && (
                <Button onClick={startDemoExecution} className="gap-2">
                  <Play className="h-4 w-4" />
                  데모 시작
                </Button>
              )}
              
              {executionStatus === 'running' && (
                <Button onClick={cancelExecution} variant="destructive" className="gap-2">
                  <Square className="h-4 w-4" />
                  취소
                </Button>
              )}
              
              {(executionStatus === 'completed' || executionStatus === 'error') && (
                <Button onClick={() => window.location.reload()} variant="outline" className="gap-2">
                  <RotateCcw className="h-4 w-4" />
                  다시 시작
                </Button>
              )}
            </div>
          </div>
        </CardHeader>

        {/* 전체 진행률 */}
        {executionStatus !== 'idle' && (
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between text-sm">
                <span>전체 진행률</span>
                <span>{Math.round(overallProgress)}%</span>
              </div>
              <Progress value={overallProgress} className="h-2" />
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-blue-500" />
                  <span>진행률: {Math.round(overallProgress)}%</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-orange-500" />
                  <span>경과: {Math.round(executionStats.elapsedTime)}초</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  <span>완료: {executionStats.completedBlocks}/{executionStats.totalBlocks}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-purple-500" />
                  <span>상태: {executionStatus}</span>
                </div>
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* 블록 진행 상황 */}
      {blocks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">블록 실행 상태</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {blocks.map((block) => {
                const Icon = getBlockIcon(block.blockType);
                return (
                  <div key={block.blockId} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-gray-100 dark:bg-gray-800">
                          <Icon className="h-4 w-4" />
                        </div>
                        <div>
                          <h4 className="font-medium">{block.blockName}</h4>
                          <p className="text-sm text-muted-foreground">{block.blockType}</p>
                        </div>
                      </div>
                      
                      <div className={cn("flex items-center gap-2", getStatusColor(block.status))}>
                        {getStatusIcon(block.status)}
                        <span className="text-sm font-medium">{block.status}</span>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span>진행률</span>
                        <span>{Math.round(block.progress)}%</span>
                      </div>
                      <Progress value={block.progress} className="h-1" />
                      
                      {block.message && (
                        <p className="text-sm text-muted-foreground">{block.message}</p>
                      )}
                      
                      {block.result && (
                        <div className="mt-2 p-2 bg-gray-50 dark:bg-gray-900 rounded text-xs">
                          <strong>결과:</strong> {JSON.stringify(block.result, null, 2)}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 실시간 로그 */}
      {events.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">실시간 로그</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-64">
              <div className="space-y-2">
                {events.slice().reverse().map((event, index) => (
                  <div key={index} className="flex items-start gap-3 text-sm p-2 rounded border">
                    <Badge variant="outline" className="text-xs">
                      {event.type}
                    </Badge>
                    <div className="flex-1">
                      <p className="font-mono text-xs text-muted-foreground">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </p>
                      <p>{JSON.stringify(event.data, null, 2)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      {/* 빈 상태 */}
      {executionStatus === 'idle' && (
        <Card>
          <CardContent className="text-center py-12">
            <Activity className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-semibold mb-2">실시간 모니터링 준비됨</h3>
            <p className="text-muted-foreground mb-6">
              데모를 시작하거나 워크플로우를 실행하여 실시간 진행 상황을 확인하세요
            </p>
            <Button onClick={startDemoExecution} className="gap-2">
              <Play className="h-4 w-4" />
              데모 워크플로우 실행
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}