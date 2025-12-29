'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Search,
  Filter,
  Star,
  Download,
  Upload,
  Users,
  TrendingUp,
  Clock,
  Eye,
  Heart,
  Share2,
  MoreVertical,
  Plus,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Crown,
  Award,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';

interface AgentTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  orchestration_type: string;
  agents: Array<{
    id: string;
    name: string;
    role: string;
    agent_id?: string;
  }>;
  tags: string[];
  is_public: boolean;
  is_featured: boolean;
  is_verified: boolean;
  created_by: {
    id: string;
    name: string;
    avatar?: string;
    is_premium?: boolean;
  };
  created_at: string;
  updated_at: string;
  usage_count: number;
  rating: number;
  rating_count: number;
  preview_image?: string;
  complexity_level: 'beginner' | 'intermediate' | 'advanced';
  estimated_execution_time: number;
  cost_estimate: number;
}

const TEMPLATE_CATEGORIES = [
  { value: 'all', label: '전체', icon: '🌟' },
  { value: 'customer_service', label: '고객 서비스', icon: '🎧' },
  { value: 'content_creation', label: '콘텐츠 제작', icon: '✍️' },
  { value: 'data_analysis', label: '데이터 분석', icon: '📊' },
  { value: 'automation', label: '자동화', icon: '🤖' },
  { value: 'research', label: '리서치', icon: '🔍' },
  { value: 'marketing', label: '마케팅', icon: '📢' },
  { value: 'development', label: '개발', icon: '💻' },
  { value: 'education', label: '교육', icon: '🎓' },
];

const COMPLEXITY_COLORS = {
  beginner: 'bg-green-100 text-green-800',
  intermediate: 'bg-yellow-100 text-yellow-800',
  advanced: 'bg-red-100 text-red-800',
};

const COMPLEXITY_LABELS = {
  beginner: '초급',
  intermediate: '중급',
  advanced: '고급',
};

interface TemplateMarketplaceProps {
  onTemplateSelect?: (template: AgentTemplate) => void;
  showCreateButton?: boolean;
}

