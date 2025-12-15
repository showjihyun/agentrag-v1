'use client';

import { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  Plus,
  Check,
  Settings,
  ExternalLink,
  Database,
  Mail,
  MessageSquare,
  Globe,
  Code,
  FileText,
  Calendar,
  Users,
  Zap,
  Wrench,
  Star,
  Verified,
} from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
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
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';

interface Tool {
  id: string;
  name: string;
  description: string;
  category: string;
  provider: string;
  icon: string;
  isOfficial: boolean;
  isPopular: boolean;
  rating: number;
  usageCount: number;
  configuration: {
    required_fields: Array<{
      name: string;
      type: 'string' | 'number' | 'boolean' | 'select' | 'textarea';
      description: string;
      required: boolean;
      options?: string[];
      default?: any;
    }>;
    optional_fields?: Array<{
      name: string;
      type: 'string' | 'number' | 'boolean' | 'select' | 'textarea';
      description: string;
      default?: any;
      options?: string[];
    }>;
  };
  examples?: Array<{
    title: string;
    description: string;
    input: any;
    output: any;
  }>;
}

const MOCK_TOOLS: Tool[] = [
  {
    id: 'slack',
    name: 'Slack',
    description: 'Slack 채널에 메시지를 전송하고 사용자와 상호작용합니다',
    category: 'communication',
    provider: 'Slack Technologies',
    icon: '💬',
    isOfficial: true,
    isPopular: true,
    rating: 4.8,
    usageCount: 15420,
    configuration: {
      required_fields: [
        {
          name: 'bot_token',
          type: 'string',
          description: 'Slack Bot Token (xoxb-로 시작)',
          required: true,
        },
        {
          name: 'channel',
          type: 'string',
          description: '메시지를 보낼 채널 ID 또는 이름',
          required: true,
        },
      ],
      optional_fields: [
        {
          name: 'username',
          type: 'string',
          description: '봇 사용자명 (기본값: 워크플로우 이름)',
          default: 'Workflow Bot',
        },
      ],
    },
    examples: [
      {
        title: '간단한 메시지 전송',
        description: '채널에 텍스트 메시지를 전송합니다',
        input: { message: '안녕하세요! 작업이 완료되었습니다.' },
        output: { success: true, message_id: 'ts_1234567890' },
      },
    ],
  },
  {
    id: 'gmail',
    name: 'Gmail',
    description: 'Gmail을 통해 이메일을 전송하고 받은편지함을 관리합니다',
    category: 'communication',
    provider: 'Google',
    icon: '📧',
    isOfficial: true,
    isPopular: true,
    rating: 4.7,
    usageCount: 12350,
    configuration: {
      required_fields: [
        {
          name: 'credentials',
          type: 'textarea',
          description: 'Google OAuth2 인증 정보 (JSON 형식)',
          required: true,
        },
      ],
    },
  },
  {
    id: 'postgresql',
    name: 'PostgreSQL',
    description: 'PostgreSQL 데이터베이스에 쿼리를 실행하고 데이터를 관리합니다',
    category: 'database',
    provider: 'PostgreSQL Global Development Group',
    icon: '🐘',
    isOfficial: true,
    isPopular: true,
    rating: 4.9,
    usageCount: 8920,
    configuration: {
      required_fields: [
        {
          name: 'connection_string',
          type: 'string',
          description: 'PostgreSQL 연결 문자열',
          required: true,
        },
      ],
      optional_fields: [
        {
          name: 'timeout',
          type: 'number',
          description: '쿼리 타임아웃 (초)',
          default: 30,
        },
      ],
    },
  },
  {
    id: 'vector_search',
    name: 'Vector Search',
    description: 'Milvus를 사용한 벡터 유사도 검색',
    category: 'ai',
    provider: 'AgenticRAG',
    icon: '🔍',
    isOfficial: true,
    isPopular: true,
    rating: 4.8,
    usageCount: 7650,
    configuration: {
      required_fields: [
        {
          name: 'collection_name',
          type: 'string',
          description: '검색할 Milvus 컬렉션 이름',
          required: true,
        },
        {
          name: 'top_k',
          type: 'number',
          description: '반환할 결과 수',
          required: true,
          default: 5,
        },
      ],
    },
  },
  {
    id: 'web_search',
    name: 'Web Search',
    description: 'DuckDuckGo를 사용한 웹 검색',
    category: 'search',
    provider: 'AgenticRAG',
    icon: '🌐',
    isOfficial: true,
    isPopular: true,
    rating: 4.6,
    usageCount: 9840,
    configuration: {
      required_fields: [
        {
          name: 'query',
          type: 'string',
          description: '검색 쿼리',
          required: true,
        },
      ],
      optional_fields: [
        {
          name: 'max_results',
          type: 'number',
          description: '최대 결과 수',
          default: 10,
        },
      ],
    },
  },
  {
    id: 'github',
    name: 'GitHub',
    description: 'GitHub 리포지토리와 이슈를 관리합니다',
    category: 'development',
    provider: 'GitHub',
    icon: '🐙',
    isOfficial: true,
    isPopular: false,
    rating: 4.5,
    usageCount: 3420,
    configuration: {
      required_fields: [
        {
          name: 'access_token',
          type: 'string',
          description: 'GitHub Personal Access Token',
          required: true,
        },
      ],
    },
  },
];

