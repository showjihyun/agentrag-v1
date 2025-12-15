'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  ArrowLeft,
  Save,
  Play,
  Users,
  Settings,
  Sparkles,
  GitMerge,
  Layers,
  Network,
  Zap,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { flowsAPI } from '@/lib/api/flows';

const ORCHESTRATION_TYPES = [
  {
    id: 'sequential',
    name: '순차 실행',
    description: '에이전트들이 순서대로 실행됩니다',
    icon: GitMerge,
    color: 'text-blue-500',
    bgColor: 'bg-blue-50 dark:bg-blue-950',
  },
  {
    id: 'parallel',
    name: '병렬 실행',
    description: '여러 에이전트가 동시에 실행됩니다',
    icon: Layers,
    color: 'text-green-500',
    bgColor: 'bg-green-50 dark:bg-green-950',
  },
  {
    id: 'hierarchical',
    name: '계층적 실행',
    description: '상위 에이전트가 하위 에이전트들을 관리합니다',
    icon: Network,
    color: 'text-purple-500',
    bgColor: 'bg-purple-50 dark:bg-purple-950',
  },
  {
    id: 'adaptive',
    name: '적응형 실행',
    description: 'AI가 상황에 따라 실행 방식을 결정합니다',
    icon: Zap,
    color: 'text-orange-500',
    bgColor: 'bg-orange-50 dark:bg-orange-950',
  },
];

const TEMPLATES = [
  {
    id: 'multi-agent-research',
    name: '리서치 에이전트 팀',
    description: '여러 에이전트가 협력하여 정보를 수집하고 분석합니다',
    orchestration: 'hierarchical',
    agents: 4,
    icon: '🔬',
    tags: ['research', 'analysis', 'multi-agent'],
  },
  {
    id: 'customer-support-team',
    name: '고객 지원 팀',
    description: '분류, 응답, 에스컬레이션을 담당하는 에이전트 팀',
    orchestration: 'adaptive',
    agents: 3,
    icon: '🎧',
    tags: ['customer-service', 'support', 'routing'],
  },
  {
    id: 'content-pipeline',
    name: '콘텐츠 생성 파이프라인',
    description: '기획, 작성, 검토, 발행을 순차적으로 처리',
    orchestration: 'sequential',
    agents: 4,
    icon: '✍️',
    tags: ['content', 'writing', 'pipeline'],
  },
  {
    id: 'data-analysis-team',
    name: '데이터 분석 팀',
    description: '여러 데이터 소스를 병렬로 분석하고 결과를 통합',
    orchestration: 'parallel',
    agents: 5,
    icon: '📊',
    tags: ['data', 'analysis', 'parallel'],
  },
];

