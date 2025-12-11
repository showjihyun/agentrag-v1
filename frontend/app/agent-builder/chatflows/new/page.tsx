'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  MessageSquare,
  ArrowLeft,
  Save,
  Database,
  Brain,
  Wrench,
  Settings,
  Plus,
  Trash,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
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
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { useQuery } from '@tanstack/react-query';

export default function NewChatflowPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const templateId = searchParams.get('template');
  const { toast } = useToast();

  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    // Chat Config
    llm_provider: 'ollama',
    llm_model: 'llama3.1',
    system_prompt: 'You are a helpful assistant.',
    temperature: 0.7,
    max_tokens: 2048,
    streaming: true,
    welcome_message: '안녕하세요! 무엇을 도와드릴까요?',
    suggested_questions: [] as string[],
    // Memory Config
    memory_type: 'buffer' as const,
    memory_max_messages: 20,
    // RAG Config
    rag_enabled: false,
    rag_knowledgebase_ids: [] as string[],
    rag_retrieval_strategy: 'hybrid' as const,
    rag_top_k: 5,
    rag_score_threshold: 0.7,
    rag_reranking_enabled: true,
    // Tools
    tool_ids: [] as string[],
    // Tags
    tags: [] as string[],
  });
  const [newTag, setNewTag] = useState('');
  const [newQuestion, setNewQuestion] = useState('');

  // Fetch knowledgebases
  const { data: knowledgebases } = useQuery({
    queryKey: ['knowledgebases'],
    queryFn: () => agentBuilderAPI.getKnowledgebases(),
  });

  // Fetch tools
  const { data: tools } = useQuery({
    queryKey: ['tools'],
    queryFn: () => agentBuilderAPI.getTools(),
  });

  // Template data loading
  useEffect(() => {
    if (templateId) {
      loadTemplateData(templateId);
    }
  }, [templateId]);

  const loadTemplateData = (templateId: string) => {
    const templateData = {
      'rag-chatbot': {
        name: 'RAG 챗봇',
        description: '문서 기반 질의응답 챗봇 (지식베이스 연동)',
        system_prompt: 'You are a helpful assistant that answers questions based on the provided documents. Always cite your sources and be accurate.',
        rag_enabled: true,
        tags: ['RAG', '문서검색', '챗봇'],
      },
      'customer-support': {
        name: '고객 지원 챗봇',
        description: 'FAQ 및 티켓 생성 기능이 포함된 지원 봇',
        system_prompt: 'You are a customer support assistant. Be helpful, professional, and empathetic. Always try to resolve issues efficiently.',
        welcome_message: '안녕하세요! 고객 지원팀입니다. 어떻게 도와드릴까요?',
        suggested_questions: ['주문 상태 확인', '환불 요청', '기술 지원', '계정 문제'],
        tags: ['고객지원', '헬프데스크'],
      },
      'code-assistant': {
        name: '코드 어시스턴트',
        description: '코드 작성, 리뷰, 디버깅을 도와주는 AI',
        system_prompt: 'You are a coding assistant. Help users write, review, and debug code. Provide clear explanations and best practices.',
        welcome_message: '안녕하세요! 코딩을 도와드리겠습니다. 어떤 언어나 문제를 다루고 계신가요?',
        suggested_questions: ['코드 리뷰 요청', '버그 디버깅', '최적화 방법', '베스트 프랙티스'],
        tags: ['코딩', '개발', '프로그래밍'],
      },
      'research-assistant': {
        name: '리서치 어시스턴트',
        description: '웹 검색과 문서 분석을 통한 리서치 지원',
        system_prompt: 'You are a research assistant. Help users find information, analyze documents, and provide comprehensive research support.',
        rag_enabled: true,
        welcome_message: '안녕하세요! 리서치를 도와드리겠습니다. 어떤 주제를 조사하고 계신가요?',
        suggested_questions: ['시장 조사', '논문 분석', '트렌드 분석', '경쟁사 분석'],
        tags: ['리서치', '분석', '조사'],
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

  const handleAddTag = () => {
    if (newTag && !formData.tags.includes(newTag)) {
      setFormData({ ...formData, tags: [...formData.tags, newTag] });
      setNewTag('');
    }
  };

  const handleRemoveTag = (tag: string) => {
    setFormData({ ...formData, tags: formData.tags.filter((t) => t !== tag) });
  };

  const handleAddQuestion = () => {
    if (newQuestion && !formData.suggested_questions.includes(newQuestion)) {
      setFormData({
        ...formData,
        suggested_questions: [...formData.suggested_questions, newQuestion],
      });
      setNewQuestion('');
    }
  };

  const handleRemoveQuestion = (question: string) => {
    setFormData({
      ...formData,
      suggested_questions: formData.suggested_questions.filter((q) => q !== question),
    });
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
      const response = await flowsAPI.createChatflow({
        name: formData.name,
        description: formData.description,
        chat_config: {
          llm_provider: formData.llm_provider,
          llm_model: formData.llm_model,
          system_prompt: formData.system_prompt,
          temperature: formData.temperature,
          max_tokens: formData.max_tokens,
          streaming: formData.streaming,
          welcome_message: formData.welcome_message,
          suggested_questions: formData.suggested_questions,
        },
        memory_config: {
          type: formData.memory_type,
          max_messages: formData.memory_max_messages,
        },
        rag_config: formData.rag_enabled
          ? {
              enabled: true,
              knowledgebase_ids: formData.rag_knowledgebase_ids,
              retrieval_strategy: formData.rag_retrieval_strategy,
              top_k: formData.rag_top_k,
              score_threshold: formData.rag_score_threshold,
              reranking_enabled: formData.rag_reranking_enabled,
            }
          : undefined,
        tags: formData.tags,
      });

      toast({
        title: '생성 완료',
        description: 'Chatflow가 생성되었습니다',
      });

      router.push(`/agent-builder/chatflows/${response.id}/edit`);
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
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
                <MessageSquare className="h-7 w-7 text-blue-600 dark:text-blue-400" />
              </div>
              새 Chatflow 만들기
            </h1>
            <p className="text-muted-foreground mt-1 text-base">AI 챗봇을 구성하세요</p>
          </div>
          <Button variant="outline" onClick={() => router.back()} size="lg">
            취소
          </Button>
          <Button 
            onClick={handleSave} 
            disabled={saving}
            size="lg"
            className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 shadow-lg hover:shadow-xl transition-all"
          >
            <Save className="h-5 w-5 mr-2" />
            {saving ? '저장 중...' : '저장하고 계속'}
          </Button>
        </div>
      </div>

      <Tabs defaultValue="basic" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="basic">기본 정보</TabsTrigger>
          <TabsTrigger value="llm">LLM 설정</TabsTrigger>
          <TabsTrigger value="rag">RAG 설정</TabsTrigger>
          <TabsTrigger value="tools">도구</TabsTrigger>
        </TabsList>

        {/* Basic Info Tab */}
        <TabsContent value="basic" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>기본 정보</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">이름 *</Label>
                <Input
                  id="name"
                  placeholder="예: 고객 지원 챗봇"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">설명</Label>
                <Textarea
                  id="description"
                  placeholder="이 챗봇이 수행하는 작업을 설명하세요"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                />
              </div>
              <div className="space-y-2">
                <Label>환영 메시지</Label>
                <Input
                  placeholder="사용자에게 보여줄 첫 메시지"
                  value={formData.welcome_message}
                  onChange={(e) => setFormData({ ...formData, welcome_message: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>추천 질문</Label>
                <div className="flex gap-2">
                  <Input
                    placeholder="추천 질문 추가"
                    value={newQuestion}
                    onChange={(e) => setNewQuestion(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleAddQuestion()}
                  />
                  <Button variant="outline" onClick={handleAddQuestion}>
                    추가
                  </Button>
                </div>
                {formData.suggested_questions.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {formData.suggested_questions.map((q) => (
                      <Badge
                        key={q}
                        variant="secondary"
                        className="cursor-pointer"
                        onClick={() => handleRemoveQuestion(q)}
                      >
                        {q} ×
                      </Badge>
                    ))}
                  </div>
                )}
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
                      <Badge
                        key={tag}
                        variant="secondary"
                        className="cursor-pointer"
                        onClick={() => handleRemoveTag(tag)}
                      >
                        {tag} ×
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* LLM Settings Tab */}
        <TabsContent value="llm" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                LLM 설정
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>LLM Provider</Label>
                  <Select
                    value={formData.llm_provider}
                    onValueChange={(v) => setFormData({ ...formData, llm_provider: v })}
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
                    value={formData.llm_model}
                    onChange={(e) => setFormData({ ...formData, llm_model: e.target.value })}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>시스템 프롬프트</Label>
                <Textarea
                  value={formData.system_prompt}
                  onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                  rows={4}
                  placeholder="AI의 역할과 행동 방식을 정의하세요"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Temperature: {formData.temperature}</Label>
                  <Slider
                    value={[formData.temperature]}
                    onValueChange={([v]) => setFormData({ ...formData, temperature: v })}
                    min={0}
                    max={2}
                    step={0.1}
                  />
                  <p className="text-xs text-muted-foreground">
                    낮을수록 일관된 응답, 높을수록 창의적인 응답
                  </p>
                </div>
                <div className="space-y-2">
                  <Label>Max Tokens</Label>
                  <Input
                    type="number"
                    value={formData.max_tokens}
                    onChange={(e) => setFormData({ ...formData, max_tokens: parseInt(e.target.value) })}
                  />
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>스트리밍 응답</Label>
                  <p className="text-xs text-muted-foreground">실시간으로 응답을 표시합니다</p>
                </div>
                <Switch
                  checked={formData.streaming}
                  onCheckedChange={(v) => setFormData({ ...formData, streaming: v })}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                메모리 설정
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>메모리 유형</Label>
                  <Select
                    value={formData.memory_type}
                    onValueChange={(v) => setFormData({ ...formData, memory_type: v as any })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="buffer">버퍼 (최근 N개 메시지)</SelectItem>
                      <SelectItem value="summary">요약 (대화 요약)</SelectItem>
                      <SelectItem value="vector">벡터 (의미 기반 검색)</SelectItem>
                      <SelectItem value="hybrid">하이브리드</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>최대 메시지 수</Label>
                  <Input
                    type="number"
                    value={formData.memory_max_messages}
                    onChange={(e) =>
                      setFormData({ ...formData, memory_max_messages: parseInt(e.target.value) })
                    }
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* RAG Settings Tab */}
        <TabsContent value="rag" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Database className="h-5 w-5" />
                    RAG 설정
                  </CardTitle>
                  <CardDescription>지식베이스를 연동하여 문서 기반 응답을 제공합니다</CardDescription>
                </div>
                <Switch
                  checked={formData.rag_enabled}
                  onCheckedChange={(v) => setFormData({ ...formData, rag_enabled: v })}
                />
              </div>
            </CardHeader>
            {formData.rag_enabled && (
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>지식베이스 선택</Label>
                  <Select
                    value={formData.rag_knowledgebase_ids[0] || ''}
                    onValueChange={(v) =>
                      setFormData({ ...formData, rag_knowledgebase_ids: v ? [v] : [] })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="지식베이스 선택..." />
                    </SelectTrigger>
                    <SelectContent>
                      {(knowledgebases || []).map((kb: any) => (
                        <SelectItem key={kb.id} value={kb.id}>
                          {kb.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>검색 전략</Label>
                    <Select
                      value={formData.rag_retrieval_strategy}
                      onValueChange={(v) =>
                        setFormData({ ...formData, rag_retrieval_strategy: v as any })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="similarity">유사도 검색</SelectItem>
                        <SelectItem value="mmr">MMR (다양성 고려)</SelectItem>
                        <SelectItem value="hybrid">하이브리드 (벡터 + 키워드)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Top K</Label>
                    <Input
                      type="number"
                      value={formData.rag_top_k}
                      onChange={(e) =>
                        setFormData({ ...formData, rag_top_k: parseInt(e.target.value) })
                      }
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>점수 임계값: {formData.rag_score_threshold}</Label>
                    <Slider
                      value={[formData.rag_score_threshold]}
                      onValueChange={([v]) => setFormData({ ...formData, rag_score_threshold: v })}
                      min={0}
                      max={1}
                      step={0.05}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>리랭킹</Label>
                      <p className="text-xs text-muted-foreground">검색 결과 재정렬</p>
                    </div>
                    <Switch
                      checked={formData.rag_reranking_enabled}
                      onCheckedChange={(v) =>
                        setFormData({ ...formData, rag_reranking_enabled: v })
                      }
                    />
                  </div>
                </div>
              </CardContent>
            )}
          </Card>
        </TabsContent>

        {/* Tools Tab */}
        <TabsContent value="tools" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wrench className="h-5 w-5" />
                도구 설정
              </CardTitle>
              <CardDescription>챗봇이 사용할 수 있는 도구를 선택하세요</CardDescription>
            </CardHeader>
            <CardContent>
              {(tools || []).length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Wrench className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>사용 가능한 도구가 없습니다</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-4">
                  {(tools || []).map((tool: any) => {
                    const isSelected = formData.tool_ids.includes(tool.id);
                    return (
                      <Card
                        key={tool.id}
                        className={`cursor-pointer transition-all ${
                          isSelected ? 'border-2 border-blue-500 bg-blue-50 dark:bg-blue-950' : ''
                        }`}
                        onClick={() => {
                          if (isSelected) {
                            setFormData({
                              ...formData,
                              tool_ids: formData.tool_ids.filter((id) => id !== tool.id),
                            });
                          } else {
                            setFormData({
                              ...formData,
                              tool_ids: [...formData.tool_ids, tool.id],
                            });
                          }
                        }}
                      >
                        <CardContent className="pt-4">
                          <div className="flex items-start gap-3">
                            <Wrench className="h-5 w-5 text-muted-foreground" />
                            <div>
                              <p className="font-medium">{tool.name}</p>
                              <p className="text-sm text-muted-foreground line-clamp-2">
                                {tool.description}
                              </p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
