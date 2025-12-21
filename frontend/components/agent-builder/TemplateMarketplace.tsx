'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Search, 
  Users, 
  MessageSquare, 
  Star,
  Download,
  Eye,
  Filter,
  Grid,
  List,
  Sparkles,
  Database,
  Wrench,
  Edit,
  Brain,
  Code,
  Globe,
  Zap
} from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface Template {
  id: string;
  name: string;
  description: string;
  longDescription: string;
  category: 'business' | 'development' | 'research' | 'support' | 'content';
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  type: 'agentflow' | 'chatflow';
  features: string[];
  tags: string[];
  icon: string;
  rating: number;
  downloads: number;
  author: string;
  preview?: string;
  orchestration?: string;
  agents?: number;
}

interface TemplateMarketplaceProps {
  type?: 'agentflow' | 'chatflow' | 'all';
  onSelectTemplate: (templateId: string) => void;
  onClose?: () => void;
}

const AGENTFLOW_TEMPLATES: Template[] = [
  {
    id: 'multi-agent-research',
    name: '리서치 에이전트 팀',
    description: '여러 에이전트가 협력하여 정보를 수집하고 분석합니다',
    longDescription: '웹 검색, 문서 분석, 데이터 수집을 담당하는 전문 에이전트들이 협력하여 종합적인 리서치를 수행합니다. 각 에이전트는 특정 영역에 특화되어 있으며, 계층적 구조로 작업을 조율합니다.',
    category: 'research',
    difficulty: 'intermediate',
    type: 'agentflow',
    features: ['웹 검색', '문서 분석', '데이터 수집', '보고서 생성'],
    tags: ['research', 'analysis', 'web-search', 'documents'],
    icon: '🔬',
    rating: 4.8,
    downloads: 1250,
    author: 'Research Team',
    orchestration: 'hierarchical',
    agents: 4
  },
  {
    id: 'customer-support-team',
    name: '고객 지원 팀',
    description: '분류, 응답, 에스컬레이션을 담당하는 에이전트 팀',
    longDescription: '고객 문의를 자동으로 분류하고, 적절한 응답을 생성하며, 필요시 인간 상담원에게 에스컬레이션하는 지능형 고객 지원 시스템입니다.',
    category: 'support',
    difficulty: 'beginner',
    type: 'agentflow',
    features: ['문의 분류', '자동 응답', '에스컬레이션', 'FAQ 검색'],
    tags: ['customer-service', 'support', 'automation', 'classification'],
    icon: '🎧',
    rating: 4.6,
    downloads: 2100,
    author: 'Support Team',
    orchestration: 'adaptive',
    agents: 3
  },
  {
    id: 'content-pipeline',
    name: '콘텐츠 생성 파이프라인',
    description: '기획, 작성, 검토, 발행을 순차적으로 처리',
    longDescription: '아이디어 기획부터 최종 발행까지 전체 콘텐츠 제작 과정을 자동화합니다. SEO 최적화, 품질 검토, 다국어 번역 등의 기능을 포함합니다.',
    category: 'content',
    difficulty: 'advanced',
    type: 'agentflow',
    features: ['콘텐츠 기획', 'SEO 최적화', '품질 검토', '자동 발행'],
    tags: ['content', 'seo', 'publishing', 'automation'],
    icon: '✍️',
    rating: 4.9,
    downloads: 890,
    author: 'Content Team',
    orchestration: 'sequential',
    agents: 4
  },
  {
    id: 'data-analysis-team',
    name: '데이터 분석 팀',
    description: '여러 데이터 소스를 병렬로 분석하고 결과를 통합',
    longDescription: '다양한 데이터 소스에서 정보를 수집하고, 병렬로 분석을 수행한 후 결과를 통합하여 인사이트를 도출합니다. 실시간 대시보드와 알림 기능을 제공합니다.',
    category: 'business',
    difficulty: 'advanced',
    type: 'agentflow',
    features: ['데이터 수집', '병렬 분석', '시각화', '알림'],
    tags: ['data', 'analytics', 'dashboard', 'insights'],
    icon: '📊',
    rating: 4.7,
    downloads: 1560,
    author: 'Analytics Team',
    orchestration: 'parallel',
    agents: 5
  }
];