export function TemplateMarketplace({
  onTemplateSelect,
  showCreateButton = true,
}: TemplateMarketplaceProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // State
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'popular' | 'recent' | 'rating'>('popular');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<AgentTemplate | null>(null);
  const [showTemplateDetails, setShowTemplateDetails] = useState(false);

  // Fetch templates
  const { data: templatesData, isLoading } = useQuery({
    queryKey: ['team-templates', selectedCategory, searchQuery, sortBy],
    queryFn: () => agentBuilderAPI.getTeamTemplates({
      category: selectedCategory === 'all' ? undefined : selectedCategory,
      search: searchQuery || undefined,
    }),
  });

  // Create template mutation
  const createTemplateMutation = useMutation({
    mutationFn: (data: Partial<AgentTemplate>) =>
      agentBuilderAPI.createTeamTemplate(data),
    onSuccess: () => {
      toast({
        title: '템플릿 생성 완료',
        description: '새로운 팀 템플릿이 마켓플레이스에 추가되었습니다.',
      });
      queryClient.invalidateQueries({ queryKey: ['team-templates'] });
      setShowCreateDialog(false);
    },
    onError: () => {
      toast({
        title: '템플릿 생성 실패',
        description: '템플릿 생성 중 오류가 발생했습니다.',
        variant: 'destructive',
      });
    },
  });

  // Use template mutation
  const useTemplateMutation = useMutation({
    mutationFn: async (template: AgentTemplate) => {
      // Create agentflow from template
      return agentBuilderAPI.createAgentflowWithAgents({
        name: `${template.name} (복사본)`,
        description: template.description,
        orchestration_type: template.orchestration_type,
        tags: [...template.tags, 'from_template'],
        agents_config: template.agents.map((agent, index) => ({
          agent_id: agent.agent_id || '',
          name: agent.name,
          role: agent.role,
          priority: index + 1,
          position_x: 100 + (index % 3) * 200,
          position_y: 100 + Math.floor(index / 3) * 150,
        })),
      });
    },
    onSuccess: (result) => {
      toast({
        title: '템플릿 적용 완료',
        description: '템플릿을 기반으로 새로운 워크플로우가 생성되었습니다.',
      });
      if (onTemplateSelect && selectedTemplate) {
        onTemplateSelect(selectedTemplate);
      }
    },
    onError: () => {
      toast({
        title: '템플릿 적용 실패',
        description: '템플릿 적용 중 오류가 발생했습니다.',
        variant: 'destructive',
      });
    },
  });

  // Filter and sort templates
  const filteredTemplates = React.useMemo(() => {
    if (!templatesData?.templates) return [];

    let filtered = templatesData.templates;

    // Apply sorting
    switch (sortBy) {
      case 'popular':
        filtered = filtered.sort((a, b) => b.usage_count - a.usage_count);
        break;
      case 'recent':
        filtered = filtered.sort((a, b) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        break;
      case 'rating':
        filtered = filtered.sort((a, b) => b.rating - a.rating);
        break;
    }

    return filtered;
  }, [templatesData?.templates, sortBy]);

  // Handle template selection
  const handleTemplateSelect = (template: AgentTemplate) => {
    setSelectedTemplate(template);
    setShowTemplateDetails(true);
  };

  // Handle template use
  const handleUseTemplate = (template: AgentTemplate) => {
    useTemplateMutation.mutate(template);
  };

  // Render template card
  const renderTemplateCard = (template: AgentTemplate) => (
    <Card
      key={template.id}
      className="cursor-pointer hover:shadow-lg transition-all duration-300 group relative overflow-hidden"
      onClick={() => handleTemplateSelect(template)}
    >
      {/* Featured/Verified badges */}
      <div className="absolute top-2 right-2 z-10 flex gap-1">
        {template.is_featured && (
          <Badge className="bg-gradient-to-r from-yellow-400 to-orange-500 text-white">
            <Crown className="w-3 h-3 mr-1" />
            추천
          </Badge>
        )}
        {template.is_verified && (
          <Badge className="bg-blue-500 text-white">
            <CheckCircle2 className="w-3 h-3 mr-1" />
            검증됨
          </Badge>
        )}
      </div>

      {/* Preview image or gradient */}
      <div className="h-32 bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 relative overflow-hidden">
        {template.preview_image ? (
          <img
            src={template.preview_image}
            alt={template.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-white text-4xl opacity-80">
              {TEMPLATE_CATEGORIES.find(c => c.value === template.category)?.icon || '🤖'}
            </div>
          </div>
        )}
        <div className="absolute inset-0 bg-black/20 group-hover:bg-black/10 transition-colors" />
      </div>

      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg line-clamp-1">{template.name}</CardTitle>
            <CardDescription className="line-clamp-2 mt-1">
              {template.description}
            </CardDescription>
          </div>
        </div>

        {/* Metadata */}
        <div className="flex items-center gap-2 mt-2">
          <Badge
            variant="secondary"
            className={COMPLEXITY_COLORS[template.complexity_level]}
          >
            {COMPLEXITY_LABELS[template.complexity_level]}
          </Badge>
          <Badge variant="outline" className="text-xs">
            {template.orchestration_type}
          </Badge>
          <Badge variant="outline" className="text-xs">
            {template.agents.length}개 에이전트
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        {/* Tags */}
        <div className="flex flex-wrap gap-1 mb-3">
          {template.tags.slice(0, 3).map((tag) => (
            <Badge key={tag} variant="outline" className="text-xs">
              {tag}
            </Badge>
          ))}
          {template.tags.length > 3 && (
            <Badge variant="outline" className="text-xs">
              +{template.tags.length - 3}
            </Badge>
          )}
        </div>

        {/* Stats */}
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1">
              <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
              <span>{template.rating.toFixed(1)}</span>
              <span className="text-xs">({template.rating_count})</span>
            </div>
            <div className="flex items-center gap-1">
              <Download className="w-4 h-4" />
              <span>{template.usage_count}</span>
            </div>
          </div>
          
          <div className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            <span>~{template.estimated_execution_time}s</span>
          </div>
        </div>

        {/* Creator */}
        <div className="flex items-center gap-2 mt-3 pt-3 border-t">
          <div className="w-6 h-6 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white text-xs font-medium">
            {template.created_by.name.charAt(0).toUpperCase()}
          </div>
          <span className="text-sm text-muted-foreground">
            {template.created_by.name}
          </span>
          {template.created_by.is_premium && (
            <Badge variant="outline" className="text-xs">
              <Sparkles className="w-3 h-3 mr-1" />
              Pro
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">템플릿 마켓플레이스</h2>
          <p className="text-muted-foreground">
            검증된 에이전트 팀 구성을 찾아보고 바로 사용해보세요
          </p>
        </div>
        {showCreateButton && (
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="w-4 h-4 mr-2" />
            템플릿 만들기
          </Button>
        )}
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
            <Input
              placeholder="템플릿 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        
        <Select value={sortBy} onValueChange={(value: any) => setSortBy(value)}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="popular">인기순</SelectItem>
            <SelectItem value="recent">최신순</SelectItem>
            <SelectItem value="rating">평점순</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Categories */}
      <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
        <TabsList className="grid w-full grid-cols-4 lg:grid-cols-9">
          {TEMPLATE_CATEGORIES.map((category) => (
            <TabsTrigger
              key={category.value}
              value={category.value}
              className="text-xs"
            >
              <span className="mr-1">{category.icon}</span>
              <span className="hidden sm:inline">{category.label}</span>
            </TabsTrigger>
          ))}
        </TabsList>

        {TEMPLATE_CATEGORIES.map((category) => (
          <TabsContent key={category.value} value={category.value} className="mt-6">
            {isLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {[...Array(6)].map((_, i) => (
                  <Card key={i} className="animate-pulse">
                    <div className="h-32 bg-gray-200" />
                    <CardHeader>
                      <div className="h-4 bg-gray-200 rounded w-3/4" />
                      <div className="h-3 bg-gray-200 rounded w-full mt-2" />
                    </CardHeader>
                    <CardContent>
                      <div className="h-3 bg-gray-200 rounded w-1/2" />
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredTemplates.map(renderTemplateCard)}
              </div>
            )}
          </TabsContent>
        ))}
      </Tabs>

      {/* Template Details Dialog */}
      <Dialog open={showTemplateDetails} onOpenChange={setShowTemplateDetails}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          {selectedTemplate && (
            <>
              <DialogHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <DialogTitle className="text-xl">{selectedTemplate.name}</DialogTitle>
                    <DialogDescription className="mt-2">
                      {selectedTemplate.description}
                    </DialogDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      onClick={() => handleUseTemplate(selectedTemplate)}
                      disabled={useTemplateMutation.isPending}
                    >
                      <Download className="w-4 h-4 mr-2" />
                      {useTemplateMutation.isPending ? '적용 중...' : '템플릿 사용'}
                    </Button>
                  </div>
                </div>
              </DialogHeader>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
                {/* Main Content */}
                <div className="lg:col-span-2 space-y-6">
                  {/* Agents */}
                  <div>
                    <h3 className="font-semibold mb-3">포함된 에이전트 ({selectedTemplate.agents.length}개)</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {selectedTemplate.agents.map((agent, index) => (
                        <Card key={agent.id} className="p-3">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                              <Users className="w-4 h-4 text-blue-600" />
                            </div>
                            <div>
                              <p className="font-medium text-sm">{agent.name}</p>
                              <p className="text-xs text-muted-foreground">{agent.role}</p>
                            </div>
                          </div>
                        </Card>
                      ))}
                    </div>
                  </div>

                  {/* Tags */}
                  <div>
                    <h3 className="font-semibold mb-3">태그</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedTemplate.tags.map((tag) => (
                        <Badge key={tag} variant="secondary">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Sidebar */}
                <div className="space-y-4">
                  {/* Stats */}
                  <Card className="p-4">
                    <h3 className="font-semibold mb-3">통계</h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">평점</span>
                        <div className="flex items-center gap-1">
                          <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                          <span className="text-sm font-medium">
                            {selectedTemplate.rating.toFixed(1)} ({selectedTemplate.rating_count})
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">사용 횟수</span>
                        <span className="text-sm font-medium">{selectedTemplate.usage_count}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">복잡도</span>
                        <Badge className={COMPLEXITY_COLORS[selectedTemplate.complexity_level]}>
                          {COMPLEXITY_LABELS[selectedTemplate.complexity_level]}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">예상 실행 시간</span>
                        <span className="text-sm font-medium">~{selectedTemplate.estimated_execution_time}초</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">예상 비용</span>
                        <span className="text-sm font-medium">${selectedTemplate.cost_estimate.toFixed(4)}</span>
                      </div>
                    </div>
                  </Card>

                  {/* Creator */}
                  <Card className="p-4">
                    <h3 className="font-semibold mb-3">제작자</h3>
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white font-medium">
                        {selectedTemplate.created_by.name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <p className="font-medium">{selectedTemplate.created_by.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(selectedTemplate.created_at).toLocaleDateString()}에 생성
                        </p>
                      </div>
                    </div>
                  </Card>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Create Template Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>새 템플릿 만들기</DialogTitle>
            <DialogDescription>
              다른 사용자들과 공유할 에이전트 팀 템플릿을 만드세요.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label>템플릿 이름</Label>
              <Input placeholder="예: 고객 서비스 자동화 팀" />
            </div>
            
            <div>
              <Label>설명</Label>
              <Textarea
                placeholder="이 템플릿의 용도와 특징을 설명하세요"
                rows={3}
              />
            </div>
            
            <div>
              <Label>카테고리</Label>
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="카테고리 선택" />
                </SelectTrigger>
                <SelectContent>
                  {TEMPLATE_CATEGORIES.slice(1).map((category) => (
                    <SelectItem key={category.value} value={category.value}>
                      {category.icon} {category.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex gap-2 pt-4">
              <Button variant="outline" onClick={() => setShowCreateDialog(false)} className="flex-1">
                취소
              </Button>
              <Button
                onClick={() => {
                  // Handle template creation
                  setShowCreateDialog(false);
                }}
                className="flex-1"
              >
                템플릿 만들기
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}