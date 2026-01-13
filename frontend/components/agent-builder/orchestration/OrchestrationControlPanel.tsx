'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Settings,
  Play,
  Pause,
  Square,
  RotateCcw,
  Users,
  MessageSquare,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Clock,
  Zap,
  Brain,
  Eye,
  Activity,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  ORCHESTRATION_TYPES,
  type OrchestrationTypeValue,
  type SupervisorConfig,
} from '@/lib/constants/orchestration';
import { PatternPreviewCanvas } from './PatternPreviewCanvas';

interface OrchestrationControlPanelProps {
  orchestrationType: OrchestrationTypeValue;
  supervisorConfig?: SupervisorConfig;
  onConfigChange?: (config: any) => void;
  onExecutionStart?: () => void;
  onExecutionPause?: () => void;
  onExecutionStop?: () => void;
  onExecutionReset?: () => void;
  
  // 실행 상태
  isExecuting?: boolean;
  isPaused?: boolean;
  executionStatus?: 'idle' | 'running' | 'paused' | 'completed' | 'failed';
  
  // 실시간 메트릭
  activeAgents?: number;
  totalAgents?: number;
  completedTasks?: number;
  failedTasks?: number;
  averageResponseTime?: number;
  tokenUsage?: number;
  
  // Agent 상태
  agentStatuses?: Record<string, {
    status: 'idle' | 'running' | 'completed' | 'failed';
    currentTask?: string;
    progress?: number;
  }>;
  
  // 통신 메트릭
  communicationCount?: number;
  consensusProgress?: number;
  
  className?: string;
}