const CATEGORIES = [
  { id: 'all', name: '전체', icon: Wrench },
  { id: 'communication', name: '커뮤니케이션', icon: MessageSquare },
  { id: 'database', name: '데이터베이스', icon: Database },
  { id: 'ai', name: 'AI/ML', icon: Zap },
  { id: 'search', name: '검색', icon: Globe },
  { id: 'development', name: '개발', icon: Code },
  { id: 'productivity', name: '생산성', icon: Calendar },
  { id: 'analytics', name: '분석', icon: FileText },
];

interface ToolSelectorProps {
  selectedTools: string[];
  onToolsChange: (tools: string[]) => void;
  maxTools?: number;
}

export function ToolSelector({ selectedTools, onToolsChange, maxTools }: ToolSelectorProps) {
  const { toast } = useToast();
  const [tools, setTools] = useState<Tool[]>(MOCK_TOOLS);
  const [filteredTools, setFilteredTools] = useState<Tool[]>(MOCK_TOOLS);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [sortBy, setSortBy] = useState<'name' | 'popularity' | 'rating'>('popularity');
  const [showOnlyOfficial, setShowOnlyOfficial] = useState(false);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null);
  const [toolConfigs, setToolConfigs] = useState<Record<string, any>>({});

  useEffect(() => {
    filterAndSortTools();
  }, [tools, searchQuery, selectedCategory, sortBy, showOnlyOfficial]);

  const filterAndSortTools = () => {
    let filtered = [...tools];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        tool =>
          tool.name.toLowerCase().includes(query) ||
          tool.description.toLowerCase().includes(query) ||
          tool.category.toLowerCase().includes(query)
      );
    }

    // Category filter
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(tool => tool.category === selectedCategory);
    }

    // Official filter
    if (showOnlyOfficial) {
      filtered = filtered.filter(tool => tool.isOfficial);
    }

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'popularity':
          return b.usageCount - a.usageCount;
        case 'rating':
          return b.rating - a.rating;
        default:
          return 0;
      }
    });

    setFilteredTools(filtered);
  };

  const handleToolToggle = (toolId: string) => {
    const isSelected = selectedTools.includes(toolId);
    
    if (isSelected) {
      onToolsChange(selectedTools.filter(id => id !== toolId));
    } else {
      if (maxTools && selectedTools.length >= maxTools) {
        toast({
          title: '제한 초과',
          description: `최대 ${maxTools}개의 도구만 선택할 수 있습니다`,
          variant: 'destructive',
        });
        return;
      }
      onToolsChange([...selectedTools, toolId]);
    }
  };

  const handleConfigureTool = (tool: Tool) => {
    setSelectedTool(tool);
    setConfigDialogOpen(true);
  };

  const handleSaveConfig = () => {
    if (!selectedTool) return;
    
    // Save configuration logic here
    setToolConfigs(prev => ({
      ...prev,
      [selectedTool.id]: { /* config data */ },
    }));
    
    setConfigDialogOpen(false);
    setSelectedTool(null);
    
    toast({
      title: '설정 저장됨',
      description: `${selectedTool.name} 도구 설정이 저장되었습니다`,
    });
  };

  const getToolIcon = (iconString: string) => {
    // For now, return the emoji. In a real app, you might map to actual icon components
    return <span className="text-2xl">{iconString}</span>;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">도구 선택</h3>
          <p className="text-sm text-muted-foreground">
            워크플로우에서 사용할 도구를 선택하세요 ({selectedTools.length}
            {maxTools && `/${maxTools}`} 선택됨)
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="도구 이름 또는 설명으로 검색..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        
        <Select value={selectedCategory} onValueChange={setSelectedCategory}>
          <SelectTrigger className="w-full md:w-[180px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {CATEGORIES.map((category) => {
              const Icon = category.icon;
              return (
                <SelectItem key={category.id} value={category.id}>
                  <div className="flex items-center gap-2">
                    <Icon className="h-4 w-4" />
                    {category.name}
                  </div>
                </SelectItem>
              );
            })}
          </SelectContent>
        </Select>

        <Select value={sortBy} onValueChange={(value: any) => setSortBy(value)}>
          <SelectTrigger className="w-full md:w-[140px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="popularity">인기순</SelectItem>
            <SelectItem value="rating">평점순</SelectItem>
            <SelectItem value="name">이름순</SelectItem>
          </SelectContent>
        </Select>

        <div className="flex items-center space-x-2">
          <Checkbox
            id="official-only"
            checked={showOnlyOfficial}
            onCheckedChange={setShowOnlyOfficial}
          />
          <Label htmlFor="official-only" className="text-sm">
            공식 도구만
          </Label>
        </div>
      </div>

      {/* Selected Tools */}
      {selectedTools.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">선택된 도구</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {selectedTools.map((toolId) => {
                const tool = tools.find(t => t.id === toolId);
                if (!tool) return null;
                
                return (
                  <Badge
                    key={toolId}
                    variant="secondary"
                    className="flex items-center gap-2 px-3 py-1"
                  >
                    {getToolIcon(tool.icon)}
                    {tool.name}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-4 w-4 p-0 hover:bg-destructive hover:text-destructive-foreground"
                      onClick={() => handleToolToggle(toolId)}
                    >
                      ×
                    </Button>
                  </Badge>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tools Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredTools.map((tool) => {
          const isSelected = selectedTools.includes(tool.id);
          
          return (
            <Card
              key={tool.id}
              className={`cursor-pointer transition-all border-2 ${
                isSelected 
                  ? 'border-primary shadow-lg' 
                  : 'border-border hover:border-primary/50'
              }`}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    {getToolIcon(tool.icon)}
                    <div>
                      <CardTitle className="text-base flex items-center gap-2">
                        {tool.name}
                        {tool.isOfficial && (
                          <Verified className="h-4 w-4 text-blue-500" />
                        )}
                        {tool.isPopular && (
                          <Star className="h-4 w-4 text-yellow-500 fill-current" />
                        )}
                      </CardTitle>
                      <CardDescription className="text-sm">
                        {tool.provider}
                      </CardDescription>
                    </div>
                  </div>
                  <Checkbox
                    checked={isSelected}
                    onCheckedChange={() => handleToolToggle(tool.id)}
                  />
                </div>
              </CardHeader>
              
              <CardContent className="space-y-3">
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {tool.description}
                </p>
                
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1">
                    <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                    <span>{tool.rating.toFixed(1)}</span>
                  </div>
                  <span className="text-muted-foreground">
                    {tool.usageCount.toLocaleString()} 사용
                  </span>
                </div>
                
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs">
                    {CATEGORIES.find(c => c.id === tool.category)?.name || tool.category}
                  </Badge>
                  {isSelected && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleConfigureTool(tool);
                      }}
                    >
                      <Settings className="h-3 w-3 mr-1" />
                      설정
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {filteredTools.length === 0 && (
        <Card className="p-12">
          <div className="text-center">
            <Wrench className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">도구를 찾을 수 없습니다</h3>
            <p className="text-muted-foreground">
              다른 검색어나 필터를 시도해보세요
            </p>
          </div>
        </Card>
      )}

      {/* Configuration Dialog */}
      <Dialog open={configDialogOpen} onOpenChange={setConfigDialogOpen}>
        <DialogContent className="max-w-2xl">
          {selectedTool && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  {getToolIcon(selectedTool.icon)}
                  {selectedTool.name} 설정
                </DialogTitle>
                <DialogDescription>
                  {selectedTool.description}
                </DialogDescription>
              </DialogHeader>

              <Tabs defaultValue="config" className="space-y-4">
                <TabsList>
                  <TabsTrigger value="config">설정</TabsTrigger>
                  <TabsTrigger value="examples">예제</TabsTrigger>
                </TabsList>

                <TabsContent value="config" className="space-y-4">
                  <ScrollArea className="max-h-96">
                    <div className="space-y-4 pr-4">
                      {/* Required Fields */}
                      <div>
                        <h4 className="font-medium mb-3">필수 설정</h4>
                        <div className="space-y-3">
                          {selectedTool.configuration.required_fields.map((field) => (
                            <div key={field.name} className="space-y-2">
                              <Label htmlFor={field.name}>
                                {field.name} *
                              </Label>
                              {field.type === 'textarea' ? (
                                <Textarea
                                  id={field.name}
                                  placeholder={field.description}
                                  rows={3}
                                />
                              ) : field.type === 'select' ? (
                                <Select>
                                  <SelectTrigger>
                                    <SelectValue placeholder={field.description} />
                                  </SelectTrigger>
                                  <SelectContent>
                                    {field.options?.map((option) => (
                                      <SelectItem key={option} value={option}>
                                        {option}
                                      </SelectItem>
                                    ))}
                                  </SelectContent>
                                </Select>
                              ) : (
                                <Input
                                  id={field.name}
                                  type={field.type === 'number' ? 'number' : 'text'}
                                  placeholder={field.description}
                                  defaultValue={field.default}
                                />
                              )}
                              <p className="text-xs text-muted-foreground">
                                {field.description}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Optional Fields */}
                      {selectedTool.configuration.optional_fields && (
                        <div>
                          <h4 className="font-medium mb-3">선택 설정</h4>
                          <div className="space-y-3">
                            {selectedTool.configuration.optional_fields.map((field) => (
                              <div key={field.name} className="space-y-2">
                                <Label htmlFor={field.name}>
                                  {field.name}
                                </Label>
                                {field.type === 'textarea' ? (
                                  <Textarea
                                    id={field.name}
                                    placeholder={field.description}
                                    defaultValue={field.default}
                                    rows={3}
                                  />
                                ) : field.type === 'select' ? (
                                  <Select defaultValue={field.default}>
                                    <SelectTrigger>
                                      <SelectValue placeholder={field.description} />
                                    </SelectTrigger>
                                    <SelectContent>
                                      {field.options?.map((option) => (
                                        <SelectItem key={option} value={option}>
                                          {option}
                                        </SelectItem>
                                      ))}
                                    </SelectContent>
                                  </Select>
                                ) : (
                                  <Input
                                    id={field.name}
                                    type={field.type === 'number' ? 'number' : 'text'}
                                    placeholder={field.description}
                                    defaultValue={field.default}
                                  />
                                )}
                                <p className="text-xs text-muted-foreground">
                                  {field.description}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                </TabsContent>

                <TabsContent value="examples">
                  <ScrollArea className="max-h-96">
                    <div className="space-y-4 pr-4">
                      {selectedTool.examples?.map((example, index) => (
                        <Card key={index}>
                          <CardHeader className="pb-3">
                            <CardTitle className="text-sm">{example.title}</CardTitle>
                            <CardDescription className="text-xs">
                              {example.description}
                            </CardDescription>
                          </CardHeader>
                          <CardContent className="space-y-3">
                            <div>
                              <Label className="text-xs">입력</Label>
                              <pre className="text-xs bg-muted p-2 rounded mt-1 overflow-x-auto">
                                {JSON.stringify(example.input, null, 2)}
                              </pre>
                            </div>
                            <div>
                              <Label className="text-xs">출력</Label>
                              <pre className="text-xs bg-muted p-2 rounded mt-1 overflow-x-auto">
                                {JSON.stringify(example.output, null, 2)}
                              </pre>
                            </div>
                          </CardContent>
                        </Card>
                      )) || (
                        <p className="text-sm text-muted-foreground text-center py-8">
                          사용 예제가 없습니다
                        </p>
                      )}
                    </div>
                  </ScrollArea>
                </TabsContent>
              </Tabs>

              <DialogFooter>
                <Button variant="outline" onClick={() => setConfigDialogOpen(false)}>
                  취소
                </Button>
                <Button onClick={handleSaveConfig}>
                  설정 저장
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}