const CHATFLOW_TEMPLATES: Template[] = [
  {
    id: 'rag-chatbot',
    name: 'RAG 챗봇',
    description: '문서 기반 질의응답 챗봇 (지식베이스 연동)',
    longDescription: '업로드된 문서들을 기반으로 정확한 답변을 제공하는 RAG(Retrieval-Augmented Generation) 챗봇입니다. 벡터 검색과 하이브리드 검색을 지원합니다.',
    category: 'business',
    difficulty: 'beginner',
    type: 'chatflow',
    features: ['RAG', 'Memory', '벡터 검색', '문서 업로드'],
    tags: ['rag', 'documents', 'qa', 'knowledge-base'],
    icon: '📚',
    rating: 4.9,
    downloads: 3200,
    author: 'AI Team'
  },
  {
    id: 'customer-support-bot',
    name: '고객 지원 챗봇',
    description: 'FAQ 및 티켓 생성 기능이 포함된 지원 봇',
    longDescription: '고객 문의에 대한 즉시 응답과 함께 복잡한 문제는 티켓으로 생성하여 담당자에게 전달하는 통합 고객 지원 솔루션입니다.',
    category: 'support',
    difficulty: 'intermediate',
    type: 'chatflow',
    features: ['Tools', 'Memory', 'FAQ 검색', '티켓 생성'],
    tags: ['support', 'faq', 'tickets', 'automation'],
    icon: '🎧',
    rating: 4.7,
    downloads: 2800,
    author: 'Support Team'
  },
  {
    id: 'code-assistant',
    name: '코드 어시스턴트',
    description: '코드 작성, 리뷰, 디버깅을 도와주는 AI',
    longDescription: '개발자를 위한 종합 코딩 어시스턴트로, 코드 생성, 리뷰, 디버깅, 문서화를 지원합니다. 다양한 프로그래밍 언어와 프레임워크를 지원합니다.',
    category: 'development',
    difficulty: 'intermediate',
    type: 'chatflow',
    features: ['Tools', 'Code', '코드 생성', '디버깅'],
    tags: ['coding', 'development', 'debugging', 'review'],
    icon: '💻',
    rating: 4.8,
    downloads: 1900,
    author: 'Dev Team'
  },
  {
    id: 'research-assistant',
    name: '리서치 어시스턴트',
    description: '웹 검색과 문서 분석을 통한 리서치 지원',
    longDescription: '학술 연구나 시장 조사를 위한 전문 어시스턴트로, 웹 검색, 논문 분석, 데이터 수집 등을 통해 종합적인 리서치를 지원합니다.',
    category: 'research',
    difficulty: 'advanced',
    type: 'chatflow',
    features: ['RAG', 'Web Search', '논문 분석', '데이터 수집'],
    tags: ['research', 'academic', 'web-search', 'analysis'],
    icon: '🔬',
    rating: 4.6,
    downloads: 1100,
    author: 'Research Team'
  }
];

const CATEGORIES = {
  all: { label: '전체', icon: Grid },
  business: { label: '비즈니스', icon: Zap },
  development: { label: '개발', icon: Code },
  research: { label: '리서치', icon: Search },
  support: { label: '고객지원', icon: MessageSquare },
  content: { label: '콘텐츠', icon: Edit }
};

const DIFFICULTIES = {
  all: '전체 난이도',
  beginner: '초급',
  intermediate: '중급',
  advanced: '고급'
};

