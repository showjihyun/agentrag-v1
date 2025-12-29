'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import {
  Users,
  Plus,
  MoreVertical,
  Edit,
  Copy,
  Trash,
  Share,
  Star,
  StarOff,
  Download,
  Upload,
  Folder,
  Tag,
  TrendingUp,
} from 'lucide-react';

interface TeamTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  agents: Array<{
    id: string;
    name: string;
    role: string;
    agent_id?: string;
  }>;
  orchestration_type: string;
  tags: string[];
  is_public: boolean;
  is_favorite: boolean;
  created_by: {
    id: string;
    name: string;
    avatar?: string;
  };
  created_at: string;
  updated_at: string;
  usage_count: number;
  rating: number;
  team_id?: string;
}

interface TeamTemplateManagerProps {
  teamId?: string;
  onTemplateSelect?: (template: TeamTemplate) => void;
}

const TEMPLATE_CATEGORIES = [
  { value: 'customer_service', label: '고객 서비스', icon: '🎧' },
  { value: 'content_creation', label: '콘텐츠 제작', icon: '✍️' },
  { value: 'data_analysis', label: '데이터 분석', icon: '📊' },
  { value: 'research', label: '연구', icon: '🔬' },
  { value: 'marketing', label: '마케팅', icon: '📢' },
  { value: 'development', label: '개발', icon: '💻' },
  { value: 'operations', label: '운영', icon: '⚙️' },
  { value: 'general', label: '일반', icon: '🔧' },
];