export default function NewAgentflowPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    orchestration_type: 'sequential',
    supervisor_config: {
      enabled: true,
      llm_provider: 'ollama',
      llm_model: 'llama3.1:8b',
      max_iterations: 10,
      decision_strategy: 'llm_based',
    },
    graph_definition: {},
    tags: [] as string[],
  });
  
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Load template if specified in URL
  useEffect(() => {
    const templateId = searchParams.get('template');
    if (templateId) {
      const template = TEMPLATES.find(t => t.id === templateId);
      if (template) {
        setSelectedTemplate(templateId);
        setFormData(prev => ({
          ...prev,
          name: template.name,
          description: template.description,
          orchestration_type: template.orchestration,
          tags: template.tags,
        }));
      }
    }
  }, [searchParams]);

  const handleSave = async () => {
    if (!formData.name.trim()) {
      toast({
        title: '오류',
        description: 'Agentflow 이름을 입력해주세요',
        variant: 'destructive',
      });
      return;
    }

    try {
      setSaving(true);
      const agentflow = await flowsAPI.createAgentflow(formData);
      
      toast({
        title: '생성 완료',
        description: `"${formData.name}" Agentflow가 생성되었습니다`,
      });
      
      router.push(`/agent-builder/agentflows/${agentflow.id}`);
    } catch (error: any) {
      toast({
        title: '오류',
        description: error.message || 'Agentflow 생성에 실패했습니다',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleTemplateSelect = (template: typeof TEMPLATES[0]) => {
    setSelectedTemplate(template.id);
    setFormData(prev => ({
      ...prev,
      name: template.name,
      description: template.description,
      orchestration_type: template.orchestration,
      tags: template.tags,
    }));
  };

  const selectedOrchestration = ORCHESTRATION_TYPES.find(
    type => type.id === formData.orchestration_type
  );

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          뒤로
        </Button>
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
              <Users className="h-6 w-6 text-purple-600 dark:text-purple-400" />
            </div>
            새 Agentflow 만들기
          </h1>
          <p className="text-muted-foreground mt-1">
            멀티 에이전트 시스템을 구축하여 복잡한 작업을 자동화하세요
          </p>
        </div>
      </div>

      <Tabs defaultValue="basic" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="basic">기본 정보</TabsTrigger>
          <TabsTrigger value="orchestration">오케스트레이션</TabsTrigger>
          <TabsTrigger value="templates">템플릿</TabsTrigger>
        </TabsList>

        {/* Basic Information */}
        <TabsContent value="basic" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>기본 정보</CardTitle>
              <CardDescription>
                Agentflow의 이름과 설명을 입력하세요
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">이름 *</Label>
                <Input
                  id="name"
                  placeholder="예: 고객 지원 자동화 시스템"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="description">설명</Label>
                <Textarea
                  id="description"
                  placeholder="이 Agentflow가 수행할 작업을 설명해주세요..."
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label>태그</Label>
                <div className="flex flex-wrap gap-2">
                  {formData.tags.map((tag, index) => (
                    <Badge key={index} variant="secondary">
                      {tag}
                    </Badge>
                  ))}
                  {formData.tags.length === 0 && (
                    <p className="text-sm text-muted-foreground">
                      템플릿을 선택하거나 오케스트레이션 유형을 설정하면 자동으로 태그가 추가됩니다
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Orchestration */}
        <TabsContent value="orchestration" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>오케스트레이션 설정</CardTitle>
              <CardDescription>
                에이전트들이 어떻게 협력할지 결정하세요
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {ORCHESTRATION_TYPES.map((type) => {
                  const Icon = type.icon;
                  const isSelected = formData.orchestration_type === type.id;
                  
                  return (
                    <Card
                      key={type.id}
                      className={`cursor-pointer transition-all border-2 ${
                        isSelected 
                          ? 'border-primary shadow-lg' 
                          : 'border-border hover:border-primary/50'
                      }`}
                      onClick={() => setFormData(prev => ({ 
                        ...prev, 
                        orchestration_type: type.id 
                      }))}
                    >
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg ${type.bgColor}`}>
                            <Icon className={`h-5 w-5 ${type.color}`} />
                          </div>
                          <div>
                            <CardTitle className="text-base">{type.name}</CardTitle>
                            <CardDescription className="text-sm">
                              {type.description}
                            </CardDescription>
                          </div>
                        </div>
                      </CardHeader>
                    </Card>
                  );
                })}
              </div>

              {selectedOrchestration && (
                <div className="mt-6 p-4 rounded-lg bg-muted">
                  <div className="flex items-center gap-2 mb-2">
                    <selectedOrchestration.icon className={`h-4 w-4 ${selectedOrchestration.color}`} />
                    <span className="font-medium">{selectedOrchestration.name} 선택됨</span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {selectedOrchestration.description}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Supervisor Configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                슈퍼바이저 설정
              </CardTitle>
              <CardDescription>
                에이전트들을 관리할 슈퍼바이저 AI를 설정하세요
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>LLM 제공자</Label>
                  <Select
                    value={formData.supervisor_config.llm_provider}
                    onValueChange={(value) => setFormData(prev => ({
                      ...prev,
                      supervisor_config: {
                        ...prev.supervisor_config,
                        llm_provider: value,
                      }
                    }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ollama">Ollama (로컬)</SelectItem>
                      <SelectItem value="openai">OpenAI</SelectItem>
                      <SelectItem value="anthropic">Anthropic</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>모델</Label>
                  <Input
                    value={formData.supervisor_config.llm_model}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      supervisor_config: {
                        ...prev.supervisor_config,
                        llm_model: e.target.value,
                      }
                    }))}
                    placeholder="llama3.1:8b"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>최대 반복 횟수</Label>
                <Input
                  type="number"
                  min="1"
                  max="50"
                  value={formData.supervisor_config.max_iterations}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    supervisor_config: {
                      ...prev.supervisor_config,
                      max_iterations: parseInt(e.target.value) || 10,
                    }
                  }))}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Templates */}
        <TabsContent value="templates" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-purple-500" />
                템플릿 선택
              </CardTitle>
              <CardDescription>
                미리 구성된 템플릿으로 빠르게 시작하세요
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {TEMPLATES.map((template) => {
                  const isSelected = selectedTemplate === template.id;
                  
                  return (
                    <Card
                      key={template.id}
                      className={`cursor-pointer transition-all border-2 ${
                        isSelected 
                          ? 'border-primary shadow-lg' 
                          : 'border-border hover:border-primary/50'
                      }`}
                      onClick={() => handleTemplateSelect(template)}
                    >
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="text-3xl mb-2">{template.icon}</div>
                          <Badge variant="outline">
                            {template.agents} 에이전트
                          </Badge>
                        </div>
                        <CardTitle className="text-base">{template.name}</CardTitle>
                        <CardDescription className="text-sm">
                          {template.description}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="flex flex-wrap gap-1">
                          {template.tags.map((tag) => (
                            <Badge key={tag} variant="secondary" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Actions */}
      <div className="flex items-center justify-between pt-6 border-t">
        <Button variant="outline" onClick={() => router.back()}>
          취소
        </Button>
        <div className="flex gap-3">
          <Button variant="outline" disabled={saving}>
            <Play className="h-4 w-4 mr-2" />
            미리보기
          </Button>
          <Button onClick={handleSave} disabled={saving || !formData.name.trim()}>
            {saving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                생성 중...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                생성하기
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}