export const OrchestrationControlPanel: React.FC<OrchestrationControlPanelProps> = ({
  orchestrationType,
  supervisorConfig,
  onConfigChange,
  onExecutionStart,
  onExecutionPause,
  onExecutionStop,
  onExecutionReset,
  isExecuting = false,
  isPaused = false,
  executionStatus = 'idle',
  activeAgents = 0,
  totalAgents = 0,
  completedTasks = 0,
  failedTasks = 0,
  averageResponseTime = 0,
  tokenUsage = 0,
  agentStatuses = {},
  communicationCount = 0,
  consensusProgress = 0,
  className,
}) => {
  const [showPreview, setShowPreview] = useState(false);
  const pattern = ORCHESTRATION_TYPES[orchestrationType];

  const getExecutionStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'text-green-600 bg-green-50';
      case 'paused':
        return 'text-yellow-600 bg-yellow-50';
      case 'completed':
        return 'text-blue-600 bg-blue-50';
      case 'failed':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getExecutionStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return Play;
      case 'paused':
        return Pause;
      case 'completed':
        return CheckCircle2;
      case 'failed':
        return AlertCircle;
      default:
        return Square;
    }
  };

  const StatusIcon = getExecutionStatusIcon(executionStatus);

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              오케스트레이션 제어
            </CardTitle>
            <CardDescription>
              {pattern?.name} 패턴으로 실행 중
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className={cn('text-xs', getExecutionStatusColor(executionStatus))}
            >
              <StatusIcon className="w-3 h-3 mr-1" />
              {executionStatus === 'idle' && '대기'}
              {executionStatus === 'running' && '실행 중'}
              {executionStatus === 'paused' && '일시정지'}
              {executionStatus === 'completed' && '완료'}
              {executionStatus === 'failed' && '실패'}
            </Badge>
            <Dialog open={showPreview} onOpenChange={setShowPreview}>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm">
                  <Eye className="w-4 h-4 mr-2" />
                  미리보기
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-4xl">
                <DialogHeader>
                  <DialogTitle>{pattern?.name} 패턴 미리보기</DialogTitle>
                  <DialogDescription>
                    현재 설정된 오케스트레이션 패턴의 구조를 확인할 수 있습니다.
                  </DialogDescription>
                </DialogHeader>
                <PatternPreviewCanvas
                  orchestrationType={orchestrationType}
                  showControls={true}
                  showMiniMap={true}
                  interactive={true}
                />
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* 실행 제어 버튼 */}
        <div className="flex items-center gap-2">
          <Button
            onClick={onExecutionStart}
            disabled={isExecuting && !isPaused}
            size="sm"
            className="flex-1"
          >
            <Play className="w-4 h-4 mr-2" />
            {isPaused ? '재개' : '시작'}
          </Button>
          <Button
            onClick={onExecutionPause}
            disabled={!isExecuting || isPaused}
            variant="outline"
            size="sm"
            className="flex-1"
          >
            <Pause className="w-4 h-4 mr-2" />
            일시정지
          </Button>
          <Button
            onClick={onExecutionStop}
            disabled={!isExecuting}
            variant="outline"
            size="sm"
            className="flex-1"
          >
            <Square className="w-4 h-4 mr-2" />
            정지
          </Button>
          <Button
            onClick={onExecutionReset}
            disabled={isExecuting}
            variant="outline"
            size="sm"
          >
            <RotateCcw className="w-4 h-4" />
          </Button>
        </div>

        <Separator />

        {/* 실시간 메트릭 */}
        <div>
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <Activity className="w-4 h-4" />
            실시간 메트릭
          </h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="text-xs text-gray-600">활성 Agent</div>
                <Users className="w-4 h-4 text-gray-400" />
              </div>
              <div className="text-lg font-semibold mt-1">
                {activeAgents}/{totalAgents}
              </div>
              {totalAgents > 0 && (
                <div className="w-full bg-gray-200 rounded-full h-1 mt-2">
                  <div
                    className="bg-blue-500 h-1 rounded-full transition-all duration-300"
                    style={{ width: `${(activeAgents / totalAgents) * 100}%` }}
                  />
                </div>
              )}
            </div>

            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="text-xs text-gray-600">완료된 작업</div>
                <CheckCircle2 className="w-4 h-4 text-green-400" />
              </div>
              <div className="text-lg font-semibold mt-1 text-green-600">
                {completedTasks}
              </div>
              {failedTasks > 0 && (
                <div className="text-xs text-red-600 mt-1">
                  실패: {failedTasks}
                </div>
              )}
            </div>

            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="text-xs text-gray-600">평균 응답시간</div>
                <Clock className="w-4 h-4 text-gray-400" />
              </div>
              <div className="text-lg font-semibold mt-1">
                {averageResponseTime > 0 ? `${averageResponseTime}ms` : '-'}
              </div>
            </div>

            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="text-xs text-gray-600">토큰 사용량</div>
                <Zap className="w-4 h-4 text-gray-400" />
              </div>
              <div className="text-lg font-semibold mt-1">
                {tokenUsage > 0 ? tokenUsage.toLocaleString() : '-'}
              </div>
            </div>
          </div>
        </div>

        <Separator />

        {/* Agent 상태 */}
        {Object.keys(agentStatuses).length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Users className="w-4 h-4" />
              Agent 상태
            </h3>
            <ScrollArea className="h-32">
              <div className="space-y-2">
                {Object.entries(agentStatuses).map(([agentId, status]) => (
                  <div key={agentId} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div className="flex items-center gap-2">
                      <div className={cn(
                        'w-2 h-2 rounded-full',
                        status.status === 'running' && 'bg-green-500 animate-pulse',
                        status.status === 'completed' && 'bg-blue-500',
                        status.status === 'failed' && 'bg-red-500',
                        status.status === 'idle' && 'bg-gray-400'
                      )} />
                      <span className="text-sm font-medium">{agentId}</span>
                    </div>
                    <div className="text-right">
                      <Badge variant="outline" className="text-xs">
                        {status.status === 'idle' && '대기'}
                        {status.status === 'running' && '실행 중'}
                        {status.status === 'completed' && '완료'}
                        {status.status === 'failed' && '실패'}
                      </Badge>
                      {status.currentTask && (
                        <div className="text-xs text-gray-600 mt-1 max-w-24 truncate">
                          {status.currentTask}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        )}

        {/* 패턴별 특수 메트릭 */}
        {(orchestrationType === 'consensus_building' || orchestrationType === 'swarm_intelligence') && (
          <>
            <Separator />
            <div>
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <MessageSquare className="w-4 h-4" />
                협업 메트릭
              </h3>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gray-50 p-3 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="text-xs text-gray-600">통신 횟수</div>
                    <MessageSquare className="w-4 h-4 text-gray-400" />
                  </div>
                  <div className="text-lg font-semibold mt-1">
                    {communicationCount}
                  </div>
                </div>

                {orchestrationType === 'consensus_building' && (
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="text-xs text-gray-600">합의 진행률</div>
                      <TrendingUp className="w-4 h-4 text-gray-400" />
                    </div>
                    <div className="text-lg font-semibold mt-1">
                      {Math.round(consensusProgress * 100)}%
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-1 mt-2">
                      <div
                        className="bg-green-500 h-1 rounded-full transition-all duration-300"
                        style={{ width: `${consensusProgress * 100}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        {/* Supervisor 정보 */}
        {supervisorConfig?.enabled && (
          <>
            <Separator />
            <div>
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Brain className="w-4 h-4" />
                Supervisor 상태
              </h3>
              <div className="bg-purple-50 p-3 rounded-lg border border-purple-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">AI Supervisor</span>
                  <Badge variant="secondary" className="text-xs">
                    {supervisorConfig.llm_provider} / {supervisorConfig.llm_model}
                  </Badge>
                </div>
                <div className="text-xs text-gray-600">
                  전략: {supervisorConfig.decision_strategy} | 
                  최대 반복: {supervisorConfig.max_iterations}회
                </div>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
};