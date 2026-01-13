'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  MessageSquare,
  ArrowRight,
  Users,
  Activity,
  Clock,
  TrendingUp,
  Filter,
  Search,
  Zap,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { COMMUNICATION_TYPES, type CommunicationType } from '@/lib/constants/orchestration';

interface CommunicationMessage {
  id: string;
  timestamp: string;
  fromAgent: string;
  toAgent: string;
  type: CommunicationType;
  content: string;
  status: 'sent' | 'delivered' | 'read' | 'failed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  responseTime?: number;
  metadata?: Record<string, any>;
}

interface AgentCommunicationStats {
  agentId: string;
  agentName: string;
  messagesSent: number;
  messagesReceived: number;
  avgResponseTime: number;
  successRate: number;
  lastActivity: string;
  isActive: boolean;
}

interface CommunicationGraphProps {
  messages: CommunicationMessage[];
  agents: AgentCommunicationStats[];
  onMessageClick?: (message: CommunicationMessage) => void;
  onAgentClick?: (agentId: string) => void;
  className?: string;
}

const MessageItem: React.FC<{
  message: CommunicationMessage;
  onClick?: () => void;
}> = ({ message, onClick }) => {
  const communicationType = COMMUNICATION_TYPES[message.type];
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'sent':
        return <Clock className="w-3 h-3 text-yellow-500" />;
      case 'delivered':
        return <CheckCircle2 className="w-3 h-3 text-blue-500" />;
      case 'read':
        return <CheckCircle2 className="w-3 h-3 text-green-500" />;
      case 'failed':
        return <AlertTriangle className="w-3 h-3 text-red-500" />;
      default:
        return <Clock className="w-3 h-3" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'border-l-red-500 bg-red-50';
      case 'high':
        return 'border-l-orange-500 bg-orange-50';
      case 'medium':
        return 'border-l-blue-500 bg-blue-50';
      case 'low':
        return 'border-l-gray-500 bg-gray-50';
      default:
        return 'border-l-gray-300 bg-white';
    }
  };

  return (
    <div
      className={cn(
        'p-3 border-l-4 rounded-r cursor-pointer transition-all duration-200 hover:shadow-md',
        getPriorityColor(message.priority)
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <Badge
            variant="outline"
            style={{ color: communicationType.color, borderColor: communicationType.color }}
          >
            {communicationType.name}
          </Badge>
          {getStatusIcon(message.status)}
          <span className="text-xs text-gray-500">{message.timestamp}</span>
        </div>
        {message.responseTime && (
          <Badge variant="secondary" className="text-xs">
            {message.responseTime}ms
          </Badge>
        )}
      </div>
      
      <div className="flex items-center gap-2 mb-2">
        <span className="font-medium text-sm">{message.fromAgent}</span>
        <ArrowRight className="w-3 h-3 text-gray-400" />
        <span className="font-medium text-sm">{message.toAgent}</span>
      </div>
      
      <p className="text-sm text-gray-700 line-clamp-2">{message.content}</p>
    </div>
  );
};

const AgentNode: React.FC<{
  agent: AgentCommunicationStats;
  onClick?: () => void;
}> = ({ agent, onClick }) => {
  return (
    <div
      className={cn(
        'p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 hover:shadow-lg',
        agent.isActive ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white'
      )}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={cn(
            'w-3 h-3 rounded-full',
            agent.isActive ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
          )} />
          <span className="font-medium">{agent.agentName}</span>
        </div>
        <Badge variant={agent.isActive ? 'default' : 'secondary'}>
          {agent.isActive ? '활성' : '비활성'}
        </Badge>
      </div>
      
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="text-center p-2 bg-white rounded">
          <div className="font-semibold text-blue-600">{agent.messagesSent}</div>
          <div className="text-gray-600">전송</div>
        </div>
        <div className="text-center p-2 bg-white rounded">
          <div className="font-semibold text-green-600">{agent.messagesReceived}</div>
          <div className="text-gray-600">수신</div>
        </div>
        <div className="text-center p-2 bg-white rounded">
          <div className="font-semibold text-purple-600">{agent.avgResponseTime}ms</div>
          <div className="text-gray-600">응답시간</div>
        </div>
        <div className="text-center p-2 bg-white rounded">
          <div className="font-semibold text-orange-600">{(agent.successRate * 100).toFixed(0)}%</div>
          <div className="text-gray-600">성공률</div>
        </div>
      </div>
      
      <div className="mt-2 text-xs text-gray-500">
        마지막 활동: {agent.lastActivity}
      </div>
    </div>
  );
};

export const CommunicationGraph: React.FC<CommunicationGraphProps> = ({
  messages,
  agents,
  onMessageClick,
  onAgentClick,
  className,
}) => {
  const [selectedTab, setSelectedTab] = useState('messages');
  const [filterType, setFilterType] = useState<CommunicationType | 'all'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 자동 스크롤
  useEffect(() => {
    if (autoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, autoScroll]);

  // 메시지 필터링
  const filteredMessages = messages.filter(message => {
    const matchesType = filterType === 'all' || message.type === filterType;
    const matchesSearch = searchTerm === '' || 
      message.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
      message.fromAgent.toLowerCase().includes(searchTerm.toLowerCase()) ||
      message.toAgent.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesType && matchesSearch;
  });

  // 통계 계산
  const totalMessages = messages.length;
  const activeAgents = agents.filter(a => a.isActive).length;
  const avgResponseTime = messages
    .filter(m => m.responseTime)
    .reduce((sum, m) => sum + (m.responseTime || 0), 0) / 
    messages.filter(m => m.responseTime).length || 0;
  const successRate = messages.length > 0 ? 
    messages.filter(m => m.status === 'delivered' || m.status === 'read').length / messages.length : 0;

  // 통신 타입별 통계
  const typeStats = Object.keys(COMMUNICATION_TYPES).map(type => {
    const typeMessages = messages.filter(m => m.type === type);
    return {
      type: type as CommunicationType,
      count: typeMessages.length,
      percentage: totalMessages > 0 ? (typeMessages.length / totalMessages) * 100 : 0,
    };
  });

  return (
    <div className={cn('space-y-6', className)}>
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">통신 그래프</h2>
          <p className="text-gray-600">Agent 간 실시간 통신 모니터링</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoScroll(!autoScroll)}
          >
            <Activity className={cn('w-4 h-4 mr-2', autoScroll && 'animate-pulse')} />
            자동 스크롤 {autoScroll ? 'ON' : 'OFF'}
          </Button>
        </div>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-50 rounded-lg">
                <MessageSquare className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{totalMessages}</div>
                <div className="text-sm text-gray-600">총 메시지</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-50 rounded-lg">
                <Users className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{activeAgents}</div>
                <div className="text-sm text-gray-600">활성 Agent</div>
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
                <div className="text-2xl font-bold">{avgResponseTime.toFixed(0)}ms</div>
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
                <div className="text-2xl font-bold">{(successRate * 100).toFixed(0)}%</div>
                <div className="text-sm text-gray-600">전달 성공률</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 메인 콘텐츠 */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList>
          <TabsTrigger value="messages">메시지 로그</TabsTrigger>
          <TabsTrigger value="agents">Agent 네트워크</TabsTrigger>
          <TabsTrigger value="stats">통신 통계</TabsTrigger>
        </TabsList>

        <TabsContent value="messages" className="space-y-4">
          {/* 필터 및 검색 */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4" />
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value as CommunicationType | 'all')}
                className="px-3 py-1 border rounded text-sm"
              >
                <option value="all">모든 타입</option>
                {Object.entries(COMMUNICATION_TYPES).map(([key, type]) => (
                  <option key={key} value={key}>{type.name}</option>
                ))}
              </select>
            </div>
            
            <div className="flex items-center gap-2 flex-1">
              <Search className="w-4 h-4" />
              <input
                type="text"
                placeholder="메시지 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="px-3 py-1 border rounded text-sm flex-1"
              />
            </div>
          </div>

          {/* 메시지 목록 */}
          <ScrollArea className="h-[500px]">
            <div className="space-y-2">
              {filteredMessages.map((message) => (
                <MessageItem
                  key={message.id}
                  message={message}
                  onClick={() => onMessageClick?.(message)}
                />
              ))}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="agents" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((agent) => (
              <AgentNode
                key={agent.agentId}
                agent={agent}
                onClick={() => onAgentClick?.(agent.agentId)}
              />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="stats" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 통신 타입별 통계 */}
            <Card>
              <CardHeader>
                <CardTitle>통신 타입별 분포</CardTitle>
                <CardDescription>각 통신 타입의 사용 빈도</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {typeStats.map(({ type, count, percentage }) => (
                    <div key={type} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded"
                          style={{ backgroundColor: COMMUNICATION_TYPES[type].color }}
                        />
                        <span className="text-sm">{COMMUNICATION_TYPES[type].name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{count}</span>
                        <span className="text-xs text-gray-500">({percentage.toFixed(1)}%)</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Agent별 활동 통계 */}
            <Card>
              <CardHeader>
                <CardTitle>Agent별 활동</CardTitle>
                <CardDescription>각 Agent의 통신 활동 수준</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {agents
                    .sort((a, b) => (b.messagesSent + b.messagesReceived) - (a.messagesSent + a.messagesReceived))
                    .slice(0, 5)
                    .map((agent) => (
                      <div key={agent.agentId} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className={cn(
                            'w-2 h-2 rounded-full',
                            agent.isActive ? 'bg-green-500' : 'bg-gray-400'
                          )} />
                          <span className="text-sm font-medium">{agent.agentName}</span>
                        </div>
                        <div className="text-sm text-gray-600">
                          {agent.messagesSent + agent.messagesReceived} 메시지
                        </div>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};