"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { 
  Loader2, 
  Network, 
  Brain, 
  Zap, 
  AlertCircle, 
  CheckCircle2, 
  Info, 
  HelpCircle,
  Sparkles,
  Clock,
  TrendingUp,
  Users,
  Building,
  MapPin,
  Calendar
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface KnowledgeGraph {
  id: string;
  knowledgebase_id: string;
  name: string;
  description?: string;
  auto_extraction_enabled: boolean;
  entity_extraction_model: string;
  relation_extraction_model: string;
  entity_count: number;
  relationship_count: number;
  processing_status: string;
  processing_error?: string;
  last_processed_at?: string;
  created_at: string;
  updated_at: string;
}

interface KnowledgeGraphConfigProps {
  knowledgebaseId: string;
  knowledgeGraph?: KnowledgeGraph;
  onKnowledgeGraphCreated?: (kg: KnowledgeGraph) => void;
  onKnowledgeGraphUpdated?: (kg: KnowledgeGraph) => void;
}

const ENTITY_EXTRACTION_MODELS = [
  { 
    value: 'spacy_en_core_web_sm', 
    label: 'spaCy English (Small)', 
    description: '빠른 처리, 기본 정확도',
    performance: '⚡ 빠름',
    accuracy: '⭐⭐⭐'
  },
  { 
    value: 'spacy_en_core_web_md', 
    label: 'spaCy English (Medium)', 
    description: '균형잡힌 성능과 정확도',
    performance: '⚡⚡ 보통',
    accuracy: '⭐⭐⭐⭐'
  },
  { 
    value: 'spacy_en_core_web_lg', 
    label: 'spaCy English (Large)', 
    description: '높은 정확도, 느린 처리',
    performance: '⚡⚡⚡ 느림',
    accuracy: '⭐⭐⭐⭐⭐'
  },
  { 
    value: 'transformers_ner', 
    label: 'Transformers NER', 
    description: '최신 트랜스포머 기반 모델',
    performance: '⚡⚡ 보통',
    accuracy: '⭐⭐⭐⭐⭐'
  },
];

const RELATION_EXTRACTION_MODELS = [
  { 
    value: 'rebel_large', 
    label: 'REBEL Large', 
    description: '고성능 관계 추출 모델',
    performance: '⚡⚡⚡ 느림',
    accuracy: '⭐⭐⭐⭐⭐'
  },
  { 
    value: 'rebel_base', 
    label: 'REBEL Base', 
    description: '균형잡힌 성능',
    performance: '⚡⚡ 보통',
    accuracy: '⭐⭐⭐⭐'
  },
  { 
    value: 'openie', 
    label: 'OpenIE', 
    description: '빠른 오픈 정보 추출',
    performance: '⚡ 빠름',
    accuracy: '⭐⭐⭐'
  },
];

// 온보딩 단계 정의
const ONBOARDING_STEPS = [
  {
    title: "지식 그래프란?",
    description: "문서에서 엔티티(인물, 조직, 장소 등)와 관계를 자동으로 추출하여 구조화된 지식 네트워크를 만듭니다.",
    icon: Network,
    benefits: ["더 정확한 검색", "맥락적 이해", "관계 기반 추천"]
  },
  {
    title: "추출되는 정보",
    description: "AI가 자동으로 식별하고 연결하는 정보 유형들입니다.",
    icon: Brain,
    examples: [
      { icon: Users, label: "인물", example: "김철수, 이영희" },
      { icon: Building, label: "조직", example: "삼성전자, 서울대학교" },
      { icon: MapPin, label: "장소", example: "서울, 강남구" },
      { icon: Calendar, label: "이벤트", example: "회의, 프로젝트" }
    ]
  },
  {
    title: "설정 완료",
    description: "모든 설정이 완료되면 자동으로 지식 추출이 시작됩니다.",
    icon: Sparkles,
    features: ["실시간 모니터링", "진행률 추적", "결과 시각화"]
  }
];

