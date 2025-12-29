'use client';

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Bot, 
  Zap, 
  Users, 
  Brain, 
  Search, 
  FileText, 
  MessageSquare, 
  BarChart3,
  Shield,
  Globe,
  Workflow,
  Sparkles
} from 'lucide-react';

interface AgentTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  orchestrationType: string[];
  icon: React.ComponentType<{ className?: string }>;
  capabilities: string[];
  tools: string[];
  configuration: {
    llm_provider: string;
    llm_model: string;
    system_prompt: string;
    temperature: number;
  };
  useCase: string;
  complexity: 'beginner' | 'intermediate' | 'advanced';
}

const AGENT_TEMPLATES: AgentTemplate[] = [
  // Sequential 최적화 템플릿
  {
    id: 'data-analyst',
    name: '데이터 분석가',
    description: '데이터를 수집하고 분석하여 인사이트를 제공하는 전문 에이전트',
    category: 'analysis',
    orchestrationType: ['sequential', 'pipeline'],
    icon: BarChart3,
    capabilities: ['데이터 분석', '통계 처리', '시각화', '보고서 생성'],
    tools: ['python_code', 'data_visualization', 'statistical_analysis'],
    configuration: {
      llm_provider: 'openai',
      llm_model: 'gpt-4',
      system_prompt: '당신은 데이터 분석 전문가입니다. 주어진 데이터를 체계적으로 분석하고 명확한 인사이트를 제공하세요.',
      temperature: 0.3
    },
    useCase: '순차적 데이터 처리 파이프라인에서 분석 단계를 담당',
    complexity: 'intermediate'
  },
  {
    id: 'content-writer',
    name: '콘텐츠 작성자',
    description: '다양한 형태의 콘텐츠를 생성하고 편집하는 창작 에이전트',
    category: 'content',
    orchestrationType: ['sequential', 'pipeline'],
    icon: FileText,
    capabilities: ['글쓰기', '편집', '번역', 'SEO 최적화'],
    tools: ['text_generation', 'grammar_check', 'seo_optimizer'],
    configuration: {
      llm_provider: 'openai',
      llm_model: 'gpt-4',
      system_prompt: '당신은 전문 콘텐츠 작성자입니다. 매력적이고 정확한 콘텐츠를 작성하세요.',
      temperature: 0.7
    },
    useCase: '콘텐츠 제작 워크플로우에서 작성 및 편집 담당',
    complexity: 'beginner'
  },

  // Parallel 최적화 템플릿
  {
    id: 'search-specialist',
    name: '검색 전문가',
    description: '다양한 소스에서 정보를 동시에 검색하고 수집하는 에이전트',
    category: 'search',
    orchestrationType: ['parallel', 'swarm'],
    icon: Search,
    capabilities: ['웹 검색', '문서 검색', '데이터베이스 쿼리', '정보 필터링'],
    tools: ['web_search', 'vector_search', 'database_query'],
    configuration: {
      llm_provider: 'openai',
      llm_model: 'gpt-3.5-turbo',
      system_prompt: '당신은 정보 검색 전문가입니다. 효율적으로 관련 정보를 찾아 정리하세요.',
      temperature: 0.2
    },
    useCase: '병렬 검색 작업에서 특정 도메인 담당',
    complexity: 'intermediate'
  },
  {
    id: 'translator',
    name: '번역 전문가',
    description: '다국어 번역과 현지화를 담당하는 언어 전문 에이전트',
    category: 'language',
    orchestrationType: ['parallel', 'map_reduce'],
    icon: Globe,
    capabilities: ['다국어 번역', '현지화', '문화적 적응', '언어 검증'],
    tools: ['translation_api', 'language_detection', 'cultural_adapter'],
    configuration: {
      llm_provider: 'openai',
      llm_model: 'gpt-4',
      system_prompt: '당신은 전문 번역가입니다. 정확하고 자연스러운 번역을 제공하세요.',
      temperature: 0.4
    },
    useCase: '다국어 콘텐츠 병렬 처리',
    complexity: 'intermediate'
  },

  // Hierarchical 최적화 템플릿
  {
    id: 'project-manager',
    name: '프로젝트 매니저',
    description: '팀을 조율하고 작업을 관리하는 리더십 에이전트',
    category: 'management',
    orchestrationType: ['hierarchical', 'adaptive'],
    icon: Users,
    capabilities: ['팀 관리', '작업 분배', '진행 모니터링', '의사결정'],
    tools: ['task_scheduler', 'progress_tracker', 'decision_maker'],
    configuration: {
      llm_provider: 'openai',
      llm_model: 'gpt-4',
      system_prompt: '당신은 프로젝트 매니저입니다. 팀을 효율적으로 조율하고 목표 달성을 이끄세요.',
      temperature: 0.5
    },
    useCase: '계층적 구조에서 상위 관리자 역할',
    complexity: 'advanced'
  },
  {
    id: 'specialist-researcher',
    name: '전문 연구원',
    description: '특정 분야의 깊이 있는 연구를 수행하는 전문가 에이전트',
    category: 'research',
    orchestrationType: ['hierarchical', 'consensus'],
    icon: Brain,
    capabilities: ['전문 연구', '문헌 조사', '가설 검증', '보고서 작성'],
    tools: ['academic_search', 'citation_manager', 'research_analyzer'],
    configuration: {
      llm_provider: 'openai',
      llm_model: 'gpt-4',
      system_prompt: '당신은 전문 연구원입니다. 체계적이고 깊이 있는 연구를 수행하세요.',
      temperature: 0.3
    },
    useCase: '계층적 연구 팀에서 전문 분야 담당',
    complexity: 'advanced'
  },

  // Consensus & Debate 최적화 템플릿
  {
    id: 'expert-advisor',
    name: '전문가 자문위원',
    description: '특정 관점에서 전문적 의견을 제시하는 자문 에이전트',
    category: 'advisory',
    orchestrationType: ['consensus', 'debate'],
    icon: Shield,
    capabilities: ['전문 자문', '의견 제시', '근거 분석', '리스크 평가'],
    tools: ['expert_knowledge', 'risk_analyzer', 'evidence_evaluator'],
    configuration: {
      llm_provider: 'openai',
      llm_model: 'gpt-4',
      system_prompt: '당신은 해당 분야의 전문가입니다. 근거 있는 의견과 조언을 제공하세요.',
      temperature: 0.4
    },
    useCase: '합의 도출이나 토론에서 전문가 의견 제공',
    complexity: 'advanced'
  },

  // Multi-modal & Advanced 템플릿
  {
    id: 'multimodal-analyst',
    name: '멀티모달 분석가',
    description: '텍스트, 이미지, 음성 등 다양한 형태의 데이터를 분석하는 에이전트',
    category: 'multimodal',
    orchestrationType: ['multi_modal', 'neural_swarm'],
    icon: Sparkles,
    capabilities: ['이미지 분석', '텍스트 분석', '음성 처리', '통합 분석'],
    tools: ['image_analyzer', 'text_processor', 'audio_processor', 'multimodal_fusion'],
    configuration: {
      llm_provider: 'openai',
      llm_model: 'gpt-4-vision',
      system_prompt: '당신은 멀티모달 분석 전문가입니다. 다양한 형태의 데이터를 종합적으로 분석하세요.',
      temperature: 0.3
    },
    useCase: '다양한 데이터 형태를 동시에 처리하는 고급 분석',
    complexity: 'advanced'
  },

  // Adaptive & Self-healing 템플릿
  {
    id: 'adaptive-optimizer',
    name: '적응형 최적화기',
    description: '상황에 따라 전략을 조정하고 최적화하는 지능형 에이전트',
    category: 'optimization',
    orchestrationType: ['adaptive', 'self_healing'],
    icon: Zap,
    capabilities: ['상황 분석', '전략 수정', '성능 최적화', '자동 복구'],
    tools: ['performance_monitor', 'strategy_optimizer', 'auto_healer'],
    configuration: {
      llm_provider: 'openai',
      llm_model: 'gpt-4',
      system_prompt: '당신은 적응형 최적화 전문가입니다. 상황을 분석하고 최적의 전략을 제시하세요.',
      temperature: 0.6
    },
    useCase: '동적 환경에서 자동 적응 및 최적화',
    complexity: 'advanced'
  }
];

