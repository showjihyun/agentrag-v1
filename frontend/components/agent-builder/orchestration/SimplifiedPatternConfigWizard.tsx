/**
 * Simplified Pattern Config Wizard (4-Step)
 * 간소화된 패턴 설정 마법사 (4단계)
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Switch } from '@/components/ui/switch';
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
  Users,
  Settings,
  Eye,
  Sparkles,
  Lightbulb,
  Zap,
  Clock,
  Target,
  Shield
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
import { useRealTimeValidation } from '@/hooks/useRealTimeValidation';
import { RealTimeValidationFeedback } from '@/components/agent-builder/validation/RealTimeValidationFeedback';

interface SimplifiedPatternConfigWizardProps {
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

// 간소화된 4단계 마법사
const SIMPLIFIED_WIZARD_STEPS = [
  {
    id: 'basic',
    title: '기본 설정',
    description: '이름, 설명 및 기본 옵션 설정',
    icon: Info,
  },
  {
    id: 'agents',
    title: 'Agent 구성',
    description: 'AI Agent 역할 및 구성 설정',
    icon: Users,
  },
  {
    id: 'advanced',
    title: '고급 설정',
    description: 'Supervisor, 통신 규칙, 성능 설정',
    icon: Settings,
  },
  {
    id: 'review',
    title: '검토 및 완료',
    description: '설정 검토 및 최종 확인',
    icon: Eye,
  },
];

// 패턴별 스마트 기본값
const SMART_DEFAULTS = {
  sequential: {
    name: '순차 처리 워크플로우',
    description: '작업을 순서대로 처리하는 워크플로우입니다.',
    agentRoles: [
      { name: '데이터 수집가', role: 'worker', priority: 1 },
      { name: '분석가', role: 'specialist', priority: 2 },
      { name: '보고서 작성자', role: 'synthesizer', priority: 3 },
    ],
    supervisorEnabled: false,
    communicationRules: {
      allowDirectCommunication: true,
      enableBroadcast: false,
      requireConsensus: false,
      maxNegotiationRounds: 1,
    },
    performanceThresholds: {
      maxExecutionTime: 300000, // 5분
      minSuccessRate: 0.9,
      maxTokenUsage: 5000,
    },
    tags: ['순차처리', '워크플로우', '자동화'],
  },
  parallel: {
    name: '병렬 처리 시스템',
    description: '여러 작업을 동시에 처리하는 시스템입니다.',
    agentRoles: [
      { name: '검색 전문가', role: 'specialist', priority: 1 },
      { name: '번역가', role: 'specialist', priority: 1 },
      { name: '요약 전문가', role: 'specialist', priority: 1 },
      { name: '결과 통합자', role: 'synthesizer', priority: 2 },
    ],
    supervisorEnabled: true,
    communicationRules: {
      allowDirectCommunication: true,
      enableBroadcast: true,
      requireConsensus: false,
      maxNegotiationRounds: 2,
    },
    performanceThresholds: {
      maxExecutionTime: 180000, // 3분
      minSuccessRate: 0.85,
      maxTokenUsage: 8000,
    },
    tags: ['병렬처리', '동시실행', '효율성'],
  },
  consensus_building: {
    name: '합의 기반 의사결정',
    description: '여러 전문가의 의견을 수렴하여 합의를 도출합니다.',
    agentRoles: [
      { name: '전문가 A', role: 'specialist', priority: 1 },
      { name: '전문가 B', role: 'specialist', priority: 1 },
      { name: '전문가 C', role: 'specialist', priority: 1 },
      { name: '중재자', role: 'coordinator', priority: 2 },
    ],
    supervisorEnabled: true,
    communicationRules: {
      allowDirectCommunication: true,
      enableBroadcast: true,
      requireConsensus: true,
      maxNegotiationRounds: 5,
    },
    performanceThresholds: {
      maxExecutionTime: 600000, // 10분
      minSuccessRate: 0.8,
      maxTokenUsage: 15000,
    },
    tags: ['합의', '의사결정', '전문가'],
  },
  dynamic_routing: {
    name: '동적 라우팅 시스템',
    description: '성능에 따라 작업을 동적으로 라우팅합니다.',
    agentRoles: [
      { name: '라우터', role: 'coordinator', priority: 1 },
      { name: '처리기 A', role: 'worker', priority: 2 },
      { name: '처리기 B', role: 'worker', priority: 2 },
      { name: '집계자', role: 'synthesizer', priority: 3 },
    ],
    supervisorEnabled: true,
    communicationRules: {
      allowDirectCommunication: true,
      enableBroadcast: false,
      requireConsensus: false,
      maxNegotiationRounds: 2,
    },
    performanceThresholds: {
      maxExecutionTime: 240000, // 4분
      minSuccessRate: 0.9,
      maxTokenUsage: 7000,
    },
    tags: ['동적라우팅', '성능최적화', '적응형'],
  },
  // 다른 패턴들의 기본값도 추가 가능
} as const;

export const SimplifiedPatternConfigWizard: React.FC<SimplifiedPatternConfigWizardProps> = ({
  orchestrationType,
  open,
  onOpenChange,
  onComplete,
  initialConfig,
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [config, setConfig] = useState<OrchestrationConfig>(() => {
    const smartDefaults = SMART_DEFAULTS[orchestrationType] || SMART_DEFAULTS.sequential;
    
    return {
      orchestrationType,
      name: smartDefaults.name,
      description: smartDefaults.description,
      supervisorConfig: {
        ...DEFAULT_SUPERVISOR_CONFIG,
        enabled: smartDefaults.supervisorEnabled,
      },
      agentRoles: smartDefaults.agentRoles.map((role, index) => ({
        id: `agent_${index + 1}`,
        name: role.name,
        role: role.role as AgentRole,
        priority: role.priority,
        maxRetries: 3,
        timeoutSeconds: 300,
        dependencies: [],
      })),
      communicationRules: smartDefaults.communicationRules,
      performanceThresholds: smartDefaults.performanceThresholds,
      tags: smartDefaults.tags,
      ...initialConfig,
    };
  });

  const pattern = ORCHESTRATION_TYPES[orchestrationType];
  const currentStepInfo = SIMPLIFIED_WIZARD_STEPS[currentStep];
  const progress = ((currentStep + 1) / SIMPLIFIED_WIZARD_STEPS.length) * 100;

  // 실시간 검증
  const {
    validationResult,
    isValidating,
    hasChanges,
    validate,
    saveConfig,
    resetValidation
  } = useRealTimeValidation({
    debounceMs: 300,
    enableAutoSave: false, // 마법사에서는 자동 저장 비활성화
    onValidationChange: (result) => {
      console.log('Validation result:', result);
    }
  });

  // 설정 변경 시 실시간 검증
  useEffect(() => {
    if (open) {
      validate(orchestrationType, config);
    } else {
      resetValidation();
    }
  }, [config, orchestrationType, open, validate, resetValidation]);

  // 스마트 기본값 적용
  const applySmartDefaults = () => {
    const smartDefaults = SMART_DEFAULTS[orchestrationType] || SMART_DEFAULTS.sequential;
    
    setConfig(prev => ({
      ...prev,
      name: smartDefaults.name,
      description: smartDefaults.description,
      agentRoles: smartDefaults.agentRoles.map((role, index) => ({
        id: `agent_${index + 1}`,
        name: role.name,
        role: role.role as AgentRole,
        priority: role.priority,
        maxRetries: 3,
        timeoutSeconds: 300,
        dependencies: [],
      })),
      supervisorConfig: {
        ...prev.supervisorConfig,
        enabled: smartDefaults.supervisorEnabled,
      },
      communicationRules: smartDefaults.communicationRules,
      performanceThresholds: smartDefaults.performanceThresholds,
      tags: smartDefaults.tags,
    }));
  };

  const handleNext = () => {
    if (currentStep < SIMPLIFIED_WIZARD_STEPS.length - 1) {
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
      case 0: // 기본 설정
        return config.name.trim() !== '';
      case 1: // Agent 구성
        return config.agentRoles.length > 0;
      case 2: // 고급 설정
        return !config.supervisorConfig.enabled || 
               (config.supervisorConfig.llm_provider !== '' && config.supervisorConfig.llm_model !== '');
      case 3: // 검토
        return validationResult?.valid !== false;
      default:
        return true;
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0: // 기본 설정
        return (
          <div className="space-y-6">
            {/* 스마트 기본값 적용 버튼 */}
            <Card className="bg-blue-50 border-blue-200">
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Lightbulb className="h-5 w-5 text-blue-600" />
                    <div>
                      <h4 className="font-medium text-blue-900">스마트 기본값 사용</h4>
                      <p className="text-sm text-blue-700">
                        {pattern.name} 패턴에 최적화된 설정을 자동으로 적용합니다
                      </p>
                    </div>
                  </div>
                  <Button variant="outline" onClick={applySmartDefaults} className="border-blue-300">
                    <Sparkles className="w-4 h-4 mr-2" />
                    적용
                  </Button>
                </div>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 gap-6">
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

            {/* 패턴 정보 표시 */}
            <Card className="bg-gray-50">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">선택된 패턴: {pattern.name}</CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <p className="text-sm text-gray-600 mb-3">{pattern.description}</p>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline" className="text-xs">
                    <Clock className="w-3 h-3 mr-1" />
                    {pattern.estimated_setup_time}
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    <Target className="w-3 h-3 mr-1" />
                    {pattern.complexity}
                  </Badge>
                </div>
              </CardContent>
            </Card>
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
            </div>
            
            <div className="space-y-4">
              {config.agentRoles.map((agent, index) => (
                <Card key={agent.id} className="p-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                              {role.name}
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
                              {priority}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
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
        
      case 2: // 고급 설정 (통합)
        return (
          <div className="space-y-6">
            {/* Supervisor 설정 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5" />
                  Supervisor 설정
                </CardTitle>
                <CardDescription>
                  LLM 기반 지능형 조정자를 설정합니다
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center space-x-2">
                  <Switch
                    id="enableSupervisor"
                    checked={config.supervisorConfig.enabled}
                    onCheckedChange={(checked) => setConfig(prev => ({
                      ...prev,
                      supervisorConfig: { ...prev.supervisorConfig, enabled: checked }
                    }))}
                  />
                  <Label htmlFor="enableSupervisor">Supervisor 활성화</Label>
                </div>
                
                {config.supervisorConfig.enabled && (
                  <div className="grid grid-cols-2 gap-4 pl-6 border-l-2 border-blue-200">
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
                          <SelectItem value="llama3.1">Llama 3.1</SelectItem>
                          <SelectItem value="gpt-4">GPT-4</SelectItem>
                          <SelectItem value="claude-3-sonnet">Claude 3 Sonnet</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* 통신 및 성능 설정 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Users className="w-4 h-4" />
                    통신 규칙
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="directComm" className="text-sm">직접 통신</Label>
                    <Switch
                      id="directComm"
                      checked={config.communicationRules.allowDirectCommunication}
                      onCheckedChange={(checked) => setConfig(prev => ({
                        ...prev,
                        communicationRules: { ...prev.communicationRules, allowDirectCommunication: checked }
                      }))}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <Label htmlFor="broadcast" className="text-sm">브로드캐스트</Label>
                    <Switch
                      id="broadcast"
                      checked={config.communicationRules.enableBroadcast}
                      onCheckedChange={(checked) => setConfig(prev => ({
                        ...prev,
                        communicationRules: { ...prev.communicationRules, enableBroadcast: checked }
                      }))}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <Label htmlFor="consensus" className="text-sm">합의 필요</Label>
                    <Switch
                      id="consensus"
                      checked={config.communicationRules.requireConsensus}
                      onCheckedChange={(checked) => setConfig(prev => ({
                        ...prev,
                        communicationRules: { ...prev.communicationRules, requireConsensus: checked }
                      }))}
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Zap className="w-4 h-4" />
                    성능 설정
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <Label className="text-sm">최대 실행 시간</Label>
                    <Select
                      value={config.performanceThresholds.maxExecutionTime.toString()}
                      onValueChange={(value) => setConfig(prev => ({
                        ...prev,
                        performanceThresholds: { ...prev.performanceThresholds, maxExecutionTime: parseInt(value) }
                      }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="180000">3분</SelectItem>
                        <SelectItem value="300000">5분</SelectItem>
                        <SelectItem value="600000">10분</SelectItem>
                        <SelectItem value="1800000">30분</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label className="text-sm">최소 성공률</Label>
                    <Select
                      value={config.performanceThresholds.minSuccessRate.toString()}
                      onValueChange={(value) => setConfig(prev => ({
                        ...prev,
                        performanceThresholds: { ...prev.performanceThresholds, minSuccessRate: parseFloat(value) }
                      }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="0.7">70%</SelectItem>
                        <SelectItem value="0.8">80%</SelectItem>
                        <SelectItem value="0.9">90%</SelectItem>
                        <SelectItem value="0.95">95%</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        );
        
      case 3: // 검토 및 완료
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold">설정 검토</h3>
              <p className="text-sm text-gray-600">
                설정한 내용을 검토하고 완료하세요
              </p>
            </div>

            {/* 실시간 검증 결과 */}
            <RealTimeValidationFeedback
              validationResult={validationResult}
              isValidating={isValidating}
              hasChanges={hasChanges}
              showDetails={true}
              compact={false}
            />
            
            <ScrollArea className="h-[300px] space-y-4">
              <div className="space-y-4">
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
                  <h4 className="font-semibold mb-2">고급 설정</h4>
                  <div className="space-y-2 text-sm">
                    <div><strong>Supervisor:</strong> {config.supervisorConfig.enabled ? '활성화' : '비활성화'}</div>
                    <div><strong>직접 통신:</strong> {config.communicationRules.allowDirectCommunication ? '허용' : '비허용'}</div>
                    <div><strong>최대 실행 시간:</strong> {Math.round(config.performanceThresholds.maxExecutionTime / 1000)}초</div>
                    <div><strong>최소 성공률:</strong> {Math.round(config.performanceThresholds.minSuccessRate * 100)}%</div>
                  </div>
                </Card>
              </div>
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
            {pattern.name} 설정 마법사 (간소화)
          </DialogTitle>
          <DialogDescription>
            4단계로 간소화된 설정 과정으로 빠르게 오케스트레이션을 구성합니다
          </DialogDescription>
        </DialogHeader>

        <div className="flex gap-6 h-[600px]">
          {/* 단계 네비게이션 */}
          <div className="w-64 border-r pr-4">
            <div className="mb-4">
              <div className="text-sm text-gray-600 mb-2">진행률</div>
              <Progress value={progress} className="h-2" />
              <div className="text-xs text-gray-500 mt-1">{currentStep + 1} / {SIMPLIFIED_WIZARD_STEPS.length}</div>
            </div>
            
            <div className="space-y-2">
              {SIMPLIFIED_WIZARD_STEPS.map((step, index) => {
                const StepIcon = step.icon;
                const isCompleted = index < currentStep;
                const isCurrent = index === currentStep;
                const isValid = isStepValid(index);
                
                return (
                  <div
                    key={step.id}
                    className={cn(
                      'flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors',
                      isCurrent && 'bg-blue-50 border border-blue-200',
                      isCompleted && 'bg-green-50',
                      !isValid && index <= currentStep && 'bg-red-50'
                    )}
                    onClick={() => setCurrentStep(index)}
                  >
                    <div className={cn(
                      'p-2 rounded',
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
            {currentStep === SIMPLIFIED_WIZARD_STEPS.length - 1 ? (
              <Button 
                onClick={handleComplete} 
                disabled={!isStepValid(currentStep) || validationResult?.valid === false}
              >
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