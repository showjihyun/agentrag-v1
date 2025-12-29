'use client';

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
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
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import {
  Settings,
  Brain,
  Target,
  Users,
  Zap,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  TrendingUp,
  Shield,
  Clock,
  BarChart3,
  Lightbulb,
  Wand2,
} from 'lucide-react';

interface SupervisorConfig {
  enabled: boolean;
  llm_provider: string;
  llm_model: string;
  max_iterations: number;
  decision_strategy: 'llm_based' | 'consensus' | 'weighted_voting' | 'expert_system';
  
  // 고급 설정
  auto_agent_selection: boolean;
  performance_based_routing: boolean;
  dynamic_role_assignment: boolean;
  learning_enabled: boolean;
  optimization_strategy: 'performance' | 'cost' | 'speed' | 'quality';
  adaptation_threshold: number;
  
  // 모니터링 설정
  monitoring_enabled: boolean;
  alert_thresholds: {
    success_rate: number;
    response_time: number;
    error_rate: number;
  };
  
  // 협업 설정
  team_learning_enabled: boolean;
  knowledge_sharing: boolean;
  template_integration: boolean;
}

interface SupervisorConfigWizardProps {
  agentflowId: string;
  orchestrationType: string;
  currentConfig?: Partial<SupervisorConfig>;
  onConfigChange: (config: SupervisorConfig) => void;
  trigger?: React.ReactNode;
}

const WIZARD_STEPS = [
  { id: 'objective', title: '목표 설정', description: '슈퍼바이저의 주요 목표를 설정하세요' },
  { id: 'strategy', title: '전략 선택', description: '의사결정 전략과 최적화 방향을 선택하세요' },
  { id: 'monitoring', title: '모니터링 설정', description: '성능 모니터링과 알림을 구성하세요' },
  { id: 'collaboration', title: '협업 기능', description: '팀 학습과 지식 공유를 설정하세요' },
  { id: 'review', title: '설정 검토', description: '최종 설정을 확인하고 적용하세요' },
];

const DECISION_STRATEGIES = [
  {
    id: 'llm_based',
    name: 'LLM 기반 의사결정',
    description: 'AI가 상황을 분석하여 최적의 결정을 내립니다',
    icon: Brain,
    complexity: '중간',
    recommended: true,
  },
  {
    id: 'consensus',
    name: '합의 기반',
    description: '모든 에이전트의 의견을 종합하여 결정합니다',
    icon: Users,
    complexity: '높음',
    recommended: false,
  },
  {
    id: 'weighted_voting',
    name: '가중 투표',
    description: '에이전트별 가중치를 적용한 투표로 결정합니다',
    icon: BarChart3,
    complexity: '중간',
    recommended: false,
  },
  {
    id: 'expert_system',
    name: '전문가 시스템',
    description: '사전 정의된 규칙에 따라 결정합니다',
    icon: Shield,
    complexity: '낮음',
    recommended: false,
  },
];

const OPTIMIZATION_STRATEGIES = [
  { id: 'performance', name: '성능 최적화', description: '처리 속도와 정확도를 최우선으로', icon: Zap },
  { id: 'cost', name: '비용 최적화', description: '리소스 사용량과 비용을 최소화', icon: TrendingUp },
  { id: 'speed', name: '속도 최적화', description: '응답 시간을 최소화', icon: Clock },
  { id: 'quality', name: '품질 최적화', description: '결과의 품질과 신뢰성을 최우선으로', icon: Target },
];