export default function KnowledgeGraphConfig({
  knowledgebaseId,
  knowledgeGraph,
  onKnowledgeGraphCreated,
  onKnowledgeGraphUpdated,
}: KnowledgeGraphConfigProps) {
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(!knowledgeGraph);
  const [onboardingStep, setOnboardingStep] = useState(0);
  const [extractionProgress, setExtractionProgress] = useState(0);
  
  // Form state
  const [name, setName] = useState(knowledgeGraph?.name || '');
  const [description, setDescription] = useState(knowledgeGraph?.description || '');
  const [autoExtractionEnabled, setAutoExtractionEnabled] = useState(
    knowledgeGraph?.auto_extraction_enabled ?? true
  );
  const [entityExtractionModel, setEntityExtractionModel] = useState(
    knowledgeGraph?.entity_extraction_model || 'spacy_en_core_web_md'
  );
  const [relationExtractionModel, setRelationExtractionModel] = useState(
    knowledgeGraph?.relation_extraction_model || 'rebel_base'
  );

  // 추출 진행률 시뮬레이션 (실제로는 WebSocket이나 polling으로 구현)
  useEffect(() => {
    if (isExtracting) {
      const interval = setInterval(() => {
        setExtractionProgress(prev => {
          if (prev >= 100) {
            clearInterval(interval);
            setIsExtracting(false);
            return 100;
          }
          return prev + Math.random() * 10;
        });
      }, 500);
      return () => clearInterval(interval);
    }
  }, [isExtracting]);

  const handleCreateKnowledgeGraph = async () => {
    if (!name.trim()) {
      toast({
        title: "오류",
        description: "지식 그래프 이름을 입력해주세요.",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('/api/agent-builder/knowledge-graphs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          knowledgebase_id: knowledgebaseId,
          name: name.trim(),
          description: description.trim() || undefined,
          auto_extraction_enabled: autoExtractionEnabled,
          entity_extraction_model: entityExtractionModel,
          relation_extraction_model: relationExtractionModel,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '지식 그래프 생성에 실패했습니다.');
      }

      const newKg = await response.json();
      
      toast({
        title: "성공",
        description: "지식 그래프가 생성되었습니다.",
      });

      onKnowledgeGraphCreated?.(newKg);
    } catch (error) {
      console.error('Error creating knowledge graph:', error);
      toast({
        title: "오류",
        description: error instanceof Error ? error.message : "지식 그래프 생성에 실패했습니다.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleTriggerExtraction = async () => {
    if (!knowledgeGraph) return;

    setIsExtracting(true);
    setExtractionProgress(0);
    
    try {
      const response = await fetch(`/api/agent-builder/knowledge-graphs/${knowledgeGraph.id}/extract`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '지식 추출에 실패했습니다.');
      }

      const result = await response.json();
      
      toast({
        title: "🎉 지식 추출 완료!",
        description: `엔티티 ${result.stats.entities_extracted}개, 관계 ${result.stats.relationships_extracted}개가 새로 발견되었습니다.`,
      });

      // Refresh knowledge graph data
      onKnowledgeGraphUpdated?.(result.knowledge_graph);
    } catch (error) {
      console.error('Error triggering extraction:', error);
      toast({
        title: "오류",
        description: error instanceof Error ? error.message : "지식 추출에 실패했습니다.",
        variant: "destructive",
      });
      setIsExtracting(false);
      setExtractionProgress(0);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ready':
        return (
          <Badge variant="default" className="bg-green-100 text-green-800 border-green-200">
            <CheckCircle2 className="w-3 h-3 mr-1" />
            준비됨
          </Badge>
        );
      case 'processing':
        return (
          <Badge variant="default" className="bg-blue-100 text-blue-800 border-blue-200">
            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
            처리 중
          </Badge>
        );
      case 'error':
        return (
          <Badge variant="destructive">
            <AlertCircle className="w-3 h-3 mr-1" />
            오류
          </Badge>
        );
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const renderOnboarding = () => {
    const step = ONBOARDING_STEPS[onboardingStep];
    const IconComponent = step.icon;

    return (
      <Card className="border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <IconComponent className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <CardTitle className="text-xl">{step.title}</CardTitle>
                <CardDescription className="text-base">{step.description}</CardDescription>
              </div>
            </div>
            <Badge variant="outline" className="text-sm">
              {onboardingStep + 1} / {ONBOARDING_STEPS.length}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 단계별 컨텐츠 */}
          {onboardingStep === 0 && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {step.benefits?.map((benefit, index) => (
                  <div key={index} className="p-4 bg-white rounded-lg border border-blue-100">
                    <div className="flex items-center space-x-2">
                      <CheckCircle2 className="w-4 h-4 text-green-600" />
                      <span className="font-medium text-sm">{benefit}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {onboardingStep === 1 && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {step.examples?.map((example, index) => {
                  const ExampleIcon = example.icon;
                  return (
                    <div key={index} className="p-4 bg-white rounded-lg border border-blue-100 text-center">
                      <ExampleIcon className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                      <div className="font-medium text-sm mb-1">{example.label}</div>
                      <div className="text-xs text-gray-600">{example.example}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {onboardingStep === 2 && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {step.features?.map((feature, index) => (
                  <div key={index} className="p-4 bg-white rounded-lg border border-blue-100">
                    <div className="flex items-center space-x-2">
                      <Sparkles className="w-4 h-4 text-purple-600" />
                      <span className="font-medium text-sm">{feature}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 네비게이션 */}
          <div className="flex items-center justify-between pt-4 border-t border-blue-200">
            <Button
              variant="outline"
              onClick={() => setOnboardingStep(Math.max(0, onboardingStep - 1))}
              disabled={onboardingStep === 0}
            >
              이전
            </Button>
            
            <div className="flex space-x-1">
              {ONBOARDING_STEPS.map((_, index) => (
                <div
                  key={index}
                  className={`w-2 h-2 rounded-full ${
                    index === onboardingStep ? 'bg-blue-600' : 'bg-blue-200'
                  }`}
                />
              ))}
            </div>

            {onboardingStep < ONBOARDING_STEPS.length - 1 ? (
              <Button onClick={() => setOnboardingStep(onboardingStep + 1)}>
                다음
              </Button>
            ) : (
              <Button onClick={() => setShowOnboarding(false)} className="bg-blue-600 hover:bg-blue-700">
                시작하기
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    );
  };

  if (knowledgeGraph) {
    return (
      <div className="space-y-6">
        {/* 추출 진행률 표시 */}
        {isExtracting && (
          <Card className="border-blue-200 bg-blue-50">
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                    <span className="font-medium">지식 추출 진행 중...</span>
                  </div>
                  <span className="text-sm text-gray-600">{Math.round(extractionProgress)}%</span>
                </div>
                <Progress value={extractionProgress} className="h-2" />
                <div className="text-sm text-gray-600">
                  문서를 분석하여 엔티티와 관계를 추출하고 있습니다. 잠시만 기다려주세요.
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Network className="w-5 h-5 text-blue-600" />
                <CardTitle>지식 그래프</CardTitle>
              </div>
              {getStatusBadge(knowledgeGraph.processing_status)}
            </div>
            <CardDescription>
              구조화된 지식 표현을 통한 고급 검색 및 추론 기능
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Knowledge Graph Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label className="text-sm font-medium text-gray-700">이름</Label>
                <p className="text-sm text-gray-900 font-medium">{knowledgeGraph.name}</p>
              </div>
              <div>
                <Label className="text-sm font-medium text-gray-700">설명</Label>
                <p className="text-sm text-gray-900">{knowledgeGraph.description || '설명 없음'}</p>
              </div>
            </div>

            <Separator />

            {/* Enhanced Statistics */}
            <div className="space-y-4">
              <h4 className="font-medium flex items-center space-x-2">
                <TrendingUp className="w-4 h-4" />
                <span>추출 통계</span>
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded-lg border border-blue-100">
                  <div className="text-2xl font-bold text-blue-600">{knowledgeGraph.entity_count}</div>
                  <div className="text-sm text-blue-800">엔티티</div>
                  <div className="text-xs text-gray-600 mt-1">발견된 개체</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg border border-green-100">
                  <div className="text-2xl font-bold text-green-600">{knowledgeGraph.relationship_count}</div>
                  <div className="text-sm text-green-800">관계</div>
                  <div className="text-xs text-gray-600 mt-1">연결된 관계</div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg border border-purple-100">
                  <div className="text-2xl font-bold text-purple-600">
                    {knowledgeGraph.entity_count > 0 ? 
                      (knowledgeGraph.relationship_count / knowledgeGraph.entity_count).toFixed(1) : '0'
                    }
                  </div>
                  <div className="text-sm text-purple-800">평균 연결도</div>
                  <div className="text-xs text-gray-600 mt-1">엔티티당 관계</div>
                </div>
                <div className="text-center p-4 bg-orange-50 rounded-lg border border-orange-100">
                  <div className="text-2xl font-bold text-orange-600">
                    {knowledgeGraph.entity_count > 0 && knowledgeGraph.relationship_count > 0 ? '높음' : '낮음'}
                  </div>
                  <div className="text-sm text-orange-800">밀도</div>
                  <div className="text-xs text-gray-600 mt-1">네트워크 연결성</div>
                </div>
              </div>
            </div>

            {/* Configuration with tooltips */}
            <div className="space-y-4">
              <h4 className="font-medium flex items-center space-x-2">
                <Brain className="w-4 h-4" />
                <span>AI 모델 설정</span>
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-sm font-medium text-gray-700">엔티티 추출 모델</Label>
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger>
                          <HelpCircle className="w-4 h-4 text-gray-400" />
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>인물, 조직, 장소 등을 식별하는 AI 모델</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                  <p className="text-sm text-gray-900 font-mono bg-white px-2 py-1 rounded border">
                    {knowledgeGraph.entity_extraction_model}
                  </p>
                  <div className="text-xs text-gray-600 mt-1">
                    {ENTITY_EXTRACTION_MODELS.find(m => m.value === knowledgeGraph.entity_extraction_model)?.description}
                  </div>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-sm font-medium text-gray-700">관계 추출 모델</Label>
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger>
                          <HelpCircle className="w-4 h-4 text-gray-400" />
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>엔티티 간의 관계를 찾는 AI 모델</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                  <p className="text-sm text-gray-900 font-mono bg-white px-2 py-1 rounded border">
                    {knowledgeGraph.relation_extraction_model}
                  </p>
                  <div className="text-xs text-gray-600 mt-1">
                    {RELATION_EXTRACTION_MODELS.find(m => m.value === knowledgeGraph.relation_extraction_model)?.description}
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded-lg">
                <Switch 
                  checked={knowledgeGraph.auto_extraction_enabled} 
                  disabled 
                />
                <Label className="text-sm">자동 추출 활성화</Label>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger>
                      <Info className="w-4 h-4 text-gray-400" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>새 문서가 추가될 때 자동으로 지식을 추출합니다</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
            </div>

            {/* Error Display */}
            {knowledgeGraph.processing_error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  <div className="font-medium mb-1">처리 오류가 발생했습니다</div>
                  <div className="text-sm">{knowledgeGraph.processing_error}</div>
                </AlertDescription>
              </Alert>
            )}

            {/* Enhanced Actions */}
            <div className="flex flex-col sm:flex-row gap-3">
              <Button
                onClick={handleTriggerExtraction}
                disabled={isExtracting || knowledgeGraph.processing_status === 'processing'}
                className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700"
              >
                {isExtracting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Brain className="w-4 h-4" />
                )}
                <span>{isExtracting ? '추출 중...' : '지식 추출 실행'}</span>
              </Button>
              
              <Button
                variant="outline"
                onClick={() => {/* 네트워크 시각화로 이동 */}}
                className="flex items-center space-x-2"
              >
                <Network className="w-4 h-4" />
                <span>네트워크 보기</span>
              </Button>
            </div>

            {/* Last Processed with enhanced info */}
            {knowledgeGraph.last_processed_at && (
              <div className="flex items-center space-x-2 text-xs text-gray-500 bg-gray-50 p-3 rounded-lg">
                <Clock className="w-4 h-4" />
                <span>마지막 처리: {new Date(knowledgeGraph.last_processed_at).toLocaleString('ko-KR')}</span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  // 온보딩 표시
  if (showOnboarding) {
    return renderOnboarding();
  }

  return (
    <Card className="border-2 border-dashed border-gray-200 hover:border-blue-300 transition-colors">
      <CardHeader>
        <div className="flex items-center space-x-2">
          <Network className="w-5 h-5 text-blue-600" />
          <CardTitle>지식 그래프 생성</CardTitle>
        </div>
        <CardDescription>
          문서에서 엔티티와 관계를 자동으로 추출하여 구조화된 지식 그래프를 생성합니다.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <div>
            <Label htmlFor="kg-name" className="flex items-center space-x-2">
              <span>이름 *</span>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <HelpCircle className="w-4 h-4 text-gray-400" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>지식 그래프를 식별할 수 있는 이름을 입력하세요</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </Label>
            <Input
              id="kg-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="예: 회사 조직도, 프로젝트 관계도"
              className="mt-1"
            />
          </div>

          <div>
            <Label htmlFor="kg-description">설명</Label>
            <Textarea
              id="kg-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="이 지식 그래프의 목적과 포함될 내용을 설명해주세요"
              className="mt-1"
              rows={3}
            />
          </div>

          <div className="flex items-center space-x-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <Switch
              checked={autoExtractionEnabled}
              onCheckedChange={setAutoExtractionEnabled}
            />
            <Label className="text-sm">자동 추출 활성화</Label>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Info className="w-4 h-4 text-blue-600" />
                </TooltipTrigger>
                <TooltipContent>
                  <p>새 문서가 추가될 때마다 자동으로 지식을 추출합니다</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label className="flex items-center space-x-2">
                <span>엔티티 추출 모델</span>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger>
                      <HelpCircle className="w-4 h-4 text-gray-400" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>인물, 조직, 장소 등을 식별하는 AI 모델을 선택하세요</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </Label>
              <Select value={entityExtractionModel} onValueChange={setEntityExtractionModel}>
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ENTITY_EXTRACTION_MODELS.map((model) => (
                    <SelectItem key={model.value} value={model.value}>
                      <div className="space-y-1">
                        <div className="font-medium">{model.label}</div>
                        <div className="text-xs text-gray-600">{model.description}</div>
                        <div className="flex space-x-2 text-xs">
                          <span>{model.performance}</span>
                          <span>{model.accuracy}</span>
                        </div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="flex items-center space-x-2">
                <span>관계 추출 모델</span>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger>
                      <HelpCircle className="w-4 h-4 text-gray-400" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>엔티티 간의 관계를 찾는 AI 모델을 선택하세요</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </Label>
              <Select value={relationExtractionModel} onValueChange={setRelationExtractionModel}>
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {RELATION_EXTRACTION_MODELS.map((model) => (
                    <SelectItem key={model.value} value={model.value}>
                      <div className="space-y-1">
                        <div className="font-medium">{model.label}</div>
                        <div className="text-xs text-gray-600">{model.description}</div>
                        <div className="flex space-x-2 text-xs">
                          <span>{model.performance}</span>
                          <span>{model.accuracy}</span>
                        </div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        <Alert className="border-blue-200 bg-blue-50">
          <Zap className="h-4 w-4 text-blue-600" />
          <AlertDescription>
            <div className="space-y-2">
              <div className="font-medium text-blue-900">지식 그래프의 장점</div>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• 더 정확하고 맥락적인 검색 결과</li>
                <li>• 엔티티 간 관계를 통한 연관 정보 발견</li>
                <li>• 시각적 네트워크로 지식 구조 파악</li>
                <li>• AI 기반 자동 분석 및 인사이트 제공</li>
              </ul>
            </div>
          </AlertDescription>
        </Alert>

        <Button
          onClick={handleCreateKnowledgeGraph}
          disabled={isLoading || !name.trim()}
          className="w-full bg-blue-600 hover:bg-blue-700 h-12"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              생성 중...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4 mr-2" />
              지식 그래프 생성하기
            </>
          )}
        </Button>

        {/* 온보딩 다시 보기 */}
        <Button
          variant="ghost"
          onClick={() => setShowOnboarding(true)}
          className="w-full text-blue-600 hover:text-blue-700 hover:bg-blue-50"
        >
          <Info className="w-4 h-4 mr-2" />
          지식 그래프에 대해 더 알아보기
        </Button>
      </CardContent>
    </Card>
  );
}