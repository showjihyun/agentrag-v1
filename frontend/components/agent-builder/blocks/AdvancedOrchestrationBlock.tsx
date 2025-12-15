"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Progress } from '@/components/ui/progress';
import { 
  Network, 
  Brain, 
  Zap, 
  Target, 
  Users, 
  GitBranch,
  BarChart3,
  Settings,
  Play,
  Pause,
  RefreshCw,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  Cpu,
  Database
} from 'lucide-react';

interface AdvancedOrchestrationBlockProps {
  id: string;
  data: any;
  onUpdate: (id: string, data: any) => void;
}

interface TaskDecomposition {
  original_task_id: string;
  subtasks: Array<{
    task_id: string;
    task_type: string;
    priority: string;
    estimated_duration: number;
    dependencies: string[];
  }>;
  dependencies: Record<string, string[]>;
  merge_strategy: string;
  estimated_improvement: number;
}

interface CollaborationPattern {
  pattern: string;
  participants: string[];
  coordination_rules: Record<string, any>;
  data_flow: Array<[string, string]>;
  synchronization_points: string[];
  quality_gates: Array<Record<string, any>>;
}

interface PerformanceMetrics {
  agent_performance: Record<string, {
    task_completion_rate: number;
    average_quality_score: number;
    collaboration_effectiveness: number;
    performance_trend: number[];
  }>;
  system_overview: {
    total_agents: number;
    active_executions: number;
    task_queue_length: number;
    learning_enabled: boolean;
    auto_scaling_enabled: boolean;
  };
}

