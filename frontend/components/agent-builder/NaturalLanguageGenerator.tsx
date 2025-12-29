'use client';

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { 
  Sparkles, 
  Wand2,
  Loader2, 
  CheckCircle, 
  AlertCircle,
  Lightbulb,
  Clock,
  Users,
  Zap,
  ArrowRight,
  Copy,
  Download,
  Eye,
  Settings,
  RefreshCw,
  BookOpen,
  Target,
  TrendingUp
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';

interface GeneratedWorkflow {
  success: boolean;
  workflow?: {
    id: string;
    name: string;
    description: string;
    nodes: any[];
    connections: any[];
    metadata: any;
  };
  analysis?: {
    complexity: string;
    estimated_execution_time: string;
    detected_nodes: string[];
  };
  generation_time_seconds: number;
  suggestions?: string[];
  error?: string;
}

interface NaturalLanguageGeneratorProps {
  onWorkflowGenerated?: (workflow: any) => void;
  onImportToCanvas?: (workflow: any) => void;
  className?: string;
}

export default function NaturalLanguageGenerator({
  onWorkflowGenerated,
  onImportToCanvas,
  className = ""
}: NaturalLanguageGeneratorProps) {
  const { toast } = useToast();
  
  // 상태 관리
  const [description, setDescription] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedWorkflow, setGeneratedWorkflow] = useState<GeneratedWorkflow | null>(null);
  const [activeTab, setActiveTab] = useState('generator');
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // 고급 설정
  const [language, setLanguage] = useState('ko');
  const [complexityPreference, setComplexityPreference] = useState('auto');
  
  // 예시 및 템플릿
  const [examples, setExamples] = useState<any[]>([]);
  const [templates, setTemplates] = useState<any>({});
  const [loadingExamples, setLoadingExamples] = useState(false);
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 예시 워크플로우 설명들
  const quickExamples = [
    {
      title: "고객 서비스 자동화",
      description: "고객 문의를 받아서 감정 분석하고 부정적이면 매니저에게 슬랙으로 알려줘",
      category: "고객 서비스",
      complexity: "simple",
      icon: "🎧"
    },
    {
      title: "일일 보고서 자동화", 
      description: "매일 오전 9시에 데이터베이스에서 신규 주문을 조회해서 요약 보고서를 만들어 이메일로 발송",
      category: "데이터 처리",
      complexity: "medium",
      icon: "📊"
    },
    {
      title: "콘텐츠 최적화",
      description: "블로그 포스트를 받아서 SEO 최적화 제안을 하고 소셜미디어용 요약본을 만들어줘",
      category: "콘텐츠 관리", 
      complexity: "medium",
      icon: "✍️"
    },
    {
      title: "회의 후속 조치",
      description: "회의록을 받아서 액션 아이템을 추출하고 담당자별로 슬랙 DM 발송",
      category: "업무 자동화",
      complexity: "simple", 
      icon: "📝"
    }
  ];

  // 컴포넌트 마운트 시 예시 로드
  useEffect(() => {
    loadExamples();
  }, []);

  // 예시 로드
  const loadExamples = useCallback(async () => {
    setLoadingExamples(true);
    try {
      const response = await fetch('/api/agent-builder/nl-generator/examples');
      if (response.ok) {
        const data = await response.json();
        setExamples(data.examples || []);
      }
    } catch (error) {
      console.error('Failed to load examples:', error);
    } finally {
      setLoadingExamples(false);
    }
  }, []);

  // 워크플로우 생성
  const handleGenerateWorkflow = useCallback(async () => {
    if (!description.trim()) {
      toast({
        title: '설명 필요',
        description: '워크플로우 설명을 입력해주세요.',
        variant: 'destructive'
      });
      return;
    }

    if (description.trim().length < 10) {
      toast({
        title: '설명이 너무 짧습니다',
        description: '최소 10자 이상의 구체적인 설명을 입력해주세요.',
        variant: 'destructive'
      });
      return;
    }

    setIsGenerating(true);
    setGeneratedWorkflow(null);

    try {
      const response = await fetch('/api/agent-builder/nl-generator/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          description: description.trim(),
          language,
          complexity_preference: complexityPreference,
          preferences: {
            include_error_handling: true,
            include_logging: true
          }
        })
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setGeneratedWorkflow(result);

      if (result.success) {
        toast({
          title: '워크플로우 생성 완료',
          description: `${result.generation_time_seconds.toFixed(1)}초 만에 생성되었습니다.`,
        });
        
        if (onWorkflowGenerated) {
          onWorkflowGenerated(result.workflow);
        }
      } else {
        toast({
          title: '생성 실패',
          description: result.error || '워크플로우 생성에 실패했습니다.',
          variant: 'destructive'
        });
      }
    } catch (error: any) {
      console.error('Generation error:', error);
      toast({
        title: '오류 발생',
        description: error.message || '워크플로우 생성 중 오류가 발생했습니다.',
        variant: 'destructive'
      });
    } finally {
      setIsGenerating(false);
    }
  }, [description, language, complexityPreference, toast, onWorkflowGenerated]);

  // 예시 적용
  const applyExample = useCallback((example: any) => {
    setDescription(example.description);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, []);

  // 캔버스로 가져오기
  const handleImportToCanvas = useCallback(() => {
    if (generatedWorkflow?.workflow && onImportToCanvas) {
      onImportToCanvas(generatedWorkflow.workflow);
      toast({
        title: '캔버스로 가져오기 완료',
        description: '생성된 워크플로우가 캔버스에 추가되었습니다.',
      });
    }
  }, [generatedWorkflow, onImportToCanvas, toast]);

  return (
    <div className={`space-y-6 ${className}`}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-500" />
            자연어 워크플로우 생성기
          </CardTitle>
          <CardDescription>
            자연어로 설명하면 AI가 자동으로 워크플로우를 생성해드립니다
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="generator">생성기</TabsTrigger>
              <TabsTrigger value="examples">예시</TabsTrigger>
              <TabsTrigger value="templates">템플릿</TabsTrigger>
            </TabsList>

            <TabsContent value="generator" className="space-y-4">
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    워크플로우 설명
                  </label>
                  <Textarea
                    ref={textareaRef}
                    placeholder="예: 고객 문의를 받아서 감정 분석하고 부정적이면 매니저에게 슬랙으로 알려줘"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="min-h-[100px] resize-none"
                    disabled={isGenerating}
                  />
                  <div className="flex justify-between items-center mt-1">
                    <span className="text-xs text-muted-foreground">
                      {description.length}/500자
                    </span>
                    <span className="text-xs text-muted-foreground">
                      구체적으로 설명할수록 더 정확한 워크플로우가 생성됩니다
                    </span>
                  </div>
                </div>

                <Collapsible open={showAdvanced} onOpenChange={setShowAdvanced}>
                  <CollapsibleTrigger asChild>
                    <Button variant="ghost" size="sm" className="w-full justify-between">
                      <span className="flex items-center gap-2">
                        <Settings className="h-4 w-4" />
                        고급 설정
                      </span>
                      <RefreshCw className={`h-4 w-4 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} />
                    </Button>
                  </CollapsibleTrigger>
                  <CollapsibleContent className="space-y-4 pt-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium mb-2 block">언어</label>
                        <Select value={language} onValueChange={setLanguage}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="ko">한국어</SelectItem>
                            <SelectItem value="en">English</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <label className="text-sm font-medium mb-2 block">복잡도</label>
                        <Select value={complexityPreference} onValueChange={setComplexityPreference}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="auto">자동</SelectItem>
                            <SelectItem value="simple">단순</SelectItem>
                            <SelectItem value="medium">보통</SelectItem>
                            <SelectItem value="complex">복잡</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </CollapsibleContent>
                </Collapsible>

                <Button
                  onClick={handleGenerateWorkflow}
                  disabled={isGenerating || !description.trim()}
                  className="w-full"
                  size="lg"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      워크플로우 생성 중...
                    </>
                  ) : (
                    <>
                      <Wand2 className="mr-2 h-4 w-4" />
                      워크플로우 생성
                    </>
                  )}
                </Button>
              </div>

              {/* 생성 결과 */}
              {generatedWorkflow && (
                <Card className="mt-6">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      {generatedWorkflow.success ? (
                        <CheckCircle className="h-5 w-5 text-green-500" />
                      ) : (
                        <AlertCircle className="h-5 w-5 text-red-500" />
                      )}
                      생성 결과
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {generatedWorkflow.success && generatedWorkflow.workflow ? (
                      <div className="space-y-4">
                        <div>
                          <h4 className="font-medium">{generatedWorkflow.workflow.name}</h4>
                          <p className="text-sm text-muted-foreground mt-1">
                            {generatedWorkflow.workflow.description}
                          </p>
                        </div>

                        {generatedWorkflow.analysis && (
                          <div className="grid grid-cols-3 gap-4 p-4 bg-muted rounded-lg">
                            <div className="text-center">
                              <div className="text-lg font-semibold">
                                {generatedWorkflow.analysis.complexity}
                              </div>
                              <div className="text-xs text-muted-foreground">복잡도</div>
                            </div>
                            <div className="text-center">
                              <div className="text-lg font-semibold">
                                {generatedWorkflow.workflow.nodes.length}
                              </div>
                              <div className="text-xs text-muted-foreground">노드 수</div>
                            </div>
                            <div className="text-center">
                              <div className="text-lg font-semibold">
                                {generatedWorkflow.generation_time_seconds.toFixed(1)}s
                              </div>
                              <div className="text-xs text-muted-foreground">생성 시간</div>
                            </div>
                          </div>
                        )}

                        <div className="flex gap-2">
                          <Button onClick={handleImportToCanvas} className="flex-1">
                            <ArrowRight className="mr-2 h-4 w-4" />
                            캔버스로 가져오기
                          </Button>
                          <Button variant="outline" size="icon">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="outline" size="icon">
                            <Copy className="h-4 w-4" />
                          </Button>
                          <Button variant="outline" size="icon">
                            <Download className="h-4 w-4" />
                          </Button>
                        </div>

                        {generatedWorkflow.suggestions && generatedWorkflow.suggestions.length > 0 && (
                          <div className="space-y-2">
                            <h5 className="text-sm font-medium flex items-center gap-2">
                              <Lightbulb className="h-4 w-4" />
                              개선 제안
                            </h5>
                            <ul className="space-y-1">
                              {generatedWorkflow.suggestions.map((suggestion, index) => (
                                <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                                  <span className="text-xs">•</span>
                                  {suggestion}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-center py-4">
                        <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
                        <p className="text-sm text-muted-foreground">
                          {generatedWorkflow.error || '워크플로우 생성에 실패했습니다.'}
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="examples" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {quickExamples.map((example, index) => (
                  <Card key={index} className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => applyExample(example)}>
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">{example.icon}</span>
                        <div className="flex-1">
                          <h4 className="font-medium">{example.title}</h4>
                          <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                            {example.description}
                          </p>
                          <div className="flex items-center gap-2 mt-2">
                            <Badge variant="secondary" className="text-xs">
                              {example.category}
                            </Badge>
                            <Badge variant={example.complexity === 'simple' ? 'default' : example.complexity === 'medium' ? 'secondary' : 'destructive'} className="text-xs">
                              {example.complexity}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="templates" className="space-y-4">
              <div className="text-center py-8">
                <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium">템플릿 준비 중</h3>
                <p className="text-muted-foreground">
                  다양한 업계별 워크플로우 템플릿을 준비하고 있습니다.
                </p>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}