'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Crown,
  Brain,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  TrendingUp,
  Users,
  Zap,
  MessageSquare,
  Target,
  BarChart3,
  Filter,
  Search,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface SupervisorDecision {
  id: string;
  timestamp: string;
  supervisorId: string;
  supervisorName: string;
  decisionType: 'routing' | 'intervention' | 'resource_allocation' | 'conflict_resolution' | 'performance_optimization';
  context: {
    triggerEvent: string;
    involvedAgents: string[];
    currentSituation: string;
    availableOptions: string[];
  };
  decision: {
    selectedOption: string;
    reasoning: string;
    confidence: number; // 0-1
    expectedOutcome: string;
    alternativePlan?: string;
  };
  execution: {
    status: 'pending' | 'executing' | 'completed' | 'failed';
    startTime?: string;
    endTime?: string;
    actualOutcome?: string;
    effectiveness?: number; // 0-1
  };
  llmProvider: string;
  llmModel: string;
  tokensUsed: number;
  responseTime: number;
  metadata?: Record<string, any>;
}

interface SupervisorMetrics {
  supervisorId: string;
  supervisorName: string;
  totalDecisions: number;
  successfulDecisions: number;
  avgConfidence: number;
  avgResponseTime: number;
  avgEffectiveness: number;
  totalTokensUsed: number;
  decisionsByType: Record<string, number>;
  recentActivity: string;
  isActive: boolean;
}

interface SupervisorDecisionLogProps {
  decisions: SupervisorDecision[];
  supervisors: SupervisorMetrics[];
  onDecisionClick?: (decision: SupervisorDecision) => void;
  onSupervisorClick?: (supervisorId: string) => void;
  className?: string;
}

