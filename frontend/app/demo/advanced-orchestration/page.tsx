"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Network, 
  Brain, 
  Zap, 
  Target, 
  Users, 
  GitBranch,
  BarChart3,
  Play,
  RefreshCw,
  TrendingUp,
  CheckCircle,
  Clock,
  Cpu,
  Database,
  AlertTriangle,
  Info
} from 'lucide-react';

interface DemoScenario {
  id: string;
  name: string;
  description: string;
  complexity: 'simple' | 'moderate' | 'complex' | 'expert';
  task_type: string;
  requirements: Record<string, any>;
  expected_pattern: string;
}

const demoScenarios: DemoScenario[] = [
  {
    id: 'multimodal_analysis',
    name: '멀티모달 콘텐츠 분석',
    description: '이미지, 텍스트, 오디오를 종합 분석하여 콘텐츠의 감정과 주제를 파악',
    complexity: 'complex',
    task_type: 'multimodal_fusion',
    requirements: {
      accuracy_threshold: 0.9,
      multi_step: true,
      real_time: false
    },
    expected_pattern: 'ensemble'
  },
  {
    id: 'document_processing',
    name: '대용량 문서 처리 파이프라인',
    description: 'PDF 문서를 OCR → 텍스트 추출 → 요약 → 번역 순서로 처리',
    complexity: 'moderate',
    task_type: 'document_processing',
    requirements: {
      batch_size: 100,
      quality_check: true
    },
    expected_pattern: 'pipeline'
  },
  {
    id: 'creative_collaboration',
    name: '창작 콘텐츠 생성',
    description: '여러 AI가 협업하여 스토리, 이미지, 음악을 동시에 생성',
    complexity: 'expert',
    task_type: 'creative_generation',
    requirements: {
      creativity_level: 'high',
      coherence: true,
      multi_modal_output: true
    },
    expected_pattern: 'peer_to_peer'
  },
  {
    id: 'research_synthesis',
    name: '연구 논문 종합 분석',
    description: '다수의 논문을 분석하여 연구 동향과 핵심 인사이트 도출',
    complexity: 'expert',
    task_type: 'research_synthesis',
    requirements: {
      depth: 'comprehensive',
      citation_analysis: true,
      trend_detection: true
    },
    expected_pattern: 'hierarchical'
  }
];