const AdvancedOrchestrationBlock: React.FC<AdvancedOrchestrationBlockProps> = ({
  id,
  data,
  onUpdate
}) => {
  const [activeTab, setActiveTab] = useState('decomposition');
  const [isProcessing, setIsProcessing] = useState(false);
  const [taskDecomposition, setTaskDecomposition] = useState<TaskDecomposition | null>(null);
  const [collaborationPattern, setCollaborationPattern] = useState<CollaborationPattern | null>(null);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics | null>(null);
  const [executionResults, setExecutionResults] = useState<any>(null);

  // 작업 분해 설정
  const [taskConfig, setTaskConfig] = useState({
    task_type: data.task_type || 'multimodal_fusion',
    complexity_threshold: data.complexity_threshold || 'moderate',
    requirements: data.requirements || {},
    input_data: data.input_data || {}
  });

  // 협업 패턴 설정
  const [collaborationConfig, setCollaborationConfig] = useState({
    pattern_type: data.pattern_type || 'ensemble',
    participating_agents: data.participating_agents || [],
    coordination_rules: data.coordination_rules || {}
  });

  // 스케일링 및 학습 설정
  const [systemConfig, setSystemConfig] = useState({
    auto_scaling_enabled: data.auto_scaling_enabled ?? true,
    learning_enabled: data.learning_enabled ?? true,
    performance_monitoring: data.performance_monitoring ?? true
  });

  useEffect(() => {
    loadPerformanceMetrics();
    const interval = setInterval(loadPerformanceMetrics, 30000); // 30초마다 업데이트
    return () => clearInterval(interval);
  }, []);

  const loadPerformanceMetrics = async () => {
    try {
      const response = await fetch('/api/agent-builder/advanced-orchestration/performance-analytics');
      if (response.ok) {
        const result = await response.json();
        setPerformanceMetrics(result.analytics);
      }
    } catch (error) {
      console.error('Failed to load performance metrics:', error);
    }
  };

  const handleTaskDecomposition = async () => {
    setIsProcessing(true);
    try {
      const response = await fetch('/api/agent-builder/advanced-orchestration/intelligent-decomposition', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task: {
            task_id: `task_${Date.now()}`,
            task_type: taskConfig.task_type,
            priority: 'high',
            requirements: taskConfig.requirements,
            input_data: taskConfig.input_data,
            estimated_duration: 120.0
          },
          complexity_threshold: taskConfig.complexity_threshold
        })
      });

      const result = await response.json();
      if (result.success && result.decomposition_needed) {
        setTaskDecomposition(result.decomposition);
      }
    } catch (error) {
      console.error('Task decomposition failed:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCreateCollaborationPattern = async () => {
    setIsProcessing(true);
    try {
      const response = await fetch('/api/agent-builder/advanced-orchestration/collaboration-pattern', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pattern_type: collaborationConfig.pattern_type,
          tasks: taskDecomposition?.subtasks || [{
            task_id: 'sample_task',
            task_type: taskConfig.task_type,
            priority: 'medium',
            requirements: taskConfig.requirements,
            input_data: taskConfig.input_data,
            estimated_duration: 30.0,
            dependencies: []
          }],
          participating_agents: collaborationConfig.participating_agents.length > 0 
            ? collaborationConfig.participating_agents 
            : undefined
        })
      });

      const result = await response.json();
      if (result.success) {
        setCollaborationPattern(result.collaboration_spec);
      }
    } catch (error) {
      console.error('Collaboration pattern creation failed:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleExecuteCollaboration = async () => {
    if (!collaborationPattern) return;

    setIsProcessing(true);
    try {
      const response = await fetch('/api/agent-builder/advanced-orchestration/collaborative-execution', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          collaboration_spec: collaborationPattern,
          tasks: taskDecomposition?.subtasks || [{
            task_id: 'sample_task',
            task_type: taskConfig.task_type,
            priority: 'medium',
            requirements: taskConfig.requirements,
            input_data: taskConfig.input_data,
            estimated_duration: 30.0,
            dependencies: []
          }]
        })
      });

      const result = await response.json();
      if (result.success) {
        setExecutionResults(result.execution_result);
      }
    } catch (error) {
      console.error('Collaborative execution failed:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAdaptiveScaling = async () => {
    setIsProcessing(true);
    try {
      const response = await fetch('/api/agent-builder/advanced-orchestration/adaptive-scaling', {
        method: 'POST'
      });

      const result = await response.json();
      if (result.success) {
        // 스케일링 결과 표시
        console.log('Scaling result:', result.scaling_result);
        loadPerformanceMetrics(); // 메트릭 새로고침
      }
    } catch (error) {
      console.error('Adaptive scaling failed:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCrossAgentLearning = async () => {
    setIsProcessing(true);
    try {
      const response = await fetch('/api/agent-builder/advanced-orchestration/cross-agent-learning', {
        method: 'POST'
      });

      const result = await response.json();
      if (result.success) {
        // 학습 결과 표시
        console.log('Learning result:', result.learning_result);
        loadPerformanceMetrics(); // 메트릭 새로고침
      }
    } catch (error) {
      console.error('Cross-agent learning failed:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const updateData = (newData: any) => {
    const updatedData = { ...data, ...newData };
    onUpdate(id, updatedData);
  };

  const renderTaskDecomposition = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="task-type">작업 유형</Label>
          <Select
            value={taskConfig.task_type}
            onValueChange={(value) => setTaskConfig(prev => ({ ...prev, task_type: value }))}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="multimodal_fusion">멀티모달 융합</SelectItem>
              <SelectItem value="complex_reasoning">복잡한 추론</SelectItem>
              <SelectItem value="creative_generation">창작 생성</SelectItem>
              <SelectItem value="research_synthesis">연구 종합</SelectItem>
              <SelectItem value="image_analysis">이미지 분석</SelectItem>
              <SelectItem value="video_analysis">비디오 분석</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor="complexity-threshold">복잡도 임계값</Label>
          <Select
            value={taskConfig.complexity_threshold}
            onValueChange={(value) => setTaskConfig(prev => ({ ...prev, complexity_threshold: value }))}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="simple">단순</SelectItem>
              <SelectItem value="moderate">보통</SelectItem>
              <SelectItem value="complex">복잡</SelectItem>
              <SelectItem value="expert">전문가</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div>
        <Label htmlFor="requirements">요구사항 (JSON)</Label>
        <Textarea
          id="requirements"
          placeholder='{"accuracy_threshold": 0.9, "real_time": false}'
          value={JSON.stringify(taskConfig.requirements, null, 2)}
          onChange={(e) => {
            try {
              const requirements = JSON.parse(e.target.value);
              setTaskConfig(prev => ({ ...prev, requirements }));
            } catch (error) {
              // 유효하지 않은 JSON은 무시
            }
          }}
          className="h-24"
        />
      </div>

      <Button 
        onClick={handleTaskDecomposition} 
        disabled={isProcessing}
        className="w-full"
      >
        {isProcessing ? (
          <>
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            분해 중...
          </>
        ) : (
          <>
            <GitBranch className="w-4 h-4 mr-2" />
            작업 분해 실행
          </>
        )}
      </Button>

      {taskDecomposition && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Target className="w-5 h-5 mr-2" />
              분해 결과
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="font-medium">하위 작업:</span> {taskDecomposition.subtasks.length}개
                </div>
                <div>
                  <span className="font-medium">병합 전략:</span> {taskDecomposition.merge_strategy}
                </div>
                <div>
                  <span className="font-medium">예상 개선:</span> {(taskDecomposition.estimated_improvement * 100).toFixed(1)}%
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-2">하위 작업 목록:</h4>
                <div className="space-y-2">
                  {taskDecomposition.subtasks.map((subtask, index) => (
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
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderCollaborationPattern = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="pattern-type">협업 패턴</Label>
          <Select
            value={collaborationConfig.pattern_type}
            onValueChange={(value) => setCollaborationConfig(prev => ({ ...prev, pattern_type: value }))}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="pipeline">파이프라인</SelectItem>
              <SelectItem value="ensemble">앙상블</SelectItem>
              <SelectItem value="hierarchical">계층적</SelectItem>
              <SelectItem value="consensus">합의</SelectItem>
              <SelectItem value="peer_to_peer">P2P</SelectItem>
              <SelectItem value="competitive">경쟁적</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor="participating-agents">참여 에이전트 (선택사항)</Label>
          <Input
            id="participating-agents"
            placeholder="agent_1,agent_2,agent_3"
            value={collaborationConfig.participating_agents.join(',')}
            onChange={(e) => {
              const agents = e.target.value.split(',').map(s => s.trim()).filter(s => s);
              setCollaborationConfig(prev => ({ ...prev, participating_agents: agents }));
            }}
          />
        </div>
      </div>

      <Button 
        onClick={handleCreateCollaborationPattern} 
        disabled={isProcessing}
        className="w-full"
      >
        {isProcessing ? (
          <>
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            패턴 생성 중...
          </>
        ) : (
          <>
            <Network className="w-4 h-4 mr-2" />
            협업 패턴 생성
          </>
        )}
      </Button>

      {collaborationPattern && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Users className="w-5 h-5 mr-2" />
              협업 패턴
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">패턴:</span> {collaborationPattern.pattern}
                </div>
                <div>
                  <span className="font-medium">참여자:</span> {collaborationPattern.participants.length}명
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-2">참여 에이전트:</h4>
                <div className="flex flex-wrap gap-2">
                  {collaborationPattern.participants.map((agent, index) => (
                    <Badge key={index} variant="secondary">{agent}</Badge>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-2">동기화 포인트:</h4>
                <div className="flex flex-wrap gap-2">
                  {collaborationPattern.synchronization_points.map((point, index) => (
                    <Badge key={index} variant="outline">{point}</Badge>
                  ))}
                </div>
              </div>

              <Button 
                onClick={handleExecuteCollaboration} 
                disabled={isProcessing}
                className="w-full"
              >
                {isProcessing ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    실행 중...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    협업 실행
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {executionResults && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <CheckCircle className="w-5 h-5 mr-2 text-green-600" />
              실행 결과
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>실행 ID:</span>
                <span className="font-mono">{executionResults.execution_id}</span>
              </div>
              <div className="flex justify-between">
                <span>상태:</span>
                <Badge variant={executionResults.status === 'completed' ? 'default' : 'destructive'}>
                  {executionResults.status}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span>패턴:</span>
                <span>{executionResults.pattern}</span>
              </div>
              {executionResults.consensus_score && (
                <div className="flex justify-between">
                  <span>합의 점수:</span>
                  <span>{(executionResults.consensus_score * 100).toFixed(1)}%</span>
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
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <Label htmlFor="auto-scaling">자동 스케일링</Label>
          <Switch
            id="auto-scaling"
            checked={systemConfig.auto_scaling_enabled}
            onCheckedChange={(checked) => {
              setSystemConfig(prev => ({ ...prev, auto_scaling_enabled: checked }));
              updateData({ auto_scaling_enabled: checked });
            }}
          />
        </div>

        <div className="flex items-center justify-between">
          <Label htmlFor="learning">교차 학습</Label>
          <Switch
            id="learning"
            checked={systemConfig.learning_enabled}
            onCheckedChange={(checked) => {
              setSystemConfig(prev => ({ ...prev, learning_enabled: checked }));
              updateData({ learning_enabled: checked });
            }}
          />
        </div>

        <div className="flex items-center justify-between">
          <Label htmlFor="monitoring">성능 모니터링</Label>
          <Switch
            id="monitoring"
            checked={systemConfig.performance_monitoring}
            onCheckedChange={(checked) => {
              setSystemConfig(prev => ({ ...prev, performance_monitoring: checked }));
              updateData({ performance_monitoring: checked });
            }}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Button 
          onClick={handleAdaptiveScaling} 
          disabled={isProcessing}
          variant="outline"
        >
          {isProcessing ? (
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Zap className="w-4 h-4 mr-2" />
          )}
          적응적 스케일링
        </Button>

        <Button 
          onClick={handleCrossAgentLearning} 
          disabled={isProcessing}
          variant="outline"
        >
          {isProcessing ? (
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Brain className="w-4 h-4 mr-2" />
          )}
          교차 학습
        </Button>
      </div>

      {performanceMetrics && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <BarChart3 className="w-5 h-5 mr-2" />
              시스템 현황
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex items-center">
                <Cpu className="w-4 h-4 mr-2 text-blue-600" />
                <span>총 에이전트: {performanceMetrics.system_overview.total_agents}</span>
              </div>
              <div className="flex items-center">
                <Clock className="w-4 h-4 mr-2 text-green-600" />
                <span>활성 실행: {performanceMetrics.system_overview.active_executions}</span>
              </div>
              <div className="flex items-center">
                <Database className="w-4 h-4 mr-2 text-orange-600" />
                <span>대기 작업: {performanceMetrics.system_overview.task_queue_length}</span>
              </div>
              <div className="flex items-center">
                {performanceMetrics.system_overview.learning_enabled ? (
                  <CheckCircle className="w-4 h-4 mr-2 text-green-600" />
                ) : (
                  <AlertTriangle className="w-4 h-4 mr-2 text-red-600" />
                )}
                <span>학습: {performanceMetrics.system_overview.learning_enabled ? '활성' : '비활성'}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderPerformanceAnalytics = () => (
    <div className="space-y-6">
      {performanceMetrics && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <TrendingUp className="w-5 h-5 mr-2" />
                에이전트 성능
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(performanceMetrics.agent_performance).map(([agentId, metrics]) => (
                  <div key={agentId} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium">{agentId}</h4>
                      <Badge variant="outline">
                        {(metrics.average_quality_score * 100).toFixed(1)}% 품질
                      </Badge>
                    </div>
                    
                    <div className="space-y-2">
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>완료율</span>
                          <span>{(metrics.task_completion_rate * 100).toFixed(1)}%</span>
                        </div>
                        <Progress value={metrics.task_completion_rate * 100} className="h-2" />
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
        </>
      )}
    </div>
  );

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center">
          <Network className="w-6 h-6 mr-2 text-purple-600" />
          고급 다중 에이전트 오케스트레이션
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="decomposition">작업 분해</TabsTrigger>
            <TabsTrigger value="collaboration">협업 패턴</TabsTrigger>
            <TabsTrigger value="system">시스템 관리</TabsTrigger>
            <TabsTrigger value="analytics">성능 분석</TabsTrigger>
          </TabsList>

          <TabsContent value="decomposition" className="mt-6">
            {renderTaskDecomposition()}
          </TabsContent>

          <TabsContent value="collaboration" className="mt-6">
            {renderCollaborationPattern()}
          </TabsContent>

          <TabsContent value="system" className="mt-6">
            {renderSystemManagement()}
          </TabsContent>

          <TabsContent value="analytics" className="mt-6">
            {renderPerformanceAnalytics()}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default AdvancedOrchestrationBlock;