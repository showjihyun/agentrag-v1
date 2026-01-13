/**
 * Enhanced Pattern Preview
 * 향상된 패턴 미리보기 컴포넌트
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Eye,
  Users,
  MessageSquare,
  Zap,
  Clock,
  Target,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Info,
  Play,
  Settings,
  BarChart3,
  Network,
  Shield
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  ORCHESTRATION_TYPES,
  AGENT_ROLES,
  type OrchestrationTypeValue,
  type AgentRole,
} from '@/lib/constants/orchestration';

interface OrchestrationConfig {
  orchestrationType: OrchestrationTypeValue;
  name: string;
  description: string;
  supervisorConfig: {
    enabled: boolean;
    llm_provider: string;
    llm_model: string;
    decision_strategy: string;
    max_iterations: number;
  };
  agentRoles: Array<{
    id: string;
    name: string;
    role: AgentRole;
    priority: number;
    maxRetries: number;
    timeoutSeconds: number;
    dependencies: string[];
  }>;
  communicationRules: {
    allowDirectCommunication: boolean;
    enableBroadcast: boolean;
    requireConsensus: boolean;
    maxNegotiationRounds: number;
  };
  performanceThresholds: {
    maxExecutionTime: number;
    minSuccessRate: number;
    maxTokenUsage: number;
  };
  tags: string[];
}

interface EnhancedPatternPreviewProps {
  config: OrchestrationConfig;
  className?: string;
  showExecutionFlow?: boolean;
  showPerformanceMetrics?: boolean;
  onExecuteTest?: () => void;
  onEditConfig?: () => void;
}

export function EnhancedPatternPreview({
  config,
  className,
  showExecutionFlow = true,
  showPerformanceMetrics = true,
  onExecuteTest,
  onEditConfig
}: EnhancedPatternPreviewProps) {
  const [activeTab, setActiveTab] = useState('overview');
  const [simulationRunning, setSimulationRunning] = useState(false);
  
  const pattern = ORCHESTRATION_TYPES[config.orchestrationType];
  
  // 설정 분석
  const configAnalysis = analyzeConfiguration(config);
  
  // 시뮬레이션 실행
  const runSimulation = async () => {
    setSimulationRunning(true);
    // 시뮬레이션 로직 (실제로는 API 호출)
    await new Promise(resolve => setTimeout(resolve, 2000));
    setSimulationRunning(false);
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-semibold">{config.name}</h3>
          <p className="text-sm text-gray-600">{pattern.name} 패턴</p>
        </div>
        <div className="flex gap-2">
          {onEditConfig && (
            <Button variant="outline" onClick={onEditConfig}>
              <Settings className="w-4 h-4 mr-2" />
              설정 수정
            </Button>
          )}
          {onExecuteTest && (
            <Button onClick={onExecuteTest}>
              <Play className="w-4 h-4 mr-2" />
              테스트 실행
            </Button>
          )}
        </div>
      </div>

      {/* 설정 분석 요약 */}
      <Card className={cn(
        "border-l-4",
        configAnalysis.overallScore >= 80 && "border-l-green-500 bg-green-50",
        configAnalysis.overallScore >= 60 && configAnalysis.overallScore < 80 && "border-l-yellow-500 bg-yellow-50",
        configAnalysis.overallScore < 60 && "border-l-red-500 bg-red-50"
      )}>
        <CardContent className="pt-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              {configAnalysis.overallScore >= 80 ? (
                <CheckCircle2 className="w-5 h-5 text-green-600" />
              ) : configAnalysis.overallScore >= 60 ? (
                <AlertTriangle className="w-5 h-5 text-yellow-600" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-red-600" />
              )}
              <span className="font-medium">설정 분석 결과</span>
            </div>
            <Badge variant={
              configAnalysis.overallScore >= 80 ? "default" :
              configAnalysis.overallScore >= 60 ? "secondary" : "destructive"
            }>
              {configAnalysis.overallScore}점
            </Badge>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <div className="font-medium text-gray-700 mb-1">강점</div>
              <ul className="space-y-1">
                {configAnalysis.strengths.map((strength, index) => (
                  <li key={index} className="flex items-center gap-1 text-green-700">
                    <CheckCircle2 className="w-3 h-3" />
                    {strength}
                  </li>
                ))}
              </ul>
            </div>
            
            <div>
              <div className="font-medium text-gray-700 mb-1">개선점</div>
              <ul className="space-y-1">
                {configAnalysis.improvements.map((improvement, index) => (
                  <li key={index} className="flex items-center gap-1 text-yellow-700">
                    <AlertTriangle className="w-3 h-3" />
                    {improvement}
                  </li>
                ))}
              </ul>
            </div>
            
            <div>
              <div className="font-medium text-gray-700 mb-1">예상 성능</div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>응답 시간</span>
                  <span className="font-medium">{configAnalysis.estimatedResponseTime}</span>
                </div>
                <div className="flex justify-between">
                  <span>성공률</span>
                  <span className="font-medium">{configAnalysis.estimatedSuccessRate}</span>
                </div>
                <div className="flex justify-between">
                  <span>비용 효율성</span>
                  <span className="font-medium">{configAnalysis.costEfficiency}</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 상세 탭 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">개요</TabsTrigger>
          <TabsTrigger value="agents">Agent 구성</TabsTrigger>
          <TabsTrigger value="flow">실행 흐름</TabsTrigger>
          <TabsTrigger value="metrics">성능 지표</TabsTrigger>
        </TabsList>

        {/* 개요 탭 */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Info className="w-4 h-4" />
                  기본 정보
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <div className="text-sm font-medium text-gray-700">설명</div>
                  <p className="text-sm text-gray-600">{config.description || '설명이 없습니다.'}</p>
                </div>
                <div>
                  <div className="text-sm font-medium text-gray-700 mb-1">태그</div>
                  <div className="flex flex-wrap gap-1">
                    {config.tags.map((tag, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium text-gray-700">패턴 특성</div>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="outline" className="text-xs">
                      <Clock className="w-3 h-3 mr-1" />
                      {pattern.estimated_setup_time}
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      <Target className="w-3 h-3 mr-1" />
                      {pattern.complexity}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Shield className="w-4 h-4" />
                  Supervisor 설정
                </CardTitle>
              </CardHeader>
              <CardContent>
                {config.supervisorConfig.enabled ? (
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">상태</span>
                      <Badge className="bg-green-100 text-green-700">활성화</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">LLM</span>
                      <span className="font-medium">
                        {config.supervisorConfig.llm_provider} / {config.supervisorConfig.llm_model}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">전략</span>
                      <span className="font-medium">{config.supervisorConfig.decision_strategy}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">최대 반복</span>
                      <span className="font-medium">{config.supervisorConfig.max_iterations}회</span>
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-gray-500 text-center py-4">
                    Supervisor가 비활성화되어 있습니다
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Agent 구성 탭 */}
        <TabsContent value="agents" className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            {config.agentRoles.map((agent, index) => (
              <Card key={agent.id}>
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <Users className="w-4 h-4 text-blue-600" />
                      </div>
                      <div>
                        <h4 className="font-medium">{agent.name}</h4>
                        <p className="text-sm text-gray-600">{AGENT_ROLES[agent.role].name}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">우선순위 {agent.priority}</Badge>
                      <Badge variant="secondary">{AGENT_ROLES[agent.role].category}</Badge>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-gray-600">최대 재시도</div>
                      <div className="font-medium">{agent.maxRetries}회</div>
                    </div>
                    <div>
                      <div className="text-gray-600">타임아웃</div>
                      <div className="font-medium">{agent.timeoutSeconds}초</div>
                    </div>
                    <div>
                      <div className="text-gray-600">의존성</div>
                      <div className="font-medium">
                        {agent.dependencies.length > 0 ? `${agent.dependencies.length}개` : '없음'}
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-3 p-2 bg-gray-50 rounded text-xs text-gray-600">
                    {AGENT_ROLES[agent.role].description}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* 실행 흐름 탭 */}
        <TabsContent value="flow" className="space-y-4">
          {showExecutionFlow && (
            <ExecutionFlowVisualization 
              config={config} 
              isSimulating={simulationRunning}
              onRunSimulation={runSimulation}
            />
          )}
        </TabsContent>

        {/* 성능 지표 탭 */}
        <TabsContent value="metrics" className="space-y-4">
          {showPerformanceMetrics && (
            <PerformanceMetricsView config={config} />
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

// 설정 분석 함수
function analyzeConfiguration(config: OrchestrationConfig) {
  const strengths: string[] = [];
  const improvements: string[] = [];
  let score = 0;

  // Agent 구성 분석
  if (config.agentRoles.length >= 2) {
    strengths.push('적절한 Agent 수');
    score += 20;
  } else {
    improvements.push('Agent 수 부족');
  }

  // Supervisor 분석
  if (config.supervisorConfig.enabled) {
    strengths.push('Supervisor 활성화');
    score += 15;
  }

  // 통신 규칙 분석
  if (config.communicationRules.allowDirectCommunication) {
    strengths.push('효율적인 통신 설정');
    score += 10;
  }

  // 성능 임계값 분석
  if (config.performanceThresholds.minSuccessRate >= 0.8) {
    strengths.push('높은 성공률 목표');
    score += 15;
  }

  if (config.performanceThresholds.maxExecutionTime <= 300000) {
    strengths.push('적절한 실행 시간 제한');
    score += 10;
  }

  // 태그 및 문서화
  if (config.tags.length > 0) {
    strengths.push('적절한 태그 설정');
    score += 5;
  }

  if (config.description && config.description.length > 10) {
    strengths.push('상세한 설명');
    score += 5;
  }

  // 개선점 추가
  if (score < 60) {
    improvements.push('전반적인 설정 개선 필요');
  }

  if (!config.supervisorConfig.enabled && config.agentRoles.length > 3) {
    improvements.push('다수 Agent 관리를 위한 Supervisor 고려');
  }

  return {
    overallScore: Math.min(score + 20, 100), // 기본 점수 20점 추가
    strengths,
    improvements,
    estimatedResponseTime: calculateEstimatedResponseTime(config),
    estimatedSuccessRate: `${Math.round(config.performanceThresholds.minSuccessRate * 100)}%`,
    costEfficiency: calculateCostEfficiency(config)
  };
}

function calculateEstimatedResponseTime(config: OrchestrationConfig): string {
  const baseTime = 2000; // 2초 기본
  const agentFactor = config.agentRoles.length * 500; // Agent당 0.5초 추가
  const supervisorFactor = config.supervisorConfig.enabled ? 1000 : 0; // Supervisor 1초 추가
  
  const totalMs = baseTime + agentFactor + supervisorFactor;
  return `${(totalMs / 1000).toFixed(1)}초`;
}

function calculateCostEfficiency(config: OrchestrationConfig): string {
  let efficiency = '보통';
  
  if (config.performanceThresholds.maxTokenUsage < 5000) {
    efficiency = '높음';
  } else if (config.performanceThresholds.maxTokenUsage > 15000) {
    efficiency = '낮음';
  }
  
  return efficiency;
}

// 실행 흐름 시각화 컴포넌트
function ExecutionFlowVisualization({ 
  config, 
  isSimulating, 
  onRunSimulation 
}: { 
  config: OrchestrationConfig; 
  isSimulating: boolean;
  onRunSimulation: () => void;
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Network className="w-5 h-5" />
            실행 흐름 시뮬레이션
          </CardTitle>
          <Button 
            onClick={onRunSimulation} 
            disabled={isSimulating}
            size="sm"
          >
            {isSimulating ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                시뮬레이션 중...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                시뮬레이션 실행
              </>
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {config.agentRoles
            .sort((a, b) => a.priority - b.priority)
            .map((agent, index) => (
              <div key={agent.id} className="flex items-center gap-4">
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium",
                  isSimulating && index === 0 ? "bg-blue-500 animate-pulse" : "bg-gray-400"
                )}>
                  {index + 1}
                </div>
                <div className="flex-1">
                  <div className="font-medium">{agent.name}</div>
                  <div className="text-sm text-gray-600">{AGENT_ROLES[agent.role].name}</div>
                </div>
                <Badge variant="outline">우선순위 {agent.priority}</Badge>
              </div>
            ))}
        </div>
      </CardContent>
    </Card>
  );
}

// 성능 지표 뷰 컴포넌트
function PerformanceMetricsView({ config }: { config: OrchestrationConfig }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            성능 임계값
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">최대 실행 시간</span>
            <span className="font-medium">{Math.round(config.performanceThresholds.maxExecutionTime / 1000)}초</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">최소 성공률</span>
            <span className="font-medium">{Math.round(config.performanceThresholds.minSuccessRate * 100)}%</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">최대 토큰 사용량</span>
            <span className="font-medium">{config.performanceThresholds.maxTokenUsage.toLocaleString()}</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            예상 지표
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">예상 응답 시간</span>
            <span className="font-medium">{calculateEstimatedResponseTime(config)}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">예상 비용 효율성</span>
            <span className="font-medium">{calculateCostEfficiency(config)}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">복잡도</span>
            <Badge variant="outline">
              {ORCHESTRATION_TYPES[config.orchestrationType].complexity}
            </Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}