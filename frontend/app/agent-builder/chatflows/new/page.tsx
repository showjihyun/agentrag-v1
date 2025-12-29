'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  ArrowLeft,
  Save,
  Play,
  MessageSquare,
  Settings,
  Sparkles,
  Database,
  Brain,
  Wrench,
  Code,
  Globe,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Slider } from '@/components/ui/slider';
import { useToast } from '@/hooks/use-toast';
import { flowsAPI } from '@/lib/api/flows';

const TEMPLATES = [
  {
    id: 'rag-chatbot',
    name: 'RAG 챗봇',
    description: '문서 기반 질의응답 챗봇 (지식베이스 연동)',
    features: ['RAG', 'Memory'],
    icon: '📚',
    config: {
      rag_enabled: true,
      memory_type: 'vector',
      tools: ['vector_search', 'web_search'],
    },
  },
  {
    id: 'customer-support',
    name: '고객 지원 챗봇',
    description: 'FAQ 및 티켓 생성 기능이 포함된 지원 봇',
    features: ['Tools', 'Memory'],
    icon: '🎧',
    config: {
      rag_enabled: false,
      memory_type: 'buffer',
      tools: ['slack', 'email', 'database'],
    },
  },
  {
    id: 'code-assistant',
    name: '코드 어시스턴트',
    description: '코드 작성, 리뷰, 디버깅을 도와주는 AI',
    features: ['Tools', 'Code'],
    icon: '💻',
    config: {
      rag_enabled: false,
      memory_type: 'summary',
      tools: ['code_execution', 'github', 'documentation'],
    },
  },
  {
    id: 'research-assistant',
    name: '리서치 어시스턴트',
    description: '웹 검색과 문서 분석을 통한 리서치 지원',
    features: ['RAG', 'Web Search'],
    icon: '🔬',
    config: {
      rag_enabled: true,
      memory_type: 'hybrid',
      tools: ['web_search', 'vector_search', 'document_analysis'],
    },
  },
];

const MEMORY_TYPES = [
  {
    id: 'buffer',
    name: '버퍼 메모리',
    description: '최근 대화 내용을 그대로 저장',
    icon: Brain,
  },
  {
    id: 'summary',
    name: '요약 메모리',
    description: '대화 내용을 요약하여 저장',
    icon: Brain,
  },
  {
    id: 'vector',
    name: '벡터 메모리',
    description: '임베딩을 사용한 의미 기반 저장',
    icon: Database,
  },
  {
    id: 'hybrid',
    name: '하이브리드 메모리',
    description: '여러 메모리 방식을 조합',
    icon: Sparkles,
  },
];