export function TeamTemplateManager({ teamId, onTemplateSelect }: TeamTemplateManagerProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<TeamTemplate | null>(null);

  // Fetch team templates
  const { data: templatesData, isLoading } = useQuery({
    queryKey: ['team-templates', teamId, selectedCategory, searchQuery],
    queryFn: () => agentBuilderAPI.getTeamTemplates({
      team_id: teamId,
      category: selectedCategory !== 'all' ? selectedCategory : undefined,
      search: searchQuery || undefined,
    }),
  });

  // Create template mutation
  const createTemplateMutation = useMutation({
    mutationFn: (data: Partial<TeamTemplate>) =>
      agentBuilderAPI.createTeamTemplate(data),
    onSuccess: () => {
      toast({
        title: '템플릿 생성 완료',
        description: '팀 템플릿이 성공적으로 생성되었습니다',
      });
      queryClient.invalidateQueries({ queryKey: ['team-templates'] });
      setShowCreateDialog(false);
    },
  });

  // Update template mutation
  const updateTemplateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<TeamTemplate> }) =>
      agentBuilderAPI.updateTeamTemplate(id, data),
    onSuccess: () => {
      toast({
        title: '템플릿 업데이트',
        description: '팀 템플릿이 업데이트되었습니다',
      });
      queryClient.invalidateQueries({ queryKey: ['team-templates'] });
      setEditingTemplate(null);
    },
  });

  // Delete template mutation
  const deleteTemplateMutation = useMutation({
    mutationFn: (id: string) => agentBuilderAPI.deleteTeamTemplate(id),
    onSuccess: () => {
      toast({
        title: '템플릿 삭제',
        description: '팀 템플릿이 삭제되었습니다',
      });
      queryClient.invalidateQueries({ queryKey: ['team-templates'] });
    },
  });

  // Toggle favorite mutation
  const toggleFavoriteMutation = useMutation({
    mutationFn: ({ id, isFavorite }: { id: string; isFavorite: boolean }) =>
      agentBuilderAPI.toggleTeamTemplateFavorite(id, isFavorite),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['team-templates'] });
    },
  });

  const handleCreateTemplate = (templateData: Partial<TeamTemplate>) => {
    createTemplateMutation.mutate({
      ...templateData,
      team_id: teamId,
    });
  };

  const handleEditTemplate = (template: TeamTemplate) => {
    setEditingTemplate(template);
  };

  const handleDeleteTemplate = (id: string) => {
    if (confirm('이 템플릿을 삭제하시겠습니까?')) {
      deleteTemplateMutation.mutate(id);
    }
  };

  const handleToggleFavorite = (template: TeamTemplate) => {
    toggleFavoriteMutation.mutate({
      id: template.id,
      isFavorite: !template.is_favorite,
    });
  };

  const getCategoryIcon = (category: string) => {
    const cat = TEMPLATE_CATEGORIES.find(c => c.value === category);
    return cat?.icon || '🔧';
  };

  const getCategoryLabel = (category: string) => {
    const cat = TEMPLATE_CATEGORIES.find(c => c.value === category);
    return cat?.label || category;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">팀 템플릿</h2>
          <p className="text-muted-foreground">
            재사용 가능한 에이전트 팀 구성을 관리하세요
          </p>
        </div>
        <Button onClick={() => setShowCreateDialog(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          새 템플릿 생성
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <Input
            placeholder="템플릿 검색..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <Select value={selectedCategory} onValueChange={setSelectedCategory}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="카테고리 선택" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">모든 카테고리</SelectItem>
            {TEMPLATE_CATEGORIES.map((category) => (
              <SelectItem key={category.value} value={category.value}>
                <div className="flex items-center gap-2">
                  <span>{category.icon}</span>
                  {category.label}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Templates Grid */}
      <Tabs defaultValue="my-templates" className="space-y-4">
        <TabsList>
          <TabsTrigger value="my-templates">내 템플릿</TabsTrigger>
          <TabsTrigger value="team-templates">팀 템플릿</TabsTrigger>
          <TabsTrigger value="public-templates">공개 템플릿</TabsTrigger>
          <TabsTrigger value="favorites">즐겨찾기</TabsTrigger>
        </TabsList>

        <TabsContent value="my-templates" className="space-y-4">
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[...Array(6)].map((_, i) => (
                <Card key={i} className="animate-pulse">
                  <CardHeader>
                    <div className="h-4 bg-muted rounded w-3/4" />
                    <div className="h-3 bg-muted rounded w-1/2" />
                  </CardHeader>
                  <CardContent>
                    <div className="h-20 bg-muted rounded" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : templatesData?.templates && templatesData.templates.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {templatesData.templates.map((template: TeamTemplate) => (
                <Card
                  key={template.id}
                  className="hover:shadow-lg transition-all cursor-pointer group"
                  onClick={() => onTemplateSelect?.(template)}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{getCategoryIcon(template.category)}</span>
                        <div>
                          <CardTitle className="text-base">{template.name}</CardTitle>
                          <CardDescription className="text-sm">
                            {getCategoryLabel(template.category)}
                          </CardDescription>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleToggleFavorite(template);
                          }}
                          className="opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          {template.is_favorite ? (
                            <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                          ) : (
                            <StarOff className="h-4 w-4" />
                          )}
                        </Button>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => e.stopPropagation()}
                              className="opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleEditTemplate(template)}>
                              <Edit className="mr-2 h-4 w-4" />
                              편집
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Copy className="mr-2 h-4 w-4" />
                              복제
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Share className="mr-2 h-4 w-4" />
                              공유
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Download className="mr-2 h-4 w-4" />
                              내보내기
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => handleDeleteTemplate(template.id)}
                              className="text-destructive"
                            >
                              <Trash className="mr-2 h-4 w-4" />
                              삭제
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {template.description}
                    </p>

                    {/* Agents Preview */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Users className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">
                          {template.agents.length}개 에이전트
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {template.agents.slice(0, 3).map((agent, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {agent.role}
                          </Badge>
                        ))}
                        {template.agents.length > 3 && (
                          <Badge variant="outline" className="text-xs">
                            +{template.agents.length - 3}개 더
                          </Badge>
                        )}
                      </div>
                    </div>

                    {/* Tags */}
                    {template.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {template.tags.slice(0, 3).map((tag) => (
                          <Badge key={tag} variant="secondary" className="text-xs">
                            <Tag className="h-3 w-3 mr-1" />
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    )}

                    {/* Stats */}
                    <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t">
                      <div className="flex items-center gap-2">
                        <TrendingUp className="h-3 w-3" />
                        {template.usage_count}회 사용
                      </div>
                      <div className="flex items-center gap-1">
                        <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                        {template.rating.toFixed(1)}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Folder className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">템플릿이 없습니다</h3>
              <p className="text-muted-foreground mb-4">
                첫 번째 팀 템플릿을 생성해보세요
              </p>
              <Button onClick={() => setShowCreateDialog(true)}>
                <Plus className="h-4 w-4 mr-2" />
                템플릿 생성
              </Button>
            </div>
          )}
        </TabsContent>

        {/* Other tabs content would be similar */}
        <TabsContent value="team-templates">
          <div className="text-center py-12 text-muted-foreground">
            팀 템플릿 기능은 곧 제공될 예정입니다
          </div>
        </TabsContent>

        <TabsContent value="public-templates">
          <div className="text-center py-12 text-muted-foreground">
            공개 템플릿 기능은 곧 제공될 예정입니다
          </div>
        </TabsContent>

        <TabsContent value="favorites">
          <div className="text-center py-12 text-muted-foreground">
            즐겨찾기 템플릿이 없습니다
          </div>
        </TabsContent>
      </Tabs>

      {/* Create Template Dialog */}
      <CreateTemplateDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onSubmit={handleCreateTemplate}
      />

      {/* Edit Template Dialog */}
      {editingTemplate && (
        <EditTemplateDialog
          template={editingTemplate}
          onClose={() => setEditingTemplate(null)}
          onSubmit={(data) => updateTemplateMutation.mutate({ id: editingTemplate.id, data })}
        />
      )}
    </div>
  );
}

// Create Template Dialog Component
function CreateTemplateDialog({
  open,
  onOpenChange,
  onSubmit,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: Partial<TeamTemplate>) => void;
}) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: 'general',
    orchestration_type: 'sequential',
    agents: [] as Array<{ id: string; name: string; role: string; agent_id?: string }>,
    tags: [] as string[],
    is_public: false,
  });

  const handleSubmit = () => {
    if (!formData.name) return;
    onSubmit(formData);
    setFormData({
      name: '',
      description: '',
      category: 'general',
      orchestration_type: 'sequential',
      agents: [],
      tags: [],
      is_public: false,
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>새 팀 템플릿 생성</DialogTitle>
          <DialogDescription>
            재사용 가능한 에이전트 팀 구성을 만드세요
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label>템플릿 이름</Label>
            <Input
              placeholder="예: 고객 서비스 팀"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label>설명</Label>
            <Textarea
              placeholder="이 템플릿의 용도와 특징을 설명하세요"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <Label>카테고리</Label>
            <Select
              value={formData.category}
              onValueChange={(value) => setFormData({ ...formData, category: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TEMPLATE_CATEGORIES.map((category) => (
                  <SelectItem key={category.value} value={category.value}>
                    <div className="flex items-center gap-2">
                      <span>{category.icon}</span>
                      {category.label}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center justify-between">
            <Label>공개 템플릿</Label>
            <Switch
              checked={formData.is_public}
              onCheckedChange={(checked) => setFormData({ ...formData, is_public: checked })}
            />
          </div>

          <div className="flex gap-2 pt-4">
            <Button variant="outline" onClick={() => onOpenChange(false)} className="flex-1">
              취소
            </Button>
            <Button onClick={handleSubmit} disabled={!formData.name} className="flex-1">
              생성
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Edit Template Dialog Component (simplified)
function EditTemplateDialog({
  template,
  onClose,
  onSubmit,
}: {
  template: TeamTemplate;
  onClose: () => void;
  onSubmit: (data: Partial<TeamTemplate>) => void;
}) {
  const [formData, setFormData] = useState({
    name: template.name,
    description: template.description,
    category: template.category,
    is_public: template.is_public,
  });

  const handleSubmit = () => {
    onSubmit(formData);
  };

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>템플릿 편집</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label>템플릿 이름</Label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label>설명</Label>
            <Textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
            />
          </div>

          <div className="flex gap-2 pt-4">
            <Button variant="outline" onClick={onClose} className="flex-1">
              취소
            </Button>
            <Button onClick={handleSubmit} className="flex-1">
              저장
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}