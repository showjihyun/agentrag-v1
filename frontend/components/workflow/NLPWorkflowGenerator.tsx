'use client';

import React, { useState, useCallback } from 'react';
import {
  Sparkles,
  Wand2,
  ArrowRight,
  Loader2,
  CheckCircle,
  AlertCircle,
  Lightbulb,
  Copy,
  Play,
  RefreshCw,
  Settings,
  Zap,
  Clock,
  BarChart3,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { cn } from '@/lib/utils';

interface GeneratedWorkflow {
  success: boolean;
  workflow_name: string;
  workflow_description: string;
  graph_definition: {
    nodes: any[];
    edges: any[];
  };
  explanation: string;
  confidence: number;
  suggestions: string[];
  complexity: string;
  estimated_execution_time: string;
  error?: string;
}

interface NLPWorkflowGeneratorProps {
  onGenerate?: (workflow: GeneratedWorkflow) => void;
  onApply?: (graphDefinition: any, name: string) => void;
}

const EXAMPLE_PROMPTS = [
  {
    text: "매일 아침 9시에 HTTP API로 뉴스를 가져와서 OpenAI로 요약한 후 Slack으로 보내줘",
    category: "자동화",
    complexity: "moderate",
  },
  {
    text: "웹훅으로 데이터를 받으면 조건에 따라 분기해서 Gmail로 알림을 보내거나 PostgreSQL에 저장해",
    category: "데이터 처리",
    complexity: "complex",
  },
  {
    text: "사용자 질문을 받아서 벡터 검색으로 관련 문서를 찾고 OpenAI로 답변을 생성해",
    category: "RAG",
    complexity: "moderate",
  },
  {
    text: "수동으로 시작해서 HTTP 요청으로 데이터를 가져온 후 Python 코드로 처리해",
    category: "데이터 변환",
    complexity: "simple",
  },
  {
    text: "스케줄로 매시간 실행해서 여러 API를 병렬로 호출하고 결과를 병합한 후 AI로 분석해",
    category: "분석",
    complexity: "complex",
  },
];

const COMPLEXITY_COLORS = {
  simple: "bg-green-100 text-green-700",
  moderate: "bg-yellow-100 text-yellow-700",
  complex: "bg-red-100 text-red-700",
};

const COMPLEXITY_LABELS = {
  simple: "간단",
  moderate: "보통",
  complex: "복잡",
};

export const NLPWorkflowGenerator: React.FC<NLPWorkflowGeneratorProps> = ({
  onGenerate,
  onApply,
}) => {
  const [prompt, setPrompt] = useState('');
  const [workflowName, setWorkflowName] = useState('');
  const [loading, setLoading] = useState(false);
  const [refining, setRefining] = useState(false);
  const [result, setResult] = useState<GeneratedWorkflow | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [useLLM, setUseLLM] = useState(true);
  const [refinementInput, setRefinementInput] = useState('');
  const [history, setHistory] = useState<GeneratedWorkflow[]>([]);
  const [activeTab, setActiveTab] = useState('generate');

  const handleGenerate = useCallback(async () => {
    if (!prompt.trim() || prompt.length < 10) {
      setError('최소 10자 이상의 설명을 입력해주세요');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('/api/agent-builder/workflow-nlp/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          description: prompt,
          language: 'ko',
          use_llm: useLLM,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || '워크플로우 생성에 실패했습니다');
      }

      const data = await response.json();
      console.log('AI workflow generated: ', data);
      setResult(data);
      setWorkflowName(data.workflow_name);
      
      // Add to history
      setHistory(prev => [data, ...prev.slice(0, 4)]);
      
      // 자동으로 결과 탭으로 전환
      setActiveTab('result');
      
      onGenerate?.(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '오류가 발생했습니다');
    } finally {
      setLoading(false);
    }
  }, [prompt, useLLM, onGenerate]);

  const handleRefine = useCallback(async () => {
    if (!result || !refinementInput.trim()) return;

    setRefining(true);
    setError(null);

    try {
      const response = await fetch('/api/agent-builder/workflow-nlp/refine', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          workflow: result.graph_definition,
          refinement: refinementInput,
          language: 'ko',
        }),
      });

      if (!response.ok) {
        throw new Error('워크플로우 수정에 실패했습니다');
      }

      const data = await response.json();
      setResult(data);
      setRefinementInput('');
      
      // Add to history
      setHistory(prev => [data, ...prev.slice(0, 4)]);
      
      onGenerate?.(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '오류가 발생했습니다');
    } finally {
      setRefining(false);
    }
  }, [result, refinementInput, onGenerate]);

  const handleApply = useCallback(() => {
    console.log('🎯 [NLPWorkflowGenerator] handleApply called');
    console.log('🎯 [NLPWorkflowGenerator] result:', result);
    console.log('🎯 [NLPWorkflowGenerator] graph_definition:', result?.graph_definition);
    
    if (result?.graph_definition) {
      console.log('🎯 [NLPWorkflowGenerator] Calling onApply with:', {
        nodes: result.graph_definition.nodes,
        edges: result.graph_definition.edges,
        workflowName: workflowName || result.workflow_name,
      });
      onApply?.(result.graph_definition, workflowName || result.workflow_name);
    } else {
      console.error('🎯 [NLPWorkflowGenerator] No graph_definition available');
    }
  }, [result, workflowName, onApply]);

  const handleExampleClick = (example: typeof EXAMPLE_PROMPTS[0]) => {
    setPrompt(example.text);
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const copyToClipboard = () => {
    if (result?.graph_definition) {
      navigator.clipboard.writeText(JSON.stringify(result.graph_definition, null, 2));
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500">
          <Sparkles className="h-6 w-6 text-white" />
        </div>
        <div>
          <h2 className="text-xl font-bold">AI 워크플로우 생성기</h2>
          <p className="text-sm text-muted-foreground">
            자연어로 설명하면 LLM이 워크플로우를 자동 생성합니다
          </p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="generate">생성</TabsTrigger>
          <TabsTrigger value="result" disabled={!result}>결과</TabsTrigger>
          <TabsTrigger value="history" disabled={history.length === 0}>
            히스토리 ({history.length})
          </TabsTrigger>
        </TabsList>

        {/* Generate Tab */}
        <TabsContent value="generate" className="space-y-4">
          <Card>
            <CardContent className="pt-6 space-y-4">
              <div className="space-y-2">
                <Label>워크플로우 설명</Label>
                <Textarea
                  placeholder="예: 매일 아침 뉴스를 검색해서 AI로 요약한 후 슬랙으로 보내줘"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  rows={4}
                  className="text-base resize-none"
                />
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>{prompt.length}자 / 최소 10자</span>
                  <div className="flex items-center gap-2">
                    <span>LLM 사용</span>
                    <Switch checked={useLLM} onCheckedChange={setUseLLM} />
                  </div>
                </div>
              </div>

              <Button
                onClick={handleGenerate}
                disabled={loading || prompt.length < 10}
                className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Wand2 className="h-4 w-4 mr-2" />
                )}
                {loading ? '생성 중...' : '워크플로우 생성'}
              </Button>
            </CardContent>
          </Card>

          {/* Example Prompts */}
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-muted-foreground">예시 프롬프트</h3>
            <div className="grid gap-2">
              {EXAMPLE_PROMPTS.map((example, index) => (
                <button
                  key={index}
                  onClick={() => handleExampleClick(example)}
                  className="p-3 text-left bg-muted/50 hover:bg-muted rounded-lg transition-colors"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="outline" className="text-xs">
                      {example.category}
                    </Badge>
                    <Badge className={cn("text-xs", COMPLEXITY_COLORS[example.complexity as keyof typeof COMPLEXITY_COLORS])}>
                      {COMPLEXITY_LABELS[example.complexity as keyof typeof COMPLEXITY_LABELS]}
                    </Badge>
                  </div>
                  <p className="text-sm">{example.text}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Error */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </TabsContent>

        {/* Result Tab */}
        <TabsContent value="result" className="space-y-4">
          {result && (
            <>
              <Card className="border border-purple-500/30 bg-gradient-to-br from-slate-900/50 to-purple-900/20">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1 flex-1">
                      <CardTitle className="flex items-center gap-2">
                        {result.success ? (
                          <div className="p-1 rounded-full bg-green-500/20">
                            <CheckCircle className="h-5 w-5 text-green-400" />
                          </div>
                        ) : (
                          <div className="p-1 rounded-full bg-red-500/20">
                            <AlertCircle className="h-5 w-5 text-red-400" />
                          </div>
                        )}
                        <Input
                          value={workflowName}
                          onChange={(e) => setWorkflowName(e.target.value)}
                          className="text-lg font-semibold border-none bg-transparent p-0 h-auto focus-visible:ring-0 text-slate-100"
                          placeholder="워크플로우 이름"
                        />
                      </CardTitle>
                      <p className="text-sm text-slate-400">{result.workflow_description}</p>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <Badge className={cn(
                        "text-xs border-0",
                        result.confidence >= 0.8 ? "bg-green-500/20 text-green-400" :
                        result.confidence >= 0.6 ? "bg-yellow-500/20 text-yellow-400" :
                        "bg-red-500/20 text-red-400"
                      )}>
                        신뢰도 {Math.round(result.confidence * 100)}%
                      </Badge>
                      <Badge className={cn(
                        "text-xs border-0",
                        result.complexity === 'simple' ? "bg-green-500/20 text-green-400" :
                        result.complexity === 'moderate' ? "bg-yellow-500/20 text-yellow-400" :
                        "bg-red-500/20 text-red-400"
                      )}>
                        {COMPLEXITY_LABELS[result.complexity as keyof typeof COMPLEXITY_LABELS]}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-3">
                    <div className="flex items-center gap-2 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                      <div className="p-1.5 rounded-md bg-blue-500/20">
                        <Zap className="h-4 w-4 text-blue-400" />
                      </div>
                      <div>
                        <div className="text-xs text-slate-500">노드</div>
                        <div className="font-semibold text-slate-200">{result.graph_definition.nodes.length}개</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                      <div className="p-1.5 rounded-md bg-green-500/20">
                        <ArrowRight className="h-4 w-4 text-green-400" />
                      </div>
                      <div>
                        <div className="text-xs text-slate-500">연결</div>
                        <div className="font-semibold text-slate-200">{result.graph_definition.edges.length}개</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 p-3 bg-orange-500/10 border border-orange-500/20 rounded-lg">
                      <div className="p-1.5 rounded-md bg-orange-500/20">
                        <Clock className="h-4 w-4 text-orange-400" />
                      </div>
                      <div>
                        <div className="text-xs text-slate-500">예상 시간</div>
                        <div className="font-semibold text-slate-200">{result.estimated_execution_time}</div>
                      </div>
                    </div>
                  </div>

                  {/* Explanation */}
                  {result.explanation && (
                    <div className="p-3 bg-slate-800/50 border border-slate-700/50 rounded-lg">
                      <p className="text-sm text-slate-300">{result.explanation}</p>
                    </div>
                  )}

                  {/* Generated Nodes */}
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium text-slate-300">생성된 노드</h4>
                    <div className="flex flex-wrap gap-2">
                      {result.graph_definition.nodes.map((node, index) => (
                        <div
                          key={node.id}
                          className="flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-800/80 border border-slate-700/50 rounded-lg text-sm"
                        >
                          <span className="text-purple-400 text-xs font-medium">{index + 1}.</span>
                          <span className="text-slate-200">{node.data?.label || node.type}</span>
                          <Badge className="text-xs ml-1 bg-purple-500/20 text-purple-300 border-0">{node.type}</Badge>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Suggestions */}
                  {result.suggestions.length > 0 && (
                    <div className="space-y-2 p-3 bg-yellow-500/5 border border-yellow-500/20 rounded-lg">
                      <h4 className="text-sm font-medium flex items-center gap-2 text-yellow-400">
                        <Lightbulb className="h-4 w-4" />
                        개선 제안
                      </h4>
                      <ul className="space-y-1">
                        {result.suggestions.map((suggestion, index) => (
                          <li key={index} className="text-sm text-slate-400 flex items-start gap-2">
                            <span className="text-yellow-500">•</span>
                            {suggestion}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Refinement */}
                  <div className="space-y-2 pt-3 border-t border-slate-700/50">
                    <h4 className="text-sm font-medium flex items-center gap-2 text-slate-300">
                      <Settings className="h-4 w-4 text-slate-400" />
                      워크플로우 수정
                    </h4>
                    <div className="flex gap-2">
                      <Input
                        placeholder="예: 에러 처리 추가해줘, 병렬 실행으로 변경해줘"
                        value={refinementInput}
                        onChange={(e) => setRefinementInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleRefine()}
                        className="bg-slate-800/50 border-slate-700/50 text-slate-200 placeholder:text-slate-500"
                      />
                      <Button
                        onClick={handleRefine}
                        disabled={refining || !refinementInput.trim()}
                        className="bg-slate-700 hover:bg-slate-600 text-slate-200 border-0"
                      >
                        {refining ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2 pt-3">
                    <Button 
                      onClick={handleApply} 
                      className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white border-0 shadow-lg shadow-purple-500/25"
                    >
                      <Play className="h-4 w-4 mr-2" />
                      에디터에 적용
                    </Button>
                    <Button 
                      onClick={copyToClipboard}
                      className="bg-slate-700 hover:bg-slate-600 text-slate-200 border-0"
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-4">
          {history.map((item, index) => (
            <Card key={index} className="cursor-pointer hover:border-purple-300" onClick={() => setResult(item)}>
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">{item.workflow_name}</h4>
                    <p className="text-sm text-muted-foreground truncate max-w-md">
                      {item.workflow_description}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={cn("text-xs", COMPLEXITY_COLORS[item.complexity as keyof typeof COMPLEXITY_COLORS])}>
                      {COMPLEXITY_LABELS[item.complexity as keyof typeof COMPLEXITY_LABELS]}
                    </Badge>
                    <Badge variant="outline">{item.graph_definition.nodes.length} 노드</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>

      {/* Tips */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-4">
          <h4 className="text-sm font-medium text-blue-700 mb-2">💡 더 좋은 결과를 위한 팁</h4>
          <ul className="text-sm text-blue-600 space-y-1">
            <li>• <strong>트리거</strong>를 명시하세요: "매일 9시에", "웹훅으로", "수동으로"</li>
            <li>• <strong>구체적인 서비스</strong>를 언급하세요: "슬랙", "이메일", "PostgreSQL"</li>
            <li>• <strong>조건</strong>이 있다면 설명하세요: "긴급한 경우", "에러가 발생하면"</li>
            <li>• <strong>데이터 흐름</strong>을 순서대로 설명하세요</li>
            <li>• 생성 후 <strong>수정 기능</strong>으로 세부 조정하세요</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
};

export default NLPWorkflowGenerator;
