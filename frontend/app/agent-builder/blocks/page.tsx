'use client';

import { useState, useEffect } from 'react';
import { Plus, Search, Filter, MoreVertical, Edit, Play, Copy, Trash, Box, Zap, Code, Layers, ArrowDownToLine, ArrowUpFromLine, Bot, Brain, Settings2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI, Block, Agent } from '@/lib/api/agent-builder';
import { useRouter } from 'next/navigation';

// 통합된 Building Block 타입
interface BuildingBlock {
  id: string;
  name: string;
  description?: string;
  type: 'block' | 'agent';
  category: string; // block_type for blocks, agent_type for agents
  created_at: string;
  updated_at: string;
  version?: string;
  is_public?: boolean;
  // Block specific
  input_schema?: any;
  output_schema?: any;
  // Agent specific
  llm_provider?: string;
  llm_model?: string;
  tools?: any[];
  capabilities?: string[];
}

export default function BuildingBlocksPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('name');
  const [activeTab, setActiveTab] = useState('all');

  useEffect(() => {
    loadData();
  }, []);

  // Reload data when returning to this page
  useEffect(() => {
    const handleFocus = () => {
      loadData();
    };
    
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [blocksData, agentsData] = await Promise.all([
        agentBuilderAPI.getBlocks(),
        agentBuilderAPI.getAgents()
      ]);
      setBlocks(Array.isArray(blocksData) ? blocksData : []);
      setAgents(Array.isArray(agentsData?.agents) ? agentsData.agents : []);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load building blocks',
        variant: 'destructive',
      });
      setBlocks([]);
      setAgents([]);
    } finally {
      setLoading(false);
    }
  };

  // 통합된 Building Blocks 생성
  const buildingBlocks: BuildingBlock[] = [
    ...blocks.map(block => ({
      id: block.id,
      name: block.name,
      ...(block.description && { description: block.description }),
      type: 'block' as const,
      category: block.block_type,
      created_at: block.created_at,
      updated_at: block.updated_at,
      ...(block.version && { version: block.version }),
      ...(block.is_public !== undefined && { is_public: block.is_public }),
      ...(block.input_schema && { input_schema: block.input_schema }),
      ...(block.output_schema && { output_schema: block.output_schema }),
    })),
    ...agents.map(agent => ({
      id: agent.id,
      name: agent.name,
      ...(agent.description && { description: agent.description }),
      type: 'agent' as const,
      category: agent.agent_type,
      created_at: agent.created_at,
      updated_at: agent.updated_at,
      ...(agent.is_public !== undefined && { is_public: agent.is_public }),
      ...(agent.llm_provider && { llm_provider: agent.llm_provider }),
      ...(agent.llm_model && { llm_model: agent.llm_model }),
      ...(agent.tools && { tools: agent.tools }),
    }))
  ];

  const handleCreateBlock = () => {
    router.push('/agent-builder/blocks/new');
  };

  const handleCreateAgent = () => {
    router.push('/agent-builder/agents/new');
  };

  const handleEdit = (item: BuildingBlock) => {
    if (item.type === 'block') {
      router.push(`/agent-builder/blocks/${item.id}/edit`);
    } else {
      router.push(`/agent-builder/agents/${item.id}/edit`);
    }
  };

  const handleTest = (item: BuildingBlock) => {
    if (item.type === 'block') {
      router.push(`/agent-builder/blocks/${item.id}/test`);
    } else {
      router.push(`/agent-builder/agents/${item.id}/test`);
    }
  };

  const handleDuplicate = async (item: BuildingBlock) => {
    try {
      if (item.type === 'block') {
        await agentBuilderAPI.duplicateBlock(item.id);
      } else {
        await agentBuilderAPI.cloneAgent(item.id);
      }
      toast({
        title: 'Success',
        description: `${item.type === 'block' ? 'Block' : 'Agent'} duplicated successfully`,
      });
      loadData();
    } catch (error) {
      toast({
        title: 'Error',
        description: `Failed to duplicate ${item.type}`,
        variant: 'destructive',
      });
    }
  };

  const handleDelete = async (item: BuildingBlock) => {
    if (!confirm(`Are you sure you want to delete this ${item.type}?`)) return;

    try {
      if (item.type === 'block') {
        await agentBuilderAPI.deleteBlock(item.id);
      } else {
        await agentBuilderAPI.deleteAgent(item.id);
      }
      toast({
        title: 'Success',
        description: `${item.type === 'block' ? 'Block' : 'Agent'} deleted successfully`,
      });
      loadData();
    } catch (error) {
      toast({
        title: 'Error',
        description: `Failed to delete ${item.type}`,
        variant: 'destructive',
      });
    }
  };

  const getItemIcon = (item: BuildingBlock) => {
    if (item.type === 'agent') {
      return <Bot className="h-5 w-5 text-purple-500" />;
    }
    
    // Block icons
    switch (item.category) {
      case 'llm':
        return <Zap className="h-5 w-5 text-blue-500" />;
      case 'tool':
        return <Box className="h-5 w-5 text-green-500" />;
      case 'logic':
        return <Code className="h-5 w-5 text-purple-500" />;
      case 'composite':
        return <Layers className="h-5 w-5 text-orange-500" />;
      default:
        return <Box className="h-5 w-5 text-gray-500" />;
    }
  };

  const getProviderBadge = (provider: string) => {
    const colors = {
      ollama: 'bg-blue-100 text-blue-800',
      openai: 'bg-green-100 text-green-800',
      anthropic: 'bg-orange-100 text-orange-800',
      google: 'bg-red-100 text-red-800',
    };
    return colors[provider as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const filteredItems = buildingBlocks
    .filter((item) => {
      // Tab filtering
      if (activeTab === 'blocks' && item.type !== 'block') return false;
      if (activeTab === 'agents' && item.type !== 'agent') return false;
      if (activeTab !== 'all' && activeTab !== 'blocks' && activeTab !== 'agents' && item.category !== activeTab) return false;
      
      // Search filtering
      if (searchQuery && 
          !item.name.toLowerCase().includes(searchQuery.toLowerCase()) && 
          !item.description?.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      
      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'name') return a.name.localeCompare(b.name);
      if (sortBy === 'recent') return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
      if (sortBy === 'type') return a.type.localeCompare(b.type);
      return 0;
    });

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
            Building Blocks
          </h1>
          <p className="text-muted-foreground">
            재사용 가능한 구성 요소와 AI 에이전트 라이브러리
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleCreateBlock}>
            <Plus className="mr-2 h-4 w-4" />
            Block 생성
          </Button>
          <Button onClick={handleCreateAgent}>
            <Plus className="mr-2 h-4 w-4" />
            Agent 생성
          </Button>
        </div>
      </div>

      {/* Tabs for Categories */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="all">전체</TabsTrigger>
          <TabsTrigger value="agents">AI Agents</TabsTrigger>
          <TabsTrigger value="llm">LLM Blocks</TabsTrigger>
          <TabsTrigger value="tool">Tool Blocks</TabsTrigger>
          <TabsTrigger value="logic">Logic Blocks</TabsTrigger>
          <TabsTrigger value="composite">Composite</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="space-y-4">
          {/* Search and Filter */}
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Building Blocks 검색..."
                  className="pl-10"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="정렬 기준" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="name">이름순</SelectItem>
                <SelectItem value="recent">최근 업데이트</SelectItem>
                <SelectItem value="type">유형별</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">{buildingBlocks.length}</div>
                <p className="text-xs text-muted-foreground">전체 Building Blocks</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold text-purple-600">{agents.length}</div>
                <p className="text-xs text-muted-foreground">AI Agents</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold text-blue-600">{blocks.length}</div>
                <p className="text-xs text-muted-foreground">Basic Blocks</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold text-green-600">
                  {buildingBlocks.filter(b => b.is_public).length}
                </div>
                <p className="text-xs text-muted-foreground">공개 Components</p>
              </CardContent>
            </Card>
          </div>
          {/* Building Blocks Grid */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[...Array(6)].map((_, i) => (
                <Card key={i}>
                  <CardHeader>
                    <Skeleton className="h-6 w-3/4" />
                    <Skeleton className="h-4 w-1/2" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-16 w-full" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-purple-100 to-blue-100 dark:from-purple-900/20 dark:to-blue-900/20 rounded-full blur-3xl opacity-60" />
                <div className="relative">
                  {activeTab === 'agents' ? (
                    <Bot className="h-12 w-12 text-purple-500 mx-auto mb-4" />
                  ) : (
                    <Box className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  )}
                </div>
              </div>
              <h3 className="text-lg font-semibold mb-2">
                {searchQuery ? '검색 결과가 없습니다' : 
                 activeTab === 'agents' ? 'AI Agent가 없습니다' : 'Building Block이 없습니다'}
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                {searchQuery ? '검색어를 조정해보세요' : 
                 activeTab === 'agents' ? '첫 번째 AI Agent를 생성해보세요' : '첫 번째 Building Block을 생성해보세요'}
              </p>
              {!searchQuery && (
                <div className="flex gap-2">
                  {activeTab !== 'agents' && (
                    <Button variant="outline" onClick={handleCreateBlock}>
                      <Plus className="mr-2 h-4 w-4" />
                      Block 생성
                    </Button>
                  )}
                  {activeTab !== 'blocks' && (
                    <Button onClick={handleCreateAgent}>
                      <Plus className="mr-2 h-4 w-4" />
                      Agent 생성
                    </Button>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredItems.map((item) => (
                <Card key={`${item.type}-${item.id}`} className="hover:shadow-lg transition-all duration-300 group">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        {getItemIcon(item)}
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <CardTitle className="text-base">{item.name}</CardTitle>
                            <Badge variant="outline" className="text-xs">
                              {item.type === 'agent' ? 'Agent' : 'Block'}
                            </Badge>
                          </div>
                          <CardDescription className="text-xs capitalize">
                            {item.category}
                          </CardDescription>
                        </div>
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="opacity-0 group-hover:opacity-100 transition-opacity">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleEdit(item)}>
                            <Edit className="mr-2 h-4 w-4" />
                            편집
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleTest(item)}>
                            <Play className="mr-2 h-4 w-4" />
                            테스트
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleDuplicate(item)}>
                            <Copy className="mr-2 h-4 w-4" />
                            복제
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem 
                            onClick={() => handleDelete(item)}
                            className="text-destructive"
                          >
                            <Trash className="mr-2 h-4 w-4" />
                            삭제
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                      {item.description || '설명이 없습니다'}
                    </p>
                    
                    {/* Type-specific badges */}
                    <div className="flex flex-wrap gap-2">
                      {item.type === 'agent' ? (
                        <>
                          {item.llm_provider && (
                            <Badge variant="secondary" className={`text-xs ${getProviderBadge(item.llm_provider)}`}>
                              {item.llm_provider}
                            </Badge>
                          )}
                          {item.capabilities && item.capabilities.length > 0 && (
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Badge variant="outline" className="text-xs">
                                    <Brain className="mr-1 h-3 w-3" />
                                    {item.capabilities.length} 기능
                                  </Badge>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <div className="max-w-xs">
                                    <p className="font-medium mb-1">기능:</p>
                                    <ul className="text-xs space-y-1">
                                      {item.capabilities.slice(0, 3).map((cap, idx) => (
                                        <li key={idx}>• {cap}</li>
                                      ))}
                                      {item.capabilities.length > 3 && (
                                        <li>• +{item.capabilities.length - 3}개 더</li>
                                      )}
                                    </ul>
                                  </div>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          )}
                          {item.tools && item.tools.length > 0 && (
                            <Badge variant="outline" className="text-xs">
                              <Settings2 className="mr-1 h-3 w-3" />
                              {item.tools.length} 도구
                            </Badge>
                          )}
                        </>
                      ) : (
                        <>
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Badge variant="outline" className="text-xs">
                                  <ArrowDownToLine className="mr-1 h-3 w-3" />
                                  {item.input_schema?.properties ? 
                                    Object.keys(item.input_schema.properties).length : 0
                                  } 입력
                                </Badge>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>입력 매개변수 수</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                          
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Badge variant="outline" className="text-xs">
                                  <ArrowUpFromLine className="mr-1 h-3 w-3" />
                                  {item.output_schema?.properties ? 
                                    Object.keys(item.output_schema.properties).length : 0
                                  } 출력
                                </Badge>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>출력 매개변수 수</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </>
                      )}
                      
                      {item.is_public && (
                        <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">
                          공개
                        </Badge>
                      )}
                    </div>
                  </CardContent>
                  <CardFooter className="flex justify-between text-xs text-muted-foreground">
                    <span>v{item.version || '1.0.0'}</span>
                    <span>{formatDate(item.updated_at)}</span>
                  </CardFooter>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}