const AdvancedOrchestrationDemo: React.FC = () => {
  const [activeTab, setActiveTab] = useState('scenarios');
  const [selectedScenario, setSelectedScenario] = useState<DemoScenario | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [decompositionResult, setDecompositionResult] = useState<any>(null);
  const [collaborationResult, setCollaborationResult] = useState<any>(null);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [performanceMetrics, setPerformanceMetrics] = useState<any>(null);
  const [systemStatus, setSystemStatus] = useState<any>(null);

  useEffect(() => {
    loadSystemStatus();
    const interval = setInterval(loadSystemStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadSystemStatus = async () => {
    try {
      const response = await fetch('/api/agent-builder/advanced-orchestration/performance-analytics');
      if (response.ok) {
        const result = await response.json();
        setPerformanceMetrics(result.analytics);
        setSystemStatus(result.analytics.system_overview);
      }
    } catch (error) {
      console.error('Failed to load system status:', error);
    }
  };

  const runCompleteDemo = async (scenario: DemoScenario) => {
    setSelectedScenario(scenario);
    setIsProcessing(true);
    setDecompositionResult(null);
    setCollaborationResult(null);
    setExecutionResult(null);

    try {
      // 1단계: 작업 복잡도 분석
      console.log('🔍 작업 복잡도 분석 중...');
      
      // 2단계: 지능형 작업 분해
      console.log('🧩 지능형 작업 분해 실행 중...');
      const decompositionResponse = await fetch('/api/agent-builder/advanced-orchestration/intelligent-decomposition', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task: {
            task_id: `demo_${scenario.id}_${Date.now()}`,
            task_type: scenario.task_type,
            priority: 'high',
            requirements: scenario.requirements,
            input_data: {
              scenario: scenario.name,
              description: scenario.description
            },
            estimated_duration: 120.0
          },
          complexity_threshold: scenario.complexity
        })
      });

      const decompositionData = await decompositionResponse.json();
      setDecompositionResult(decompositionData);

      if (decompositionData.success && decompositionData.decomposition_needed) {
        // 3단계: 협업 패턴 생성
        console.log('🤝 협업 패턴 생성 중...');
        const collaborationResponse = await fetch('/api/agent-builder/advanced-orchestration/collaboration-pattern', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            pattern_type: scenario.expected_pattern,
            tasks: decompositionData.decomposition.subtasks
          })
        });

        const collaborationData = await collaborationResponse.json();
        setCollaborationResult(collaborationData);

        if (collaborationData.success) {
          // 4단계: 협업 실행
          console.log('🚀 협업 워크플로우 실행 중...');
          const executionResponse = await fetch('/api/agent-builder/advanced-orchestration/collaborative-execution', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              collaboration_spec: collaborationData.collaboration_spec,
              tasks: decompositionData.decomposition.subtasks
            })
          });

          const executionData = await executionResponse.json();
          setExecutionResult(executionData);
        }
      }

      // 성능 메트릭 새로고침
      await loadSystemStatus();

    } catch (error) {
      console.error('Demo execution failed:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const triggerAdaptiveScaling = async () => {
    try {
      const response = await fetch('/api/agent-builder/advanced-orchestration/adaptive-scaling', {
        method: 'POST'
      });
      const result = await response.json();
      console.log('Scaling result:', result);
      await loadSystemStatus();
    } catch (error) {
      console.error('Scaling failed:', error);
    }
  };

  const triggerCrossAgentLearning = async () => {
    try {
      const response = await fetch('/api/agent-builder/advanced-orchestration/cross-agent-learning', {
        method: 'POST'
      });
      const result = await response.json();
      console.log('Learning result:', result);
      await loadSystemStatus();
    } catch (error) {
      console.error('Learning failed:', error);
    }
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'simple': return 'bg-green-100 text-green-800';
      case 'moderate': return 'bg-yellow-100 text-yellow-800';
      case 'complex': return 'bg-orange-100 text-orange-800';
      case 'expert': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const renderScenarios = () => (
    <div className="space-y-6">
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          다양한 복잡도의 시나리오를 통해 고급 다중 에이전트 오케스트레이션 기능을 체험해보세요.
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {demoScenarios.map((scenario) => (
          <Card key={scenario.id} className="cursor-pointer hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{scenario.name}</CardTitle>
                <Badge className={getComplexityColor(scenario.complexity)}>
                  {scenario.complexity}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 mb-4">{scenario.description}</p>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="font-medium">작업 유형:</span>
                  <span>{scenario.task_type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">예상 패턴:</span>
                  <Badge variant="outline">{scenario.expected_pattern}</Badge>
                </div>
              </div>

              <Button 
                onClick={() => runCompleteDemo(scenario)}
                disabled={isProcessing}
                className="w-full mt-4"
              >
                {isProcessing && selectedScenario?.id === scenario.id ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    실행 중...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    데모 실행
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderResults = () => (
    <div className="space-y-6">
      {selectedScenario && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Target className="w-5 h-5 mr-2" />
              실행 중인 시나리오: {selectedScenario.name}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600">{selectedScenario.description}</p>
          </CardContent>
        </Card>
      )}

      {decompositionResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <GitBranch className="w-5 h-5 mr-2" />
              1단계: 작업 분해 결과
            </CardTitle>
          </CardHeader>
          <CardContent>
            {decompositionResult.decomposition_needed ? (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="font-medium">하위 작업:</span> {decompositionResult.decomposition.subtasks.length}개
                  </div>
                  <div>
                    <span className="font-medium">병합 전략:</span> {decompositionResult.decomposition.merge_strategy}
                  </div>
                  <div>
                    <span className="font-medium">예상 개선:</span> {(decompositionResult.decomposition.estimated_improvement * 100).toFixed(1)}%
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-2">하위 작업:</h4>
                  <div className="space-y-2">
                    {decompositionResult.decomposition.subtasks.map((subtask: any, index: number) => (
                      <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <div>
                          <span className="font-medium">{subtask.task_id}</span>
                          <Badge variant="outline" className="ml-2">{subtask.task_type}</Badge>
                        </div>
                        <div className="text-sm text-gray-600">
                          {subtask.estimated_duration}초
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-gray-600">작업 복잡도가 임계값 이하로 분해가 필요하지 않습니다.</p>
            )}
          </CardContent>
        </Card>
      )}

      {collaborationResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Network className="w-5 h-5 mr-2" />
              2단계: 협업 패턴 생성
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">패턴:</span> {collaborationResult.collaboration_spec.pattern}
                </div>
                <div>
                  <span className="font-medium">참여자:</span> {collaborationResult.collaboration_spec.participants.length}명
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-2">참여 에이전트:</h4>
                <div className="flex flex-wrap gap-2">
                  {collaborationResult.collaboration_spec.participants.map((agent: string, index: number) => (
                    <Badge key={index} variant="secondary">{agent}</Badge>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-2">동기화 포인트:</h4>
                <div className="flex flex-wrap gap-2">
                  {collaborationResult.collaboration_spec.synchronization_points.map((point: string, index: number) => (
                    <Badge key={index} variant="outline">{point}</Badge>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {executionResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <CheckCircle className="w-5 h-5 mr-2 text-green-600" />
              3단계: 실행 결과
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex justify-between">
                  <span>실행 ID:</span>
                  <span className="font-mono text-xs">{executionResult.execution_result.execution_id}</span>
                </div>
                <div className="flex justify-between">
                  <span>상태:</span>
                  <Badge variant={executionResult.execution_result.status === 'completed' ? 'default' : 'destructive'}>
                    {executionResult.execution_result.status}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span>패턴:</span>
                  <span>{executionResult.execution_result.pattern}</span>
                </div>
                {executionResult.execution_result.consensus_score && (
                  <div className="flex justify-between">
                    <span>합의 점수:</span>
                    <span>{(executionResult.execution_result.consensus_score * 100).toFixed(1)}%</span>
                  </div>
                )}
              </div>

              {executionResult.collaboration_analysis && (
                <div className="p-4 bg-green-50 rounded-lg">
                  <h4 className="font-medium text-green-800 mb-2">협업 분석</h4>
                  <div className="text-sm text-green-700 space-y-1">
                    <div>참여 에이전트: {executionResult.collaboration_analysis.participants}명</div>
                    <div>실행 상태: {executionResult.collaboration_analysis.execution_status}</div>
                    {executionResult.collaboration_analysis.efficiency_score && (
                      <div>효율성 점수: {(executionResult.collaboration_analysis.efficiency_score * 100).toFixed(1)}%</div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderSystemManagement = () => (
    <div className="space-y-6">
      {systemStatus && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <BarChart3 className="w-5 h-5 mr-2" />
              시스템 현황
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <Cpu className="w-8 h-8 mx-auto mb-2 text-blue-600" />
                <div className="text-2xl font-bold text-blue-600">{systemStatus.total_agents}</div>
                <div className="text-sm text-blue-700">총 에이전트</div>
              </div>
              
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <Clock className="w-8 h-8 mx-auto mb-2 text-green-600" />
                <div className="text-2xl font-bold text-green-600">{systemStatus.active_executions}</div>
                <div className="text-sm text-green-700">활성 실행</div>
              </div>
              
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <Database className="w-8 h-8 mx-auto mb-2 text-orange-600" />
                <div className="text-2xl font-bold text-orange-600">{systemStatus.task_queue_length}</div>
                <div className="text-sm text-orange-700">대기 작업</div>
              </div>
              
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                {systemStatus.learning_enabled ? (
                  <CheckCircle className="w-8 h-8 mx-auto mb-2 text-purple-600" />
                ) : (
                  <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-red-600" />
                )}
                <div className="text-sm font-medium text-purple-700">
                  {systemStatus.learning_enabled ? '학습 활성' : '학습 비활성'}
                </div>
                <div className="text-xs text-purple-600">교차 학습</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Button 
          onClick={triggerAdaptiveScaling}
          variant="outline"
          className="h-20"
        >
          <div className="text-center">
            <Zap className="w-6 h-6 mx-auto mb-1" />
            <div className="font-medium">적응적 스케일링</div>
            <div className="text-xs text-gray-600">시스템 부하에 따른 자동 조정</div>
          </div>
        </Button>

        <Button 
          onClick={triggerCrossAgentLearning}
          variant="outline"
          className="h-20"
        >
          <div className="text-center">
            <Brain className="w-6 h-6 mx-auto mb-1" />
            <div className="font-medium">교차 학습</div>
            <div className="text-xs text-gray-600">에이전트 간 지식 공유</div>
          </div>
        </Button>
      </div>
    </div>
  );

  const renderPerformanceAnalytics = () => (
    <div className="space-y-6">
      {performanceMetrics && performanceMetrics.agent_performance && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="w-5 h-5 mr-2" />
              에이전트 성능 분석
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(performanceMetrics.agent_performance).map(([agentId, metrics]: [string, any]) => (
                <div key={agentId} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium">{agentId}</h4>
                    <Badge variant="outline">
                      {(metrics.average_quality_score * 100).toFixed(1)}% 품질
                    </Badge>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>완료율</span>
                        <span>{(metrics.task_completion_rate * 100).toFixed(1)}%</span>
                      </div>
                      <Progress value={metrics.task_completion_rate * 100} className="h-2" />
                    </div>
                    
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>품질 점수</span>
                        <span>{(metrics.average_quality_score * 100).toFixed(1)}%</span>
                      </div>
                      <Progress value={metrics.average_quality_score * 100} className="h-2" />
                    </div>
                    
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>협업 효율성</span>
                        <span>{(metrics.collaboration_effectiveness * 100).toFixed(1)}%</span>
                      </div>
                      <Progress value={metrics.collaboration_effectiveness * 100} className="h-2" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-4 flex items-center">
          <Network className="w-8 h-8 mr-3 text-purple-600" />
          고급 다중 에이전트 오케스트레이션 데모
        </h1>
        <p className="text-gray-600 text-lg">
          지능형 작업 분해, 협업 패턴, 적응적 스케일링, 교차 학습 등 고급 기능을 체험해보세요.
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="scenarios">시나리오</TabsTrigger>
          <TabsTrigger value="results">실행 결과</TabsTrigger>
          <TabsTrigger value="system">시스템 관리</TabsTrigger>
          <TabsTrigger value="analytics">성능 분석</TabsTrigger>
        </TabsList>

        <TabsContent value="scenarios" className="mt-6">
          {renderScenarios()}
        </TabsContent>

        <TabsContent value="results" className="mt-6">
          {renderResults()}
        </TabsContent>

        <TabsContent value="system" className="mt-6">
          {renderSystemManagement()}
        </TabsContent>

        <TabsContent value="analytics" className="mt-6">
          {renderPerformanceAnalytics()}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdvancedOrchestrationDemo;