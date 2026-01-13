'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  Users,
  ArrowLeft,
  Save,
  Plus,
  Trash,
  Settings,
  Loader2,
  Brain,
  Sparkles,
  BarChart3,
  CheckCircle2,
  TrendingUp,
  ArrowRight,
  Zap,
  GitBranch,
  MessageSquare,
  Route,
  Hexagon,
  Bell,
  RefreshCw,
  Atom,
  Leaf,
  Network,
  Heart,
  Crystal,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { useToast } from '@/hooks/use-toast';
import { flowsAPI } from '@/lib/api/flows';
import { agentBuilderAPI, type Agent } from '@/lib/api/agent-builder';
import { 
  ORCHESTRATION_TYPES, 
  CORE_ORCHESTRATION_TYPES,
  TRENDS_2025_ORCHESTRATION_TYPES,
  TRENDS_2026_ORCHESTRATION_TYPES,
  CATEGORY_COLORS,
  type OrchestrationTypeValue 
} from '@/lib/constants/orchestration';
import { AgentSelector } from '@/components/agent-builder/AgentSelector';
import { SupervisorDashboard } from '@/components/agent-builder/SupervisorDashboard';
import { SupervisorConfigWizard } from '@/components/agent-builder/SupervisorConfigWizard';
import { SupervisorAIAssistant } from '@/components/agent-builder/SupervisorAIAssistant';
import { AgentflowIntegrationPanel } from '@/components/agent-builder/AgentflowIntegrationPanel';

// Icon mapping for orchestration types
const getIconComponent = (iconName: string) => {
  const iconMap: Record<string, any> = {
    ArrowRight,
    Zap,
    Users,
    GitBranch,
    MessageSquare,
    Route,
    Hexagon,
    Bell,
    RefreshCw,
    Brain,
    Atom,
    Leaf,
    TrendingUp,
    Network,
    Heart,
    Crystal,
  };
  return iconMap[iconName] || ArrowRight; // fallback to ArrowRight
};

// Orchestration types are now imported from constants

interface AgentConfig {
  id: string;
  agent_id: string;
  name: string;
  role: string;
  description: string;
  priority: number;
  max_retries: number;
  timeout_seconds: number;
  capabilities?: string[];
  dependencies?: string[];
}

interface AvailableAgent {
  id: string;
  name: string;
  description: string;
  agent_type: string;
  llm_provider: string;
  llm_model: string;
  configuration: any;
  tools: Array<{ tool_id: string; configuration: any }>;
  capabilities: string[];
}

