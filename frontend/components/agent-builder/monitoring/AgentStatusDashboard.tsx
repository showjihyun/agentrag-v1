'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Activity,
  Bot,
  Clock,
  Cpu,
  MessageSquare,
  TrendingUp,
  Users,
  Zap,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Pause,
  Play,
  RotateCcw,
  Settings,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { AGENT_ROLES, type AgentRole } from '@/lib/constants/orchestration';

interface AgentStatus {
  id: string;
  name: string;
  role: AgentRole;
  status: 'idle' | 'running' | 'completed' | 'error' | 'paused';
  progress: number;
  currentTask?: string;
  performance: {
    responseTime: number;
    successRate: number;
    tokensUsed: number;
    tasksCompleted: number;
    errorCount: number;
  };
  resources: {
    cpuUsage: number;
    memoryUsage: number;
    networkLatency: number;
  };
  communication: {
    messagesSent: number;
    messagesReceived: number;
    lastActivity: string;
  };
  metadata: {
    startTime: string;
    lastUpdate: string;
    version: string;
  };
}

interface AgentStatusDashboardProps {
  agents: AgentStatus[];
  onAgentControl?: (agentId: string, action: 'pause' | 'resume' | 'restart' | 'configure') => void;
  onRefresh?: () => void;
  className?: string;
}

