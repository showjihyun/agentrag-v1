'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  MessageSquare,
  ArrowLeft,
  Save,
  Settings,
  Loader2,
  Plus,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Skeleton } from '@/components/ui/skeleton';
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

export default function EditChatflowPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const { toast } = useToast();

  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    llm_provider: 'ollama',
    llm_model: 'llama3.1',
    system_prompt: 'You are a helpful assistant.',
    temperature: 0.7,
    max_tokens: 2048,
    streaming: true,
    welcome_message: '안녕하세요! 무엇을 도와드릴까요?',
    suggested_questions: [] as string[],
    memory_type: 'buffer' as const,
    memory_max_messages: 20,
    rag_enabled: false,
    rag_knowledgebase_ids: [] as string[],
    rag_retrieval_strategy: 'hybrid' as const,
    rag_top_k: 5,
    rag_score_threshold: 0.7,
    rag_reranking_enabled: true,
    tool_ids: [] as string[],
    tags: [] as string[],
  });
  const [newTag, setNewTag] = useState('');
  const [newQuestion, setNewQuestion] = useState('');

  // Fetch existing flow data
  const { data: flowData, isLoading: flowLoading } = useQuery({
    queryKey: ['chatflow', params.id],
    queryFn: () => flowsAPI.getFlow(params.id),
  });

  const flow = flowData as any;

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

  // Load existing data
  useEffect(() => {
    if (flow) {
      setFormData({
        name: flow.name || '',
        description: flow.description || '',
        llm_provider: flow.chat_config?.llm_provider || 'ollama',
        llm_model: flow.chat_config?.llm_model || 'llama3.1',
        system_prompt: flow.chat_config?.system_prompt || 'You are a helpful assistant.',
        temperature: flow.chat_config?.temperature || 0.7,
        max_tokens: flow.chat_config?.max_tokens || 2048,
        streaming: flow.chat_config?.streaming !== false,
        welcome_message: flow.chat_config?.welcome_message || '안녕하세요! 무엇을 도와드릴까요?',
        suggested_questions: flow.chat_config?.suggested_questions || [],
        memory_type: flow.memory_config?.type || 'buffer',
        memory_max_messages: flow.memory_config?.max_messages || 20,
        rag_enabled: flow.rag_config?.enabled || false,
        rag_knowledgebase_ids: flow.rag_config?.knowledgebase_ids || [],
        rag_retrieval_strategy: flow.rag_config?.retrieval_strategy || 'hybrid',
        rag_top_k: flow.rag_config?.top_k || 5,
        rag_score_threshold: flow.rag_config?.score_threshold || 0.7,
        rag_reranking_enabled: flow.rag_config?.reranking_enabled !== false,
        tool_ids: flow.tools || [],
        tags: flow.tags || [],
      });
    }
  }, [flow]);

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
      await flowsAPI.updateFlow(params.id, {
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
      } as any);

      toast({
        title: '저장 완료',
        description: 'Chatflow가 업데이트되었습니다',
      });

      router.push(`/agent-builder/chatflows/${params.id}`);
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
            <p className="text-red-500">Chatflow를 불러오는데 실패했습니다</p>
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
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
                <MessageSquare className="h-7 w-7 text-blue-600 dark:text-blue-400" />
              </div>
              Chatflow 편집
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
            className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 shadow-lg hover:shadow-xl transition-all"
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

      <Tabs defaultValue="basic" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="basic">기본 정보</TabsTrigger>
          <TabsTrigger value="llm">LLM 설정</TabsTrigger>
          <TabsTrigger value="rag">RAG 설정</TabsTrigger>
          <TabsTrigger value="advanced">고급 설정</TabsTrigger>
        </TabsList>

        {/* Basic Info Tab */}
        <TabsContent value="basic" className="space-y-6">
          <Card className="border-2">
            <CardHeader className="border-b bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-950/20 dark:to-cyan-950/20">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
                  <Settings className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <CardTitle className="text-lg">기본 정보</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4 pt-6">
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
                  placeholder="이 Chatflow가 무엇을 하는지 설명하세요"
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
        </TabsContent>

        {/* LLM Settings Tab */}
        <TabsContent value="llm" className="space-y-6">
          <Card className="border-2">
            <CardHeader className="border-b bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-950/20 dark:to-cyan-950/20">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
                  <Settings className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <CardTitle className="text-lg">LLM 설정</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4 pt-6">
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
                      <SelectItem value="ollama">Ollama</SelectItem>
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
                />
              </div>
              <div className="space-y-2">
                <Label>Temperature: {formData.temperature}</Label>
                <Slider
                  value={[formData.temperature]}
                  onValueChange={([v]) => setFormData({ ...formData, temperature: v })}
                  min={0}
                  max={2}
                  step={0.1}
                />
              </div>
              <div className="space-y-2">
                <Label>Max Tokens</Label>
                <Input
                  type="number"
                  value={formData.max_tokens}
                  onChange={(e) => setFormData({ ...formData, max_tokens: parseInt(e.target.value) })}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* RAG Settings Tab */}
        <TabsContent value="rag" className="space-y-6">
          <Card className="border-2">
            <CardHeader className="border-b bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-950/20 dark:to-cyan-950/20">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
                    <Settings className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <CardTitle className="text-lg">RAG 설정</CardTitle>
                </div>
                <Switch
                  checked={formData.rag_enabled}
                  onCheckedChange={(v) => setFormData({ ...formData, rag_enabled: v })}
                />
              </div>
            </CardHeader>
            {formData.rag_enabled && (
              <CardContent className="space-y-4 pt-6">
                <div className="space-y-2">
                  <Label>검색 전략</Label>
                  <Select
                    value={formData.rag_retrieval_strategy}
                    onValueChange={(v) => setFormData({ ...formData, rag_retrieval_strategy: v as any })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="hybrid">Hybrid (Vector + BM25)</SelectItem>
                      <SelectItem value="vector">Vector Only</SelectItem>
                      <SelectItem value="bm25">BM25 Only</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Top K</Label>
                    <Input
                      type="number"
                      value={formData.rag_top_k}
                      onChange={(e) => setFormData({ ...formData, rag_top_k: parseInt(e.target.value) })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Score Threshold</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={formData.rag_score_threshold}
                      onChange={(e) => setFormData({ ...formData, rag_score_threshold: parseFloat(e.target.value) })}
                    />
                  </div>
                </div>
              </CardContent>
            )}
          </Card>
        </TabsContent>

        {/* Advanced Settings Tab */}
        <TabsContent value="advanced" className="space-y-6">
          <Card className="border-2">
            <CardHeader className="border-b bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-950/20 dark:to-cyan-950/20">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
                  <Settings className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <CardTitle className="text-lg">고급 설정</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4 pt-6">
              <div className="space-y-2">
                <Label>환영 메시지</Label>
                <Input
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
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                {formData.suggested_questions.length > 0 && (
                  <div className="space-y-2 mt-2">
                    {formData.suggested_questions.map((q, i) => (
                      <div key={i} className="flex items-center gap-2 p-2 border rounded">
                        <span className="flex-1 text-sm">{q}</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemoveQuestion(q)}
                        >
                          ×
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