export function TemplateMarketplace({ type = 'all', onSelectTemplate, onClose }: TemplateMarketplaceProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Combine templates based on type filter
  const allTemplates = type === 'all' 
    ? [...AGENTFLOW_TEMPLATES, ...CHATFLOW_TEMPLATES]
    : type === 'agentflow' 
    ? AGENTFLOW_TEMPLATES 
    : CHATFLOW_TEMPLATES;

  // Filter templates
  const filteredTemplates = allTemplates.filter(template => {
    const matchesSearch = !searchQuery || 
      template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesCategory = selectedCategory === 'all' || template.category === selectedCategory;
    const matchesDifficulty = selectedDifficulty === 'all' || template.difficulty === selectedDifficulty;
    
    return matchesSearch && matchesCategory && matchesDifficulty;
  });

  const getFeatureIcon = (feature: string) => {
    if (feature.includes('RAG')) return <Database className="h-3 w-3" />;
    if (feature.includes('Tools') || feature.includes('도구')) return <Wrench className="h-3 w-3" />;
    if (feature.includes('Memory') || feature.includes('메모리')) return <Brain className="h-3 w-3" />;
    if (feature.includes('Code') || feature.includes('코드')) return <Code className="h-3 w-3" />;
    if (feature.includes('Web') || feature.includes('웹')) return <Globe className="h-3 w-3" />;
    return <Sparkles className="h-3 w-3" />;
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'bg-green-100 text-green-800 border-green-200';
      case 'intermediate': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'advanced': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <Card className="w-full max-w-7xl mx-auto">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-purple-500" />
              템플릿 마켓플레이스
            </CardTitle>
            <CardDescription>
              검증된 템플릿으로 빠르게 시작하세요 ({filteredTemplates.length}개 템플릿)
            </CardDescription>
          </div>
          {onClose && (
            <Button variant="outline" onClick={onClose}>
              닫기
            </Button>
          )}
        </div>
      </CardHeader>
      
      <CardContent>
        {/* Search and Filters */}
        <div className="flex flex-col md:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="템플릿 이름, 설명, 태그로 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          
          <div className="flex gap-2">
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="w-[140px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">전체 카테고리</SelectItem>
                {Object.entries(CATEGORIES).slice(1).map(([key, { label }]) => (
                  <SelectItem key={key} value={key}>{label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Select value={selectedDifficulty} onValueChange={setSelectedDifficulty}>
              <SelectTrigger className="w-[120px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(DIFFICULTIES).map(([key, label]) => (
                  <SelectItem key={key} value={key}>{label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <div className="flex border rounded-lg p-1">
              <Button
                variant={viewMode === 'grid' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('grid')}
                className="h-8 w-8 p-0"
              >
                <Grid className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === 'list' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('list')}
                className="h-8 w-8 p-0"
              >
                <List className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Templates Grid/List */}
        {viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredTemplates.map((template) => (
              <Card 
                key={template.id}
                className="cursor-pointer hover:shadow-lg transition-all border-2 hover:border-purple-400 group"
                onClick={() => onSelectTemplate(template.id)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between mb-2">
                    <div className="text-3xl">{template.icon}</div>
                    <div className="flex items-center gap-1 text-sm text-muted-foreground">
                      <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                      {template.rating}
                    </div>
                  </div>
                  
                  <CardTitle className="text-base group-hover:text-purple-600 transition-colors">
                    {template.name}
                  </CardTitle>
                  <CardDescription className="text-sm line-clamp-2">
                    {template.description}
                  </CardDescription>
                </CardHeader>
                
                <CardContent className="pt-0">
                  <div className="space-y-3">
                    {/* Difficulty and Type */}
                    <div className="flex items-center gap-2">
                      <Badge className={getDifficultyColor(template.difficulty)}>
                        {DIFFICULTIES[template.difficulty as keyof typeof DIFFICULTIES]}
                      </Badge>
                      <Badge variant="outline">
                        {template.type === 'agentflow' ? (
                          <Users className="h-3 w-3 mr-1" />
                        ) : (
                          <MessageSquare className="h-3 w-3 mr-1" />
                        )}
                        {template.type === 'agentflow' ? 'Agentflow' : 'Chatflow'}
                      </Badge>
                    </div>
                    
                    {/* Features */}
                    <div className="flex flex-wrap gap-1">
                      {template.features.slice(0, 3).map((feature) => (
                        <Badge key={feature} variant="secondary" className="text-xs">
                          {getFeatureIcon(feature)}
                          <span className="ml-1">{feature}</span>
                        </Badge>
                      ))}
                      {template.features.length > 3 && (
                        <Badge variant="secondary" className="text-xs">
                          +{template.features.length - 3}
                        </Badge>
                      )}
                    </div>
                    
                    {/* Stats */}
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Download className="h-3 w-3" />
                        {template.downloads.toLocaleString()}
                      </div>
                      <div>{template.author}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {filteredTemplates.map((template) => (
              <Card 
                key={template.id}
                className="cursor-pointer hover:shadow-lg transition-all border-l-4 border-l-purple-400 group"
                onClick={() => onSelectTemplate(template.id)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center gap-4">
                    <div className="text-2xl">{template.icon}</div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold group-hover:text-purple-600 transition-colors">
                          {template.name}
                        </h3>
                        <Badge className={getDifficultyColor(template.difficulty)}>
                          {DIFFICULTIES[template.difficulty as keyof typeof DIFFICULTIES]}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground line-clamp-1">
                        {template.description}
                      </p>
                    </div>
                    
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                        {template.rating}
                      </div>
                      <div className="flex items-center gap-1">
                        <Download className="h-3 w-3" />
                        {template.downloads.toLocaleString()}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
        
        {filteredTemplates.length === 0 && (
          <div className="text-center py-12">
            <Search className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">검색 결과가 없습니다</h3>
            <p className="text-muted-foreground">
              다른 검색어나 필터를 시도해보세요
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}