const DecisionCard: React.FC<{
  decision: SupervisorDecision;
  onClick?: () => void;
}> = ({ decision, onClick }) => {
  const getDecisionTypeColor = (type: string) => {
    switch (type) {
      case 'routing':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'intervention':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'resource_allocation':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'conflict_resolution':
        return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'performance_optimization':
        return 'text-purple-600 bg-purple-50 border-purple-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getDecisionTypeLabel = (type: string) => {
    switch (type) {
      case 'routing':
        return '라우팅 결정';
      case 'intervention':
        return '개입 결정';
      case 'resource_allocation':
        return '리소스 할당';
      case 'conflict_resolution':
        return '충돌 해결';
      case 'performance_optimization':
        return '성능 최적화';
      default:
        return '기타 결정';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'executing':
        return <Zap className="w-4 h-4 text-blue-500 animate-pulse" />;
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <Card 
      className={cn(
        'cursor-pointer transition-all duration-200 hover:shadow-md border-l-4',
        getDecisionTypeColor(decision.decisionType)
      )}
      onClick={onClick}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Crown className="w-4 h-4" />
              <span className="font-medium">{decision.supervisorName}</span>
              <Badge variant="outline" className="text-xs">
                {getDecisionTypeLabel(decision.decisionType)}
              </Badge>
            </div>
            <div className="text-sm text-gray-600">{decision.timestamp}</div>
          </div>
          <div className="flex items-center gap-2">
            {getStatusIcon(decision.execution.status)}
            <Badge 
              variant="outline" 
              className={cn('text-xs', getConfidenceColor(decision.decision.confidence))}
            >
              신뢰도 {(decision.decision.confidence * 100).toFixed(0)}%
            </Badge>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-3">
        {/* 상황 설명 */}
        <div>
          <div className="text-sm font-medium text-gray-700 mb-1">상황</div>
          <div className="text-sm text-gray-600 line-clamp-2">
            {decision.context.currentSituation}
          </div>
        </div>
        
        {/* 결정 내용 */}
        <div>
          <div className="text-sm font-medium text-gray-700 mb-1">결정</div>
          <div className="text-sm text-gray-900 font-medium line-clamp-1">
            {decision.decision.selectedOption}
          </div>
        </div>
        
        {/* 관련 Agent */}
        <div className="flex items-center gap-2">
          <Users className="w-3 h-3 text-gray-500" />
          <div className="text-xs text-gray-600">
            관련 Agent: {decision.context.involvedAgents.join(', ')}
          </div>
        </div>
        
        {/* 메트릭 */}
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center gap-3">
            <span>{decision.responseTime}ms</span>
            <span>{decision.tokensUsed} 토큰</span>
            <span>{decision.llmModel}</span>
          </div>
          {decision.execution.effectiveness && (
            <Badge variant="secondary" className="text-xs">
              효과 {(decision.execution.effectiveness * 100).toFixed(0)}%
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

const SupervisorCard: React.FC<{
  supervisor: SupervisorMetrics;
  onClick?: () => void;
}> = ({ supervisor, onClick }) => {
  const successRate = supervisor.totalDecisions > 0 ? 
    (supervisor.successfulDecisions / supervisor.totalDecisions) * 100 : 0;

  return (
    <Card 
      className={cn(
        'cursor-pointer transition-all duration-200 hover:shadow-md',
        supervisor.isActive && 'ring-2 ring-blue-500'
      )}
      onClick={onClick}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-purple-50 rounded-lg">
              <Crown className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <CardTitle className="text-lg">{supervisor.supervisorName}</CardTitle>
              <div className="flex items-center gap-2 mt-1">
                <div className={cn(
                  'w-2 h-2 rounded-full',
                  supervisor.isActive ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
                )} />
                <span className="text-sm text-gray-600">
                  {supervisor.isActive ? '활성' : '비활성'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* 성과 메트릭 */}
        <div className="grid grid-cols-2 gap-3">
          <div className="text-center p-2 bg-blue-50 rounded">
            <div className="text-lg font-semibold text-blue-600">
              {supervisor.totalDecisions}
            </div>
            <div className="text-xs text-gray-600">총 결정</div>
          </div>
          <div className="text-center p-2 bg-green-50 rounded">
            <div className="text-lg font-semibold text-green-600">
              {successRate.toFixed(0)}%
            </div>
            <div className="text-xs text-gray-600">성공률</div>
          </div>
          <div className="text-center p-2 bg-purple-50 rounded">
            <div className="text-lg font-semibold text-purple-600">
              {(supervisor.avgConfidence * 100).toFixed(0)}%
            </div>
            <div className="text-xs text-gray-600">평균 신뢰도</div>
          </div>
          <div className="text-center p-2 bg-orange-50 rounded">
            <div className="text-lg font-semibold text-orange-600">
              {supervisor.avgResponseTime.toFixed(0)}ms
            </div>
            <div className="text-xs text-gray-600">응답 시간</div>
          </div>
        </div>
        
        {/* 결정 타입별 분포 */}
        <div>
          <div className="text-sm font-medium text-gray-700 mb-2">결정 타입 분포</div>
          <div className="space-y-1">
            {Object.entries(supervisor.decisionsByType)
              .sort(([,a], [,b]) => b - a)
              .slice(0, 3)
              .map(([type, count]) => (
                <div key={type} className="flex items-center justify-between text-xs">
                  <span className="text-gray-600">
                    {type === 'routing' ? '라우팅' :
                     type === 'intervention' ? '개입' :
                     type === 'resource_allocation' ? '리소스' :
                     type === 'conflict_resolution' ? '충돌해결' :
                     type === 'performance_optimization' ? '성능최적화' : type}
                  </span>
                  <span className="font-medium">{count}</span>
                </div>
              ))}
          </div>
        </div>
        
        {/* 최근 활동 */}
        <div className="text-xs text-gray-500">
          마지막 활동: {supervisor.recentActivity}
        </div>
      </CardContent>
    </Card>
  );
};

export const SupervisorDecisionLog: React.FC<SupervisorDecisionLogProps> = ({
  decisions,
  supervisors,
  onDecisionClick,
  onSupervisorClick,
  className,
}) => {
  const [selectedTab, setSelectedTab] = useState('decisions');
  const [filterType, setFilterType] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // 결정 필터링
  const filteredDecisions = decisions.filter(decision => {
    const matchesType = filterType === 'all' || decision.decisionType === filterType;
    const matchesSearch = searchTerm === '' || 
      decision.context.currentSituation.toLowerCase().includes(searchTerm.toLowerCase()) ||
      decision.decision.selectedOption.toLowerCase().includes(searchTerm.toLowerCase()) ||
      decision.supervisorName.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesType && matchesSearch;
  });

  // 통계 계산
  const totalDecisions = decisions.length;
  const activeSupervisors = supervisors.filter(s => s.isActive).length;
  const avgResponseTime = decisions.length > 0 ? 
    decisions.reduce((sum, d) => sum + d.responseTime, 0) / decisions.length : 0;
  const avgConfidence = decisions.length > 0 ? 
    decisions.reduce((sum, d) => sum + d.decision.confidence, 0) / decisions.length : 0;
  const totalTokens = decisions.reduce((sum, d) => sum + d.tokensUsed, 0);

  // 결정 타입별 통계
  const decisionTypeStats = [
    'routing', 'intervention', 'resource_allocation', 'conflict_resolution', 'performance_optimization'
  ].map(type => {
    const typeDecisions = decisions.filter(d => d.decisionType === type);
    return {
      type,
      count: typeDecisions.length,
      percentage: totalDecisions > 0 ? (typeDecisions.length / totalDecisions) * 100 : 0,
    };
  });

  return (
    <div className={cn('space-y-6', className)}>
      {/* 헤더 */}
      <div>
        <h2 className="text-2xl font-bold">Supervisor 의사결정 로그</h2>
        <p className="text-gray-600">AI Supervisor의 실시간 의사결정 과정 추적</p>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-50 rounded-lg">
                <Brain className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{totalDecisions}</div>
                <div className="text-sm text-gray-600">총 결정</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-50 rounded-lg">
                <Crown className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{activeSupervisors}</div>
                <div className="text-sm text-gray-600">활성 Supervisor</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-50 rounded-lg">
                <TrendingUp className="w-5 h-5 text-green-600" />
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
                <Target className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{(avgConfidence * 100).toFixed(0)}%</div>
                <div className="text-sm text-gray-600">평균 신뢰도</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-50 rounded-lg">
                <Zap className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{totalTokens.toLocaleString()}</div>
                <div className="text-sm text-gray-600">총 토큰 사용</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 메인 콘텐츠 */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList>
          <TabsTrigger value="decisions">결정 로그 ({totalDecisions})</TabsTrigger>
          <TabsTrigger value="supervisors">Supervisor ({supervisors.length})</TabsTrigger>
          <TabsTrigger value="analytics">분석</TabsTrigger>
        </TabsList>

        <TabsContent value="decisions" className="space-y-4">
          {/* 필터 및 검색 */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4" />
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-3 py-1 border rounded text-sm"
              >
                <option value="all">모든 타입</option>
                <option value="routing">라우팅 결정</option>
                <option value="intervention">개입 결정</option>
                <option value="resource_allocation">리소스 할당</option>
                <option value="conflict_resolution">충돌 해결</option>
                <option value="performance_optimization">성능 최적화</option>
              </select>
            </div>
            
            <div className="flex items-center gap-2 flex-1">
              <Search className="w-4 h-4" />
              <input
                type="text"
                placeholder="결정 내용 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="px-3 py-1 border rounded text-sm flex-1"
              />
            </div>
          </div>

          {/* 결정 목록 */}
          <ScrollArea className="h-[600px]">
            <div className="space-y-3">
              {filteredDecisions.map((decision) => (
                <DecisionCard
                  key={decision.id}
                  decision={decision}
                  onClick={() => onDecisionClick?.(decision)}
                />
              ))}
              {filteredDecisions.length === 0 && (
                <div className="text-center text-gray-500 py-12">
                  <Brain className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <div className="text-lg font-medium mb-2">결정 로그가 없습니다</div>
                  <div className="text-sm">Supervisor의 의사결정이 시작되면 여기에 표시됩니다.</div>
                </div>
              )}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="supervisors" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
            {supervisors.map((supervisor) => (
              <SupervisorCard
                key={supervisor.supervisorId}
                supervisor={supervisor}
                onClick={() => onSupervisorClick?.(supervisor.supervisorId)}
              />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 결정 타입별 분포 */}
            <Card>
              <CardHeader>
                <CardTitle>결정 타입별 분포</CardTitle>
                <CardDescription>각 결정 타입의 사용 빈도</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {decisionTypeStats.map(({ type, count, percentage }) => (
                    <div key={type} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-blue-500 rounded" />
                        <span className="text-sm">
                          {type === 'routing' ? '라우팅 결정' :
                           type === 'intervention' ? '개입 결정' :
                           type === 'resource_allocation' ? '리소스 할당' :
                           type === 'conflict_resolution' ? '충돌 해결' :
                           type === 'performance_optimization' ? '성능 최적화' : type}
                        </span>
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

            {/* Supervisor 성과 순위 */}
            <Card>
              <CardHeader>
                <CardTitle>Supervisor 성과 순위</CardTitle>
                <CardDescription>효과성 기준 상위 Supervisor</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {supervisors
                    .sort((a, b) => b.avgEffectiveness - a.avgEffectiveness)
                    .slice(0, 5)
                    .map((supervisor, index) => (
                      <div key={supervisor.supervisorId} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge variant={index === 0 ? 'default' : 'secondary'}>
                            #{index + 1}
                          </Badge>
                          <span className="text-sm font-medium">{supervisor.supervisorName}</span>
                        </div>
                        <div className="text-sm text-gray-600">
                          {(supervisor.avgEffectiveness * 100).toFixed(0)}% 효과성
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