const AgentStatusCard: React.FC<{
  agent: AgentStatus;
  onControl?: (action: 'pause' | 'resume' | 'restart' | 'configure') => void;
}> = ({ agent, onControl }) => {
  const roleInfo = AGENT_ROLES[agent.role];
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'text-blue-600 bg-blue-50';
      case 'completed':
        return 'text-green-600 bg-green-50';
      case 'error':
        return 'text-red-600 bg-red-50';
      case 'paused':
        return 'text-yellow-600 bg-yellow-50';
      case 'idle':
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Activity className="w-4 h-4 animate-pulse" />;
      case 'completed':
        return <CheckCircle2 className="w-4 h-4" />;
      case 'error':
        return <XCircle className="w-4 h-4" />;
      case 'paused':
        return <Pause className="w-4 h-4" />;
      case 'idle':
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div
              className="p-2 rounded-lg"
              style={{ backgroundColor: `${roleInfo.color}20`, color: roleInfo.color }}
            >
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <CardTitle className="text-lg">{agent.name}</CardTitle>
              <CardDescription className="flex items-center gap-2">
                <Badge variant="outline" style={{ color: roleInfo.color }}>
                  {roleInfo.name}
                </Badge>
                <Badge className={cn('text-xs', getStatusColor(agent.status))}>
                  {getStatusIcon(agent.status)}
                  <span className="ml-1">
                    {agent.status === 'running' ? '실행 중' :
                     agent.status === 'completed' ? '완료' :
                     agent.status === 'error' ? '오류' :
                     agent.status === 'paused' ? '일시정지' : '대기'}
                  </span>
                </Badge>
              </div>
            </div>
          </div>
          
          {/* 제어 버튼 */}
          <div className="flex items-center gap-1">
            {agent.status === 'running' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onControl?.('pause')}
              >
                <Pause className="w-3 h-3" />
              </Button>
            )}
            {agent.status === 'paused' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onControl?.('resume')}
              >
                <Play className="w-3 h-3" />
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => onControl?.('restart')}
            >
              <RotateCcw className="w-3 h-3" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onControl?.('configure')}
            >
              <Settings className="w-3 h-3" />
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* 진행률 */}
        {agent.status === 'running' && (
          <div>
            <div className="flex items-center justify-between text-sm mb-2">
              <span>진행률</span>
              <span>{agent.progress}%</span>
            </div>
            <Progress value={agent.progress} className="h-2" />
            {agent.currentTask && (
              <p className="text-xs text-gray-600 mt-1">{agent.currentTask}</p>
            )}
          </div>
        )}
        
        {/* 성능 메트릭 */}
        <div className="grid grid-cols-2 gap-3">
          <div className="text-center p-2 bg-gray-50 rounded">
            <div className="text-lg font-semibold text-blue-600">
              {agent.performance.responseTime.toFixed(1)}s
            </div>
            <div className="text-xs text-gray-600">응답 시간</div>
          </div>
          <div className="text-center p-2 bg-gray-50 rounded">
            <div className="text-lg font-semibold text-green-600">
              {(agent.performance.successRate * 100).toFixed(0)}%
            </div>
            <div className="text-xs text-gray-600">성공률</div>
          </div>
          <div className="text-center p-2 bg-gray-50 rounded">
            <div className="text-lg font-semibold text-purple-600">
              {agent.performance.tokensUsed.toLocaleString()}
            </div>
            <div className="text-xs text-gray-600">토큰 사용</div>
          </div>
          <div className="text-center p-2 bg-gray-50 rounded">
            <div className="text-lg font-semibold text-orange-600">
              {agent.performance.tasksCompleted}
            </div>
            <div className="text-xs text-gray-600">완료 작업</div>
          </div>
        </div>
        
        {/* 리소스 사용량 */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-1">
              <Cpu className="w-3 h-3" />
              CPU
            </span>
            <span>{agent.resources.cpuUsage}%</span>
          </div>
          <Progress value={agent.resources.cpuUsage} className="h-1" />
          
          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-1">
              <Activity className="w-3 h-3" />
              메모리
            </span>
            <span>{agent.resources.memoryUsage}%</span>
          </div>
          <Progress value={agent.resources.memoryUsage} className="h-1" />
        </div>
        
        {/* 통신 상태 */}
        <div className="flex items-center justify-between text-xs text-gray-600">
          <div className="flex items-center gap-1">
            <MessageSquare className="w-3 h-3" />
            <span>메시지: {agent.communication.messagesSent}↑ {agent.communication.messagesReceived}↓</span>
          </div>
          <div>
            마지막 활동: {agent.communication.lastActivity}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export const AgentStatusDashboard: React.FC<AgentStatusDashboardProps> = ({
  agents,
  onAgentControl,
  onRefresh,
  className,
}) => {
  const [selectedTab, setSelectedTab] = useState('overview');
  const [autoRefresh, setAutoRefresh] = useState(true);

  // 자동 새로고침
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      onRefresh?.();
    }, 2000); // 2초마다 새로고침
    
    return () => clearInterval(interval);
  }, [autoRefresh, onRefresh]);

  // 전체 통계 계산
  const totalAgents = agents.length;
  const runningAgents = agents.filter(a => a.status === 'running').length;
  const completedAgents = agents.filter(a => a.status === 'completed').length;
  const errorAgents = agents.filter(a => a.status === 'error').length;
  const avgResponseTime = agents.reduce((sum, a) => sum + a.performance.responseTime, 0) / totalAgents;
  const avgSuccessRate = agents.reduce((sum, a) => sum + a.performance.successRate, 0) / totalAgents;
  const totalTokens = agents.reduce((sum, a) => sum + a.performance.tokensUsed, 0);

  return (
    <div className={cn('space-y-6', className)}>
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Agent 상태 대시보드</h2>
          <p className="text-gray-600">실시간 Agent 모니터링 및 제어</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <Activity className={cn('w-4 h-4 mr-2', autoRefresh && 'animate-pulse')} />
            자동 새로고침 {autoRefresh ? 'ON' : 'OFF'}
          </Button>
          <Button variant="outline" size="sm" onClick={onRefresh}>
            <RotateCcw className="w-4 h-4 mr-2" />
            새로고침
          </Button>
        </div>
      </div>

      {/* 전체 통계 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-50 rounded-lg">
                <Users className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{totalAgents}</div>
                <div className="text-sm text-gray-600">전체 Agent</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-50 rounded-lg">
                <Activity className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{runningAgents}</div>
                <div className="text-sm text-gray-600">실행 중</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-50 rounded-lg">
                <TrendingUp className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{avgResponseTime.toFixed(1)}s</div>
                <div className="text-sm text-gray-600">평균 응답시간</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-50 rounded-lg">
                <Zap className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{totalTokens.toLocaleString()}</div>
                <div className="text-sm text-gray-600">총 토큰 사용</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Agent 목록 */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList>
          <TabsTrigger value="overview">전체 보기</TabsTrigger>
          <TabsTrigger value="running">실행 중 ({runningAgents})</TabsTrigger>
          <TabsTrigger value="completed">완료 ({completedAgents})</TabsTrigger>
          {errorAgents > 0 && (
            <TabsTrigger value="error" className="text-red-600">
              오류 ({errorAgents})
            </TabsTrigger>
          )}
        </TabsList>

        <TabsContent value="overview">
          <ScrollArea className="h-[600px]">
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
              {agents.map((agent) => (
                <AgentStatusCard
                  key={agent.id}
                  agent={agent}
                  onControl={(action) => onAgentControl?.(agent.id, action)}
                />
              ))}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="running">
          <ScrollArea className="h-[600px]">
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
              {agents
                .filter(agent => agent.status === 'running')
                .map((agent) => (
                  <AgentStatusCard
                    key={agent.id}
                    agent={agent}
                    onControl={(action) => onAgentControl?.(agent.id, action)}
                  />
                ))}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="completed">
          <ScrollArea className="h-[600px]">
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
              {agents
                .filter(agent => agent.status === 'completed')
                .map((agent) => (
                  <AgentStatusCard
                    key={agent.id}
                    agent={agent}
                    onControl={(action) => onAgentControl?.(agent.id, action)}
                  />
                ))}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="error">
          <ScrollArea className="h-[600px]">
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
              {agents
                .filter(agent => agent.status === 'error')
                .map((agent) => (
                  <AgentStatusCard
                    key={agent.id}
                    agent={agent}
                    onControl={(action) => onAgentControl?.(agent.id, action)}
                  />
                ))}
            </div>
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  );
};