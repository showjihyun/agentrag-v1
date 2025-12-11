'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  Users,
  ArrowLeft,
  Save,
  GitMerge,
  Layers,
  Network,
  Sparkles,
  Plus,
  Trash,
  Settings,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
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
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { useQuery } from '@tanstack/react-query';

const ORCHESTRATION_OPTIONS = [
  {
    value: 'sequential',
    label: '순차 실행',
    description: '에이전트들이 순서대로 실행됩니다',
    icon: GitMerge,
  },
  {
    value: 'parallel',
    label: '병렬 실행',
    description: '에이전트들이 동시에 실행됩니다',
    icon: Layers,
  },
  {
    value: 'hierarchical',
    label: '계층적 실행',
    description: '슈퍼바이저가 하위 에이전트를 조율합니다',
    icon: Network,
  },
  {
    value: 'adaptive',
    label: '적응형 실행',
    description: 'LLM이 상황에 따라 최적의 에이전트를 선택합니다',
    icon: Sparkles,
  },
];

interface AgentConfig {
  id: string;
  agent_id: string;
  name: string;
  role: string;
  description: string;
  priority: number;
  max_retries: number;
  timeout_seconds: number;
}

export default function NewAgentflowPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const templateId = searchParams.get('template');
  const { toast } = useToast();

  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    orchestration_type: 'sequential' as const,
    supervisor_enabled: false,
    supervisor_llm_provider: 'ollama',
    supervisor_llm_model: 'llama3.1',
    supervisor_max_iterations: 10,
    supervisor_decision_strategy: 'llm_based' as const,
    tags: [] as string[],
  });
  const [agents, setAgents] = useState<AgentConfig[]>([]);
  const [newTag, setNewTag] = useState('');

  // Template data loading
  useEffect(() => {
    if (templateId) {
      loadTemplateData(templateId);
    }
  }, [templateId]);

  const loadTemplateData = (templateId: string) => {
    const templateData = {
      'multi-agent-research': {
        name: '리서치 에이전트 팀',
        description: '여러 에이전트가 협력하여 정보를 수집하고 분석합니다',
        orchestration_type: 'hierarchical' as const,
        tags: ['리서치', '분석', '협업'],
      },
      'customer-support-team': {
        name: '고객 지원 팀',
        description: '분류, 응답, 에스컬레이션을 담당하는 에이전트 팀',
        orchestration_type: 'adaptive' as const,
        tags: ['고객지원', '자동화'],
      },
      'content-pipeline': {
        name: '콘텐츠 생성 파이프라인',
        description: '기획, 작성, 검토, 발행을 순차적으로 처리',
        orchestration_type: 'sequential' as const,
        tags: ['콘텐츠', '파이프라인'],
      },
      'data-analysis-team': {
        name: '데이터 분석 팀',
        description: '여러 데이터 소스를 병렬로 분석하고 결과를 통합',
        orchestration_type: 'parallel' as const,
        tags: ['데이터', '분석', '병렬'],
      },
    };

    const template = templateData[templateId as keyof typeof templateData];
    if (template) {
      setFormData(prev => ({
        ...prev,
        ...template,
      }));
    }
  };

  // Fetch available agents
  const { data: availableAgents } = useQuery({
    queryKey: ['available-agents'],
    queryFn: () => agentBuilderAPI.getAgents(),
  });

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
          // If selecting an existing agent, populate name and description
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
      const response = await flowsAPI.createAgentflow({
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
          agent_id: agent.agent_id,
          name: agent.name,
          role: agent.role,
          description: agent.description,
          priority: agent.priority,
          max_retries: agent.max_retries,
          timeout_seconds: agent.timeout_seconds,
        })) : undefined,
        tags: formData.tags,
      });

      toast({
        title: '생성 완료',
        description: 'Agentflow가 생성되었습니다',
      });

      router.push(`/agent-builder/agentflows/${response.id}/edit`);
    } catch (error: any) {
      toast({
        title: '오류',
        description: error.message || '생성에 실패했습니다',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

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
              새 Agentflow 만들기
            </h1>
            <p className="text-muted-foreground mt-1 text-base">멀티 에이전트 시스템을 구성하세요</p>
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
            <Save className="h-5 w-5 mr-2" />
            {saving ? '저장 중...' : '저장하고 계속'}
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
                  onKeyDown={(e) => e.key === 'Enter' && handleAddTag()}
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
          <CardContent className="pt-6">
            <div className="grid grid-cols-2 gap-4">
              {ORCHESTRATION_OPTIONS.map((option) => {
                const Icon = option.icon;
                const isSelected = formData.orchestration_type === option.value;
                return (
                  <Card
                    key={option.value}
                    className={`cursor-pointer transition-all duration-300 hover:shadow-lg group ${
                      isSelected 
                        ? 'border-2 border-purple-500 bg-purple-50 dark:bg-purple-950/20 ring-2 ring-purple-500 shadow-lg scale-[1.02]' 
                        : 'hover:border-purple-300 hover:scale-[1.01]'
                    }`}
                    onClick={() => setFormData({ ...formData, orchestration_type: option.value as any })}
                  >
                    <CardContent className="pt-6">
                      <div className="flex flex-col items-center text-center gap-3">
                        <div className={`p-4 rounded-xl transition-all duration-300 ${
                          isSelected 
                            ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg scale-110' 
                            : 'bg-gray-100 dark:bg-gray-800 group-hover:bg-purple-100 dark:group-hover:bg-purple-900/20'
                        }`}>
                          <Icon className="h-8 w-8" />
                        </div>
                        <div>
                          <p className={`font-semibold text-lg mb-1 ${isSelected ? 'text-purple-600 dark:text-purple-400' : ''}`}>
                            {option.label}
                          </p>
                          <p className="text-sm text-muted-foreground leading-relaxed">
                            {option.description}
                          </p>
                        </div>
                        {isSelected && (
                          <Badge className="bg-purple-500 hover:bg-purple-600">
                            선택됨 ✓
                          </Badge>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Supervisor Config (for hierarchical/adaptive) */}
        {(formData.orchestration_type === 'hierarchical' || formData.orchestration_type === 'adaptive') && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>슈퍼바이저 설정</CardTitle>
                  <CardDescription>에이전트들을 조율하는 슈퍼바이저를 구성하세요</CardDescription>
                </div>
                <Switch
                  checked={formData.supervisor_enabled}
                  onCheckedChange={(v) => setFormData({ ...formData, supervisor_enabled: v })}
                />
              </div>
            </CardHeader>
            {formData.supervisor_enabled && (
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
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
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>최대 반복 횟수</Label>
                    <Input
                      type="number"
                      value={formData.supervisor_max_iterations}
                      onChange={(e) => setFormData({ ...formData, supervisor_max_iterations: parseInt(e.target.value) })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>결정 전략</Label>
                    <Select
                      value={formData.supervisor_decision_strategy}
                      onValueChange={(v) => setFormData({ ...formData, supervisor_decision_strategy: v as any })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="llm_based">LLM 기반</SelectItem>
                        <SelectItem value="rule_based">규칙 기반</SelectItem>
                        <SelectItem value="round_robin">라운드 로빈</SelectItem>
                        <SelectItem value="priority">우선순위</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
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
              <Button 
                onClick={handleAddAgent}
                size="lg"
                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 shadow-md hover:shadow-lg transition-all"
              >
                <Plus className="h-5 w-5 mr-2" />
                에이전트 추가
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            {agents.length === 0 ? (
              <div className="relative">
                {/* Background gradient blur */}
                <div className="absolute inset-0 bg-gradient-to-r from-purple-100 to-blue-100 dark:from-purple-900/20 dark:to-blue-900/20 rounded-full blur-3xl opacity-60" />
                
                <div className="relative text-center py-12">
                  <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-white dark:bg-gray-900 shadow-lg mb-4">
                    <Users className="h-10 w-10 text-purple-500" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">아직 에이전트가 없습니다</h3>
                  <p className="text-muted-foreground mb-6">에이전트를 추가하여 팀을 구성하세요</p>
                  <Button 
                    onClick={handleAddAgent}
                    size="lg"
                    className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                  >
                    <Plus className="h-5 w-5 mr-2" />
                    첫 번째 에이전트 추가
                  </Button>
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
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="space-y-4 pt-4">
                      <div className="grid grid-cols-2 gap-4">
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
                          <Label>역할</Label>
                          <Input
                            placeholder="예: 데이터 분석가"
                            value={agent.role}
                            onChange={(e) => handleAgentChange(agent.id, 'role', e.target.value)}
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-3 gap-4">
                        <div className="space-y-2">
                          <Label>우선순위</Label>
                          <Input
                            type="number"
                            value={agent.priority}
                            onChange={(e) => handleAgentChange(agent.id, 'priority', parseInt(e.target.value))}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>최대 재시도</Label>
                          <Input
                            type="number"
                            value={agent.max_retries}
                            onChange={(e) => handleAgentChange(agent.id, 'max_retries', parseInt(e.target.value))}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>타임아웃 (초)</Label>
                          <Input
                            type="number"
                            value={agent.timeout_seconds}
                            onChange={(e) => handleAgentChange(agent.id, 'timeout_seconds', parseInt(e.target.value))}
                          />
                        </div>
                      </div>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleRemoveAgent(agent.id)}
                      >
                        <Trash className="h-4 w-4 mr-2" />
                        에이전트 제거
                      </Button>
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