export default function NewChatflowPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    chat_config: {
      llm_provider: 'ollama',
      llm_model: 'llama3.1:8b',
      system_prompt: '당신은 도움이 되는 AI 어시스턴트입니다. 사용자의 질문에 정확하고 친절하게 답변해주세요.',
      temperature: 0.7,
      max_tokens: 2000,
      streaming: true,
      welcome_message: '안녕하세요! 무엇을 도와드릴까요?',
      suggested_questions: [
        '이 시스템은 어떻게 사용하나요?',
        '도움이 필요합니다',
        '문서를 분석해주세요',
      ],
    },
    memory_config: {
      type: 'buffer',
      max_messages: 20,
      summary_threshold: null,
      vector_store_id: null,
    },
    rag_config: {
      enabled: false,
      knowledgebase_ids: [],
      retrieval_strategy: 'hybrid',
      top_k: 5,
      score_threshold: 0.7,
      reranking_enabled: true,
      reranking_model: null,
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
          memory_config: {
            ...prev.memory_config,
            type: template.config.memory_type,
          },
          rag_config: {
            ...prev.rag_config,
            enabled: template.config.rag_enabled,
          },
          tags: template.features.map(f => f.toLowerCase()),
        }));
      }
    }
  }, [searchParams]);

  const handleSave = async () => {
    if (!formData.name.trim()) {
      toast({
        title: '오류',
        description: 'Chatflow 이름을 입력해주세요',
        variant: 'destructive',
      });
      return;
    }

    try {
      setSaving(true);
      const chatflow = await flowsAPI.createChatflow(formData as any);
      
      toast({
        title: '생성 완료',
        description: `"${formData.name}" Chatflow가 생성되었습니다`,
      });
      
      router.push(`/agent-builder/chatflows/${chatflow.id}`);
    } catch (error: any) {
      toast({
        title: '오류',
        description: error.message || 'Chatflow 생성에 실패했습니다',
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
      memory_config: {
        ...prev.memory_config,
        type: template.config.memory_type,
      },
      rag_config: {
        ...prev.rag_config,
        enabled: template.config.rag_enabled,
      },
      tags: template.features.map(f => f.toLowerCase()),
    }));
  };

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
            <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
              <MessageSquare className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            새 Chatflow 만들기
          </h1>
          <p className="text-muted-foreground mt-1">
            RAG 기반 챗봇과 AI 어시스턴트를 구축하세요
          </p>
        </div>
      </div>

      <Tabs defaultValue="basic" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="basic">기본 정보</TabsTrigger>
          <TabsTrigger value="chat">채팅 설정</TabsTrigger>
          <TabsTrigger value="memory">메모리 & RAG</TabsTrigger>
          <TabsTrigger value="templates">템플릿</TabsTrigger>
        </TabsList>

        {/* Basic Information */}
        <TabsContent value="basic" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>기본 정보</CardTitle>
              <CardDescription>
                Chatflow의 이름과 설명을 입력하세요
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">이름 *</Label>
                <Input
                  id="name"
                  placeholder="예: 고객 지원 챗봇"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="description">설명</Label>
                <Textarea
                  id="description"
                  placeholder="이 Chatflow가 수행할 작업을 설명해주세요..."
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
                      템플릿을 선택하면 자동으로 태그가 추가됩니다
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Chat Configuration */}
        <TabsContent value="chat" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>LLM 설정</CardTitle>
              <CardDescription>
                채팅에 사용할 언어 모델을 설정하세요
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>LLM 제공자</Label>
                  <Select
                    value={formData.chat_config.llm_provider}
                    onValueChange={(value) => setFormData(prev => ({
                      ...prev,
                      chat_config: { ...prev.chat_config, llm_provider: value }
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
                    value={formData.chat_config.llm_model}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      chat_config: { ...prev.chat_config, llm_model: e.target.value }
                    }))}
                    placeholder="llama3.1:8b"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>시스템 프롬프트</Label>
                <Textarea
                  value={formData.chat_config.system_prompt}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    chat_config: { ...prev.chat_config, system_prompt: e.target.value }
                  }))}
                  rows={4}
                  placeholder="AI의 역할과 행동 방식을 정의하세요..."
                />
              </div>

              <div className="space-y-2">
                <Label>Temperature: {formData.chat_config.temperature}</Label>
                <Slider
                  value={[formData.chat_config.temperature]}
                  onValueChange={([value]) => setFormData(prev => ({
                    ...prev,
                    chat_config: { ...prev.chat_config, temperature: value ?? 0.7 }
                  }))}
                  max={2}
                  min={0}
                  step={0.1}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground">
                  낮을수록 일관된 답변, 높을수록 창의적인 답변
                </p>
              </div>

              <div className="space-y-2">
                <Label>최대 토큰 수</Label>
                <Input
                  type="number"
                  min="100"
                  max="8000"
                  value={formData.chat_config.max_tokens}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    chat_config: { ...prev.chat_config, max_tokens: parseInt(e.target.value) || 2000 }
                  }))}
                />
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="streaming"
                  checked={formData.chat_config.streaming}
                  onCheckedChange={(checked) => setFormData(prev => ({
                    ...prev,
                    chat_config: { ...prev.chat_config, streaming: checked }
                  }))}
                />
                <Label htmlFor="streaming">스트리밍 응답</Label>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>사용자 경험</CardTitle>
              <CardDescription>
                사용자와의 첫 만남을 설정하세요
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>환영 메시지</Label>
                <Input
                  value={formData.chat_config.welcome_message}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    chat_config: { ...prev.chat_config, welcome_message: e.target.value }
                  }))}
                  placeholder="안녕하세요! 무엇을 도와드릴까요?"
                />
              </div>

              <div className="space-y-2">
                <Label>추천 질문</Label>
                {formData.chat_config.suggested_questions.map((question, index) => (
                  <Input
                    key={index}
                    value={question}
                    onChange={(e) => {
                      const newQuestions = [...formData.chat_config.suggested_questions];
                      newQuestions[index] = e.target.value;
                      setFormData(prev => ({
                        ...prev,
                        chat_config: { ...prev.chat_config, suggested_questions: newQuestions }
                      }));
                    }}
                    placeholder={`추천 질문 ${index + 1}`}
                  />
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Memory & RAG */}
        <TabsContent value="memory" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>메모리 설정</CardTitle>
              <CardDescription>
                대화 기록을 어떻게 저장하고 활용할지 설정하세요
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {MEMORY_TYPES.map((type) => {
                  const Icon = type.icon;
                  const isSelected = formData.memory_config.type === type.id;
                  
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
                        memory_config: { ...prev.memory_config, type: type.id }
                      }))}
                    >
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-3">
                          <Icon className="h-5 w-5 text-blue-500" />
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

              <div className="mt-4 space-y-4">
                <div className="space-y-2">
                  <Label>최대 메시지 수</Label>
                  <Input
                    type="number"
                    min="5"
                    max="100"
                    value={formData.memory_config.max_messages}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      memory_config: { ...prev.memory_config, max_messages: parseInt(e.target.value) || 20 }
                    }))}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5 text-purple-500" />
                RAG 설정
              </CardTitle>
              <CardDescription>
                지식베이스와 연동하여 정확한 정보를 제공하세요
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-2">
                <Switch
                  id="rag-enabled"
                  checked={formData.rag_config.enabled}
                  onCheckedChange={(checked) => setFormData(prev => ({
                    ...prev,
                    rag_config: { ...prev.rag_config, enabled: checked }
                  }))}
                />
                <Label htmlFor="rag-enabled">RAG 활성화</Label>
              </div>

              {formData.rag_config.enabled && (
                <div className="space-y-4 p-4 border rounded-lg">
                  <div className="space-y-2">
                    <Label>검색 전략</Label>
                    <Select
                      value={formData.rag_config.retrieval_strategy}
                      onValueChange={(value) => setFormData(prev => ({
                        ...prev,
                        rag_config: { ...prev.rag_config, retrieval_strategy: value }
                      }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="similarity">유사도 검색</SelectItem>
                        <SelectItem value="mmr">MMR (다양성 고려)</SelectItem>
                        <SelectItem value="hybrid">하이브리드 검색</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Top K</Label>
                      <Input
                        type="number"
                        min="1"
                        max="20"
                        value={formData.rag_config.top_k}
                        onChange={(e) => setFormData(prev => ({
                          ...prev,
                          rag_config: { ...prev.rag_config, top_k: parseInt(e.target.value) || 5 }
                        }))}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>점수 임계값</Label>
                      <Input
                        type="number"
                        min="0"
                        max="1"
                        step="0.1"
                        value={formData.rag_config.score_threshold}
                        onChange={(e) => setFormData(prev => ({
                          ...prev,
                          rag_config: { ...prev.rag_config, score_threshold: parseFloat(e.target.value) || 0.7 }
                        }))}
                      />
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="reranking"
                      checked={formData.rag_config.reranking_enabled}
                      onCheckedChange={(checked) => setFormData(prev => ({
                        ...prev,
                        rag_config: { ...prev.rag_config, reranking_enabled: checked }
                      }))}
                    />
                    <Label htmlFor="reranking">리랭킹 활성화</Label>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Templates */}
        <TabsContent value="templates" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-blue-500" />
                Chatflow 템플릿
              </CardTitle>
              <CardDescription>
                미리 구성된 챗봇 템플릿으로 빠르게 시작하세요
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
                        <div className="text-3xl mb-2">{template.icon}</div>
                        <CardTitle className="text-base">{template.name}</CardTitle>
                        <CardDescription className="text-sm">
                          {template.description}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center gap-2 flex-wrap">
                          {template.features.map((feature) => (
                            <Badge key={feature} variant="secondary" className="text-xs">
                              {feature === 'RAG' && <Database className="h-3 w-3 mr-1" />}
                              {feature === 'Tools' && <Wrench className="h-3 w-3 mr-1" />}
                              {feature === 'Memory' && <Brain className="h-3 w-3 mr-1" />}
                              {feature === 'Code' && <Code className="h-3 w-3 mr-1" />}
                              {feature === 'Web Search' && <Globe className="h-3 w-3 mr-1" />}
                              {feature}
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