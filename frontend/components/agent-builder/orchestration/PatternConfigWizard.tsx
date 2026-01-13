'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  AlertCircle,
  Info,
  Settings,
  Users,
  MessageSquare,
  Clock,
  Target,
  Zap,
  Shield,
  Brain,
  Sparkles,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  ORCHESTRATION_TYPES,
  AGENT_ROLES,
  DEFAULT_SUPERVISOR_CONFIG,
  type OrchestrationTypeValue,
  type SupervisorConfig,
  type AgentRole,
} from '@/lib/constants/orchestration';

interface PatternConfigWizardProps {
  orchestrationType: OrchestrationTypeValue;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onComplete: (config: OrchestrationConfig) => void;
  initialConfig?: Partial<OrchestrationConfig>;
}

interface OrchestrationConfig {
  orchestrationType: OrchestrationTypeValue;
  name: string;
  description: string;
  supervisorConfig: SupervisorConfig;
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

const WIZARD_STEPS = [
  {
    id: 'basic',
    title: '기본 정보',
    description: '오케스트레이션의 기본 정보를 설정합니다',
    icon: Info,
  },
  {
    id: 'agents',
    title: 'Agent 구성',
    description: 'Agent 역할과 우선순위를 설정합니다',
    icon: Users,
  },
  {
    id: 'supervisor',
    title: 'Supervisor 설정',
    description: 'LLM 기반 조정자를 설정합니다',
    icon: Brain,
  },
  {
    id: 'communication',
    title: '통신 규칙',
    description: 'Agent 간 통신 방식을 설정합니다',
    icon: MessageSquare,
  },
  {
    id: 'performance',
    title: '성능 설정',
    description: '성능 임계값과 제한을 설정합니다',
    icon: Zap,
  },
  {
    id: 'review',
    title: '검토 및 완료',
    description: '설정을 검토하고 완료합니다',
    icon: CheckCircle2,
  },
];

export const PatternConfigWizard: React.FC<PatternConfigWizardProps> = ({
  orchestrationType,
  open,
  onOpenChange,
  onComplete,
  initialConfig,
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [config, setConfig] = useState<OrchestrationConfig>(() => ({
    orchestrationType,
    name: '',
    description: '',
    supervisorConfig: { ...DEFAULT_SUPERVISOR_CONFIG },
    agentRoles: [],
    communicationRules: {
      allowDirectCommunication: true,
      enableBroadcast: false,
      requireConsensus: false,
      maxNegotiationRounds: 3,
    },
    performanceThresholds: {
      maxExecutionTime: 300000, // 5분
      minSuccessRate: 0.8,
      maxTokenUsage: 10000,
    },
    tags: [],
    ...initialConfig,
  }));

  const pattern = ORCHESTRATION_TYPES[orchestrationType];
  const currentStepInfo = WIZARD_STEPS[currentStep];
  const progress = ((currentStep + 1) / WIZARD_STEPS.length) * 100;

  // 패턴별 기본 Agent 역할 추천
  const getRecommendedAgentRoles = (type: OrchestrationTypeValue) => {
    const roleMap: Record<OrchestrationTypeValue, Array<{ name: string; role: AgentRole; priority: number }>> = {
      sequential: [
        { name: '데이터 수집가', role: 'worker', priority: 1 },
        { name: '분석가', role: 'worker', priority: 2 },
        { name: '보고서 작성자', role: 'synthesizer', priority: 3 },
      ],
      parallel: [
        { name: '검색 전문가', role: 'specialist', priority: 1 },
        { name: '번역가', role: 'specialist', priority: 1 },
        { name: '요약 전문가', role: 'specialist', priority: 1 },
        { name: '결과 통합자', role: 'synthesizer', priority: 2 },
      ],
      hierarchical: [
        { name: '프로젝트 매니저', role: 'manager', priority: 1 },
        { name: '연구원 A', role: 'worker', priority: 2 },
        { name: '연구원 B', role: 'worker', priority: 2 },
        { name: '품질 검토자', role: 'critic', priority: 3 },
      ],
      consensus_building: [
        { name: '전문가 A', role: 'specialist', priority: 1 },
        { name: '전문가 B', role: 'specialist', priority: 1 },
        { name: '전문가 C', role: 'specialist', priority: 1 },
        { name: '중재자', role: 'coordinator', priority: 2 },
      ],
      swarm_intelligence: [
        { name: '탐색자 1', role: 'worker', priority: 1 },
        { name: '탐색자 2', role: 'worker', priority: 1 },
        { name: '탐색자 3', role: 'worker', priority: 1 },
        { name: '조율자', role: 'coordinator', priority: 2 },
      ],
      // 다른 패턴들도 추가 가능
      adaptive: [
        { name: '상황 분석가', role: 'specialist', priority: 1 },
        { name: '전략 수립자', role: 'manager', priority: 2 },
        { name: '실행자', role: 'worker', priority: 3 },
      ],
      dynamic_routing: [
        { name: '라우터', role: 'coordinator', priority: 1 },
        { name: '처리기 A', role: 'worker', priority: 2 },
        { name: '처리기 B', role: 'worker', priority: 2 },
        { name: '집계자', role: 'synthesizer', priority: 3 },
      ],
      event_driven: [
        { name: '이벤트 감지기', role: 'specialist', priority: 1 },
        { name: '처리기', role: 'worker', priority: 2 },
        { name: '응답자', role: 'worker', priority: 3 },
      ],
      reflection: [
        { name: '분석가', role: 'worker', priority: 1 },
        { name: '검토자', role: 'critic', priority: 2 },
        { name: '개선자', role: 'synthesizer', priority: 3 },
      ],
      neuromorphic: [
        { name: '뉴런 A', role: 'worker', priority: 1 },
        { name: '뉴런 B', role: 'worker', priority: 1 },
        { name: '시냅스', role: 'coordinator', priority: 2 },
      ],
      quantum_enhanced: [
        { name: '양자 분석가', role: 'specialist', priority: 1 },
        { name: '중첩 처리기', role: 'worker', priority: 2 },
        { name: '측정자', role: 'synthesizer', priority: 3 },
      ],
      bio_inspired: [
        { name: '센서', role: 'specialist', priority: 1 },
        { name: '프로세서', role: 'worker', priority: 2 },
        { name: '액추에이터', role: 'synthesizer', priority: 3 },
      ],
      self_evolving: [
        { name: '학습자', role: 'worker', priority: 1 },
        { name: '적응자', role: 'coordinator', priority: 2 },
        { name: '진화자', role: 'synthesizer', priority: 3 },
      ],
      federated: [
        { name: '로컬 에이전트 A', role: 'worker', priority: 1 },
        { name: '로컬 에이전트 B', role: 'worker', priority: 1 },
        { name: '글로벌 조율자', role: 'coordinator', priority: 2 },
        { name: '동기화자', role: 'synthesizer', priority: 3 },
      ],
      emotional_ai: [
        { name: '감정 분석가', role: 'specialist', priority: 1 },
        { name: '공감 에이전트', role: 'worker', priority: 2 },
        { name: '반응 조절자', role: 'coordinator', priority: 3 },
      ],
      predictive: [
        { name: '예측자', role: 'specialist', priority: 1 },
        { name: '검증자', role: 'critic', priority: 2 },
        { name: '조정자', role: 'coordinator', priority: 3 },
      ],
    };
    
    return roleMap[type] || [
      { name: '범용 에이전트', role: 'worker', priority: 1 },
      { name: '전문가', role: 'specialist', priority: 2 },
      { name: '조율자', role: 'coordinator', priority: 3 },
    ];
  };

  // 추천 Agent 역할 적용
  const applyRecommendedRoles = () => {
    const recommended = getRecommendedAgentRoles(orchestrationType);
    const newRoles = recommended.map((rec, index) => ({
      id: `agent_${index + 1}`,
      name: rec.name,
      role: rec.role,
      priority: rec.priority,
      maxRetries: 3,
      timeoutSeconds: 300,
      dependencies: [],
    }));
    
    setConfig(prev => ({ ...prev, agentRoles: newRoles }));
  };

  const handleNext = () => {
    if (currentStep < WIZARD_STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = () => {
    onComplete(config);
    onOpenChange(false);
  };

  const isStepValid = (stepIndex: number): boolean => {
    switch (stepIndex) {
      case 0: // 기본 정보
        return config.name.trim() !== '';
      case 1: // Agent 구성
        return config.agentRoles.length > 0;
      case 2: // Supervisor 설정
        return !config.supervisorConfig.enabled || 
               (config.supervisorConfig.llm_provider !== '' && config.supervisorConfig.llm_model !== '');
      case 3: // 통신 규칙
        return true; // 기본값이 있으므로 항상 유효
      case 4: // 성능 설정
        return config.performanceThresholds.maxExecutionTime > 0 &&
               config.performanceThresholds.minSuccessRate > 0 &&
               config.performanceThresholds.maxTokenUsage > 0;
      default:
        return true;
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0: // 기본 정보
        return (
          <div className="space-y-6">
            <div>
              <Label htmlFor="name">오케스트레이션 이름 *</Label>
              <Input
                id="name"
                value={config.name}
                onChange={(e) => setConfig(prev => ({ ...prev, name: e.target.value }))}
                placeholder="예: 고객 문의 처리 시스템"
                className="mt-1"
              />
            </div>
            
            <div>
              <Label htmlFor="description">설명</Label>
              <Textarea
                id="description"
                value={config.description}
                onChange={(e) => setConfig(prev => ({ ...prev, description: e.target.value }))}
                placeholder="이 오케스트레이션의 목적과 기능을 설명해주세요"
                className="mt-1"
                rows={3}
              />
            </div>
            
            <div>
              <Label>태그</Label>
              <div className="mt-1 flex flex-wrap gap-2">
                {config.tags.map((tag, index) => (
                  <Badge key={index} variant="secondary" className="cursor-pointer"
                    onClick={() => setConfig(prev => ({
                      ...prev,
                      tags: prev.tags.filter((_, i) => i !== index)
                    }))}>
                    {tag} ×
                  </Badge>
                ))}
                <Input
                  placeholder="태그 추가 (Enter로 추가)"
                  className="w-32"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                      const newTag = e.currentTarget.value.trim();
                      if (!config.tags.includes(newTag)) {
                        setConfig(prev => ({ ...prev, tags: [...prev.tags, newTag] }));
                      }
                      e.currentTarget.value = '';
                    }
                  }}
                />
              </div>
            </div>
          </div>
        );
        
      case 1: // Agent 구성
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Agent 역할 구성</h3>
                <p className="text-sm text-gray-600">
                  {pattern.name} 패턴에 필요한 Agent들을 구성하세요
                </p>
              </div>
              <Button variant="outline" onClick={applyRecommendedRoles}>
                <Sparkles className="w-4 h-4 mr-2" />
                추천 역할 적용
              </Button>
            </div>
            
            <div className="space-y-4">
              {config.agentRoles.map((agent, index) => (
                <Card key={agent.id} className="p-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Agent 이름</Label>
                      <Input
                        value={agent.name}
                        onChange={(e) => {
                          const newRoles = [...config.agentRoles];
                          newRoles[index].name = e.target.value;
                          setConfig(prev => ({ ...prev, agentRoles: newRoles }));
                        }}
                        placeholder="Agent 이름"
                      />
                    </div>
                    <div>
                      <Label>역할</Label>
                      <Select
                        value={agent.role}
                        onValueChange={(value: AgentRole) => {
                          const newRoles = [...config.agentRoles];
                          newRoles[index].role = value;
                          setConfig(prev => ({ ...prev, agentRoles: newRoles }));
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.entries(AGENT_ROLES).map(([key, role]) => (
                            <SelectItem key={key} value={key}>
                              {role.name} - {role.description}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>우선순위</Label>
                      <Select
                        value={agent.priority.toString()}
                        onValueChange={(value) => {
                          const newRoles = [...config.agentRoles];
                          newRoles[index].priority = parseInt(value);
                          setConfig(prev => ({ ...prev, agentRoles: newRoles }));
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {[1, 2, 3, 4, 5].map(priority => (
                            <SelectItem key={priority} value={priority.toString()}>
                              {priority} (높을수록 우선)
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>타임아웃 (초)</Label>
                      <Input
                        type="number"
                        value={agent.timeoutSeconds}
                        onChange={(e) => {
                          const newRoles = [...config.agentRoles];
                          newRoles[index].timeoutSeconds = parseInt(e.target.value) || 300;
                          setConfig(prev => ({ ...prev, agentRoles: newRoles }));
                        }}
                        min={30}
                        max={3600}
                      />
                    </div>
                  </div>
                  <div className="mt-4 flex justify-end">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const newRoles = config.agentRoles.filter((_, i) => i !== index);
                        setConfig(prev => ({ ...prev, agentRoles: newRoles }));
                      }}
                    >
                      제거
                    </Button>
                  </div>
                </Card>
              ))}
              
              <Button
                variant="outline"
                className="w-full"
                onClick={() => {
                  const newAgent = {
                    id: `agent_${config.agentRoles.length + 1}`,
                    name: `Agent ${config.agentRoles.length + 1}`,
                    role: 'worker' as AgentRole,
                    priority: 1,
                    maxRetries: 3,
                    timeoutSeconds: 300,
                    dependencies: [],
                  };
                  setConfig(prev => ({ ...prev, agentRoles: [...prev.agentRoles, newAgent] }));
                }}
              >
                + Agent 추가
              </Button>
            </div>
          </div>
        );
        
      case 2: // Supervisor 설정
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold">Supervisor 설정</h3>
              <p className="text-sm text-gray-600">
                LLM 기반 지능형 조정자를 설정합니다
              </p>
            </div>
            
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="enableSupervisor"
                checked={config.supervisorConfig.enabled}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  supervisorConfig: { ...prev.supervisorConfig, enabled: e.target.checked }
                }))}
              />
              <Label htmlFor="enableSupervisor">Supervisor 활성화</Label>
            </div>
            
            {config.supervisorConfig.enabled && (
              <div className="space-y-4 pl-6 border-l-2 border-blue-200">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>LLM 제공자</Label>
                    <Select
                      value={config.supervisorConfig.llm_provider}
                      onValueChange={(value) => setConfig(prev => ({
                        ...prev,
                        supervisorConfig: { ...prev.supervisorConfig, llm_provider: value }
                      }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="ollama">Ollama (로컬)</SelectItem>
                        <SelectItem value="openai">OpenAI</SelectItem>
                        <SelectItem value="claude">Claude</SelectItem>
                        <SelectItem value="google">Google AI</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>모델</Label>
                    <Select
                      value={config.supervisorConfig.llm_model}
                      onValueChange={(value) => setConfig(prev => ({
                        ...prev,
                        supervisorConfig: { ...prev.supervisorConfig, llm_model: value }
                      }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {config.supervisorConfig.llm_provider === 'ollama' && (
                          <>
                            <SelectItem value="llama3.1">Llama 3.1</SelectItem>
                            <SelectItem value="mistral">Mistral</SelectItem>
                            <SelectItem value="codellama">Code Llama</SelectItem>
                          </>
                        )}
                        {config.supervisorConfig.llm_provider === 'openai' && (
                          <>
                            <SelectItem value="gpt-4">GPT-4</SelectItem>
                            <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                          </>
                        )}
                        {config.supervisorConfig.llm_provider === 'claude' && (
                          <>
                            <SelectItem value="claude-3-opus">Claude 3 Opus</SelectItem>
                            <SelectItem value="claude-3-sonnet">Claude 3 Sonnet</SelectItem>
                          </>
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                <div>
                  <Label>의사결정 전략</Label>
                  <Select
                    value={config.supervisorConfig.decision_strategy}
                    onValueChange={(value: any) => setConfig(prev => ({
                      ...prev,
                      supervisorConfig: { ...prev.supervisorConfig, decision_strategy: value }
                    }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="llm_based">LLM 기반 결정</SelectItem>
                      <SelectItem value="consensus">합의 기반</SelectItem>
                      <SelectItem value="weighted_voting">가중 투표</SelectItem>
                      <SelectItem value="expert_system">전문가 시스템</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label>최대 반복 횟수</Label>
                  <Input
                    type="number"
                    value={config.supervisorConfig.max_iterations}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      supervisorConfig: { ...prev.supervisorConfig, max_iterations: parseInt(e.target.value) || 10 }
                    }))}
                    min={1}
                    max={50}
                  />
                </div>
              </div>
            )}
          </div>
        );
        
      case 3: // 통신 규칙
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold">Agent 간 통신 규칙</h3>
              <p className="text-sm text-gray-600">
                Agent들이 서로 소통하는 방식을 설정합니다
              </p>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="allowDirectCommunication"
                  checked={config.communicationRules.allowDirectCommunication}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    communicationRules: { ...prev.communicationRules, allowDirectCommunication: e.target.checked }
                  }))}
                />
                <Label htmlFor="allowDirectCommunication">직접 통신 허용</Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="enableBroadcast"
                  checked={config.communicationRules.enableBroadcast}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    communicationRules: { ...prev.communicationRules, enableBroadcast: e.target.checked }
                  }))}
                />
                <Label htmlFor="enableBroadcast">브로드캐스트 통신 활성화</Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="requireConsensus"
                  checked={config.communicationRules.requireConsensus}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    communicationRules: { ...prev.communicationRules, requireConsensus: e.target.checked }
                  }))}
                />
                <Label htmlFor="requireConsensus">합의 필요</Label>
              </div>
              
              <div>
                <Label>최대 협상 라운드</Label>
                <Input
                  type="number"
                  value={config.communicationRules.maxNegotiationRounds}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    communicationRules: { ...prev.communicationRules, maxNegotiationRounds: parseInt(e.target.value) || 3 }
                  }))}
                  min={1}
                  max={10}
                  className="mt-1"
                />
              </div>
            </div>
          </div>
        );
        
      case 4: // 성능 설정
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold">성능 임계값</h3>
              <p className="text-sm text-gray-600">
                오케스트레이션의 성능 제한과 임계값을 설정합니다
              </p>
            </div>
            
            <div className="space-y-4">
              <div>
                <Label>최대 실행 시간 (밀리초)</Label>
                <Input
                  type="number"
                  value={config.performanceThresholds.maxExecutionTime}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    performanceThresholds: { ...prev.performanceThresholds, maxExecutionTime: parseInt(e.target.value) || 300000 }
                  }))}
                  min={10000}
                  max={3600000}
                  className="mt-1"
                />
                <p className="text-xs text-gray-500 mt-1">
                  현재: {Math.round(config.performanceThresholds.maxExecutionTime / 1000)}초
                </p>
              </div>
              
              <div>
                <Label>최소 성공률</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={config.performanceThresholds.minSuccessRate}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    performanceThresholds: { ...prev.performanceThresholds, minSuccessRate: parseFloat(e.target.value) || 0.8 }
                  }))}
                  min={0.1}
                  max={1.0}
                  className="mt-1"
                />
                <p className="text-xs text-gray-500 mt-1">
                  현재: {Math.round(config.performanceThresholds.minSuccessRate * 100)}%
                </p>
              </div>
              
              <div>
                <Label>최대 토큰 사용량</Label>
                <Input
                  type="number"
                  value={config.performanceThresholds.maxTokenUsage}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    performanceThresholds: { ...prev.performanceThresholds, maxTokenUsage: parseInt(e.target.value) || 10000 }
                  }))}
                  min={1000}
                  max={100000}
                  className="mt-1"
                />
              </div>
            </div>
          </div>
        );
        
      case 5: // 검토 및 완료
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold">설정 검토</h3>
              <p className="text-sm text-gray-600">
                설정한 내용을 검토하고 완료하세요
              </p>
            </div>
            
            <ScrollArea className="h-[400px] space-y-4">
              <Card className="p-4">
                <h4 className="font-semibold mb-2">기본 정보</h4>
                <div className="space-y-1 text-sm">
                  <div><strong>이름:</strong> {config.name}</div>
                  <div><strong>패턴:</strong> {pattern.name}</div>
                  <div><strong>설명:</strong> {config.description || '없음'}</div>
                  <div><strong>태그:</strong> {config.tags.join(', ') || '없음'}</div>
                </div>
              </Card>
              
              <Card className="p-4">
                <h4 className="font-semibold mb-2">Agent 구성 ({config.agentRoles.length}개)</h4>
                <div className="space-y-2">
                  {config.agentRoles.map((agent, index) => (
                    <div key={index} className="text-sm flex items-center justify-between">
                      <span>{agent.name} ({AGENT_ROLES[agent.role].name})</span>
                      <Badge variant="outline">우선순위 {agent.priority}</Badge>
                    </div>
                  ))}
                </div>
              </Card>
              
              <Card className="p-4">
                <h4 className="font-semibold mb-2">Supervisor</h4>
                <div className="text-sm">
                  {config.supervisorConfig.enabled ? (
                    <div className="space-y-1">
                      <div><strong>활성화:</strong> 예</div>
                      <div><strong>LLM:</strong> {config.supervisorConfig.llm_provider} / {config.supervisorConfig.llm_model}</div>
                      <div><strong>전략:</strong> {config.supervisorConfig.decision_strategy}</div>
                    </div>
                  ) : (
                    <div>비활성화</div>
                  )}
                </div>
              </Card>
              
              <Card className="p-4">
                <h4 className="font-semibold mb-2">통신 규칙</h4>
                <div className="space-y-1 text-sm">
                  <div><strong>직접 통신:</strong> {config.communicationRules.allowDirectCommunication ? '허용' : '비허용'}</div>
                  <div><strong>브로드캐스트:</strong> {config.communicationRules.enableBroadcast ? '활성화' : '비활성화'}</div>
                  <div><strong>합의 필요:</strong> {config.communicationRules.requireConsensus ? '예' : '아니오'}</div>
                  <div><strong>최대 협상 라운드:</strong> {config.communicationRules.maxNegotiationRounds}</div>
                </div>
              </Card>
              
              <Card className="p-4">
                <h4 className="font-semibold mb-2">성능 설정</h4>
                <div className="space-y-1 text-sm">
                  <div><strong>최대 실행 시간:</strong> {Math.round(config.performanceThresholds.maxExecutionTime / 1000)}초</div>
                  <div><strong>최소 성공률:</strong> {Math.round(config.performanceThresholds.minSuccessRate * 100)}%</div>
                  <div><strong>최대 토큰 사용량:</strong> {config.performanceThresholds.maxTokenUsage.toLocaleString()}</div>
                </div>
              </Card>
            </ScrollArea>
          </div>
        );
        
      default:
        return null;
    }
  };

  if (!pattern) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            {pattern.name} 설정 마법사
          </DialogTitle>
          <DialogDescription>
            단계별로 오케스트레이션을 설정합니다
          </DialogDescription>
        </DialogHeader>

        <div className="flex gap-6 h-[600px]">
          {/* 단계 네비게이션 */}
          <div className="w-64 border-r pr-4">
            <div className="mb-4">
              <div className="text-sm text-gray-600 mb-2">진행률</div>
              <Progress value={progress} className="h-2" />
              <div className="text-xs text-gray-500 mt-1">{currentStep + 1} / {WIZARD_STEPS.length}</div>
            </div>
            
            <div className="space-y-2">
              {WIZARD_STEPS.map((step, index) => {
                const StepIcon = step.icon;
                const isCompleted = index < currentStep;
                const isCurrent = index === currentStep;
                const isValid = isStepValid(index);
                
                return (
                  <div
                    key={step.id}
                    className={cn(
                      'flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors',
                      isCurrent && 'bg-blue-50 border border-blue-200',
                      isCompleted && 'bg-green-50',
                      !isValid && index <= currentStep && 'bg-red-50'
                    )}
                    onClick={() => setCurrentStep(index)}
                  >
                    <div className={cn(
                      'p-1 rounded',
                      isCurrent && 'bg-blue-500 text-white',
                      isCompleted && 'bg-green-500 text-white',
                      !isValid && index <= currentStep && 'bg-red-500 text-white',
                      !isCurrent && !isCompleted && isValid && 'bg-gray-200'
                    )}>
                      {isCompleted ? (
                        <CheckCircle2 className="w-4 h-4" />
                      ) : !isValid && index <= currentStep ? (
                        <AlertCircle className="w-4 h-4" />
                      ) : (
                        <StepIcon className="w-4 h-4" />
                      )}
                    </div>
                    <div>
                      <div className="text-sm font-medium">{step.title}</div>
                      <div className="text-xs text-gray-500">{step.description}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 단계 내용 */}
          <div className="flex-1 overflow-y-auto">
            <div className="mb-6">
              <h2 className="text-xl font-semibold">{currentStepInfo.title}</h2>
              <p className="text-gray-600">{currentStepInfo.description}</p>
            </div>
            
            {renderStepContent()}
          </div>
        </div>

        {/* 하단 버튼 */}
        <div className="flex items-center justify-between pt-4 border-t">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={currentStep === 0}
          >
            <ChevronLeft className="w-4 h-4 mr-2" />
            이전
          </Button>
          
          <div className="flex gap-2">
            {currentStep === WIZARD_STEPS.length - 1 ? (
              <Button onClick={handleComplete} disabled={!isStepValid(currentStep)}>
                <CheckCircle2 className="w-4 h-4 mr-2" />
                완료
              </Button>
            ) : (
              <Button onClick={handleNext} disabled={!isStepValid(currentStep)}>
                다음
                <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};