export function SupervisorConfigWizard({
  agentflowId,
  orchestrationType,
  currentConfig,
  onConfigChange,
  trigger,
}: SupervisorConfigWizardProps) {
  const { toast } = useToast();
  const [open, setOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [config, setConfig] = useState<SupervisorConfig>({
    enabled: true,
    llm_provider: 'ollama',
    llm_model: 'llama3.1',
    max_iterations: 10,
    decision_strategy: 'llm_based',
    auto_agent_selection: true,
    performance_based_routing: true,
    dynamic_role_assignment: false,
    learning_enabled: true,
    optimization_strategy: 'performance',
    adaptation_threshold: 0.8,
    monitoring_enabled: true,
    alert_thresholds: {
      success_rate: 85,
      response_time: 5,
      error_rate: 10,
    },
    team_learning_enabled: false,
    knowledge_sharing: false,
    template_integration: true,
    ...currentConfig,
  });

  // AI 추천 설정 조회
  const { data: recommendations } = useQuery({
    queryKey: ['supervisor-recommendations', agentflowId, orchestrationType],
    queryFn: () => agentBuilderAPI.getSupervisorRecommendations(agentflowId, orchestrationType),
    enabled: open,
  });

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

  const handleApplyRecommendation = (recommendedConfig: Partial<SupervisorConfig>) => {
    setConfig({ ...config, ...recommendedConfig });
    toast({
      title: 'AI 추천 적용',
      description: '추천 설정이 적용되었습니다',
    });
  };

  const handleFinish = () => {
    onConfigChange(config);
    setOpen(false);
    toast({
      title: '슈퍼바이저 설정 완료',
      description: '고급 슈퍼바이저 설정이 적용되었습니다',
    });
  };

  const renderStepContent = () => {
    switch (WIZARD_STEPS[currentStep].id) {
      case 'objective':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <Target className="h-12 w-12 text-purple-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">슈퍼바이저의 주요 목표를 설정하세요</h3>
              <p className="text-muted-foreground">
                {orchestrationType} 오케스트레이션에 최적화된 설정을 추천해드립니다
              </p>
            </div>

            {/* AI 추천 카드 */}
            {recommendations?.recommended_config && (
              <Card className="border-purple-200 bg-purple-50 dark:bg-purple-950/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-purple-700 dark:text-purple-300">
                    <Sparkles className="h-5 w-5" />
                    AI 추천 설정
                  </CardTitle>
                  <CardDescription>
                    현재 오케스트레이션 유형에 최적화된 설정입니다
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium">의사결정 전략:</span>
                      <span className="ml-2">{recommendations.recommended_config.decision_strategy}</span>
                    </div>
                    <div>
                      <span className="font-medium">최적화 전략:</span>
                      <span className="ml-2">{recommendations.recommended_config.optimization_strategy}</span>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    onClick={() => handleApplyRecommendation(recommendations.recommended_config)}
                    className="w-full gap-2"
                  >
                    <Wand2 className="h-4 w-4" />
                    추천 설정 적용
                  </Button>
                </CardContent>
              </Card>
            )}

            <div className="space-y-4">
              <div className="space-y-2">
                <Label>최적화 전략</Label>
                <div className="grid grid-cols-2 gap-3">
                  {OPTIMIZATION_STRATEGIES.map((strategy) => {
                    const Icon = strategy.icon;
                    const isSelected = config.optimization_strategy === strategy.id;
                    return (
                      <Card
                        key={strategy.id}
                        className={`cursor-pointer transition-all ${
                          isSelected ? 'border-purple-500 bg-purple-50 dark:bg-purple-950/20' : ''
                        }`}
                        onClick={() => setConfig({ ...config, optimization_strategy: strategy.id as any })}
                      >
                        <CardContent className="pt-4 pb-3">
                          <div className="flex items-center gap-2 mb-2">
                            <Icon className="h-4 w-4" />
                            <span className="font-medium text-sm">{strategy.name}</span>
                          </div>
                          <p className="text-xs text-muted-foreground">{strategy.description}</p>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </div>

              <div className="space-y-2">
                <Label>적응 임계값</Label>
                <div className="space-y-2">
                  <Input
                    type="range"
                    min="0.1"
                    max="1.0"
                    step="0.1"
                    value={config.adaptation_threshold}
                    onChange={(e) => setConfig({ ...config, adaptation_threshold: parseFloat(e.target.value) })}
                  />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>민감함 (0.1)</span>
                    <span>현재: {config.adaptation_threshold}</span>
                    <span>안정적 (1.0)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 'strategy':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <Brain className="h-12 w-12 text-purple-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">의사결정 전략을 선택하세요</h3>
              <p className="text-muted-foreground">
                에이전트들 간의 협력과 의사결정 방식을 설정합니다
              </p>
            </div>

            <div className="space-y-3">
              {DECISION_STRATEGIES.map((strategy) => {
                const Icon = strategy.icon;
                const isSelected = config.decision_strategy === strategy.id;
                return (
                  <Card
                    key={strategy.id}
                    className={`cursor-pointer transition-all ${
                      isSelected ? 'border-purple-500 bg-purple-50 dark:bg-purple-950/20' : ''
                    }`}
                    onClick={() => setConfig({ ...config, decision_strategy: strategy.id as any })}
                  >
                    <CardContent className="pt-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <Icon className="h-5 w-5" />
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{strategy.name}</span>
                              {strategy.recommended && (
                                <Badge variant="outline" className="text-xs bg-green-50 text-green-700">
                                  추천
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground">{strategy.description}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <Badge variant="outline">{strategy.complexity}</Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            <div className="space-y-4">
              <Separator />
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>자동 에이전트 선택</Label>
                    <p className="text-sm text-muted-foreground">작업에 최적화된 에이전트를 자동으로 선택</p>
                  </div>
                  <Switch
                    checked={config.auto_agent_selection}
                    onCheckedChange={(checked) => setConfig({ ...config, auto_agent_selection: checked })}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>성능 기반 라우팅</Label>
                    <p className="text-sm text-muted-foreground">실시간 성능을 기반으로 작업 분배</p>
                  </div>
                  <Switch
                    checked={config.performance_based_routing}
                    onCheckedChange={(checked) => setConfig({ ...config, performance_based_routing: checked })}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>동적 역할 재할당</Label>
                    <p className="text-sm text-muted-foreground">상황에 따라 에이전트 역할을 실시간 조정</p>
                  </div>
                  <Switch
                    checked={config.dynamic_role_assignment}
                    onCheckedChange={(checked) => setConfig({ ...config, dynamic_role_assignment: checked })}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>학습 기능</Label>
                    <p className="text-sm text-muted-foreground">성능 데이터를 학습하여 지속적으로 개선</p>
                  </div>
                  <Switch
                    checked={config.learning_enabled}
                    onCheckedChange={(checked) => setConfig({ ...config, learning_enabled: checked })}
                  />
                </div>
              </div>
            </div>
          </div>
        );

      case 'monitoring':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <BarChart3 className="h-12 w-12 text-purple-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">모니터링과 알림을 설정하세요</h3>
              <p className="text-muted-foreground">
                실시간 성능 추적과 문제 상황 알림을 구성합니다
              </p>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>실시간 모니터링</Label>
                  <p className="text-sm text-muted-foreground">에이전트 성능과 시스템 상태를 실시간으로 추적</p>
                </div>
                <Switch
                  checked={config.monitoring_enabled}
                  onCheckedChange={(checked) => setConfig({ ...config, monitoring_enabled: checked })}
                />
              </div>

              {config.monitoring_enabled && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">알림 임계값 설정</CardTitle>
                    <CardDescription>
                      다음 조건에 도달하면 알림을 받습니다
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label>최소 성공률 (%)</Label>
                      <Input
                        type="number"
                        min="0"
                        max="100"
                        value={config.alert_thresholds.success_rate}
                        onChange={(e) => setConfig({
                          ...config,
                          alert_thresholds: {
                            ...config.alert_thresholds,
                            success_rate: parseInt(e.target.value) || 85
                          }
                        })}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>최대 응답시간 (초)</Label>
                      <Input
                        type="number"
                        min="1"
                        max="60"
                        value={config.alert_thresholds.response_time}
                        onChange={(e) => setConfig({
                          ...config,
                          alert_thresholds: {
                            ...config.alert_thresholds,
                            response_time: parseInt(e.target.value) || 5
                          }
                        })}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>최대 오류율 (%)</Label>
                      <Input
                        type="number"
                        min="0"
                        max="50"
                        value={config.alert_thresholds.error_rate}
                        onChange={(e) => setConfig({
                          ...config,
                          alert_thresholds: {
                            ...config.alert_thresholds,
                            error_rate: parseInt(e.target.value) || 10
                          }
                        })}
                      />
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        );

      case 'collaboration':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <Users className="h-12 w-12 text-purple-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">협업 기능을 설정하세요</h3>
              <p className="text-muted-foreground">
                팀 학습과 지식 공유로 전체 시스템의 성능을 향상시킵니다
              </p>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>팀 학습 활성화</Label>
                  <p className="text-sm text-muted-foreground">다른 팀의 성공 패턴을 학습하여 성능 개선</p>
                </div>
                <Switch
                  checked={config.team_learning_enabled}
                  onCheckedChange={(checked) => setConfig({ ...config, team_learning_enabled: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>지식 공유</Label>
                  <p className="text-sm text-muted-foreground">성능 인사이트와 최적화 전략을 팀 간 공유</p>
                </div>
                <Switch
                  checked={config.knowledge_sharing}
                  onCheckedChange={(checked) => setConfig({ ...config, knowledge_sharing: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>템플릿 통합</Label>
                  <p className="text-sm text-muted-foreground">검증된 팀 템플릿을 기반으로 자동 최적화</p>
                </div>
                <Switch
                  checked={config.template_integration}
                  onCheckedChange={(checked) => setConfig({ ...config, template_integration: checked })}
                />
              </div>

              {(config.team_learning_enabled || config.knowledge_sharing) && (
                <Card className="bg-blue-50 dark:bg-blue-950/20 border-blue-200">
                  <CardContent className="pt-4">
                    <div className="flex items-start gap-3">
                      <Lightbulb className="h-5 w-5 text-blue-600 mt-0.5" />
                      <div>
                        <h4 className="font-medium text-blue-800 dark:text-blue-200 mb-1">
                          협업 기능 활성화됨
                        </h4>
                        <p className="text-sm text-blue-700 dark:text-blue-300">
                          이 설정으로 다른 팀과 성능 데이터를 공유하고 집단 지능을 활용할 수 있습니다.
                          개인정보는 보호되며, 성능 패턴만 익명으로 공유됩니다.
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        );

      case 'review':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <CheckCircle2 className="h-12 w-12 text-green-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">설정 검토</h3>
              <p className="text-muted-foreground">
                최종 설정을 확인하고 슈퍼바이저를 활성화하세요
              </p>
            </div>

            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">기본 설정</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>LLM 제공자:</span>
                    <span className="font-medium">{config.llm_provider}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>모델:</span>
                    <span className="font-medium">{config.llm_model}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>최대 반복:</span>
                    <span className="font-medium">{config.max_iterations}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>의사결정 전략:</span>
                    <span className="font-medium">
                      {DECISION_STRATEGIES.find(s => s.id === config.decision_strategy)?.name}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>최적화 전략:</span>
                    <span className="font-medium">
                      {OPTIMIZATION_STRATEGIES.find(s => s.id === config.optimization_strategy)?.name}
                    </span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">고급 기능</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>자동 에이전트 선택:</span>
                    <Badge variant={config.auto_agent_selection ? 'default' : 'secondary'}>
                      {config.auto_agent_selection ? '활성화' : '비활성화'}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>성능 기반 라우팅:</span>
                    <Badge variant={config.performance_based_routing ? 'default' : 'secondary'}>
                      {config.performance_based_routing ? '활성화' : '비활성화'}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>학습 기능:</span>
                    <Badge variant={config.learning_enabled ? 'default' : 'secondary'}>
                      {config.learning_enabled ? '활성화' : '비활성화'}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>실시간 모니터링:</span>
                    <Badge variant={config.monitoring_enabled ? 'default' : 'secondary'}>
                      {config.monitoring_enabled ? '활성화' : '비활성화'}
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              {(config.team_learning_enabled || config.knowledge_sharing) && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">협업 기능</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>팀 학습:</span>
                      <Badge variant={config.team_learning_enabled ? 'default' : 'secondary'}>
                        {config.team_learning_enabled ? '활성화' : '비활성화'}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>지식 공유:</span>
                      <Badge variant={config.knowledge_sharing ? 'default' : 'secondary'}>
                        {config.knowledge_sharing ? '활성화' : '비활성화'}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button className="gap-2">
            <Settings className="h-4 w-4" />
            고급 설정
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            슈퍼바이저 설정 마법사
          </DialogTitle>
          <DialogDescription>
            단계별 가이드를 통해 고급 슈퍼바이저를 구성하세요
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* 진행 상황 */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>진행 상황</span>
              <span>{currentStep + 1} / {WIZARD_STEPS.length}</span>
            </div>
            <Progress value={(currentStep + 1) / WIZARD_STEPS.length * 100} />
            <div className="flex justify-between text-xs text-muted-foreground">
              {WIZARD_STEPS.map((step, index) => (
                <span
                  key={step.id}
                  className={index <= currentStep ? 'text-purple-600' : ''}
                >
                  {step.title}
                </span>
              ))}
            </div>
          </div>

          {/* 현재 단계 내용 */}
          <div className="min-h-[400px]">
            <div className="mb-4">
              <h3 className="text-lg font-semibold">{WIZARD_STEPS[currentStep].title}</h3>
              <p className="text-muted-foreground">{WIZARD_STEPS[currentStep].description}</p>
            </div>
            {renderStepContent()}
          </div>

          {/* 네비게이션 버튼 */}
          <div className="flex justify-between">
            <Button
              variant="outline"
              onClick={handlePrevious}
              disabled={currentStep === 0}
              className="gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              이전
            </Button>

            {currentStep === WIZARD_STEPS.length - 1 ? (
              <Button onClick={handleFinish} className="gap-2">
                <CheckCircle2 className="h-4 w-4" />
                설정 완료
              </Button>
            ) : (
              <Button onClick={handleNext} className="gap-2">
                다음
                <ArrowRight className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}