interface AgentTemplateSelectorProps {
  onSelect: (template: AgentTemplate) => void;
  orchestrationType?: string;
  trigger?: React.ReactNode;
}

export function AgentTemplateSelector({ 
  onSelect, 
  orchestrationType,
  trigger 
}: AgentTemplateSelectorProps) {
  const [open, setOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');

  // 오케스트레이션 유형에 맞는 템플릿 필터링
  const filteredTemplates = React.useMemo(() => {
    let templates = AGENT_TEMPLATES;
    
    if (orchestrationType) {
      templates = templates.filter(template => 
        template.orchestrationType.includes(orchestrationType)
      );
    }
    
    if (selectedCategory !== 'all') {
      templates = templates.filter(template => 
        template.category === selectedCategory
      );
    }
    
    // 오케스트레이션 유형에 맞는 템플릿을 상단에 정렬
    if (orchestrationType) {
      templates.sort((a, b) => {
        const aMatch = a.orchestrationType.includes(orchestrationType);
        const bMatch = b.orchestrationType.includes(orchestrationType);
        if (aMatch && !bMatch) return -1;
        if (!aMatch && bMatch) return 1;
        return 0;
      });
    }
    
    return templates;
  }, [orchestrationType, selectedCategory]);

  // 카테고리 목록
  const categories = [
    { id: 'all', name: '전체', icon: Workflow },
    { id: 'analysis', name: '분석', icon: BarChart3 },
    { id: 'content', name: '콘텐츠', icon: FileText },
    { id: 'search', name: '검색', icon: Search },
    { id: 'language', name: '언어', icon: Globe },
    { id: 'management', name: '관리', icon: Users },
    { id: 'research', name: '연구', icon: Brain },
    { id: 'advisory', name: '자문', icon: Shield },
    { id: 'multimodal', name: '멀티모달', icon: Sparkles },
    { id: 'optimization', name: '최적화', icon: Zap }
  ];

  const handleSelectTemplate = (template: AgentTemplate) => {
    onSelect(template);
    setOpen(false);
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'beginner': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
      case 'intermediate': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300';
      case 'advanced': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300';
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline">
            <Bot className="h-4 w-4 mr-2" />
            템플릿에서 생성
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-6xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            Agent 템플릿 선택
            {orchestrationType && (
              <Badge variant="outline" className="ml-2">
                {orchestrationType} 최적화
              </Badge>
            )}
          </DialogTitle>
          <DialogDescription>
            {orchestrationType 
              ? `${orchestrationType} 오케스트레이션에 최적화된 Agent 템플릿을 선택하세요`
              : '사전 구성된 Agent 템플릿을 선택하여 빠르게 시작하세요'
            }
          </DialogDescription>
        </DialogHeader>

        <Tabs value={selectedCategory} onValueChange={setSelectedCategory} className="w-full">
          <TabsList className="grid w-full grid-cols-5 lg:grid-cols-10">
            {categories.map((category) => {
              const Icon = category.icon;
              return (
                <TabsTrigger 
                  key={category.id} 
                  value={category.id}
                  className="flex items-center gap-1 text-xs"
                >
                  <Icon className="h-3 w-3" />
                  <span className="hidden sm:inline">{category.name}</span>
                </TabsTrigger>
              );
            })}
          </TabsList>

          <TabsContent value={selectedCategory} className="mt-4">
            <ScrollArea className="h-[500px]">
              {filteredTemplates.length === 0 ? (
                <div className="text-center py-12">
                  <Bot className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">템플릿이 없습니다</h3>
                  <p className="text-muted-foreground">
                    선택한 조건에 맞는 템플릿이 없습니다. 다른 카테고리를 선택해보세요.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredTemplates.map((template) => {
                    const Icon = template.icon;
                    const isRecommended = orchestrationType && 
                      template.orchestrationType.includes(orchestrationType);
                    
                    return (
                      <Card
                        key={template.id}
                        className={`cursor-pointer transition-all duration-200 hover:shadow-lg hover:scale-[1.02] ${
                          isRecommended 
                            ? 'border-blue-400 bg-blue-50 dark:bg-blue-950/20' 
                            : 'hover:border-purple-300'
                        }`}
                        onClick={() => handleSelectTemplate(template)}
                      >
                        <CardHeader className="pb-3">
                          <div className="flex items-start justify-between">
                            <div className="flex items-center gap-3">
                              <div className={`p-2 rounded-lg ${
                                isRecommended 
                                  ? 'bg-blue-500 text-white' 
                                  : 'bg-purple-100 dark:bg-purple-900 text-purple-600 dark:text-purple-400'
                              }`}>
                                <Icon className="h-5 w-5" />
                              </div>
                              <div>
                                <CardTitle className="text-base">{template.name}</CardTitle>
                                <div className="flex gap-1 mt-1">
                                  <Badge className={getComplexityColor(template.complexity)}>
                                    {template.complexity}
                                  </Badge>
                                  {isRecommended && (
                                    <Badge className="bg-blue-500 hover:bg-blue-600 text-white">
                                      ⭐ 추천
                                    </Badge>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          <CardDescription className="text-sm">
                            {template.description}
                          </CardDescription>
                          
                          <div>
                            <p className="text-xs font-medium text-muted-foreground mb-2">
                              적합한 오케스트레이션:
                            </p>
                            <div className="flex flex-wrap gap-1">
                              {template.orchestrationType.map((type) => (
                                <Badge 
                                  key={type} 
                                  variant="outline" 
                                  className={`text-xs ${
                                    type === orchestrationType 
                                      ? 'border-blue-500 text-blue-700 dark:text-blue-300' 
                                      : ''
                                  }`}
                                >
                                  {type}
                                </Badge>
                              ))}
                            </div>
                          </div>

                          <div>
                            <p className="text-xs font-medium text-muted-foreground mb-2">
                              주요 기능:
                            </p>
                            <div className="flex flex-wrap gap-1">
                              {template.capabilities.slice(0, 3).map((capability) => (
                                <Badge key={capability} variant="secondary" className="text-xs">
                                  {capability}
                                </Badge>
                              ))}
                              {template.capabilities.length > 3 && (
                                <Badge variant="outline" className="text-xs">
                                  +{template.capabilities.length - 3}개 더
                                </Badge>
                              )}
                            </div>
                          </div>

                          <div className="pt-2 border-t">
                            <p className="text-xs text-muted-foreground">
                              <strong>사용 사례:</strong> {template.useCase}
                            </p>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              )}
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}