export default function EditAgentflowPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const { toast } = useToast();
  
  // Unwrap params using React.use()
  const { id } = React.use(params);

  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    orchestration_type: 'sequential' as OrchestrationTypeValue,
    supervisor_enabled: false,
    supervisor_llm_provider: 'ollama',
    supervisor_llm_model: 'llama3.1',
    supervisor_max_iterations: 10,
    supervisor_decision_strategy: 'llm_based' as 'llm_based' | 'consensus' | 'weighted_voting' | 'expert_system',
    tags: [] as string[],
  });
  const [agents, setAgents] = useState<AgentConfig[]>([]);
  const [newTag, setNewTag] = useState('');

  // Recommended roles based on orchestration type
  const getRecommendedRoles = (orchestrationType: OrchestrationTypeValue): string[] => {
    const roleMap: Record<OrchestrationTypeValue, string[]> = {
      sequential: ['Data Collector', 'Analyst', 'Report Writer'],
      parallel: ['Search Expert', 'Translator', 'Summary Expert'],
      hierarchical: ['매니저', '연구원', '검토자', '실행자'],
      adaptive: ['상황 분석가', '전략 수립자', '실행자'],
      consensus_building: ['전문가 A', '전문가 B', '중재자'],
      dynamic_routing: ['라우터', '처리기', '집계자'],
      swarm_intelligence: ['탐색자', '수집가', '조율자'],
      event_driven: ['이벤트 감지기', '처리기', '응답자'],
      reflection: ['분석가', '검토자', '개선자'],
      neuromorphic: ['뉴런 A', '뉴런 B', '시냅스'],
      quantum_enhanced: ['양자 분석가', '중첩 처리기', '측정자'],
      bio_inspired: ['센서', '프로세서', '액추에이터'],
      self_evolving: ['학습자', '적응자', '진화자'],
      federated: ['로컬 에이전트', '글로벌 조율자', '동기화자'],
      emotional_ai: ['감정 분석가', '공감 에이전트', '반응 조절자'],
      predictive: ['예측자', '검증자', '조정자'],
    };
    
    return roleMap[orchestrationType] || ['범용 에이전트', '전문가', '조율자'];
  };

  // Fetch existing flow data
  const { data: flowData, isLoading: flowLoading } = useQuery({
    queryKey: ['agentflow', id],
    queryFn: () => flowsAPI.getFlow(id),
  });

  const flow = flowData as any;

  // Fetch available agents
  const { data: availableAgents } = useQuery({
    queryKey: ['available-agents'],
    queryFn: () => agentBuilderAPI.getAgents(),
  });

  // Load existing data
  useEffect(() => {
    if (flow) {
      setFormData({
        name: flow.name || '',
        description: flow.description || '',
        orchestration_type: flow.orchestration_type || 'sequential',
        supervisor_enabled: flow.supervisor_config?.enabled || false,
        supervisor_llm_provider: flow.supervisor_config?.llm_provider || 'ollama',
        supervisor_llm_model: flow.supervisor_config?.llm_model || 'llama3.1',
        supervisor_max_iterations: flow.supervisor_config?.max_iterations || 10,
        supervisor_decision_strategy: flow.supervisor_config?.decision_strategy || 'llm_based',
        tags: flow.tags || [],
      });
      
      if (flow.agents) {
        setAgents(flow.agents.map((agent: any, index: number) => ({
          id: agent.id || `agent-${index}`,
          agent_id: agent.agent_id || '',
          name: agent.name || '',
          role: agent.role || '',
          description: agent.description || '',
          priority: agent.priority || index + 1,
          max_retries: agent.max_retries || 3,
          timeout_seconds: agent.timeout_seconds || 60,
          capabilities: agent.capabilities || [],
          dependencies: agent.dependencies || [],
        })));
      }
    }
  }, [flow]);

  const handleAddAgent = () => {
    const newAgent: AgentConfig = {
      id: `agent-${Date.now()}`,
      agent_id: '',
      name: '',
      role: '',
      description: '',
      priority: agents.length + 1,
      max_retries: 3,
      timeout_seconds: 60,
      capabilities: [],
      dependencies: [],
    };
    setAgents([...agents, newAgent]);
  };

  const handleSelectFromBuildingBlock = (selectedAgent: Agent) => {
    const newAgent: AgentConfig = {
      id: `agent-${Date.now()}`,
      agent_id: selectedAgent.id,
      name: selectedAgent.name,
      role: '', // User will set this
      description: selectedAgent.description || '',
      priority: agents.length + 1,
      max_retries: 3,
      timeout_seconds: 60,
      capabilities: [], // API Agent doesn't have capabilities, so use empty array
      dependencies: [],
    };
    setAgents([...agents, newAgent]);
  };

  const handleRemoveAgent = (id: string) => {
    setAgents(agents.filter((a) => a.id !== id));
  };

  const handleAgentChange = (id: string, field: keyof AgentConfig, value: any) => {
    setAgents(
      agents.map((a) => {
        if (a.id === id) {
          if (field === 'agent_id' && availableAgents?.agents) {
            const selectedAgent = availableAgents.agents.find((ag: any) => ag.id === value);
            if (selectedAgent) {
              return {
                ...a,
                agent_id: value,
                name: selectedAgent.name,
                description: selectedAgent.description || '',
              };
            }
          }
          return { ...a, [field]: value };
        }
        return a;
      })
    );
  };

  const handleAddTag = () => {
    if (newTag && !formData.tags.includes(newTag)) {
      setFormData({ ...formData, tags: [...formData.tags, newTag] });
      setNewTag('');
    }
  };

  const handleRemoveTag = (tag: string) => {
    setFormData({ ...formData, tags: formData.tags.filter((t) => t !== tag) });
  };

  const handleSave = async () => {
    if (!formData.name) {
      toast({
        title: '오류',
        description: '이름을 입력해주세요',
        variant: 'destructive',
      });
      return;
    }

    try {
      setSaving(true);
      await flowsAPI.updateFlow(id, {
        name: formData.name,
        description: formData.description,
        orchestration_type: formData.orchestration_type,
        supervisor_config: formData.supervisor_enabled
          ? {
              enabled: true,
              llm_provider: formData.supervisor_llm_provider,
              llm_model: formData.supervisor_llm_model,
              max_iterations: formData.supervisor_max_iterations,
              decision_strategy: formData.supervisor_decision_strategy,
            }
          : undefined,
        agents: agents.length > 0 ? agents.map(agent => ({
          agent_id: agent.agent_id || undefined,
          name: agent.name,
          role: agent.role,
          description: agent.description,
          capabilities: agent.capabilities || [],
          priority: agent.priority,
          max_retries: agent.max_retries,
          timeout_seconds: agent.timeout_seconds,
          dependencies: agent.dependencies || [],
        })) : undefined,
        tags: formData.tags,
      } as any);

      toast({
        title: '저장 완료',
        description: 'Agentflow가 업데이트되었습니다',
      });

      router.push(`/agent-builder/agentflows/${id}`);
    } catch (error: any) {
      toast({
        title: '오류',
        description: error.message || '저장에 실패했습니다',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  if (flowLoading) {
    return (
      <div className="container mx-auto p-6 max-w-4xl">
        <Skeleton className="h-12 w-full mb-6" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!flow) {
    return (
      <div className="container mx-auto p-6 max-w-4xl">
        <Card className="border-red-500">
          <CardContent className="pt-6">
            <p className="text-red-500">Agentflow를 불러오는데 실패했습니다</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      {/* Header - Enhanced with Gradient */}
      <div className="sticky top-0 z-10 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b mb-6 -mx-6 px-6 py-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex-1">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
                <Users className="h-7 w-7 text-purple-600 dark:text-purple-400" />
              </div>
              Agentflow 편집
            </h1>
            <p className="text-muted-foreground mt-1 text-base">{flow.name}</p>
          </div>
          <Button variant="outline" onClick={() => router.back()} size="lg">
            취소
          </Button>
          <Button 
            onClick={handleSave} 
            disabled={saving}
            size="lg"
            className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 shadow-lg hover:shadow-xl transition-all"
          >
            {saving ? (
              <>
                <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                저장 중...
              </>
            ) : (
              <>
                <Save className="h-5 w-5 mr-2" />
                변경사항 저장
              </>
            )}
          </Button>
        </div>
      </div>

      <div className="space-y-6">
        {/* Basic Info - Enhanced Design */}
        <Card className="border-2">
          <CardHeader className="border-b bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-950/20 dark:to-blue-950/20">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
                <Settings className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <CardTitle className="text-lg">기본 정보</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 pt-6">
            <div className="space-y-2">
              <Label htmlFor="name">이름 *</Label>
              <Input
                id="name"
                placeholder="예: 고객 지원 에이전트 팀"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">설명</Label>
              <Textarea
                id="description"
                placeholder="이 Agentflow가 수행하는 작업을 설명하세요"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
              />
            </div>
            <div className="space-y-2">
              <Label>태그</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="태그 추가"
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                />
                <Button variant="outline" onClick={handleAddTag}>
                  추가
                </Button>
              </div>
              {formData.tags.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {formData.tags.map((tag) => (
                    <Badge key={tag} variant="secondary" className="cursor-pointer" onClick={() => handleRemoveTag(tag)}>
                      {tag} ×
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Orchestration Type - Enhanced Design */}
        <Card className="border-2">
          <CardHeader className="border-b bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-950/20 dark:to-blue-950/20">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
                <Settings className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <CardTitle className="text-lg">오케스트레이션 유형</CardTitle>
                <CardDescription>에이전트들이 어떻게 협력할지 선택하세요</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-6 space-y-6">
            {/* Core Patterns */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                <h4 className="font-medium">핵심 패턴</h4>
                <Badge variant="outline" className="text-xs">안정적</Badge>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {Object.values(CORE_ORCHESTRATION_TYPES).map((type) => {
                  const Icon = getIconComponent(type.icon);
                  const isSelected = formData.orchestration_type === type.id;
                  return (
                    <Card
                      key={type.id}
                      className={`cursor-pointer transition-all duration-300 hover:shadow-lg group ${
                        isSelected 
                          ? 'border-2 border-purple-500 bg-purple-50 dark:bg-purple-950/20 ring-2 ring-purple-500 shadow-lg scale-[1.02]' 
                          : 'hover:border-purple-300 hover:scale-[1.01]'
                      }`}
                      onClick={() => setFormData({ ...formData, orchestration_type: type.id })}
                    >
                      <CardContent className="pt-4 pb-3">
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg transition-all duration-300 ${
                            isSelected 
                              ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg' 
                              : 'bg-blue-50 dark:bg-blue-950 group-hover:bg-purple-100 dark:group-hover:bg-purple-900/20'
                          }`}>
                            <Icon className="h-4 w-4" />
                          </div>
                          <div className="flex-1">
                            <p className={`font-medium text-sm ${isSelected ? 'text-purple-600 dark:text-purple-400' : ''}`}>
                              {type.name}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {type.description}
                            </p>
                          </div>
                          {isSelected && (
                            <Badge className="bg-purple-500 hover:bg-purple-600 text-xs">
                              ✓
                            </Badge>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>

            {/* 2025 Trends */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <div className="w-3 h-3 rounded-full bg-purple-500"></div>
                <h4 className="font-medium">2025 트렌드 패턴</h4>
                <Badge variant="outline" className="text-xs bg-purple-50 text-purple-700">고급</Badge>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {Object.values(TRENDS_2025_ORCHESTRATION_TYPES).map((type) => {
                  const Icon = getIconComponent(type.icon);
                  const isSelected = formData.orchestration_type === type.id;
                  return (
                    <Card
                      key={type.id}
                      className={`cursor-pointer transition-all duration-300 hover:shadow-lg group ${
                        isSelected 
                          ? 'border-2 border-purple-500 bg-purple-50 dark:bg-purple-950/20 ring-2 ring-purple-500 shadow-lg scale-[1.02]' 
                          : 'hover:border-purple-300 hover:scale-[1.01]'
                      }`}
                      onClick={() => setFormData({ ...formData, orchestration_type: type.id })}
                    >
                      <CardContent className="pt-4 pb-3">
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg transition-all duration-300 ${
                            isSelected 
                              ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg' 
                              : 'bg-purple-50 dark:bg-purple-950 group-hover:bg-purple-100 dark:group-hover:bg-purple-900/20'
                          }`}>
                            <Icon className="h-4 w-4" />
                          </div>
                          <div className="flex-1">
                            <p className={`font-medium text-sm ${isSelected ? 'text-purple-600 dark:text-purple-400' : ''}`}>
                              {type.name}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {type.description}
                            </p>
                            <div className="flex gap-1 mt-1">
                              <Badge variant="secondary" className="text-xs">
                                {type.complexity}
                              </Badge>
                            </div>
                          </div>
                          {isSelected && (
                            <Badge className="bg-purple-500 hover:bg-purple-600 text-xs">
                              ✓
                            </Badge>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>

            {/* 2026 Trends */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
                <h4 className="font-medium">2026 차세대 패턴</h4>
                <Badge variant="outline" className="text-xs bg-emerald-50 text-emerald-700">실험적</Badge>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {Object.values(TRENDS_2026_ORCHESTRATION_TYPES).map((type) => {
                  const Icon = getIconComponent(type.icon);
                  const isSelected = formData.orchestration_type === type.id;
                  return (
                    <Card
                      key={type.id}
                      className={`cursor-pointer transition-all duration-300 hover:shadow-lg group ${
                        isSelected 
                          ? 'border-2 border-purple-500 bg-purple-50 dark:bg-purple-950/20 ring-2 ring-purple-500 shadow-lg scale-[1.02]' 
                          : 'hover:border-purple-300 hover:scale-[1.01]'
                      }`}
                      onClick={() => setFormData({ ...formData, orchestration_type: type.id })}
                    >
                      <CardContent className="pt-4 pb-3">
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg transition-all duration-300 ${
                            isSelected 
                              ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg' 
                              : 'bg-emerald-50 dark:bg-emerald-950 group-hover:bg-purple-100 dark:group-hover:bg-purple-900/20'
                          }`}>
                            <Icon className="h-4 w-4" />
                          </div>
                          <div className="flex-1">
                            <p className={`font-medium text-sm ${isSelected ? 'text-purple-600 dark:text-purple-400' : ''}`}>
                              {type.name}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {type.description}
                            </p>
                            <div className="flex gap-1 mt-1">
                              <Badge variant="secondary" className="text-xs">
                                {type.complexity}
                              </Badge>
                            </div>
                          </div>
                          {isSelected && (
                            <Badge className="bg-purple-500 hover:bg-purple-600 text-xs">
                              ✓
                            </Badge>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>

            {/* Selected orchestration info */}
            {formData.orchestration_type && ORCHESTRATION_TYPES[formData.orchestration_type] && (
              <div className="mt-4 p-4 rounded-lg bg-muted">
                <div className="flex items-center gap-2 mb-2">
                  {React.createElement(ORCHESTRATION_TYPES[formData.orchestration_type].icon, {
                    className: `h-4 w-4 ${
                      ORCHESTRATION_TYPES[formData.orchestration_type].category === 'core' ? 'text-blue-500' :
                      ORCHESTRATION_TYPES[formData.orchestration_type].category === '2025_trends' ? 'text-purple-500' :
                      'text-emerald-500'
                    }`
                  })}
                  <span className="font-medium">{ORCHESTRATION_TYPES[formData.orchestration_type].name} Selected</span>
                  <Badge variant="outline" className="text-xs">
                    {ORCHESTRATION_TYPES[formData.orchestration_type].category === 'core' ? 'Core' : 
                     ORCHESTRATION_TYPES[formData.orchestration_type].category === '2025_trends' ? '2025 Trends' : '2026 Next-Gen'}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">
                  {ORCHESTRATION_TYPES[formData.orchestration_type].description}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Enhanced Supervisor Configuration */}
        {(['hierarchical', 'adaptive'].includes(formData.orchestration_type)) && (
          <Card className="border-2">
            <CardHeader className="border-b bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-950/20 dark:to-blue-950/20">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
                    <Brain className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">지능형 슈퍼바이저</CardTitle>
                    <CardDescription>AI 기반 에이전트 오케스트레이션 및 실시간 모니터링</CardDescription>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <SupervisorConfigWizard
                    agentflowId={id}
                    orchestrationType={formData.orchestration_type}
                    currentConfig={{
                      enabled: formData.supervisor_enabled,
                      llm_provider: formData.supervisor_llm_provider,
                      llm_model: formData.supervisor_llm_model,
                      max_iterations: formData.supervisor_max_iterations,
                      decision_strategy: formData.supervisor_decision_strategy,
                    }}
                    onConfigChange={(config) => {
                      setFormData({
                        ...formData,
                        supervisor_enabled: config.enabled,
                        supervisor_llm_provider: config.llm_provider,
                        supervisor_llm_model: config.llm_model,
                        supervisor_max_iterations: config.max_iterations,
                        supervisor_decision_strategy: config.decision_strategy,
                      });
                    }}
                    trigger={
                      <Button variant="outline" className="gap-2">
                        <Sparkles className="h-4 w-4" />
                        고급 설정
                      </Button>
                    }
                  />
                  <Switch
                    checked={formData.supervisor_enabled}
                    onCheckedChange={(v) => setFormData({ ...formData, supervisor_enabled: v })}
                  />
                </div>
              </div>
            </CardHeader>
            
            {formData.supervisor_enabled ? (
              <CardContent className="space-y-6 pt-6">
                {/* 기본 설정 */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label>LLM Provider</Label>
                      <Select
                        value={formData.supervisor_llm_provider}
                        onValueChange={(v) => setFormData({ ...formData, supervisor_llm_provider: v })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ollama">Ollama</SelectItem>
                          <SelectItem value="openai">OpenAI</SelectItem>
                          <SelectItem value="anthropic">Anthropic</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>모델</Label>
                      <Input
                        value={formData.supervisor_llm_model}
                        onChange={(e) => setFormData({ ...formData, supervisor_llm_model: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>최대 반복 횟수</Label>
                      <Input
                        type="number"
                        min="1"
                        max="50"
                        value={formData.supervisor_max_iterations}
                        onChange={(e) => setFormData({ ...formData, supervisor_max_iterations: parseInt(e.target.value) || 10 })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>의사결정 전략</Label>
                      <Select
                        value={formData.supervisor_decision_strategy}
                        onValueChange={(v) => setFormData({ ...formData, supervisor_decision_strategy: v as any })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="llm_based">LLM 기반 의사결정</SelectItem>
                          <SelectItem value="consensus">합의 기반</SelectItem>
                          <SelectItem value="weighted_voting">가중 투표</SelectItem>
                          <SelectItem value="expert_system">전문가 시스템</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {/* AI 어시스턴트 */}
                  <div className="space-y-4">
                    <SupervisorAIAssistant
                      agentflowId={id}
                      supervisorConfig={{
                        enabled: formData.supervisor_enabled,
                        llm_provider: formData.supervisor_llm_provider,
                        llm_model: formData.supervisor_llm_model,
                        decision_strategy: formData.supervisor_decision_strategy,
                      }}
                      onConfigUpdate={(config) => {
                        setFormData({ ...formData, ...config });
                      }}
                    />
                  </div>
                </div>

                {/* 실시간 대시보드 */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-purple-600" />
                    <h4 className="font-semibold">실시간 모니터링</h4>
                  </div>
                  <SupervisorDashboard
                    agentflowId={id}
                    supervisorEnabled={formData.supervisor_enabled}
                    onToggleSupervisor={(enabled) => setFormData({ ...formData, supervisor_enabled: enabled })}
                  />
                </div>

                {/* 기능 요약 */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card className="bg-green-50 dark:bg-green-950/20 border-green-200">
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                        <span className="font-medium text-green-800 dark:text-green-200">지능형 라우팅</span>
                      </div>
                      <p className="text-sm text-green-700 dark:text-green-300">
                        AI가 실시간으로 최적의 에이전트를 선택하여 작업을 분배합니다
                      </p>
                    </CardContent>
                  </Card>

                  <Card className="bg-blue-50 dark:bg-blue-950/20 border-blue-200">
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-2 mb-2">
                        <TrendingUp className="h-4 w-4 text-blue-600" />
                        <span className="font-medium text-blue-800 dark:text-blue-200">성능 최적화</span>
                      </div>
                      <p className="text-sm text-blue-700 dark:text-blue-300">
                        실시간 성능 데이터를 분석하여 자동으로 시스템을 최적화합니다
                      </p>
                    </CardContent>
                  </Card>

                  <Card className="bg-purple-50 dark:bg-purple-950/20 border-purple-200">
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Brain className="h-4 w-4 text-purple-600" />
                        <span className="font-medium text-purple-800 dark:text-purple-200">학습 기능</span>
                      </div>
                      <p className="text-sm text-purple-700 dark:text-purple-300">
                        과거 실행 데이터를 학습하여 지속적으로 성능을 개선합니다
                      </p>
                    </CardContent>
                  </Card>
                </div>
              </CardContent>
            ) : (
              <CardContent className="py-12">
                <div className="text-center">
                  <Brain className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">슈퍼바이저 비활성화</h3>
                  <p className="text-muted-foreground mb-4">
                    {formData.orchestration_type === 'hierarchical' 
                      ? '계층적 오케스트레이션에서는 슈퍼바이저가 에이전트들을 효율적으로 관리합니다'
                      : '적응형 오케스트레이션에서는 슈퍼바이저가 상황에 따라 전략을 조정합니다'
                    }
                  </p>
                  <Button 
                    onClick={() => setFormData({ ...formData, supervisor_enabled: true })}
                    className="gap-2"
                  >
                    <Settings className="h-4 w-4" />
                    슈퍼바이저 활성화
                  </Button>
                </div>
              </CardContent>
            )}
          </Card>
        )}

        {/* Agents - Enhanced Design */}
        <Card className="border-2">
          <CardHeader className="border-b bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-950/20 dark:to-blue-950/20">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
                  <Users className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <CardTitle className="text-lg">에이전트 구성</CardTitle>
                  <CardDescription>팀에 포함될 에이전트들을 추가하세요</CardDescription>
                </div>
              </div>
              <div className="flex gap-2">
                <AgentSelector
                  onSelect={handleSelectFromBuildingBlock}
                  selectedAgentIds={agents.map(a => a.agent_id).filter(Boolean)}
                  orchestrationType={ORCHESTRATION_TYPES[formData.orchestration_type]?.name}
                  preferredRoles={getRecommendedRoles(formData.orchestration_type)}
                  trigger={
                    <Button 
                      variant="outline"
                      size="lg"
                      className="shadow-md hover:shadow-lg transition-all"
                    >
                      <Plus className="h-5 w-5 mr-2" />
                      Building Block에서 선택
                    </Button>
                  }
                />
                <Button 
                  onClick={handleAddAgent}
                  size="lg"
                  className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 shadow-md hover:shadow-lg transition-all"
                >
                  <Plus className="h-5 w-5 mr-2" />
                  직접 추가
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            {agents.length === 0 ? (
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-purple-100 to-blue-100 dark:from-purple-900/20 dark:to-blue-900/20 rounded-full blur-3xl opacity-60" />
                
                <div className="relative text-center py-12">
                  <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-white dark:bg-gray-900 shadow-lg mb-6">
                    <Users className="h-10 w-10 text-purple-500" />
                  </div>
                  <h3 className="text-2xl font-bold mb-3 bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                    팀에 에이전트를 추가하세요
                  </h3>
                  <p className="text-muted-foreground mb-2 text-lg">
                    선택한 <span className="font-semibold text-purple-600">{ORCHESTRATION_TYPES[formData.orchestration_type]?.name}</span> 오케스트레이션에
                  </p>
                  <p className="text-muted-foreground mb-8">
                    적합한 에이전트들을 구성하여 강력한 AI 팀을 만들어보세요
                  </p>
                  
                  {/* 추천 에이전트 역할 */}
                  <div className="mb-8 p-4 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-950/20 dark:to-blue-950/20 rounded-lg border border-purple-200 dark:border-purple-800">
                    <h4 className="font-semibold mb-3 text-purple-700 dark:text-purple-300">
                      {ORCHESTRATION_TYPES[formData.orchestration_type]?.name}에 추천하는 에이전트 역할:
                    </h4>
                    <div className="flex flex-wrap gap-2 justify-center">
                      {getRecommendedRoles(formData.orchestration_type).map((role, index) => (
                        <Badge key={index} variant="outline" className="bg-white dark:bg-gray-900 border-purple-300 text-purple-700 dark:text-purple-300">
                          {role}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div className="flex gap-4 justify-center">
                    <AgentSelector
                      onSelect={handleSelectFromBuildingBlock}
                      selectedAgentIds={[]}
                      orchestrationType={ORCHESTRATION_TYPES[formData.orchestration_type]?.name}
                      preferredRoles={getRecommendedRoles(formData.orchestration_type)}
                      trigger={
                        <Button 
                          size="lg"
                          variant="outline"
                          className="shadow-md hover:shadow-lg transition-all border-purple-300 hover:border-purple-400 hover:bg-purple-50 dark:hover:bg-purple-950/20"
                        >
                          <Plus className="h-5 w-5 mr-2" />
                          Building Block에서 선택
                        </Button>
                      }
                    />
                    <Button 
                      onClick={handleAddAgent}
                      size="lg"
                      className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 shadow-md hover:shadow-lg transition-all"
                    >
                      <Plus className="h-5 w-5 mr-2" />
                      직접 추가
                    </Button>
                  </div>

                  {/* 도움말 */}
                  <div className="mt-8 text-sm text-muted-foreground">
                    <p>💡 <strong>팁:</strong> Building Block에서 미리 생성한 에이전트를 선택하면 더 빠르게 구성할 수 있습니다</p>
                  </div>
                </div>
              </div>
            ) : (
              <Accordion type="multiple" className="space-y-2">
                {agents.map((agent, index) => (
                  <AccordionItem key={agent.id} value={agent.id} className="border rounded-lg px-4">
                    <AccordionTrigger className="hover:no-underline">
                      <div className="flex items-center gap-3">
                        <Badge variant="outline">{index + 1}</Badge>
                        <span>{agent.name || '새 에이전트'}</span>
                        {agent.role && <Badge variant="secondary">{agent.role}</Badge>}
                        {agent.agent_id && (
                          <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">
                            Building Block
                          </Badge>
                        )}
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="space-y-4 pt-4">
                      <div className="grid grid-cols-2 gap-4">
                        {!agent.agent_id ? (
                          <>
                            <div className="space-y-2">
                              <Label>기존 에이전트 선택</Label>
                              <Select
                                value={agent.agent_id}
                                onValueChange={(v) => handleAgentChange(agent.id, 'agent_id', v)}
                              >
                                <SelectTrigger>
                                  <SelectValue placeholder="에이전트 선택..." />
                                </SelectTrigger>
                                <SelectContent>
                                  {availableAgents?.agents?.map((a: any) => (
                                    <SelectItem key={a.id} value={a.id}>
                                      {a.name}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </div>
                            <div className="space-y-2">
                              <Label>이름</Label>
                              <Input
                                placeholder="에이전트 이름"
                                value={agent.name}
                                onChange={(e) => handleAgentChange(agent.id, 'name', e.target.value)}
                              />
                            </div>
                          </>
                        ) : (
                          <div className="col-span-2 space-y-2">
                            <Label>선택된 에이전트</Label>
                            <div className="p-3 bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 rounded-lg">
                              <div className="flex items-center gap-2">
                                <Badge className="bg-green-500 hover:bg-green-600">Building Block</Badge>
                                <span className="font-medium">{agent.name}</span>
                              </div>
                              {agent.description && (
                                <p className="text-sm text-muted-foreground mt-1">{agent.description}</p>
                              )}
                              {agent.capabilities && agent.capabilities.length > 0 && (
                                <div className="flex flex-wrap gap-1 mt-2">
                                  {agent.capabilities.slice(0, 3).map((capability, idx) => (
                                    <Badge key={idx} variant="outline" className="text-xs">
                                      {capability}
                                    </Badge>
                                  ))}
                                  {agent.capabilities.length > 3 && (
                                    <Badge variant="outline" className="text-xs">
                                      +{agent.capabilities.length - 3}개 더
                                    </Badge>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>역할 *</Label>
                          <Input
                            placeholder="예: 데이터 분석가"
                            value={agent.role}
                            onChange={(e) => handleAgentChange(agent.id, 'role', e.target.value)}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>우선순위</Label>
                          <Input
                            type="number"
                            min="1"
                            value={agent.priority}
                            onChange={(e) => handleAgentChange(agent.id, 'priority', parseInt(e.target.value) || 1)}
                          />
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label>설명</Label>
                        <Textarea
                          placeholder="이 에이전트의 역할과 책임을 설명하세요"
                          value={agent.description}
                          onChange={(e) => handleAgentChange(agent.id, 'description', e.target.value)}
                          rows={2}
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>최대 재시도 횟수</Label>
                          <Input
                            type="number"
                            min="0"
                            max="10"
                            value={agent.max_retries}
                            onChange={(e) => handleAgentChange(agent.id, 'max_retries', parseInt(e.target.value) || 3)}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>타임아웃 (초)</Label>
                          <Input
                            type="number"
                            min="10"
                            max="3600"
                            value={agent.timeout_seconds}
                            onChange={(e) => handleAgentChange(agent.id, 'timeout_seconds', parseInt(e.target.value) || 60)}
                          />
                        </div>
                      </div>

                      <div className="flex justify-between items-center pt-4 border-t">
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleRemoveAgent(agent.id)}
                        >
                          <Trash className="h-4 w-4 mr-2" />
                          에이전트 제거
                        </Button>
                        
                        {!agent.agent_id && (
                          <AgentSelector
                            onSelect={(selectedAgent) => {
                              handleAgentChange(agent.id, 'agent_id', selectedAgent.id);
                              handleAgentChange(agent.id, 'name', selectedAgent.name);
                              handleAgentChange(agent.id, 'description', selectedAgent.description || '');
                              // API Agent doesn't have capabilities, so we skip this
                            }}
                            selectedAgentIds={agents.map(a => a.agent_id).filter(Boolean)}
                            orchestrationType={ORCHESTRATION_TYPES[formData.orchestration_type]?.name}
                            preferredRoles={getRecommendedRoles(formData.orchestration_type)}
                            trigger={
                              <Button variant="outline" size="sm">
                                Building Block에서 선택
                              </Button>
                            }
                          />
                        )}
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
